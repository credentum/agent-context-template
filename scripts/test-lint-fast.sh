#!/bin/bash
# test-lint-fast.sh - Fast formatting checks only
# Runs Black, isort, and Flake8 in parallel for speed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Running Fast Formatting Checks${NC}"
echo "===================================="
echo "Black, isort, and Flake8 in parallel"
echo

# Track failures
declare -A CHECK_STATUS
declare -A CHECK_OUTPUT

# Function to run check in background
run_background_check() {
    local name=$1
    local cmd=$2
    local output_file="/tmp/ci-check-$name.out"

    echo -e "${BLUE}▶ Starting $name...${NC}"

    # Run command in background and capture output
    (
        if eval "$cmd" > "$output_file" 2>&1; then
            echo "PASSED" > "/tmp/ci-check-$name.status"
        else
            echo "FAILED" > "/tmp/ci-check-$name.status"
        fi
    ) &
}

# Start all checks in parallel
run_background_check "black" "black --check src/ tests/ scripts/"
run_background_check "isort" "isort --check-only --profile black src/ tests/ scripts/"
run_background_check "flake8" "flake8 src/ tests/ scripts/"

# Wait for all background jobs to complete
echo -e "\n${YELLOW}Waiting for checks to complete...${NC}"
wait

# Collect results
FAILED=0
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}FORMATTING CHECK RESULTS${NC}"
echo -e "${BLUE}========================================${NC}"

for check in black isort flake8; do
    status=$(cat "/tmp/ci-check-$check.status" 2>/dev/null || echo "UNKNOWN")

    if [ "$status" = "PASSED" ]; then
        echo -e "✅ $check: ${GREEN}PASSED${NC}"
    else
        echo -e "❌ $check: ${RED}FAILED${NC}"
        FAILED=$((FAILED + 1))

        # Show output for failed checks
        if [ -f "/tmp/ci-check-$check.out" ]; then
            echo -e "${YELLOW}Output from $check:${NC}"
            cat "/tmp/ci-check-$check.out" | head -20
            echo
        fi
    fi

    # Clean up temp files
    rm -f "/tmp/ci-check-$check.status" "/tmp/ci-check-$check.out"
done

# Summary
echo -e "\n${BLUE}========================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All formatting checks passed!${NC}"
    echo
    echo "Quick reference:"
    echo "  - Black: Code formatting"
    echo "  - isort: Import sorting"
    echo "  - Flake8: Style guide enforcement"
    exit 0
else
    echo -e "${RED}❌ $FAILED formatting checks failed${NC}"
    echo
    echo "Quick fixes:"
    echo "  - Format code: black src/ tests/ scripts/"
    echo "  - Sort imports: isort --profile black src/ tests/ scripts/"
    echo "  - Check Flake8 errors above and fix manually"
    exit 1
fi
