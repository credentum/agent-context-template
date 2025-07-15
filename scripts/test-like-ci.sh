#!/bin/bash
# test-like-ci.sh - Run tests exactly like CI does
# This matches .github/workflows/lint-verification.yml exactly

set -e  # Exit on error

echo "🚀 Running CI Lint Checks (exactly like GitHub Actions)"
echo "======================================================"
echo "Matching: .github/workflows/lint-verification.yml"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run a command and check status
run_check() {
    local name=$1
    local cmd=$2
    echo -e "\n${YELLOW}▶ $name${NC}"
    echo "  Command: $cmd"
    if eval "$cmd"; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "📋 LINT VERIFICATION WORKFLOW"
echo "----------------------------"

# From lint-verification.yml lines 43-45
run_check "Black formatting" "black --check src/ tests/ scripts/"

# From lint-verification.yml lines 47-49
run_check "isort import sorting" "isort --check-only --profile black src/ tests/ scripts/"

# From lint-verification.yml lines 51-53
run_check "Flake8 linting" "flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503"

# From lint-verification.yml lines 55-57
run_check "MyPy type checking (src/)" "mypy src/ --config-file=mypy.ini"

# From lint-verification.yml lines 59-62 (allowed to fail)
echo -e "\n${YELLOW}▶ MyPy type checking (tests/) - allowed to fail${NC}"
echo "  Command: mypy tests/ --config-file=mypy.ini"
if mypy tests/ --config-file=mypy.ini; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
else
    echo -e "  ${YELLOW}⚠ FAILED (allowed in CI)${NC}"
fi

# From lint-verification.yml lines 69-71
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/"

# From lint-verification.yml lines 73-75
run_check "Import check" "python -m pytest --collect-only -q"

# Additional: GitHub Actions workflow validation
echo -e "\n${YELLOW}▶ GitHub Actions workflow validation${NC}"
echo "  Command: yamllint -c .yamllint-workflows.yml .github/workflows/"
if yamllint -c .yamllint-workflows.yml .github/workflows/; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
else
    echo -e "  ${YELLOW}⚠ WARNINGS (this is expected for complex workflows)${NC}"
    # Don't fail the build for workflow yamllint issues
fi

# Summary
echo -e "\n========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All CI lint checks passed!${NC}"
    echo "Your code matches CI requirements and is safe to push."
    exit 0
else
    echo -e "${RED}❌ $FAILED CI check(s) failed${NC}"
    echo "Fix these issues before pushing to avoid CI failures."
    echo -e "\nTips:"
    echo "  - Run 'black src/ tests/ scripts/' to auto-format code"
    echo "  - Run 'isort src/ tests/ scripts/' to fix import order"
    echo "  - Check flake8 errors and fix manually"
    exit 1
fi
