# GitHub Actions Configuration

## Overview

### Available Workflows

1. **`.github/workflows/claude.yml`** - Interactive Assistant
   - Triggers on:
     - Issue comments containing `@claude`
     - Pull request review comments containing `@claude`
     - Issues opened/assigned with `@claude` in title/body
     - Pull request reviews containing `@claude`

2. **`.github/workflows/claude-code-review.yml`** - Automated Code Review
   - Triggers on:
     - Pull request opened/synchronized events
     - No `@claude` mention required
     - Uses `direct_prompt` for automated review instructions

## Configuration Options

### Basic Configuration
```yaml
model: "claude-opus-4-20250514"  # or claude-sonnet-4-20250514
max_turns: 3                      # limit conversation turns
timeout_minutes: 10               # job timeout
```

### Tool Restrictions
```yaml
allowed_tools: "Bash(npm test),Bash(npm run lint)"
```

### Automated Reviews
```yaml
direct_prompt: |
  Review this PR for:
  - Code quality and maintainability
  - Potential bugs or issues
  - Security concerns
  - Performance implications
  - Test coverage
```

### PR Comment Management
```yaml
use_sticky_comment: true  # reuse same PR comment
```

### Trigger Configuration
```yaml
assignee_trigger: "username"     # trigger on assignment
label_trigger: "needs-claude"    # trigger on label
```

## Example Configurations

### Basic Interactive Setup
```yaml
name: Claude AI Assistant
on:
  issue_comment:
    types: [created]

jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@beta
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          model: "claude-opus-4-20250514"
```

### Automated PR Review
```yaml
name: Claude Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@beta
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          direct_prompt: |
            Review this PR focusing on code quality and bugs
          use_sticky_comment: true
```
