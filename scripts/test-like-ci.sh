#!/bin/bash
# test-like-ci.sh - Run tests exactly like CI does

set -e  # Exit on error

echo "=== Running tests like CI ==="
echo "This script simulates the exact CI environment tests"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a command and check status
run_check() {
    local name=$1
    local cmd=$2
    echo -e "${YELLOW}Running: $name${NC}"
    echo "Command: $cmd"
    if eval "$cmd"; then
        echo -e "${GREEN}✓ $name passed${NC}\n"
        return 0
    else
        echo -e "${RED}✗ $name failed${NC}\n"
        return 1
    fi
}

# Track failures
FAILED=0

# 1. Black formatting check (like context-lint.yml:50)
if ! run_check "Black formatting" "black --check --diff ."; then
    FAILED=$((FAILED + 1))
    echo "Tip: Run 'black .' to auto-format"
fi

# 2. MyPy type checking (like context-lint.yml:54)
# Note: CI allows failures with || true, but we'll show them
echo -e "${YELLOW}Running: MyPy type checking${NC}"
echo "Command: mypy . --config-file mypy.ini"
if mypy . --config-file mypy.ini; then
    echo -e "${GREEN}✓ MyPy passed${NC}\n"
else
    echo -e "${YELLOW}⚠ MyPy has issues (CI allows these to fail)${NC}\n"
fi

# 3. Flake8 linting (checking if it's run in CI)
# Based on pre-commit config, but running on all files like CI would
if ! run_check "Flake8 linting" "flake8 . --max-line-length=100 --extend-ignore=E203,W503"; then
    FAILED=$((FAILED + 1))
fi

# 4. Context validation (like context-lint.yml:43)
if ! run_check "Context validation" "python -m src.agents.context_lint validate context/ --verbose"; then
    FAILED=$((FAILED + 1))
fi

# 5. Unit tests (like test.yml:68-70)
echo -e "${YELLOW}Running: Unit tests${NC}"
if pytest tests/ -v --tb=short -m "not integration and not e2e" \
    --cov=. --cov-report=term-missing --cov-report=xml \
    --timeout=60 --timeout-method=thread -x; then
    echo -e "${GREEN}✓ Unit tests passed${NC}\n"
else
    echo -e "${RED}✗ Unit tests failed${NC}\n"
    FAILED=$((FAILED + 1))
fi

# Summary
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! Safe to push.${NC}"
    exit 0
else
    echo -e "${RED}$FAILED check(s) failed. Fix these before pushing.${NC}"
    exit 1
fi
