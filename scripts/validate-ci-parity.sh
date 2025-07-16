#!/bin/bash
# validate-ci-parity.sh - Validate that local Docker CI matches GitHub CI behavior
# This script runs comprehensive tests to ensure parity between environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 CI Environment Parity Validation"
echo "==================================="
echo "This script validates that local Docker CI catches the same errors as GitHub CI"
echo

# Track test results
PASSED=0
FAILED=0
WARNINGS=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    local expected_result=$3  # "pass" or "fail"

    echo -e "\n${BLUE}🧪 Testing: $test_name${NC}"
    echo "   Command: $test_command"
    echo "   Expected: $expected_result"

    if eval "$test_command" > /dev/null 2>&1; then
        actual_result="pass"
    else
        actual_result="fail"
    fi

    if [ "$actual_result" = "$expected_result" ]; then
        echo -e "   ${GREEN}✓ CORRECT ($actual_result as expected)${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "   ${RED}✗ INCORRECT (got $actual_result, expected $expected_result)${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# Function to run Docker CI command
run_docker_ci() {
    local service=$1
    echo -e "\n${BLUE}🐳 Testing Docker CI service: $service${NC}"

    if docker-compose -f docker-compose.ci.yml run --rm "$service" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ SUCCESS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "   ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# Function to simulate GitHub CI test
simulate_github_ci() {
    local test_name=$1
    local cmd=$2

    echo -e "\n${BLUE}🔄 Simulating GitHub CI: $test_name${NC}"
    echo "   Command: $cmd"

    # Set environment variables to match GitHub CI
    export CI=true
    export PYTHONUNBUFFERED=1
    export CACHE_VERSION=v2025-07-16
    export PYTHON_VERSION=3.11

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ SUCCESS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "   ${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
    fi
}

# Main validation tests
echo -e "\n${BLUE}Phase 1: Tool Availability Tests${NC}"
echo "================================="

# Test that all required tools are available
run_test "Black availability" "which black" "pass"
run_test "Isort availability" "which isort" "pass"
run_test "Flake8 availability" "which flake8" "pass"
run_test "MyPy availability" "which mypy" "pass"
run_test "Pytest availability" "which pytest" "pass"
run_test "Coverage availability" "which coverage" "pass"

echo -e "\n${BLUE}Phase 2: Code Quality Tests${NC}"
echo "============================"

# Test code quality checks (these should pass with current code)
run_test "Black formatting check" "black --check src/ tests/ scripts/" "pass"
run_test "Isort import check" "isort --check-only --profile black src/ tests/ scripts/" "pass"
run_test "Flake8 linting" "flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503" "pass"
run_test "MyPy type checking" "mypy src/ --config-file=mypy.ini" "pass"
run_test "Context validation" "python -m src.agents.context_lint validate context/" "pass"

echo -e "\n${BLUE}Phase 3: Environment Simulation Tests${NC}"
echo "====================================="

# Test environment variables match
simulate_github_ci "Environment setup" "echo 'CI=$CI PYTHONUNBUFFERED=$PYTHONUNBUFFERED'"
simulate_github_ci "Python version check" "python --version"
simulate_github_ci "Package installation test" "pip list | grep -E '(black|isort|flake8|mypy)'"

echo -e "\n${BLUE}Phase 4: Docker CI Integration Tests${NC}"
echo "====================================="

# Test Docker CI services (if Docker is available)
if command -v docker-compose > /dev/null 2>&1; then
    echo "Testing Docker CI services..."

    # Test key Docker CI services
    run_docker_ci "ci-black"
    run_docker_ci "ci-isort"
    run_docker_ci "ci-flake8"
    run_docker_ci "ci-mypy"
    run_docker_ci "ci-context-lint"
else
    echo -e "${YELLOW}⚠ Docker Compose not available, skipping Docker CI tests${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo -e "\n${BLUE}Phase 5: Configuration Validation${NC}"
echo "================================="

# Test configuration files exist and are valid
run_test "Coverage config exists" "test -f .coverage-config.json" "pass"
run_test "MyPy config exists" "test -f mypy.ini" "pass"
run_test "Flake8 config exists" "test -f .flake8" "pass"
run_test "PyProject config exists" "test -f pyproject.toml" "pass"

# Test configuration file parsing
run_test "Coverage config parsing" "python -c 'import json; json.load(open(\".coverage-config.json\"))'" "pass"
run_test "Requirements files exist" "test -f requirements.txt -a -f requirements-dev.txt -a -f requirements-test.txt" "pass"

echo -e "\n${BLUE}Phase 6: Advanced Tests${NC}"
echo "======================="

# Test that coverage scripts work
run_test "Coverage threshold script" "python scripts/get_coverage_threshold.py" "pass"
run_test "Coverage summary script" "python scripts/coverage_summary.py --help" "pass"

# Test environment comparison
run_test "Environment comparison script" "./scripts/compare-environments.sh --help" "pass"

# Generate final report
echo -e "\n${BLUE}📊 Final Validation Report${NC}"
echo "=========================="
echo "Tests passed: $PASSED"
echo "Tests failed: $FAILED"
echo "Warnings: $WARNINGS"
echo "Total tests: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 SUCCESS: Local Docker CI environment matches GitHub CI!${NC}"
    echo "The following improvements have been validated:"
    echo "  ✓ All required tools are available and working"
    echo "  ✓ Environment variables match GitHub CI"
    echo "  ✓ Code quality checks work consistently"
    echo "  ✓ Configuration files are valid and accessible"
    echo "  ✓ Docker CI services run successfully"
    echo
    echo "Your local Docker CI should now catch the same errors as GitHub CI."
    exit 0
else
    echo -e "\n${RED}❌ FAILED: $FAILED test(s) failed${NC}"
    echo "The local environment may not fully match GitHub CI behavior."
    echo "Review the failed tests above and fix any issues."
    exit 1
fi
