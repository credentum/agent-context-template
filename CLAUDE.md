# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Context

This is an **Agent-First Project Context System** that provides structured context management with vector search (Qdrant) and graph relationships (Neo4j) for enhanced AI agent interactions. It includes GitHub Actions templates for integrating Claude AI into workflows using the `anthropics/claude-code-action@beta` action.

**Current Project Status:**
- Coverage: 59.53% (Target: 85%)
- Critical modules need attention (validators <40% coverage)
- Python 3.8+ codebase with async support

## 1 ⚠️ Security & Secrets (first things first)
* **Never hard‑code API keys or tokens.**

  **For OAuth authentication (recommended):**
  Add `CLAUDE_CODE_OAUTH_TOKEN` in GitHub Secrets:
  ```yaml
  claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
  ```

  **For API key authentication:**
  Add `ANTHROPIC_API_KEY` in GitHub Secrets:
  ```yaml
  anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
  ```

  **Additional secrets needed for this project:**
  - `QDRANT_API_KEY` - Vector database authentication
  - `NEO4J_PASSWORD` - Graph database authentication
  - `GITHUB_TOKEN` - For GitHub API operations

Grant the minimal permissions your workflow needs:

```yaml
permissions:
  contents: read          # read repo
  pull-requests: write    # create/update PRs
  issues: write          # for issue automation
```

To run unattended you may append `--dangerously-skip-permissions`.
Only do this inside a throw‑away container or GitHub runner; it bypasses every safety prompt.

## 2 🚀 Quick Start
Install CLI (once per machine):

```bash
npm install -g @anthropic-ai/claude-code
```

Bootstrap in repo root:

```bash
claude          # starts interactive session
/init           # generates initial CLAUDE.md (this file)
```

Tag @claude in any issue / PR to summon the GitHub Action.

## 3 📁 Project Structure & Key Files

```
src/
├── agents/         # CLI tools and automation agents
├── core/           # Base classes and utilities
├── storage/        # Database components (Qdrant, Neo4j)
├── analytics/      # Analytics and reporting
├── integrations/   # External service integrations
└── validators/     # Input validation (PRIORITY: <40% coverage)

context/
├── design/         # System design documents
├── decisions/      # Architectural decision records (ADRs)
├── sprints/        # Sprint planning
└── mcp_contracts/  # Inter-agent contracts

Key configuration files:
- .ctxrc.yaml       # Main configuration
- pyproject.toml    # Python project config
- .pre-commit-config.yaml  # Code quality hooks
```

## 4 🛠️ CLI Cheat‑Sheet (keep nearby)
claude -c or --continue – reopen last session

/clear – wipe context; use between tasks

/compact – summarise convo to free tokens

/review – AI code‑review current diff or PR

/model – switch between models (e.g., claude-opus-4-20250514, claude-sonnet-4-20250514)

/help – list all slash commands

Headless mode: claude -p "<prompt>" --output-format stream-json

Add tools: claude mcp add playwright npx @playwright/mcp@latest

## 5 📋 Coding & Review Guidelines

### Python Standards:
- **Style**: Black formatter (line length: 88), isort for imports
- **Type hints**: Required for all functions
- **Docstrings**: Google style for all public methods
- **Testing**: pytest with minimum 85% coverage

### Code Quality Checklist:
- [ ] All functions have type hints
- [ ] Docstrings explain purpose, args, returns, raises
- [ ] Tests cover happy path, edge cases, and errors
- [ ] No hardcoded secrets or credentials
- [ ] Async functions properly handle exceptions
- [ ] Validators check all edge cases

### Commit Standards:
- Conventional Commits format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat(storage): add vector similarity search`

### Priority Areas for Improvement:
1. **validators/** - Increase coverage from ~34% to 90%
2. **storage/vector_db_init.py** - Add error handling tests
3. **analytics/context_analytics.py** - Complete unit tests

## 6 🔄 Recommended Workflows

### Testing Workflow:
```bash
# ALWAYS run before creating/pushing PR:
pre-commit run --all-files

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Update coverage metrics
python scripts/update_coverage_metrics.py

# Check specific module
pytest tests/test_validators.py -v

