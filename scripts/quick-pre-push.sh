#!/bin/bash
# Quick Pre-Push Validation Script
# Faster alternative to full Docker CI for pre-push hooks

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
REPO_ROOT="$(git rev-parse --show-toplevel)"

echo -e "${BLUE}🚀 Quick Pre-Push Validation${NC}"
echo -e "${YELLOW}This runs essential checks in ~30 seconds${NC}"
echo

# Track overall status
OVERALL_STATUS=0

# Function to run a check
run_check() {
    local name=$1
    local command=$2

    echo -ne "${BLUE}▶ ${name}...${NC}"

    if eval "$command" > /tmp/quick-check.log 2>&1; then
        echo -e " ${GREEN}✓${NC}"
    else
        echo -e " ${RED}✗${NC}"
        echo -e "${YELLOW}  See /tmp/quick-check.log for details${NC}"
        OVERALL_STATUS=1
    fi
}

# 1. Check for syntax errors in Python files
run_check "Python syntax" "python -m py_compile \$(find src tests -name '*.py' -type f)"

# 2. Quick import check
run_check "Import check" "python -c 'import src'"

# 3. Check for obvious formatting issues (if black is available)
if command -v black >/dev/null 2>&1; then
    run_check "Black format (check only)" "black --check --quiet src tests"
fi

# 4. Basic linting with flake8 (if available)
if command -v flake8 >/dev/null 2>&1; then
    run_check "Flake8 (errors only)" "flake8 --select=E9,F63,F7,F82 --statistics src tests"
fi

# 5. Check YAML files
run_check "YAML syntax" "python -c \"
import yaml
import sys
from pathlib import Path

errors = []
for yaml_file in Path('.').rglob('*.yml'):
    if '.git' in yaml_file.parts:
        continue
    try:
        with open(yaml_file) as f:
            yaml.safe_load(f)
    except Exception as e:
        errors.append(f'{yaml_file}: {e}')

for yaml_file in Path('.').rglob('*.yaml'):
    if '.git' in yaml_file.parts:
        continue
    try:
        with open(yaml_file) as f:
            yaml.safe_load(f)
    except Exception as e:
        errors.append(f'{yaml_file}: {e}')

if errors:
    print('\\n'.join(errors))
    sys.exit(1)
\""

# 6. Check for merge conflicts
run_check "Merge conflict markers" "! grep -r '^<<<<<<< \\|^======= \\|^>>>>>>> ' --include='*.py' --include='*.yml' --include='*.yaml' src tests .github 2>/dev/null"

# 7. Check for large files
run_check "Large files (>1MB)" "! find . -type f -size +1M -not -path './.git/*' -not -path './.*' | grep ."

# 8. Quick test discovery (don't run, just check they can be collected)
if command -v pytest >/dev/null 2>&1; then
    run_check "Test collection" "pytest --collect-only -q > /dev/null"
fi

# 9. Check git status
echo
echo -e "${BLUE}📊 Git Status:${NC}"
CHANGED_FILES=$(git diff --name-only HEAD)
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$CHANGED_FILES" ] && [ -z "$STAGED_FILES" ]; then
    echo -e "${GREEN}  ✓ Working directory clean${NC}"
else
    if [ -n "$CHANGED_FILES" ]; then
        echo -e "${YELLOW}  ⚠️  Unstaged changes:${NC}"
        echo "$CHANGED_FILES" | sed 's/^/    /'
    fi
    if [ -n "$STAGED_FILES" ]; then
        echo -e "${BLUE}  📝 Staged changes:${NC}"
        echo "$STAGED_FILES" | sed 's/^/    /'
    fi
fi

# 10. Branch check
CURRENT_BRANCH=$(git branch --show-current)
echo
echo -e "${BLUE}🌿 Current branch:${NC} $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    echo -e "${RED}  ⚠️  WARNING: You're on the main branch!${NC}"
    OVERALL_STATUS=1
fi

# Summary
echo
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ All quick checks passed!${NC}"
    echo -e "${BLUE}Ready to push (full CI will run on GitHub)${NC}"
else
    echo -e "${RED}❌ Some checks failed!${NC}"
    echo -e "${YELLOW}Fix issues before pushing or use:${NC}"
    echo -e "${YELLOW}  SKIP_CI=1 git push  # Skip pre-push hooks${NC}"
    echo -e "${YELLOW}  git push --no-verify  # Skip all hooks${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Optional: Show timing
SCRIPT_END=$(date +%s)
SCRIPT_START=${SCRIPT_START:-$SCRIPT_END}
DURATION=$((SCRIPT_END - SCRIPT_START))

if [ $DURATION -gt 0 ]; then
    echo -e "${CYAN}Completed in ${DURATION} seconds${NC}"
fi

exit $OVERALL_STATUS
