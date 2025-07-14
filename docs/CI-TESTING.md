# CI Testing Guide

This guide explains how to run GitHub CI tests locally to catch issues before pushing.

## Quick Start

```bash
# Docker method (recommended - exact CI match)
./scripts/run-ci-docker.sh

# Make method (uses local Python)
make lint

# Direct script method
./scripts/test-like-ci.sh
```

## Why Local CI Testing?

GitHub CI runs specific lint checks that might not be caught by pre-commit hooks:
- Uses Python 3.11 specifically
- Runs additional validation on context YAML files
- Has specific command-line arguments for each tool
- Validates imports can be collected

## Methods

### 1. Docker Method (Recommended)

Runs the exact same environment as GitHub Actions:

```bash
# Run all CI checks
./scripts/run-ci-docker.sh

# Run specific checks
./scripts/run-ci-docker.sh black
./scripts/run-ci-docker.sh flake8
./scripts/run-ci-docker.sh mypy
./scripts/run-ci-docker.sh context

# Debug interactively
./scripts/run-ci-docker.sh debug

# Rebuild after requirements change
./scripts/run-ci-docker.sh build
```

**Advantages:**
- Exact match to GitHub CI environment
- Uses Python 3.11 like CI
- No local setup required
- Isolated from your system

### 2. Make Method

Uses your local Python environment:

```bash
# Run all lint checks
make lint

# Run specific types
make lint-quick      # Just pre-commit
make lint-context    # Just context validation
make lint-docker     # Use Docker (same as method 1)
```

### 3. Direct Script Method

```bash
# Run the CI simulation script
./scripts/test-like-ci.sh
```

## CI Checks Performed

1. **Black** - Code formatting (line length 100)
2. **isort** - Import sorting (black profile)
3. **Flake8** - Linting (E203,W503 ignored)
4. **MyPy** - Type checking (src/ only)
5. **Context Lint** - YAML validation
6. **Import Check** - Ensure tests can be collected

## Common Issues

### Black/isort Failures
```bash
# Auto-fix formatting
black src/ tests/ scripts/
isort src/ tests/ scripts/
```

### Context Validation Failures
- Don't commit template files with placeholders
- Ensure all YAML files have valid schema

### Line Length Issues
- Keep lines under 100 characters
- Black will auto-fix most cases

## Pre-Push Workflow

1. Make your changes
2. Run `./scripts/run-ci-docker.sh`
3. Fix any issues
4. Commit and push

## Integration with pre-commit

The pre-commit hooks run automatically on commit, but CI has additional checks:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Troubleshooting

### Docker Issues
```bash
# Clean up containers
./scripts/run-ci-docker.sh clean

# Rebuild image
./scripts/run-ci-docker.sh build
```

### Python Version Mismatch
CI uses Python 3.11. If you have a different version locally, use the Docker method for accurate results.

### Missing Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-test.txt
```