# If pre-commit made changes:
git add -A && git commit --amend --no-edit
```

### Development Workflow:
When | Ask Claude to...
---|---
Small fix | read files → plan → patch → test → pre-commit → /review → commit
New feature | TDD: write failing tests → commit → implement until green → pre-commit
High coverage | analyze uncovered lines → write specific tests → verify >85%
Refactor | generate checklist → test baseline → refactor → test again → pre-commit
Debug | reproduce issue → add logging → isolate → fix → add regression test

**Before EVERY commit/push:**
1. Run `pre-commit run --all-files`
2. Run `pytest --cov=src --cov-report=term-missing`
3. Fix any issues before proceeding

Use /clear between distinct tasks to avoid context bleed.

## 7 ▶️ GitHub Actions Overview

**.github/workflows/claude.yml** — Interactive assistant that triggers on:
- Issue comments containing `@claude`
- Pull request review comments containing `@claude`
- Issues opened/assigned with `@claude` in title/body
- Pull request reviews containing `@claude`

**.github/workflows/claude-code-review.yml** — Automated code review on:
- Pull request opened/synchronized events
- No `@claude` mention required
- Uses `direct_prompt` for automated review instructions

**.github/workflows/test-coverage.yml** — Coverage tracking:
- Runs pytest with coverage on every PR
- Updates coverage badges
- Fails if coverage drops below threshold

**Configuration options include:**
```yaml
model: "claude-opus-4-20250514"  # or claude-sonnet-4-20250514
max_turns: 3                      # limit conversation turns
timeout_minutes: 10               # job timeout
allowed_tools: "Bash(npm test),Bash(npm run lint)"
direct_prompt: |                  # for automated reviews
  Review for:
  - Code quality and bugs
  - Test coverage (target: 85%)
  - Type hints and docstrings
  - Security issues
use_sticky_comment: true          # reuse same PR comment
assignee_trigger: "username"      # trigger on assignment
label_trigger: "needs-claude"     # trigger on label
```

## 8 💰 Tokens & Cost Control
Run `npx ccusage@latest` locally to inspect monthly token burn.
Keep prompts tight; prefer bullet lists to prose.
Use `/compact` every ~100 lines of dialogue.
In Actions set `max_turns: 3` unless the task truly needs more.

For this project specifically:
- Use `/compact` after analyzing large Python modules
- Clear context between different subsystems (storage vs analytics)
- Batch related file reviews together

## 9 🧩 Extending Claude

### Project-Specific Extensions:
1. **Custom validators**: Place in `src/validators/` with corresponding tests
2. **New agents**: Follow template in `src/agents/base_agent.py`
3. **Context schemas**: Define in YAML under `context/schemas/`

### Testing Patterns:
```python
# Standard test structure
import pytest
from unittest.mock import Mock, patch

