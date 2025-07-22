#!/bin/bash
# Test script for claude-test-changed.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"

    echo -n "Testing: $test_name ... "

    if eval "$test_command"; then
        if [[ "$expected_result" == "pass" ]]; then
            echo -e "${GREEN}PASSED${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAILED${NC} (expected to fail)"
            ((TESTS_FAILED++))
        fi
    else
        if [[ "$expected_result" == "fail" ]]; then
            echo -e "${GREEN}PASSED${NC} (correctly failed)"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}FAILED${NC}"
            ((TESTS_FAILED++))
        fi
    fi
}

# Test script location
SCRIPT_PATH="$(dirname "$0")/../../scripts/claude-test-changed.sh"

echo -e "${YELLOW}Running tests for claude-test-changed.sh${NC}\n"

# Test 1: Script exists and is executable
run_test "Script exists and is executable" "[[ -x $SCRIPT_PATH ]]" "pass"

# Test 2: Help option works
run_test "Help option" "$SCRIPT_PATH --help 2>&1 | grep -q 'Smart test runner'" "pass"

# Test 3: Dry run option
run_test "Dry run option" "$SCRIPT_PATH --dry-run 2>&1 | grep -q 'Would run'" "pass"

# Test 4: JSON output format (default)
run_test "JSON output format" "$SCRIPT_PATH --dry-run 2>&1 | grep -q '\"files_changed\"'" "pass"

# Test 5: Text output format
run_test "Text output format" "$SCRIPT_PATH --dry-run --format text 2>&1 | grep -q 'Smart Test Runner Results'" "pass"

# Test 6: All tests option
run_test "All tests option" "$SCRIPT_PATH --all --dry-run 2>&1 | grep -q 'full test suite'" "pass"

# Test 7: Invalid option handling
run_test "Invalid option handling" "$SCRIPT_PATH --invalid-option 2>&1 | grep -q 'Unknown option'" "pass"

# Test 8: Verbose mode
run_test "Verbose mode" "$SCRIPT_PATH --verbose --dry-run 2>&1 | grep -q '\[VERBOSE\]'" "pass"

# Test 9: Base branch option
run_test "Base branch option" "$SCRIPT_PATH --base develop --dry-run >/dev/null 2>&1" "pass"

# Test 10: Shellcheck validation
if command -v shellcheck >/dev/null 2>&1; then
    run_test "Shellcheck validation" "shellcheck $SCRIPT_PATH" "pass"
else
    echo -e "Skipping: Shellcheck validation ... ${YELLOW}SKIPPED${NC} (shellcheck not installed)"
fi

# Test 11: JSON output structure validation
if command -v jq >/dev/null 2>&1; then
    run_test "JSON output validation" "$SCRIPT_PATH --dry-run 2>/dev/null | jq -e '.files_changed' >/dev/null" "pass"
else
    echo -e "Skipping: JSON output validation ... ${YELLOW}SKIPPED${NC} (jq not installed)"
fi

echo -e "\n${YELLOW}Test Summary:${NC}"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "  Failed: 0"
fi

# Exit with appropriate code
if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi
