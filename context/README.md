# Context System Documentation

This directory contains the structured context for the Agent-First Project Context System.

## Directory Structure

```
context/
├── design/          # System design documents
├── decisions/       # Architectural decision records (ADRs)
├── trace/          # Execution traces and agent interactions
├── sprints/        # Sprint planning and tracking
├── logs/           # System logs and audit trails
├── archive/        # Archived/expired documents
└── mcp_contracts/  # Model Context Protocol contracts
```

## Document Schema

All YAML documents follow a consistent schema with these required fields:

- `schema_version`: Semantic version of the document schema
- `document_type`: Type of document (design, decision, sprint, etc.)
- `id`: Unique identifier
- `title`: Human-readable title
- `status`: Current status (active, archived, deprecated)
- `last_modified`: ISO 8601 timestamp
- `last_referenced`: ISO 8601 timestamp of last access
- `expires`: Optional expiration date

## Quick Start

1. **Adding a new design document**:
   ```bash
   cp context/design/001-system-architecture.yaml context/design/002-your-design.yaml
   # Edit the new file with your content
   ```

2. **Recording a decision**:
   ```bash
   cp context/decisions/001-technology-stack.yaml context/decisions/002-your-decision.yaml
   # Document your decision and alternatives
   ```

3. **Validating documents**:
   ```bash
   context-lint validate context/
   ```

## Integration Points

- **Vector Search**: Documents are automatically embedded in Qdrant
- **Graph Relationships**: Neo4j indexes the `graph_metadata` sections
- **Agent Access**: Agents query context via the retrieval API
- **Cleanup**: Expired documents move to `archive/` automatically

## Best Practices

1. Keep documents focused on a single topic
2. Use consistent naming: `{number}-{kebab-case-title}.yaml`
3. Update `last_modified` when editing
4. Include `graph_metadata` for relationship mapping
5. Set appropriate `expires` dates for temporary content

## Configuration

See `.ctxrc.yaml` in the project root for system-wide settings.