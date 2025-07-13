# Code Quality Tools

This project uses automated code quality tools to maintain consistency and catch issues early.

## Tools

### Black (Code Formatter)
- Automatic Python code formatting
- Line length: 100 characters
- Target Python version: 3.11

### Mypy (Type Checker)
- Static type checking for Python
- Gradual typing adoption allowed
- Configuration in `mypy.ini`

## Usage

### Manual Commands
```bash
# Format all Python files
make format

# Check formatting without changing files
make format-check

# Run type checking
make type-check

# Run all quality checks
make pre-commit
```

### Pre-commit Hooks
Install pre-commit hooks to run automatically:
```bash
pip install pre-commit
pre-commit install
```

### GitHub Actions
Code quality checks run automatically on:
- Push to any branch
- Pull requests
- When Python files are modified

## Gradual Adoption

### Black
To format the entire codebase:
```bash
black .
```

### Mypy
Type checking is set to allow gradual adoption:
- `allow_untyped_defs = True` - Functions without type annotations are allowed
- `allow_incomplete_defs = True` - Partial type annotations are allowed
- Add type annotations incrementally as you work on files

### Ignoring Checks
When necessary, you can ignore specific checks:
- Black: `# fmt: off` and `# fmt: on`
- Mypy: `# type: ignore[error-code]`

Use sparingly and document why the ignore is necessary.
