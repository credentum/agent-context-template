#!/bin/bash
# Quick CI-like test for specific test files

set -e

echo "=== Quick CI Test - Specific Files ==="
echo

# Use existing venv or create new one
if [ -d ".venv_ci_test" ]; then
    echo "Using existing CI test environment..."
    source .venv_ci_test/bin/activate
else
    echo "Creating clean virtual environment..."
    python3 -m venv .venv_ci_test
    source .venv_ci_test/bin/activate

    echo "Installing dependencies..."
    python -m pip install --upgrade pip >/dev/null 2>&1
    pip install -r requirements.txt >/dev/null 2>&1
    pip install -r requirements-test.txt >/dev/null 2>&1
fi

# Create required directories
mkdir -p context/{trace,archive,logs/{cleanup,eval,kv,prompts,signatures}}
mkdir -p context/{.duckdb,.graph_cache,.vector_cache,mcp_contracts}

# Run specific test files
TEST_FILES=${1:-"tests/test_edge_cases.py tests/test_hash_diff_embedder.py tests/test_chaos_engineering.py"}

echo "Running tests: $TEST_FILES"
echo

python -m pytest $TEST_FILES -v --tb=short -x

deactivate
