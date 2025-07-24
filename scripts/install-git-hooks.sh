#!/bin/bash
# Git Hooks Installer for CI Migration Phase 3
# This script installs enhanced git hooks that run local CI before push

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$SCRIPT_DIR/..")"

echo -e "${BLUE}==== Git Hooks Installer for CI Migration ====${NC}"
echo

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
HOOKS_DIR="$REPO_ROOT/.git/hooks"
CUSTOM_HOOKS_DIR="$REPO_ROOT/.git-hooks"

mkdir -p "$HOOKS_DIR"
mkdir -p "$CUSTOM_HOOKS_DIR"

# Function to backup existing hooks
backup_hook() {
    local hook_name=$1
    local hook_path="$HOOKS_DIR/$hook_name"

    if [ -f "$hook_path" ] && [ ! -L "$hook_path" ]; then
        local backup_path="${hook_path}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}Backing up existing $hook_name to $(basename "$backup_path")${NC}"
        cp "$hook_path" "$backup_path"
    fi
}

# Function to install a hook
install_hook() {
    local hook_name=$1
    local source_path="$CUSTOM_HOOKS_DIR/$hook_name"
    local target_path="$HOOKS_DIR/$hook_name"

    # Backup existing hook
    backup_hook "$hook_name"

    # Create symbolic link
    echo -e "${GREEN}Installing $hook_name hook${NC}"
    ln -sf "$source_path" "$target_path"
    chmod +x "$source_path"
}

# Create the enhanced pre-push hook
echo -e "${BLUE}Creating enhanced pre-push hook...${NC}"
cat > "$CUSTOM_HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Enhanced pre-push hook for CI Migration Phase 3
# Runs local CI checks before allowing push to remote

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get repository root
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Check for bypass flags
if [ "$SKIP_CI" = "1" ] || [ "$CI_BYPASS" = "1" ] || [ "$SKIP_HOOKS" = "1" ]; then
    echo -e "${YELLOW}⚠️  CI checks bypassed via environment variable${NC}"
    exit 0
fi

# Check for --no-verify flag (handled by git)
# This is automatic - if user runs `git push --no-verify`, this hook won't run

echo -e "${BLUE}🚀 Running pre-push CI checks...${NC}"
echo

# Function to run with timeout and progress
run_with_progress() {
    local cmd=$1
    local description=$2
    local timeout=${3:-300}  # Default 5 minutes

    echo -ne "${BLUE}▶ $description...${NC}"

    # Run command with timeout
    if timeout "$timeout" bash -c "$cmd" > /tmp/ci-output.log 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        local exit_code=$?
        echo -e " ${RED}✗${NC}"

        if [ $exit_code -eq 124 ]; then
            echo -e "${RED}Command timed out after ${timeout}s${NC}"
        else
            echo -e "${RED}Command failed with exit code $exit_code${NC}"
        fi

        # Show last 20 lines of output
        echo -e "${YELLOW}Last 20 lines of output:${NC}"
        tail -20 /tmp/ci-output.log

        return $exit_code
    fi
}

# Check if LFS is needed (preserve existing LFS functionality)
if command -v git-lfs >/dev/null 2>&1; then
    echo -e "${BLUE}▶ Running Git LFS pre-push...${NC}"
    git lfs pre-push "$@" || {
        echo -e "${RED}Git LFS pre-push failed${NC}"
        exit 1
    }
fi

# Check if claude-ci.sh exists
if [ ! -f "$REPO_ROOT/scripts/claude-ci.sh" ]; then
    echo -e "${YELLOW}⚠️  claude-ci.sh not found, skipping CI checks${NC}"
    echo -e "${YELLOW}   (This is expected if you haven't set up the CI migration yet)${NC}"
    exit 0
fi

