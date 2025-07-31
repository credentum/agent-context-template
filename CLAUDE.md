# CLAUDE.md

This repository is a GitHub Actions template for integrating Claude AI into workflows using `anthropics/claude-code-action@beta`.

## Quick Reference
- **Security & Secrets**: See `.claude/guides/security.md`
- **Git Workflow Rules**: See `.claude/workflows/git-workflow.md`
- **CLI Reference**: See `.claude/guides/cli-reference.md`
- **Coding Standards**: See `.claude/guides/coding-standards.md`
- **GitHub Actions Setup**: See `.claude/workflows/github-actions.md`
- **Cost Management**: See `.claude/guides/cost-management.md`

## Essential Rules (Always Apply)
1. **NEVER push directly to main** - always use feature branches and PRs
2. **NEVER hard-code API keys** - use GitHub Secrets
3. Use `/clear` between distinct tasks to manage context
4. Run tests before committing any new logic
5. Follow conventional commits: `type(scope): message`

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

# Tag @claude in any GitHub issue/PR to trigger the action
```

## Repository Context
This is a GitHub Actions template repository that provides workflow templates for integrating Claude AI into GitHub workflows.

For detailed information on any topic, explore the `.claude/` directory structure.
