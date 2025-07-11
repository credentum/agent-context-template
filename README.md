# agent-context-template

A GitHub Actions template repository that provides workflow templates for integrating Claude AI into GitHub workflows using the `anthropics/claude-code-action@beta` action, enhanced with an Agent-First Project Context System.

## Features

### Claude AI Integration
- **Interactive Claude Assistant** (`claude.yml`): Responds to @claude mentions in issues and PRs
- **Automated Code Review** (`claude-code-review.yml`): Automatic PR review without mentions
- **OAuth Authentication**: Secure token-based authentication (recommended)
- **Flexible Configuration**: Model selection, turn limits, tool restrictions

### Agent-First Context System
- **Structured Context Management**: Organized storage of project knowledge in `context/`
- **Vector Search**: Semantic search via Qdrant for intelligent retrieval
- **Graph Relationships**: Neo4j-powered GraphRAG for enhanced context understanding
- **Automated Agents**: Specialized agents for documentation, project management, and CI
- **Schema Validation**: YAML-based schemas with yamale validation

## Quick Start

1. **Use this template** to create a new repository
2. **Set up authentication** in GitHub Secrets:
   - For OAuth (recommended): Add `CLAUDE_CODE_OAUTH_TOKEN`
   - For API key: Add `ANTHROPIC_API_KEY`
3. **Configure workflows** in `.github/workflows/`:
   - Customize `claude.yml` for interactive assistance
   - Adjust `claude-code-review.yml` for automated reviews
4. **Initialize context system** (optional):
   ```bash
   # Install dependencies
   npm install -g @anthropic-ai/claude-code
   
   # Initialize context
   claude
   /init
   ```

## Context System Structure

```
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

## Workflow Configuration

### Interactive Claude Assistant
```yaml
# Trigger with @claude mentions
model: "claude-opus-4-20250514"
max_turns: 3
allowed_tools: "Bash(npm test),Bash(npm run lint)"
```

### Automated Code Review
```yaml
# Automatic on PR open/sync
direct_prompt: |
  Review this PR for:
  - Code quality and best practices
  - Potential bugs or issues
  - Performance considerations
```

## Security

- Never commit API keys or tokens
- Use GitHub Secrets for authentication
- Grant minimal required permissions
- Sigstore signing available for artifacts

## Documentation

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [GitHub Actions Guide](https://docs.github.com/en/actions)
- See `CLAUDE.md` for Claude-specific guidance
- Check `context/README.md` for context system details

## License

This template is available under the MIT License.