class TestFeature:
    """Test module_name.feature_name"""

    def test_happy_path(self):
        """Test normal operation."""

    def test_edge_cases(self):
        """Test boundary conditions."""

    def test_error_handling(self):
        """Test error scenarios."""

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async functions."""
```

### Custom Slash Commands:
Place custom commands as Markdown files in `.claude/commands/`. They become `/project:<name>`.

Example command for GitHub issue workflow:

**`/fix-issue`** - Analyze and fix GitHub issues systematically:
```
Please analyze and fix the GitHub issue:
$ARGUMENTS.

Follow these steps:

# PLAN
1. Use 'gh issue view' to get the issue details
2. Understand the problem described in the issue
3. Ask clarifying questions if necessary
4. Understand the prior art for this issue
   - Search context/trace/scratchpad/ for previous thoughts
   - Search context/decisions/ for relevant ADRs
   - Search PRs to see if you can find history on this issue
   - Search the codebase focusing on src/ for relevant files
5. Think harder about how to break the issue down into a series of small, manageable tasks
6. Document your plan in a new scratchpad
   - Save to context/trace/scratchpad/YYYY-MM-DD-issue-{number}-{title}.md
   - Include the issue link and sprint reference
   - Update context/sprints/current.yaml if this affects sprint goals

# CREATE
- Create a new branch following the convention: fix/{issue-number}-{description} or feature/{issue-number}-{description}
- Solve the issue in small, manageable steps according to your plan
- Commit your changes after each step using conventional commits:
  - feat(scope): description
  - fix(scope): description
  - test(scope): description
- Update CLAUDE.md if the changes affect development workflow

# TEST
- Run pre-commit hooks: `pre-commit run --all-files`
- Write pytest tests for new functionality in tests/
- Ensure validators have >90% coverage if modified
- Run the full test suite: `pytest --cov=src --cov-report=term-missing`
- Update coverage metrics: `python scripts/update_coverage_metrics.py`
- If working on MCP tools, test with a mock MCP client
- Ensure all tests pass and coverage doesn't drop below 59.53%

# VERIFY
- Check that all YAML files pass validation: `context-lint`
- Verify any new context files have proper schema_version
- If you modified embed_doc.py, check hash-diff functionality
- If you touched GraphRAG, verify Neo4j queries still work

# DEPLOY
- Ensure your branch is up to date with main
- Run final pre-commit and test suite
- Open a PR with:
  - Clear description linking to the issue
  - Test results and coverage report
  - Any changes to context/ structure documented
  - Label with appropriate sprint tag
- Request a review
- Update context/trace/logs/ with completion notes

# IMPORTANT REMINDERS
- NEVER push directly to main
- ALWAYS run pre-commit before pushing
- If this creates new MCP tools, update context/mcp_contracts/
- If this affects agent behavior, update relevant agent in src/agents/
- Consider if this needs a new ADR in context/decisions/

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.
```

## 10 📚 Project-Specific Resources

### Key Documentation:
- `context/README.md` - Context system architecture
- `docs/test-coverage-guide.md` - Coverage improvement guide
- `docs/sprint-automation.md` - Sprint workflow automation

### Database Operations:
```python
# Vector DB example
from src.storage.vector_db_init import initialize_qdrant
client = initialize_qdrant()

# Graph DB example
from src.storage.neo4j_init import get_neo4j_driver
driver = get_neo4j_driver()
```

### Common Tasks:
```bash
# Validate YAML schemas
python -m src.validators.config_validator config.yaml

# Run analytics
python -m src.analytics.context_analytics

# Update embeddings
python -m src.storage.hash_diff_embedder_async
```

# 🚨 CRITICAL: Git Workflow Rules

**NEVER push directly to main branch!** Always follow this workflow:

1. Start from updated main:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create a feature branch:
   ```bash
   git checkout -b fix/description
   # or
   git checkout -b feature/description
   # or
   git checkout -b test/module-name  # for test improvements
   ```

3. Make changes and commit:
   ```bash
   git add -A
   git commit -m "type(scope): description"
   ```

4. **ALWAYS run pre-commit hooks and tests before pushing:**
   ```bash
   # Run pre-commit hooks (Black, isort, flake8, etc.)
   pre-commit run --all-files

   # If pre-commit made changes, stage them
   git add -A
   git commit --amend --no-edit

   # Run full test suite with coverage
   pytest --cov=src --cov-report=term-missing
   # Ensure coverage doesn't drop!
   ```

5. Push to feature branch:
   ```bash
   git push -u origin fix/description
   ```

6. Create PR:
   ```bash
   gh pr create --title "type(scope): description" --body "..."
   ```

**IMPORTANT**:
- NEVER use `git push origin main`
- ALWAYS run `pre-commit run --all-files` before pushing
- ALWAYS run `pytest --cov=src` and verify tests pass
- ALWAYS create a PR for code review
- Include test results and coverage report in PR descriptions
- Wait for CI checks to pass before merging
- Ensure coverage stays above 59.53% (current baseline)
- If pre-commit makes changes, amend your commit before pushing

## 🎯 Current Focus Areas

1. **Immediate Priority**: Increase validator coverage
   - `validators/kv_validators.py` (33.64% → 90%)
   - `validators/config_validator.py` (34.66% → 90%)

2. **Phase 1 Goals**:
   - Overall coverage: 59.53% → 70%
   - Critical modules: All above 85%
   - Complete async error handling

3. **Code Review Focus**:
   - Verify all new code has tests
   - Check for proper async/await usage
   - Ensure validators handle edge cases
   - Look for potential security issues
