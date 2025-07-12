# Development Setup Guide

This guide explains how to set up automated linting and testing before committing code.

## Quick Start

```bash
# Install all dependencies including pre-commit
make install

# Set up pre-commit hooks
make dev-setup

# The hooks will now run automatically on git commit!
```

## Manual Testing Before Commit

If you want to run all checks manually before committing:

```bash
# Run all quality checks at once
make pre-commit

# Or run individual checks:
make format-check  # Check Black formatting
make lint         # Run context lint
make type-check   # Run mypy
make test         # Run tests
```

## Pre-commit Hooks

The project uses [pre-commit](https://pre-commit.com/) to automatically run checks before each commit. The following hooks are configured:

### On Every Commit
- **Black** - Python code formatter
- **trailing-whitespace** - Removes trailing whitespace
- **end-of-file-fixer** - Ensures files end with a newline
- **check-yaml** - Validates YAML syntax
- **check-json** - Validates JSON syntax
- **check-merge-conflict** - Checks for merge conflict markers
- **debug-statements** - Checks for debugger imports
- **mypy** - Static type checking
- **isort** - Import sorting
- **context-lint** - Validates context YAML files

### Running Pre-commit Manually

```bash
# Run on all files
pre-commit run --all-files

# Run on specific files
pre-commit run --files path/to/file.py

# Run a specific hook
pre-commit run black --all-files
```

## Bypassing Hooks (Emergency Only)

If you absolutely need to commit without running hooks:

```bash
git commit --no-verify -m "Emergency fix"
```

**Note:** This should be used sparingly. The CI will still run these checks!

## Troubleshooting

### Pre-commit not installed
```bash
pip install pre-commit
pre-commit install
```

### Black formatting issues
```bash
# Auto-fix formatting
make format
# or
black .
```

### Mypy type errors
```bash
# Run mypy with details
mypy . --config-file mypy.ini
```

### Context lint errors
```bash
# Validate context files
python -m src.agents.context_lint validate context/
```

## VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true
}
```

## GitHub Actions

All these checks also run in CI on every PR. See:
- `.github/workflows/context-lint.yml` - Runs linting and formatting checks
- `.github/workflows/test.yml` - Runs the test suite
