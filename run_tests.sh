#!/bin/bash
# Test runner for the Agent-First Context System

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo -e "\n=== Running Directory Structure Tests ==="
pytest tests/test_directory_structure.py -v

echo -e "\n=== Running Config Parser Tests ==="
pytest tests/test_config_parser.py -v

echo -e "\n=== Running Context Lint Tests ==="
pytest tests/test_context_lint.py -v

echo -e "\n=== Running Context Lint Validation ==="
python context_lint.py check-config --verbose
python context_lint.py validate context/ --verbose

echo -e "\n=== Running Cleanup Agent (Dry Run) ==="
python cleanup_agent.py --dry-run --verbose

echo -e "\n=== All tests passed! ===""