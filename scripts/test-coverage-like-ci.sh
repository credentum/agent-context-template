#!/bin/bash
# test-coverage-like-ci.sh - Run coverage tests exactly like GitHub CI does
# This matches .github/workflows/test-coverage.yml exactly

set -e  # Exit on error

echo "🚀 Running Coverage Tests (exactly like GitHub Actions)"
echo "======================================================"
echo "Matching: .github/workflows/test-coverage.yml"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Debug environment details
echo -e "\n${YELLOW}🔍 Environment debugging information:${NC}"
echo "Python version: $(python --version)"
echo "pip version: $(pip --version)"
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "CI environment: $CI"
echo "Cache version: $CACHE_VERSION"
echo "Redis host: $REDIS_HOST"
echo "Redis port: $REDIS_PORT"
echo "Available tools:"
which python pip pytest coverage mutmut || echo "Some tools not found"
echo -e "${GREEN}✅ Environment debugging complete${NC}\n"

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

echo "📋 COVERAGE ANALYSIS WORKFLOW"
echo "----------------------------"

# Verify all required tools are available
echo -e "${YELLOW}🔍 Verifying all required tools are available:${NC}"
for tool in python pytest coverage mutmut; do
    if which $tool > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ $tool: $(which $tool)${NC}"
    else
        echo -e "  ${RED}✗ $tool: NOT FOUND${NC}"
        FAILED=$((FAILED + 1))
    fi
done
echo

# Create test-artifacts directory if it doesn't exist
mkdir -p test-artifacts

# From test-coverage.yml lines 62-74
export REDIS_HOST=localhost
export REDIS_PORT=6379
run_check "Run tests with coverage" "python -m pytest --cov=src --cov-branch --cov-report=term-missing:skip-covered --cov-report=xml:test-artifacts/coverage.xml --cov-report=json:test-artifacts/coverage.json -v"

# From test-coverage.yml lines 76-78
run_check "Check coverage thresholds" "python scripts/coverage_summary.py"

# From test-coverage.yml lines 80-83
# Get threshold from centralized config
THRESHOLD=$(python scripts/get_coverage_threshold.py)
run_check "Enforce coverage thresholds" "python -m coverage report --fail-under=$THRESHOLD"

# From test-coverage.yml lines 85-88 (allowed to fail)
echo -e "\n${YELLOW}▶ Check mutation testing baseline - allowed to fail${NC}"
echo "  Command: python scripts/check_mutation_baseline.py"
if python scripts/check_mutation_baseline.py; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
else
    echo -e "  ${YELLOW}⚠ FAILED (allowed in CI)${NC}"
fi

# From test-coverage.yml lines 90-107 (allowed to fail)
echo -e "\n${YELLOW}▶ Run mutation testing (sample) - allowed to fail${NC}"
export MUTMUT_PATHS="src/validators/kv_validators.py src/storage/context_kv.py"
echo "  Command: Run mutation testing on configurable modules"
for path in $MUTMUT_PATHS; do
    if [ -f "$path" ]; then
        echo "    Running mutation testing on $path"
        # Note: mutmut doesn't have --paths-to-mutate, using configured paths from pyproject.toml
        mutmut run --max-children 2 || true
    else
        echo "    Path $path not found, skipping"
    fi
done
mutmut results || true
echo -e "  ${YELLOW}⚠ ALLOWED TO FAIL (continue-on-error: true)${NC}"

# Generate coverage badge
echo -e "\n${YELLOW}▶ Generate coverage badge${NC}"
echo "  Command: coverage-badge -o coverage.svg -f"
if coverage-badge -o coverage.svg -f; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
else
    echo -e "  ${YELLOW}⚠ FAILED (badge generation)${NC}"
fi

# Verify test traceability
run_check "Verify test traceability" "python -m pytest tests/test_traceability_matrix.py -v"

# Summary
echo -e "\n========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All coverage tests passed!${NC}"
    echo "Your code meets coverage requirements and is safe to push."
    exit 0
else
    echo -e "${RED}❌ $FAILED coverage check(s) failed${NC}"
    echo "Fix these issues before pushing to avoid CI failures."
    echo -e "\nTips:"
    echo "  - Add tests to increase line coverage above 80%"
    echo "  - Focus on uncovered lines shown in coverage report"
    echo "  - Check coverage.json for detailed module breakdown"
    exit 1
fi
