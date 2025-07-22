#!/bin/bash
# claude-test-changed.sh - Smart test runner for Claude Code CLI
# Detects changed files and runs only relevant tests with coverage

set -euo pipefail

# Default values
RUN_ALL=false
DRY_RUN=false
VERBOSE=false
OUTPUT_FORMAT="json"
BASE_BRANCH="main"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage function
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Smart test runner that detects changed files and runs only relevant tests.

OPTIONS:
    --all               Run full test suite instead of smart detection
    --dry-run          Show what tests would be run without executing
    --verbose          Show detailed output
    --format FORMAT    Output format: json (default), text, quiet
    --base BRANCH      Base branch for comparison (default: main)
    -h, --help         Show this help message

EXAMPLES:
    $(basename "$0")                    # Run tests for changed files
    $(basename "$0") --all              # Run full test suite
    $(basename "$0") --dry-run          # Show what tests would be run
    $(basename "$0") --format text      # Human-readable output

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --base)
            BASE_BRANCH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Function to log verbose messages
log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1" >&2
    fi
}

# Function to detect changed files
detect_changed_files() {
    local changed_files=()

    # Get uncommitted changes (staged and unstaged)
    if git diff --name-only --diff-filter=ACMR > /dev/null 2>&1; then
        mapfile -t unstaged < <(git diff --name-only --diff-filter=ACMR)
        mapfile -t staged < <(git diff --cached --name-only --diff-filter=ACMR)

        # Combine and deduplicate
        for file in "${unstaged[@]}" "${staged[@]}"; do
            if [[ " ${changed_files[@]} " != *" ${file} "* ]]; then
                changed_files+=("$file")
            fi
        done
    fi

    # Get changes compared to base branch
    if git diff --name-only "$BASE_BRANCH"...HEAD --diff-filter=ACMR > /dev/null 2>&1; then
        mapfile -t branch_changes < <(git diff --name-only "$BASE_BRANCH"...HEAD --diff-filter=ACMR)

        # Add branch changes
        for file in "${branch_changes[@]}"; do
            if [[ " ${changed_files[@]} " != *" ${file} "* ]]; then
                changed_files+=("$file")
            fi
        done
    fi

    # Filter only Python files
    local python_files=()
    for file in "${changed_files[@]}"; do
        if [[ "$file" == *.py ]]; then
            python_files+=("$file")
        fi
    done

    printf '%s\n' "${python_files[@]}"
}

