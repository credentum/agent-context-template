# CI Testing Guide

## Problem
Local tests pass but fail in CI due to environment differences and configuration mismatches.

## Root Causes
1. **Linting scope mismatch**: CI runs `black` and `mypy` on ALL files, but local pre-commit only runs on `src/`
2. **Different Python environments**: Local might have different package versions
3. **Missing dependencies**: CI installs from multiple requirements files
4. **Directory structure**: CI creates specific directories that tests might expect

## Solutions

### Quick Solution: Use the CI Test Script
```bash
# Run all tests exactly like CI does
./scripts/test-like-ci.sh
```

This script runs:
- Black formatting check on all files
- MyPy type checking on all files
- Flake8 linting on all files
- Context validation
- Unit tests with coverage

### Docker Solution: Perfect CI Environment Match
```bash
# Build the CI environment
docker-compose -f docker-compose.ci.yml build

# Run CI tests in Docker
docker-compose -f docker-compose.ci.yml run --rm ci-test

# Or run interactively for debugging
docker-compose -f docker-compose.ci.yml run --rm ci-debug
```

### Pre-commit Solution: Match CI Configuration
```bash
# Use the CI-matching pre-commit config
pre-commit run --all-files -c .pre-commit-config-ci.yaml
```

## Recommended Workflow

1. **Before pushing any PR**:
   ```bash
   # Option 1: Quick local check
   ./scripts/test-like-ci.sh

   # Option 2: Full CI simulation with Docker
   docker-compose -f docker-compose.ci.yml run --rm ci-test
   ```

2. **For debugging CI failures**:
   ```bash
   # Run interactive Docker session
   docker-compose -f docker-compose.ci.yml run --rm ci-debug

   # Inside container, run specific tests
   black --check --diff .
   mypy . --config-file mypy.ini
   flake8 . --max-line-length=100 --extend-ignore=E203,W503
   ```

3. **Update pre-commit hooks**:
   ```bash
   # Compare configs
   diff .pre-commit-config.yaml .pre-commit-config-ci.yaml

   # Consider updating main config to match CI
   cp .pre-commit-config-ci.yaml .pre-commit-config.yaml
   ```

## Key Differences to Remember

| Check | Local Pre-commit | CI |
|-------|-----------------|-----|
| Black | src/ only | All files (.) |
| MyPy | src/ only | All files (.) |
| Flake8 | src/ only | All files (.) |
| Tests | Not run | Full pytest suite |

## Troubleshooting

### Black failures
```bash
# Auto-fix formatting
black .
```

### MyPy failures
```bash
# Check specific file
mypy path/to/file.py --config-file mypy.ini

# Add type ignores if needed
# type: ignore[error-code]
```

### Flake8 failures
```bash
# Check specific file
flake8 path/to/file.py --max-line-length=100 --extend-ignore=E203,W503

# Common fixes:
# - Remove unused imports
# - Break long lines
# - Fix whitespace issues
```

## CI Configuration Files

- `.github/workflows/context-lint.yml` - Runs linting checks
- `.github/workflows/test.yml` - Runs unit tests
- `.github/workflows/test-suite.yml` - Runs comprehensive test suite
- `scripts/test-like-ci.sh` - Local CI simulation
- `Dockerfile.ci` - CI environment container
- `docker-compose.ci.yml` - Docker composition for CI testing
