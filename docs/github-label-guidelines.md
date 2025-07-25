# GitHub Label Guidelines

This document outlines the standardized label system for the agent-context-template repository.

## Label Categories

Our label system uses a structured approach with clear categories. Each issue/PR should have:
- **One type label** (what kind of change)
- **One status label** (workflow state) - optional
- **One priority label** (urgency) - only when needed
- **One component label** (area affected) - when applicable
- **Sprint/phase labels** as needed

## Core Label Categories

### Type Labels (Required - Choose One)
- `bug` - Bug fixes and error corrections
- `enhancement` - New features or improvements
- `documentation` - Documentation only changes
- `question` - Questions or clarifications needed
- `duplicate` - Duplicate of another issue
- `invalid` - Not a valid issue
- `wontfix` - Will not be implemented

### Priority Labels (Use Sparingly)
- `priority:critical` - Must fix immediately (production down)
- `priority:high` - Important, do soon
- `priority:medium` - Normal priority
- `priority:low` - Nice to have

### Component Labels (When Applicable)
- `component:agents` - Agent components
- `component:ci` - CI/CD workflows
- `component:dx` - Developer experience
- `component:evaluation` - Evaluation systems
- `component:graph` - Graph database (Neo4j)
- `component:infra` - Infrastructure
- `component:mcp` - MCP protocol
- `component:observability` - Monitoring/logging
- `component:release` - Release process
- `component:security` - Security related
- `component:testing` - Test suite
- `component:tooling` - Development tools
- `component:vector` - Vector database (Qdrant)

### Sprint/Phase Labels
- `sprint-current` - Active sprint work
- `phase:4.1` - Current phase (adjust number as needed)
- `phase:5` - Next phase planning

### Special Labels
- `good first issue` - Beginner friendly
- `help wanted` - Community contributions welcome
- `claude-ready` - Optimized for Claude Code execution
- `investigation` - Needs investigation to determine scope
- `needs-scope` - Scope needs to be defined
- `from-code-review` - Generated from code review feedback
- `automation` - Automation related

## Label Usage Guidelines

### 1. New Issues
- Default to no labels if unsure
- Let triage process add appropriate labels
- Use `investigation` if scope is unclear

### 2. During Triage
- Add one type label (required)
- Add component label if clear
- Add priority only for high/critical items
- Add `sprint-current` if addressing immediately

### 3. Label Validation
- Workflows validate labels before use
- Missing labels default to safe alternatives
- Use `scripts/validate-labels.py` to check labels

### 4. Creating New Labels
- Follow naming convention: `category:name`
- Use lowercase with hyphens
- Get team consensus before creating
- Document in this guide

## Migration from Old Labels

The following labels have been standardized:

| Old Label | New Label |
|-----------|-----------|
| `testing`, `test`, `tests` | `component:testing` |
| `infrastructure` | `component:infra` |
| `ci`, `ci/cd` | `component:ci` |
| `docs` | `documentation` |
| `feature`, `feat` | `enhancement` |
| `bugfix`, `fix` | `bug` |
| `phase-1`, `phase-2`, etc. | `phase:1`, `phase:2`, etc. |
| `urgent`, `p0` | `priority:critical` |
| `p1` | `priority:high` |
| `p2` | `priority:medium` |
| `p3` | `priority:low` |

## Automation

### Label Validation Script
```bash
# Check if labels exist
./scripts/validate-labels.py bug enhancement "bad-label"

# Get suggestions for invalid labels
./scripts/validate-labels.py --json testing infrastructure
```

### Migration Script
```bash
# Dry run (default) - see what would change
./scripts/migrate-labels.sh

# Execute migration
./scripts/migrate-labels.sh --execute

# Verbose output
./scripts/migrate-labels.sh --verbose
```

### Workflow Integration
Workflows automatically validate labels using the `validate-labels.py` utility. If a label doesn't exist, workflows will:
1. Log a warning
2. Use a safe fallback label
3. Continue execution without failing

## Best Practices

1. **Keep it simple** - Don't over-label issues
2. **Be consistent** - Use existing labels before creating new ones
3. **Regular cleanup** - Remove unused labels quarterly
4. **Document changes** - Update this guide when adding labels
5. **Validate first** - Check labels exist before using in automation

## Label Colors

We use a consistent color scheme:
- **Red** (#D73A4A) - Bugs, critical issues
- **Green** (#0E8A16) - Enhancements, ready states
- **Blue** (#0052CC) - Components, informational
- **Yellow** (#FBCA04) - Warnings, needs attention
- **Purple** (#5319E7) - Special states, automation
- **Gray** (#CCCCCC) - Won't fix, invalid

## Maintenance

### Quarterly Review
- Remove unused labels
- Consolidate similar labels
- Update automation mappings
- Review this documentation

### Adding New Labels
1. Check if existing label covers the need
2. Propose in team discussion
3. Follow naming convention
4. Update this documentation
5. Add to validation script if needed
