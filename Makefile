.PHONY: format lint type-check test clean install all

# Default target
all: format lint type-check test

# Install all dependencies
install:
	pip install -r requirements.txt

# Format code with Black
format:
	black .

# Check code formatting without modifying
format-check:
	black --check --diff .

# Run linting
lint:
	python -m src.agents.context_lint validate context/

# Run type checking with mypy
type-check:
	mypy . --config-file mypy.ini

# Run tests
test:
	python -m pytest tests/ -v

# Run tests with coverage
test-cov:
	python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Development setup
dev-setup: install
	pre-commit install

# Quick quality check before committing
pre-commit: format-check lint type-check test
