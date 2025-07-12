# Schema Files

This directory contains Yamale schema definitions for validating context documents.

## Schema Files

- `base.yaml` - Common fields for all document types (used with include)
- `design.yaml` - Schema for design documents (uses include)
- `decision.yaml` - Schema for decision documents (uses include)
- `sprint.yaml` - Schema for sprint documents (uses include)

## Full Schema Files

Due to limitations with Yamale's include directive in certain environments, we also provide full schemas:

- `design_full.yaml` - Complete schema for design documents
- `decision_full.yaml` - Complete schema for decision documents
- `sprint_full.yaml` - Complete schema for sprint documents

The context-lint tool will try to use the `*_full.yaml` versions first, falling back to the include-based schemas if needed.

## Known Issues

- Regex patterns in Yamale may generate SyntaxWarning messages about invalid escape sequences. These warnings are harmless and don't affect validation.
- The warnings occur because Yamale evaluates regex patterns as Python strings before compiling them as regex.

## Adding New Document Types

1. Create a new schema file: `{type}.yaml` with include directives
2. Create a full schema file: `{type}_full.yaml` with all fields expanded
3. Update the base schema's document_type enum to include the new type
