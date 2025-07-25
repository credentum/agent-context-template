# Security & Secrets Guide

## ⚠️ Critical Security Rules

**Never hard-code API keys or tokens in any file.**

### OAuth Authentication (Recommended)
Add `CLAUDE_CODE_OAUTH_TOKEN` in GitHub Secrets:
```yaml
claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

### API Key Authentication
Add `ANTHROPIC_API_KEY` in GitHub Secrets:
```yaml
anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### GitHub Permissions
Grant minimal permissions your workflow needs:
```yaml
permissions:
  contents: read          # read repo
  pull-requests: write    # create/update PRs
```

### Unattended Execution
To run unattended, you may append `--dangerously-skip-permissions`.

**WARNING**: Only do this inside a throwaway container or GitHub runner; it bypasses every safety prompt.

### Best Practices
- Rotate API keys regularly
- Use repository secrets, never organization secrets for sensitive data
- Audit secret usage in workflow runs
- Never log or output secret values
- Use environment-specific secrets when possible
