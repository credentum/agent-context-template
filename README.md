# agent-context-template

A GitHub Actions template repository that provides workflow templates for an Agent-First Project Context System.

## Features

### Agent-First Context System
- **Structured Context Management**: Organized storage of project knowledge in `context/`
- **Vector Search**: Semantic search via Qdrant for intelligent retrieval
- **Graph Relationships**: Neo4j-powered GraphRAG for enhanced context understanding
- **Automated Agents**: Specialized agents for documentation, project management, and CI
- **Schema Validation**: YAML-based schemas with yamale validation
- 

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

- Check `context/README.md` for context system details

## License

This template is available under the MIT License.
