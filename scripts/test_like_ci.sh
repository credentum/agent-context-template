#!/bin/bash
# Test script that mimics CI environment

set -e  # Exit on error

echo "=== Testing like CI - Clean Environment ==="
echo

# Create a virtual environment to simulate clean CI
echo "1. Creating clean virtual environment..."
python3 -m venv .venv_ci_test
source .venv_ci_test/bin/activate

# Install dependencies exactly like CI workflows
echo "2. Installing dependencies (like test-suite.yml)..."
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-test.txt

# Create required directories (from test-suite.yml)
echo "3. Creating required directories..."
mkdir -p context/.duckdb
mkdir -p context/.graph_cache
mkdir -p context/.vector_cache
mkdir -p context/trace
mkdir -p context/archive
mkdir -p context/mcp_contracts
mkdir -p context/logs/cleanup
mkdir -p context/logs/eval
mkdir -p context/logs/kv
mkdir -p context/logs/prompts
mkdir -p context/logs/signatures

# Run unit tests like CI
echo "4. Running unit tests (like test-suite.yml)..."
python -m pytest tests/ -m "not integration and not e2e and not slow" \
    --junit-xml=test-results/junit-unit.xml \
    --cov=src --cov-branch \
    --cov-report=xml:coverage-unit.xml \
    --cov-report=term \
    -v --tb=short \
    || true  # Continue even if tests fail

# Show summary
echo
echo "=== Test Summary ==="
if [ -f coverage-unit.xml ]; then
    echo "Coverage report generated: coverage-unit.xml"
fi

# Cleanup
deactivate
echo
echo "To remove test environment: rm -rf .venv_ci_test"
echo "To see full pytest output, remove '--tb=short' from the pytest command"