# Get the branch being pushed
while read local_ref local_sha remote_ref remote_sha; do
    # Extract branch name
    branch_name=$(echo "$local_ref" | sed 's|refs/heads/||')

    echo -e "${BLUE}Checking branch: $branch_name${NC}"

    # Skip CI for certain branches if needed
    if [[ "$branch_name" =~ ^(wip|tmp|temp)/ ]]; then
        echo -e "${YELLOW}Skipping CI for temporary branch${NC}"
        continue
    fi

    # Run quick CI checks
    echo -e "${BLUE}Running CI checks before push...${NC}"

    # 1. Quick validation (30 seconds timeout)
    if ! run_with_progress "$REPO_ROOT/scripts/claude-ci.sh all --quick --output json > /tmp/ci-quick.json" "Quick validation" 30; then
        echo -e "${RED}❌ Quick validation failed${NC}"
        echo -e "${YELLOW}Fix issues or bypass with: SKIP_CI=1 git push${NC}"
        exit 1
    fi

    # 2. Check for critical issues in quick validation
    if [ -f /tmp/ci-quick.json ]; then
        critical_issues=$(jq -r '.critical_issues // 0' /tmp/ci-quick.json 2>/dev/null || echo "0")
        if [ "$critical_issues" != "0" ]; then
            echo -e "${RED}❌ Found $critical_issues critical issues${NC}"
            jq -r '.issues[] | "  - \(.severity): \(.message)"' /tmp/ci-quick.json 2>/dev/null || true
            echo -e "${YELLOW}Fix issues or bypass with: SKIP_CI=1 git push${NC}"
            exit 1
        fi
    fi

    # 3. If pushing to main or release branches, run comprehensive checks
    if [[ "$remote_ref" =~ ^refs/heads/(main|master|release/.*)$ ]]; then
        echo -e "${YELLOW}⚠️  Pushing to protected branch, running comprehensive checks...${NC}"

        if ! run_with_progress "$REPO_ROOT/scripts/claude-ci.sh all --comprehensive --output json > /tmp/ci-comprehensive.json" "Comprehensive validation" 600; then
            echo -e "${RED}❌ Comprehensive validation failed${NC}"
            echo -e "${YELLOW}Fix issues or bypass with: SKIP_CI=1 git push${NC}"
            exit 1
        fi
    fi
done

echo -e "${GREEN}✅ All pre-push checks passed!${NC}"
echo

# Show push command
echo -e "${BLUE}Proceeding with push...${NC}"

# Clean up temp files
rm -f /tmp/ci-output.log /tmp/ci-quick.json /tmp/ci-comprehensive.json

exit 0
EOF

# Make the hook executable
chmod +x "$CUSTOM_HOOKS_DIR/pre-push"

# Install the hook
install_hook "pre-push"

# Create a simple pre-commit hook for quick checks
echo -e "${BLUE}Creating pre-commit hook...${NC}"
cat > "$CUSTOM_HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for basic validation
# Runs quick format checks before commit

set -e

# Colors
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check for bypass
if [ "$SKIP_HOOKS" = "1" ]; then
    exit 0
fi

echo -e "${BLUE}Running pre-commit checks...${NC}"

# Run pre-commit if available
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --all-files || {
        echo -e "${YELLOW}Pre-commit checks failed. Fix issues and try again.${NC}"
        exit 1
    }
fi

exit 0
EOF

chmod +x "$CUSTOM_HOOKS_DIR/pre-commit"
install_hook "pre-commit"

# Create configuration file
CONFIG_FILE="$REPO_ROOT/.git-hooks/config"
echo -e "${BLUE}Creating hooks configuration...${NC}"
cat > "$CONFIG_FILE" << 'EOF'
# Git Hooks Configuration for CI Migration
# Created: $(date)

# Bypass options:
# - SKIP_CI=1 git push         # Skip CI checks only
# - SKIP_HOOKS=1 git push      # Skip all hooks
# - git push --no-verify       # Skip all hooks (git native)

# Timeout settings (seconds)
QUICK_TIMEOUT=30
COMPREHENSIVE_TIMEOUT=600

# Branch patterns to skip CI
SKIP_CI_BRANCHES="^(wip|tmp|temp)/"

# Protected branches requiring comprehensive checks
PROTECTED_BRANCHES="^(main|master|release/.*)$"
EOF

echo
echo -e "${GREEN}✅ Git hooks installed successfully!${NC}"
echo
echo -e "${BLUE}Installed hooks:${NC}"
echo "  - pre-push: Runs CI checks before push"
echo "  - pre-commit: Runs format checks before commit"
echo
echo -e "${BLUE}Configuration:${NC}"
echo "  - Config file: .git-hooks/config"
echo "  - Hooks directory: .git-hooks/"
echo
echo -e "${BLUE}Bypass options:${NC}"
echo "  - ${YELLOW}SKIP_CI=1 git push${NC} - Skip CI checks only"
echo "  - ${YELLOW}SKIP_HOOKS=1 git push${NC} - Skip all hooks"
echo "  - ${YELLOW}git push --no-verify${NC} - Skip all hooks"
echo
echo -e "${BLUE}To uninstall:${NC}"
echo "  - Remove symbolic links from .git/hooks/"
echo "  - Restore from .git/hooks/*.backup.* if needed"
echo
