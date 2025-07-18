.PHONY: format lint type-check test clean install all up down health

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

# Run linting (matches GitHub CI exactly)
lint:
	@echo "Running CI lint checks locally..."
	@echo "=== Black ==="
	black --check src/ tests/ scripts/
	@echo "=== isort ==="
	isort --check-only --profile black src/ tests/ scripts/
	@echo "=== Flake8 ==="
	flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "=== MyPy (src) ==="
	mypy src/ --config-file=mypy.ini
	@echo "=== Context Lint ==="
	python -m src.agents.context_lint validate context/
	@echo "=== Import Check ==="
	python -m pytest --collect-only -q

# Quick lint with pre-commit
lint-quick:
	pre-commit run --all-files

# Original context lint only
lint-context:
	python -m src.agents.context_lint validate context/

# Docker-based CI lint (exact match to GitHub Actions)
lint-docker:
	./scripts/run-ci-docker.sh all

# Build Docker CI image
lint-docker-build:
	./scripts/run-ci-docker.sh build

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

# Docker infrastructure management
up:
	NEO4J_AUTH=none docker-compose up -d

down:
	docker-compose down -v

health:
	@echo "Checking Qdrant health..."
	@curl -f http://localhost:6333/collections 2>/dev/null && echo "Qdrant is healthy" || echo "Qdrant not healthy"
	@echo "Checking Neo4j health..."
	@docker exec neo4j cypher-shell "RETURN 1" 2>/dev/null && echo "Neo4j is healthy" || echo "Neo4j not healthy"
