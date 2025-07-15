#!/bin/bash
# test-suite-like-ci.sh - Run full test suite exactly like GitHub Actions
# This matches .github/workflows/test-suite.yml exactly

set -e  # Exit on error

echo "🧪 Running Full Test Suite (exactly like GitHub Actions)"
echo "======================================================="
echo "Matching: .github/workflows/test-suite.yml"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run a command and check status (allows continue-on-error)
run_check() {
    local name=$1
    local cmd=$2
    local allow_failure=${3:-false}
    echo -e "\n${YELLOW}▶ $name${NC}"
    echo "  Command: $cmd"
    if eval "$cmd"; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        return 0
    else
        if [ "$allow_failure" = "true" ]; then
            echo -e "  ${YELLOW}⚠ FAILED (allowed in CI)${NC}"
        else
            echo -e "  ${RED}✗ FAILED${NC}"
            FAILED=$((FAILED + 1))
        fi
        return 1
    fi
}

echo "📋 FULL TEST SUITE WORKFLOW"
echo "---------------------------"

# Create directories (from test-suite.yml lines 44-55)
echo -e "\n${YELLOW}▶ Creating test directories${NC}"
mkdir -p context/.duckdb
mkdir -p context/.graph_cache
mkdir -p context/.vector_cache
mkdir -p context/.embeddings_cache
mkdir -p context/trace
mkdir -p context/archive
mkdir -p context/mcp_contracts
mkdir -p context/logs/cleanup
mkdir -p context/logs/eval
mkdir -p context/logs/kv
mkdir -p context/logs/prompts
mkdir -p context/logs/signatures
mkdir -p test-results
echo -e "  ${GREEN}✓ PASSED${NC}"

# From test-suite.yml unit tests (continue-on-error: true)
run_check "Unit tests" "pytest tests/ -m \"not integration and not e2e and not slow\" --junit-xml=test-results/junit-unit.xml --cov=src --cov-branch --cov-report=xml:coverage-unit.xml --cov-report=html:htmlcov-unit --cov-report=term" true

# From test-suite.yml integration tests (continue-on-error: true)
run_check "Integration tests" "pytest tests/ -m \"integration\" --junit-xml=test-results/junit-integration.xml --cov=src --cov-branch --cov-append --cov-report=xml:coverage-integration.xml --cov-report=html:htmlcov-integration --cov-report=term" true

# From test-suite.yml performance benchmarks (continue-on-error: true)
run_check "Performance benchmarks" "pytest tests/ -m \"benchmark\" --junit-xml=test-results/junit-benchmark.xml --benchmark-only --benchmark-json=benchmark-results.json" true

# From test-suite.yml mutation tests (continue-on-error: true)
run_check "Mutation tests" "mutmut run --paths-to-mutate=src/ --tests-dir=tests/ --runner=\"pytest -x\" --use-coverage" true

# Summary
echo -e "\n========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical tests passed!${NC}"
    echo "Your code matches CI requirements and is safe to push."
    exit 0
else
    echo -e "${RED}❌ $FAILED critical test(s) failed${NC}"
    echo "Fix these issues before pushing to avoid CI failures."
    exit 1
fi
