#!/bin/bash
set -e

echo "🧪 Testing GitHub CI Workflows Locally"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed_checks=0
total_checks=0

run_check() {
    local test_name="$1"
    local command="$2"

    total_checks=$((total_checks + 1))
    echo ""
    echo -e "${YELLOW}🔍 Testing: $test_name${NC}"
    echo "Command: $command"
    echo "----------------------------------------"

    if eval "$command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        failed_checks=$((failed_checks + 1))
    fi
}

echo ""
echo "🚀 1. LINTING CHECKS (from test.yml and lint workflows)"
echo "======================================================"

run_check "Black formatting" "black --check src/ tests/ scripts/"
run_check "isort import sorting" "isort --check-only --profile black src/ tests/ scripts/"
run_check "Flake8 linting" "flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503"
run_check "MyPy type checking (src/)" "mypy src/ --config-file=mypy.ini"
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/"

echo ""
echo "🧪 2. UNIT TESTS (from test.yml)"
echo "==============================="

run_check "Unit tests with coverage" "python -m pytest tests/ -v --tb=short -m 'not integration and not e2e' --cov=src --cov-report=term-missing --timeout=60 --timeout-method=thread"

echo ""
echo "🔬 3. MUTATION TESTING (from test-suite.yml)"
echo "==========================================="

# Check if mutmut commands work
run_check "Mutmut basic command" "mutmut --help > /dev/null"
run_check "Mutmut results command" "mutmut results --help > /dev/null"

# Test the actual commands from the workflow
echo "Testing mutmut commands from test-suite.yml:"
echo "mutmut results > /tmp/mutation-report.txt || true"
mutmut results > /tmp/mutation-report.txt || true

echo "mutmut results --all true > /tmp/mutation-detailed-report.txt || true"
mutmut results --all true > /tmp/mutation-detailed-report.txt || true

if [ -f /tmp/mutation-report.txt ] && [ -f /tmp/mutation-detailed-report.txt ]; then
    echo -e "${GREEN}✅ PASSED: Mutation testing commands${NC}"
else
    echo -e "${RED}❌ FAILED: Mutation testing commands${NC}"
    failed_checks=$((failed_checks + 1))
fi
total_checks=$((total_checks + 1))

echo ""
echo "📊 4. COVERAGE ANALYSIS (from claude-code-review.yml)"
echo "===================================================="

# Test the exact coverage command from ARC-Reviewer
echo "Running ARC-Reviewer coverage analysis..."
pytest tests/ --cov=src --cov-report=term --cov-report=json -m "not integration and not e2e" > /tmp/coverage_output.txt 2>&1 || true

if [ -f coverage.json ]; then
    coverage_pct=$(python -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])" 2>/dev/null || echo "0")
    echo "Coverage detected: $coverage_pct%"

    if (( $(echo "$coverage_pct >= 78.89" | bc -l) )); then
        echo -e "${GREEN}✅ PASSED: Coverage meets baseline ($coverage_pct% >= 78.89%)${NC}"
    else
        echo -e "${RED}❌ FAILED: Coverage below baseline ($coverage_pct% < 78.89%)${NC}"
        failed_checks=$((failed_checks + 1))
    fi
else
    echo -e "${RED}❌ FAILED: coverage.json not generated${NC}"
    failed_checks=$((failed_checks + 1))
fi
total_checks=$((total_checks + 1))

echo ""
echo "📋 5. SUMMARY"
echo "============="
passed_checks=$((total_checks - failed_checks))
echo "Total checks: $total_checks"
echo -e "Passed: ${GREEN}$passed_checks${NC}"
echo -e "Failed: ${RED}$failed_checks${NC}"

if [ $failed_checks -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! Your code should pass GitHub CI.${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 $failed_checks CHECK(S) FAILED! Fix these issues before pushing.${NC}"
    echo ""
    echo "To debug individual failures, run the failed commands manually."
    exit 1
fi
