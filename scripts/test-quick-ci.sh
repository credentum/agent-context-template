#!/bin/bash
# test-quick-ci.sh - Quick essential CI checks for Claude's 2-minute timeout
# Runs the most important checks that can complete quickly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Running Quick Essential CI Checks${NC}"
echo "=========================================="
echo "Optimized for Claude's 2-minute timeout"
echo

# Track start time
START_TIME=$(date +%s)

# Track failures
FAILED=0
TOTAL_CHECKS=0

# Function to run a command and check status
run_check() {
    local name=$1
    local cmd=$2
    local section=$3
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}[$section] $name${NC}"
    
    # Show progress indicator
    echo -n "  Running... "
    
    if eval "$cmd"; then
        echo -e "\r  ${GREEN}✓ PASSED${NC}    "
    else
        echo -e "\r  ${RED}✗ FAILED${NC}    "
        FAILED=$((FAILED + 1))
    fi
}

# Section 1: Pre-commit hooks (includes most other checks)
echo -e "\n${YELLOW}📋 SECTION 1: PRE-COMMIT HOOKS${NC}"
echo "================================"
echo "Running pre-commit hooks first as they include formatting checks..."
run_check "Pre-commit hooks" "/bin/bash scripts/run-precommit-ci-safe.sh" "1/4"

# Section 2: Quick MyPy check (with fix for duplicate modules)
echo -e "\n${YELLOW}📋 SECTION 2: TYPE CHECKING${NC}"
echo "=========================="
echo "Running MyPy with explicit package bases..."
run_check "MyPy type checking" "mypy src/ --config-file=mypy.ini --explicit-package-bases" "2/4"

# Section 3: Context validation
echo -e "\n${YELLOW}📋 SECTION 3: CONTEXT VALIDATION${NC}"
echo "==============================="
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/" "3/4"

# Section 4: Import check
echo -e "\n${YELLOW}📋 SECTION 4: IMPORT CHECK${NC}"
echo "========================="
run_check "Import verification" "python -m pytest --collect-only -q" "4/4"

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}QUICK CI CHECK SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL $TOTAL_CHECKS CHECKS PASSED!${NC}"
    echo -e "${GREEN}Completed in $ELAPSED seconds${NC}"
    echo
    echo "✅ Pre-commit hooks: PASSED"
    echo "✅ Type checking: PASSED"
    echo "✅ Context validation: PASSED"
    echo "✅ Import check: PASSED"
    echo
    echo "🚀 Your code passed essential checks!"
    exit 0
else
    echo -e "${RED}❌ $FAILED out of $TOTAL_CHECKS checks failed${NC}"
    echo -e "${YELLOW}Completed in $ELAPSED seconds${NC}"
    echo
    echo "Quick fixes:"
    echo "  - Run: pre-commit run --all-files"
    echo "  - Check MyPy errors and add type annotations"
    echo "  - Validate YAML files in context/"
    echo
    exit 1
fi