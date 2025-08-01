# CLAUDE.md

This repository is a GitHub Actions template for integrating Claude AI into workflows using `anthropics/claude-code-action@beta`.

## Quick Reference
- **Security & Secrets**: See `.claude/guides/security.md`
- **Git Workflow Rules**: See `.claude/workflows/git-workflow.md`
- **CLI Reference**: See `.claude/guides/cli-reference.md`
- **Coding Standards**: See `.claude/guides/coding-standards.md`
- **GitHub Actions Setup**: See `.claude/workflows/github-actions.md`
- **Cost Management**: See `.claude/guides/cost-management.md`
- **🆕 Autonomous PR Creation**: See `.claude/troubleshooting/autonomous-pr-creation.md`

## Essential Rules (Always Apply)
1. **NEVER push directly to main** - always use feature branches and PRs
2. **NEVER hard-code API keys** - use GitHub Secrets
3. Use `/clear` between distinct tasks to manage context
4. Run tests before committing any new logic
5. Follow conventional commits: `type(scope): message`

## 🚀 Autonomous PR Creation (Fixed!)

### Quick Commands
```bash
# Fix authentication and create PR
unset GITHUB_TOKEN
./scripts/create-autonomous-pr.sh --repo credentum/context-store --title "feat: New feature" --body "Description"

# Or use aliases
fix-pr-auth
create-pr --repo credentum/context-store --title "feat: Add schemas" --body "Schema collection"
```

### Setup (One-Time)
1. **Generate Token**: https://github.com/settings/tokens (scopes: `repo`, `workflow`, `read:org`)
2. **Add Secret**: Repository → Settings → Codespaces → `PERSONAL_ACCESS_TOKEN`
3. **Restart Codespace**: For changes to take effect

### Troubleshooting
- **"Bad credentials"**: Token expired, generate new one
- **"Resource not accessible"**: Run `unset GITHUB_TOKEN` first
- **"No common history"**: Our script fixes this automatically

Full guide: `.claude/troubleshooting/autonomous-pr-creation.md`

## CI/CD Best Practices
### Docker CI Timeout Guidance
- **Claude's tool timeout**: Commands have a 2-minute limit by default
- **Quick CI mode**: Use `./scripts/run-ci-docker.sh quick` for fast essential checks
- **Split long operations**:
  - `./scripts/run-ci-docker.sh lint` - Format checks only (Black, isort, Flake8)
  - `./scripts/run-ci-docker.sh typecheck` - MyPy only
  - `./scripts/run-ci-docker.sh precommit` - Pre-commit hooks only
- **Full CI**: Use `./scripts/run-ci-docker.sh all` when you have more time
- **GitHub Actions**: Full CI runs have 12-minute timeout in GitHub Actions

## Quick Start
```bash
# Install CLI (once per machine)
npm install -g @anthropic-ai/claude-code

# Start interactive session
claude

# Generate initial CLAUDE.md
/init

# Create PR autonomously
/create-pr --repo OWNER/REPO --title "Title" --body "Description"

# Tag @claude in any GitHub issue/PR to trigger the action
```

## Repository Context
This is a GitHub Actions template repository that provides workflow templates for integrating Claude AI into GitHub workflows.

For detailed information on any topic, explore the `.claude/` directory structure.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
