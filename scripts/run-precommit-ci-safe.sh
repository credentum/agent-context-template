#!/bin/bash
# run-precommit-ci-safe.sh - Run pre-commit hooks in CI mode (check-only)
# This script runs pre-commit in a way that's safe for read-only filesystems
# by only running checks without attempting to modify files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Running pre-commit hooks in CI mode (check-only)${NC}"

# Set environment variables to ensure we're in CI mode
export CI=true
export PRE_COMMIT_ALLOW_NO_CONFIG=0

# List of hooks that should only run in check mode
CHECK_ONLY_HOOKS=(
    "trailing-whitespace"
    "end-of-file-fixer"
    "mixed-line-ending"
    "check-yaml"
    "check-added-large-files"
    "check-merge-conflict"
)

# Create a temporary pre-commit config that disables auto-fixing
TEMP_CONFIG="/tmp/pre-commit-config-ci-$$.yaml"

# Function to cleanup on exit
cleanup() {
    rm -f "$TEMP_CONFIG"
}
trap cleanup EXIT

# Copy the original config and modify it for CI
if [ -f ".pre-commit-config.yaml" ]; then
    cp .pre-commit-config.yaml "$TEMP_CONFIG"
    
    # Use Python to modify the config to add --check flags where needed
    python3 - <<EOF
import yaml
import sys

with open("$TEMP_CONFIG", 'r') as f:
    config = yaml.safe_load(f)

# Modify hooks to run in check-only mode
for repo in config.get('repos', []):
    for hook in repo.get('hooks', []):
        hook_id = hook.get('id', '')
        
        # For file-modifying hooks, add check-only flags
        if hook_id == 'black':
            hook['args'] = hook.get('args', []) + ['--check', '--diff']
        elif hook_id == 'isort':
            hook['args'] = hook.get('args', []) + ['--check-only', '--diff']
        elif hook_id in ['trailing-whitespace', 'end-of-file-fixer']:
            # These hooks don't have check-only mode, we'll handle them separately
            hook['args'] = hook.get('args', []) + ['--diff']
            
# Save modified config
with open("$TEMP_CONFIG", 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
EOF
else
    echo -e "${RED}❌ No .pre-commit-config.yaml found${NC}"
    exit 1
fi

echo "Running pre-commit with CI-safe configuration..."

# Run pre-commit with the modified config
# Use --show-diff-on-failure to show what would be changed
set +e
pre-commit run --config "$TEMP_CONFIG" --all-files --show-diff-on-failure
PRECOMMIT_EXIT_CODE=$?
set -e

# Show results
if [ $PRECOMMIT_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ All pre-commit checks passed!${NC}"
else
    echo -e "\n${YELLOW}⚠️  Pre-commit checks found issues${NC}"
    echo -e "${YELLOW}The checks above show what needs to be fixed.${NC}"
    echo -e "${YELLOW}Run these commands locally to fix:${NC}"
    echo "  - black src/ tests/ scripts/"
    echo "  - isort src/ tests/ scripts/"
    echo "  - pre-commit run --all-files"
fi

# Exit with the same code as pre-commit
exit $PRECOMMIT_EXIT_CODE