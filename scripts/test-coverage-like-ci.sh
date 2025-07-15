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

# From test-coverage.yml lines 62-74
echo -e "\n${YELLOW}▶ Run tests with coverage${NC}"
echo "  Command: python -m pytest --cov=src --cov-branch --cov-report=term-missing:skip-covered --cov-report=html --cov-report=xml --cov-report=json -v"
export REDIS_HOST=localhost
export REDIS_PORT=6379
if python -m pytest --cov=src --cov-branch --cov-report=term-missing:skip-covered --cov-report=html --cov-report=xml --cov-report=json -v; then
    echo -e "  ${GREEN}✓ PASSED${NC}"
else
    echo -e "  ${RED}✗ FAILED${NC}"
    FAILED=$((FAILED + 1))
fi

# From test-coverage.yml lines 76-78
run_check "Check coverage thresholds" "python scripts/coverage_summary.py"

# From test-coverage.yml lines 80-83
run_check "Enforce coverage thresholds" "python -m coverage report --fail-under=80"

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
