#!/bin/bash
# test-unit-like-ci.sh - Run unit tests exactly like GitHub Actions
# This matches .github/workflows/test.yml exactly

set -e  # Exit on error

echo "🧪 Running Unit Tests (exactly like GitHub Actions)"
echo "=================================================="
echo "Matching: .github/workflows/test.yml"
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

echo "📋 UNIT TEST WORKFLOW"
echo "--------------------"

# Create directories (from test.yml lines 52-65)
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
echo -e "  ${GREEN}✓ PASSED${NC}"

# From test.yml lines 67-71
run_check "Unit tests with coverage" "python -m pytest tests/ -v --tb=short -m \"not integration and not e2e\" --cov=src --cov-report=term-missing --cov-report=xml --timeout=60 --timeout-method=thread -x"

# Summary
echo -e "\n========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All unit tests passed!${NC}"
    echo "Your code matches CI requirements and is safe to push."
    exit 0
else
    echo -e "${RED}❌ $FAILED unit test(s) failed${NC}"
    echo "Fix these issues before pushing to avoid CI failures."
    exit 1
fi
