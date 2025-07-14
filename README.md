# agent-context-template

A GitHub Actions template repository that provides workflow templates for an Agent-First Project Context System.

## Test Coverage

Coverage is automatically tracked using `pytest-cov` and updated via:
1. **Local Updates**: Run `python scripts/update_coverage_metrics.py` to update metrics
2. **CI Integration**: Coverage runs on every PR via `.github/workflows/test-coverage.yml`
3. **Badge Updates**: Coverage badges are updated automatically in PR comments
4. **Report Generation**: HTML coverage reports are generated in `htmlcov/`

For current coverage status, run:
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make
- Python 3.11+

### Local Development Setup
1. **Start Infrastructure**:
   ```bash
   make up          # Start Qdrant (6333) and Neo4j (7474/7687)
   make health      # Check service health
   ```

2. **Install Dependencies**:
   ```bash
   make install     # Install Python dependencies
   make dev-setup   # Install pre-commit hooks
   ```

3. **Run Tests**:
   ```bash
   make test        # Run test suite
   make test-cov    # Run with coverage
   ```

4. **Stop Infrastructure**:
   ```bash
   make down        # Stop services and remove volumes
   ```

## Features

### Agent-First Context System
- **Structured Context Management**: Organized storage of project knowledge in `context/`
- **Vector Search**: Semantic search via Qdrant for intelligent retrieval
- **Graph Relationships**: Neo4j-powered GraphRAG for enhanced context understanding
- **Automated Agents**: Specialized agents for documentation, project management, and CI
- **Schema Validation**: YAML-based schemas with yamale validation

## Project Structure

```
src/
├── agents/          # CLI tools and automation agents
├── core/            # Base classes and utilities
├── storage/         # Database and storage components
├── analytics/       # Analytics and reporting
├── integrations/    # External service integrations
└── validators/      # Input validation and sanitization

context/
├── design/          # System design documents
├── decisions/       # Architectural decision records
├── trace/          # Execution traces
├── sprints/        # Sprint planning
├── logs/           # Audit trails
├── archive/        # Expired documents
└── mcp_contracts/  # Inter-agent contracts
```

Configuration is managed via `.ctxrc.yaml` with settings for:
- Qdrant vector database (v1.14.x)
- Neo4j graph database
- Agent behaviors and schedules
- Security and evaluation thresholds


## Security

- Never commit API keys or tokens
- Use GitHub Secrets for authentication
- Grant minimal required permissions
- Sigstore signing available for artifacts

## Documentation

- [GitHub Actions Guide](https://docs.github.com/en/actions)
- [Sprint Automation Guide](docs/sprint-automation.md)
- Check `context/README.md` for context system details

## License

This template is available under the MIT License.
