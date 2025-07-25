# Extending Claude

## 🧩 Advanced Claude Patterns

### Custom Slash Commands
Place Markdown files in `.claude/commands/`:
```
.claude/
└── commands/
    ├── project-status.md
    ├── generate-docs.md
    └── run-tests.md
```

They become available as `/project:1`, `/project:2`, etc.

### Multi-Claude Pattern
Open multiple terminals/worktrees:
- Terminal 1: Claude for development
- Terminal 2: Claude for code review
- Terminal 3: Claude for test writing

Each maintains separate context.

### Headless Pipelines
Wire Claude into CI scripts:
```bash
# Automated migration
claude -p "Migrate all console.log to logger.info" \
  --output-format stream-json | \
  jq -r '.content'

# Lint fixes
claude -p "Fix all ESLint errors in src/" \
  --dangerously-skip-permissions
```

### MCP (Model Context Protocol) Integration
Add specialized tools:
```bash
# Add Playwright for browser testing
claude mcp add playwright npx @playwright/mcp@latest

# Add custom tools
claude mcp add my-tool ./path/to/tool
```

### Further Reading
- Anthropic "Best practices for agentic coding" (Apr 2025)
- Claude Code GitHub Actions docs
- Model Context Protocol (MCP) specs
