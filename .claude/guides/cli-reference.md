# CLI Reference Guide

## 🛠️ CLI Cheat Sheet

### Session Management
- `claude` - Start interactive session
- `claude -c` or `--continue` - Reopen last session
- `/clear` - Wipe context; use between tasks
- `/compact` - Summarize conversation to free tokens

### Code Operations
- `/review` - AI code review current diff or PR
- `/init` - Generate initial CLAUDE.md
- `/help` - List all slash commands

### Model Management
- `/model` - Switch between models
  - `claude-opus-4-20250514` (most powerful)
  - `claude-sonnet-4-20250514` (faster)

### Advanced Usage
- **Headless mode**: `claude -p "<prompt>" --output-format stream-json`
- **Add tools**: `claude mcp add playwright npx @playwright/mcp@latest`

## Recommended Workflows

### Small Fix
```bash
# Read files → plan → patch → review → commit
claude
# "Fix the bug in user.js"
/review
# If good, commit
```

### New Feature
```bash
# TDD approach
claude
# "Write failing tests for new feature X"
git commit -m "test: add failing tests for feature X"
# "Now implement feature X to make tests pass"
```

### Design Spike
```bash
claude
# "ultrathink: Design a high-level architecture for feature Y"
```

### Large Refactor
```bash
claude
# "Generate a refactoring checklist for module Z"
# Then iteratively work through items
```

### Best Practices
- Use `/clear` between distinct threads to avoid context bleed
- Keep prompts concise; prefer bullet lists to prose
- For complex tasks, break into smaller sub-tasks
