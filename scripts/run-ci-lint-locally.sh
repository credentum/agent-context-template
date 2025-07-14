#!/bin/bash
# This script runs all the same lint checks that GitHub CI runs
# to ensure local and CI environments are identical

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Running GitHub CI Lint Checks Locally"
echo "========================================"

# Track failures
FAILED_CHECKS=()

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    echo -e "\n${YELLOW}Running: ${name}${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ ${name} passed${NC}"
    else
        echo -e "${RED}✗ ${name} failed${NC}"
        FAILED_CHECKS+=("$name")
    fi
}

# 1. Black formatting check
run_check "Black" "black --check src/ tests/ scripts/"

# 2. isort import sorting
run_check "isort" "isort --check-only --profile black src/ tests/ scripts/"

# 3. Flake8 linting
run_check "Flake8" "flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503"

# 4. MyPy type checking on src/
run_check "MyPy (src)" "mypy src/ --config-file=mypy.ini"

# 5. MyPy type checking on tests/ (allowed to fail in CI)
echo -e "\n${YELLOW}Running: MyPy (tests) - allowed to fail${NC}"
mypy tests/ --config-file=mypy.ini || echo -e "${YELLOW}⚠ MyPy tests check failed (this is allowed in CI)${NC}"

# 6. YAML linting (allowed to fail in CI)
if command -v yamllint &> /dev/null; then
    echo -e "\n${YELLOW}Running: yamllint - allowed to fail${NC}"
    yamllint context/ -d "{extends: default, rules: {line-length: {max: 120}}, ignore: 'context/schemas/'}" || echo -e "${YELLOW}⚠ YAML lint failed (this is allowed in CI)${NC}"
else
    echo -e "${YELLOW}⚠ yamllint not installed - skipping (install with: pip install yamllint)${NC}"
fi

# 7. Context YAML validation
run_check "Context Lint" "python -m src.agents.context_lint validate context/"

# 8. Check imports
run_check "Import Check" "python -m pytest --collect-only -q"

# 9. Pre-commit hooks (additional check)
if [ -f .pre-commit-config.yaml ]; then
    echo -e "\n${YELLOW}Running: pre-commit hooks${NC}"
    if pre-commit run --all-files; then
        echo -e "${GREEN}✓ pre-commit hooks passed${NC}"
    else
        echo -e "${RED}✗ pre-commit hooks failed${NC}"
        FAILED_CHECKS+=("pre-commit")
    fi
fi

# Summary
echo -e "\n========================================"
if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Failed checks:${NC}"
    for check in "${FAILED_CHECKS[@]}"; do
        echo -e "  - $check"
    done
    exit 1
fi