# Function to map source file to test files
map_source_to_tests() {
    local source_file="$1"
    local test_files=()

    # Skip if already a test file
    if [[ "$source_file" == tests/* ]] || [[ "$source_file" == *test*.py ]]; then
        echo "$source_file"
        return
    fi

    # Extract module path from source file
    local module_path="${source_file#src/}"
    local module_name="${module_path%.py}"
    local module_basename=$(basename "$module_name")
    local module_dir=$(dirname "$module_name")

    log_verbose "Mapping source file: $source_file"
    log_verbose "Module path: $module_path, Module name: $module_name"

    # Pattern 1: Direct test file mapping (tests/test_module.py)
    local test_pattern1="tests/test_${module_basename}.py"
    if [[ -f "$test_pattern1" ]]; then
        test_files+=("$test_pattern1")
        log_verbose "Found direct test mapping: $test_pattern1"
    fi

    # Pattern 2: Module directory test file (tests/module_dir/test_module.py)
    if [[ "$module_dir" != "." ]]; then
        local test_pattern2="tests/${module_dir}/test_${module_basename}.py"
        if [[ -f "$test_pattern2" ]]; then
            test_files+=("$test_pattern2")
            log_verbose "Found module directory test: $test_pattern2"
        fi

        # Pattern 3: Test directory matching source structure
        local test_pattern3="tests/test_${module_dir}.py"
        if [[ -f "$test_pattern3" ]]; then
            test_files+=("$test_pattern3")
            log_verbose "Found test directory file: $test_pattern3"
        fi
    fi

    # Pattern 4: Search for files that import this module
    local module_import="${module_name//\//.}"
    log_verbose "Searching for imports of: $module_import"

    # Find test files that import this module
    if command -v rg >/dev/null 2>&1; then
        mapfile -t import_tests < <(rg -l "from src\.${module_import} import|import src\.${module_import}" tests/ 2>/dev/null || true)
    else
        mapfile -t import_tests < <(grep -r -l "from src\.${module_import} import\|import src\.${module_import}" tests/ 2>/dev/null || true)
    fi

    for test in "${import_tests[@]}"; do
        if [[ " ${test_files[@]} " != *" ${test} "* ]]; then
            test_files+=("$test")
            log_verbose "Found test importing module: $test"
        fi
    done

    # Output unique test files
    printf '%s\n' "${test_files[@]}" | sort -u
}

# Function to run pytest with coverage
run_tests() {
    local test_files=("$@")
    local pytest_args=()
    local coverage_modules=()

    # Build pytest arguments
    if [[ ${#test_files[@]} -gt 0 ]]; then
        pytest_args+=("${test_files[@]}")

        # Calculate coverage modules from changed source files
        for file in "${CHANGED_FILES[@]}"; do
            if [[ "$file" == src/*.py ]] && [[ "$file" != src/__init__.py ]]; then
                local module="${file#src/}"
                module="${module%.py}"
                module="src.${module//\//.}"
                coverage_modules+=("$module")
            fi
        done

        # Add coverage arguments if we have specific modules
        if [[ ${#coverage_modules[@]} -gt 0 ]]; then
            local cov_modules=$(IFS=,; echo "${coverage_modules[*]}")
            pytest_args+=("--cov=$cov_modules")
        else
            pytest_args+=("--cov=src")
        fi
    else
        # Run all tests
        pytest_args+=("--cov=src")
    fi

    # Add common pytest arguments
    pytest_args+=("--cov-report=term-missing")
    pytest_args+=("--tb=short")
    pytest_args+=("-v")

    # Run pytest
    log_verbose "Running: pytest ${pytest_args[*]}"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "Would run: pytest ${pytest_args[*]}"
        return 0
    fi

    # Capture pytest output
    local pytest_output
    local pytest_exit_code

    pytest_output=$(pytest "${pytest_args[@]}" 2>&1) || pytest_exit_code=$?

    # Parse results
    local tests_passed=0
    local tests_failed=0
    local tests_skipped=0
    local coverage_percentage=0
    local duration="0s"

    # Extract test results
    if echo "$pytest_output" | grep -q "passed"; then
        tests_passed=$(echo "$pytest_output" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+" | head -1)
    fi
    if echo "$pytest_output" | grep -q "failed"; then
        tests_failed=$(echo "$pytest_output" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+" | head -1)
    fi
    if echo "$pytest_output" | grep -q "skipped"; then
        tests_skipped=$(echo "$pytest_output" | grep -oE "[0-9]+ skipped" | grep -oE "[0-9]+" | head -1)
    fi

    # Extract coverage
    if echo "$pytest_output" | grep -q "TOTAL"; then
        coverage_percentage=$(echo "$pytest_output" | grep "TOTAL" | awk '{print $(NF-1)}' | tr -d '%')
    fi

    # Extract duration
    if echo "$pytest_output" | grep -q "in [0-9]"; then
        duration=$(echo "$pytest_output" | grep -oE "in [0-9]+\.[0-9]+s" | grep -oE "[0-9]+\.[0-9]+s")
    fi

    # Store results for output
    TEST_RESULTS_JSON=$(cat <<EOF
{
  "test_results": {
    "passed": ${tests_passed:-0},
    "failed": ${tests_failed:-0},
    "skipped": ${tests_skipped:-0},
    "exit_code": ${pytest_exit_code:-0}
  },
  "coverage": {
    "percentage": ${coverage_percentage:-0},
    "modules": [$(printf '"%s",' "${coverage_modules[@]}" | sed 's/,$//')],
    "report": "Run with --verbose to see full coverage report"
  },
  "duration": "${duration}",
  "recommendation": "$(get_recommendation $tests_failed $coverage_percentage)"
}
EOF
)

    # Show full output in verbose mode
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "\n${BLUE}=== Full pytest output ===${NC}"
        echo "$pytest_output"
        echo -e "${BLUE}=== End pytest output ===${NC}\n"
    fi

    return ${pytest_exit_code:-0}
}

# Function to get recommendation
get_recommendation() {
    local failed=$1
    local coverage=$2

    if [[ $failed -gt 0 ]]; then
        echo "Tests failed! Fix failing tests before proceeding."
    elif [[ $coverage -lt 70 ]]; then
        echo "Coverage is low. Consider adding more tests."
    elif [[ $coverage -lt 80 ]]; then
        echo "All tests passed. Coverage is acceptable but could be improved."
    else
        echo "All tests passed. Coverage is good."
    fi
}

# Function to output results
output_results() {
    local changed_files=("${CHANGED_FILES[@]}")
    local test_files=("${TEST_FILES[@]}")

    case "$OUTPUT_FORMAT" in
        json)
            cat <<EOF
{
  "files_changed": [$(printf '"%s",' "${changed_files[@]}" | sed 's/,$//')],
  "tests_run": [$(printf '"%s",' "${test_files[@]}" | sed 's/,$//')],
  $(echo "$TEST_RESULTS_JSON" | tail -n +2)
EOF
            ;;
        text)
            echo -e "\n${GREEN}Smart Test Runner Results${NC}"
            echo -e "${BLUE}=========================${NC}"
            echo -e "\nFiles changed: ${#changed_files[@]}"
            for file in "${changed_files[@]}"; do
                echo "  - $file"
            done

            echo -e "\nTests run: ${#test_files[@]}"
            for test in "${test_files[@]}"; do
                echo "  - $test"
            done

            # Parse JSON results for text output
            local passed=$(echo "$TEST_RESULTS_JSON" | grep -oE '"passed": [0-9]+' | grep -oE '[0-9]+')
            local failed=$(echo "$TEST_RESULTS_JSON" | grep -oE '"failed": [0-9]+' | grep -oE '[0-9]+')
            local skipped=$(echo "$TEST_RESULTS_JSON" | grep -oE '"skipped": [0-9]+' | grep -oE '[0-9]+')
            local coverage=$(echo "$TEST_RESULTS_JSON" | grep -oE '"percentage": [0-9]+' | grep -oE '[0-9]+')
            local duration=$(echo "$TEST_RESULTS_JSON" | grep -oE '"duration": "[^"]*"' | cut -d'"' -f4)
            local recommendation=$(echo "$TEST_RESULTS_JSON" | grep -oE '"recommendation": "[^"]*"' | cut -d'"' -f4)

            echo -e "\nTest Results:"
            echo -e "  ${GREEN}Passed: $passed${NC}"
            [[ $failed -gt 0 ]] && echo -e "  ${RED}Failed: $failed${NC}" || echo -e "  Failed: 0"
            echo -e "  Skipped: $skipped"
            echo -e "\nCoverage: ${coverage}%"
            echo -e "Duration: $duration"
            echo -e "\n${YELLOW}Recommendation:${NC} $recommendation"
            ;;
        quiet)
            # Just exit with appropriate code
            ;;
    esac
}

# Main execution
main() {
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo -e "${RED}Error: Not in a git repository${NC}" >&2
        exit 1
    fi

    # Run full test suite if requested
    if [[ "$RUN_ALL" == "true" ]]; then
        log_verbose "Running full test suite"
        CHANGED_FILES=()
        TEST_FILES=()

        if [[ "$DRY_RUN" == "true" ]]; then
            echo "Would run full test suite: pytest --cov=src --cov-report=term-missing"
            exit 0
        fi

        run_tests
        TEST_RESULTS_JSON=$(echo "$TEST_RESULTS_JSON" | sed 's/"files_changed": \[\]/"files_changed": ["all"]/')
        TEST_RESULTS_JSON=$(echo "$TEST_RESULTS_JSON" | sed 's/"tests_run": \[\]/"tests_run": ["all"]/')
        output_results
        exit $?
    fi

    # Detect changed files
    log_verbose "Detecting changed files..."
    mapfile -t CHANGED_FILES < <(detect_changed_files)

    if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            cat <<EOF
{
  "files_changed": [],
  "tests_run": [],
  "message": "No Python files changed",
  "recommendation": "No tests needed"
}
EOF
        else
            echo -e "${YELLOW}No Python files changed. No tests to run.${NC}"
        fi
        exit 0
    fi

    log_verbose "Found ${#CHANGED_FILES[@]} changed Python files"

    # Map changed files to test files
    TEST_FILES=()
    for file in "${CHANGED_FILES[@]}"; do
        mapfile -t mapped_tests < <(map_source_to_tests "$file")
        for test in "${mapped_tests[@]}"; do
            if [[ " ${TEST_FILES[@]} " != *" ${test} "* ]] && [[ -f "$test" ]]; then
                TEST_FILES+=("$test")
            fi
        done
    done

    if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            cat <<EOF
{
  "files_changed": [$(printf '"%s",' "${CHANGED_FILES[@]}" | sed 's/,$//')],
  "tests_run": [],
  "message": "No test files found for changed files",
  "recommendation": "Consider adding tests for these files"
}
EOF
        else
            echo -e "${YELLOW}No test files found for changed files.${NC}"
            echo "Changed files:"
            for file in "${CHANGED_FILES[@]}"; do
                echo "  - $file"
            done
            echo -e "\n${YELLOW}Recommendation:${NC} Consider adding tests for these files"
        fi
        exit 0
    fi

    log_verbose "Found ${#TEST_FILES[@]} test files to run"

    # Run tests
    if run_tests "${TEST_FILES[@]}"; then
        output_results
        exit 0
    else
        output_results
        exit 1
    fi
}

# Run main function
main
