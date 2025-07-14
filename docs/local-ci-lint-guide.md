# Local CI Lint Guide

This guide ensures your local development environment runs the same lint checks as GitHub CI.

## The Problem

GitHub CI runs multiple lint checks that may not be caught by pre-commit hooks alone:
- Different Python versions (3.11 in CI)
- Different command-line arguments
- Additional tools like yamllint
- Context validation that fails on template files

## The Solution

### 1. Quick Check - Use Make

```bash
# Run all CI lint checks locally
make lint

# Run just pre-commit hooks
make lint-quick

# Run just context validation
make lint-context
```

### 2. Install All Required Tools

```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install pre-commit yamllint

# Install pre-commit hooks
pre-commit install
```

### 3. CI Lint Commands Reference

These are the exact commands GitHub CI runs:

```bash
# Black formatting check
black --check src/ tests/ scripts/

# isort import sorting
isort --check-only --profile black src/ tests/ scripts/

# Flake8 linting
flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503

# MyPy type checking (src only)
mypy src/ --config-file=mypy.ini

# Context YAML validation
python -m src.agents.context_lint validate context/

# Import checking
python -m pytest --collect-only -q
```

### 4. Common Issues and Solutions

#### Issue: Template files fail validation
**Solution**: Don't commit template files with placeholder values (e.g., `sprint-template.yaml`)

#### Issue: Line length violations
**Solution**: Run `black .` to auto-format before committing

#### Issue: Import order violations
**Solution**: Run `isort .` to auto-fix imports

#### Issue: Type errors in tests
**Solution**: MyPy on tests is allowed to fail in CI, focus on src/ type errors

### 5. Pre-Push Checklist

Before pushing to GitHub:

1. Run `make lint` to catch all CI issues
2. Fix any failures
3. Run `pre-commit run --all-files` as a final check
4. Push your changes

### 6. Differences Between Local and CI

| Check | Local (pre-commit) | CI (GitHub Actions) |
|-------|-------------------|---------------------|
| Python Version | Your local version | 3.11 only |
| Black | ✓ | ✓ |
| isort | ✓ | ✓ |
| Flake8 | ✓ | ✓ |
| MyPy | src/ only | src/ (required), tests/ (optional) |
| YAML lint | Only changed files | All context files |
| Import check | Only on test changes | Always |

### 7. VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=100", "--extend-ignore=E203,W503"],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## 8. Docker-Based CI Testing (Recommended)

Run the exact CI environment locally using Docker:

```bash
# Run all CI checks in Docker (exactly like GitHub Actions)
./scripts/run-ci-docker.sh

# Run specific checks
./scripts/run-ci-docker.sh black     # Black formatting only
./scripts/run-ci-docker.sh flake8    # Flake8 linting only
./scripts/run-ci-docker.sh mypy      # Type checking only

# Interactive debugging
./scripts/run-ci-docker.sh debug     # Opens bash shell in CI environment

# Build/rebuild the CI image
./scripts/run-ci-docker.sh build
```

### Why Use Docker?

1. **Exact CI Match**: Uses the same Python 3.11 environment as GitHub Actions
2. **No Local Setup**: No need to install Python 3.11 or dependencies locally
3. **Isolation**: Doesn't interfere with your local Python environment
4. **Consistency**: Everyone gets the same results regardless of their OS

### Docker Commands Reference

```bash
# Run all checks (default)
docker-compose -f docker-compose.ci.yml run --rm ci-lint

# Run individual checks
docker-compose -f docker-compose.ci.yml run --rm ci-black
docker-compose -f docker-compose.ci.yml run --rm ci-isort
docker-compose -f docker-compose.ci.yml run --rm ci-flake8
docker-compose -f docker-compose.ci.yml run --rm ci-mypy
docker-compose -f docker-compose.ci.yml run --rm ci-context-lint
docker-compose -f docker-compose.ci.yml run --rm ci-import-check

# Debug interactively
docker-compose -f docker-compose.ci.yml run --rm ci-debug
```

## Summary

Three ways to run CI checks locally:
1. **Quick**: `make lint` - Uses your local Python
2. **Docker**: `./scripts/run-ci-docker.sh` - Exact CI environment match
3. **Manual**: Run individual commands from section 3

For the most accurate results matching GitHub CI, use the Docker method!
