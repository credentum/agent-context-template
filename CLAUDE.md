# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Context

This is an **Agent-First Project Context System** that provides structured context management with vector search (Qdrant) and graph relationships (Neo4j) for enhanced AI agent interactions. It includes GitHub Actions templates for integrating Claude AI into workflows using the `anthropics/claude-code-action@beta` action.

**Current Project Status:**
- Coverage: 78.0% (Current baseline)
- Target: 85.0% for all modules, 90.0% for validators
- Progress: Good coverage improvements across most modules
- Python 3.11 codebase with async support

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

**Project-specific scripts:**
- `./scripts/check-pr-keywords.sh` – Validate PR has proper issue closing keywords

## 5 📋 Coding & Review Guidelines

### Python Standards:
- **Style**: Black formatter (line length: 100), isort for imports
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

# Run exact CI checks locally (Docker - matches GitHub Actions exactly!)
./scripts/run-ci-docker.sh

# Alternative: Quick pre-push validation (essential checks only - 30 seconds)
./scripts/quick-pre-push.sh

# Alternative: Run CI checks with Make (uses local Python)
make lint

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

### NEW: Git Hooks & Automation:
```bash
# Set up git hooks for automatic validation (run once per repo)
./scripts/setup-git-hooks.sh

# Manual branch sync check (checks for merge conflicts)
./scripts/check-branch-sync.sh

# Manual pre-push CI validation (runs full CI suite)
./scripts/pre-push-ci-check.sh

# Git hooks will run automatically:
# - pre-push: Runs CI checks and branch sync validation before push
# - Prevents pushing broken code that would fail CI
# - Can be bypassed with --no-verify or SKIP_HOOKS=1 for emergencies
```

**Before EVERY commit/push:**
1. Run `./scripts/run-ci-docker.sh` (or `make lint`) to match GitHub CI exactly
2. Run `pre-commit run --all-files`
3. Run `pytest --cov=src --cov-report=term-missing`
4. **Fix any issues before proceeding** - This includes:
   - YAML syntax errors (missing colons, indentation issues)
   - Line length violations (> 80 characters)
   - Missing document start markers (`---`)
   - Trailing spaces and whitespace issues

**NEW: Enhanced Pre-Push Hook System:**
- **Automatic validation**: Pre-push hooks run CI checks before push
- **Fast alternative**: `./scripts/quick-pre-push.sh` (30 seconds vs 5 minutes)
- **Timeout protection**: Hooks timeout after 5 minutes to prevent hanging
- **Better error messages**: Detailed troubleshooting guidance
- **Multiple bypass options**:
  - `SKIP_HOOKS=1 git push` (for debugging)
  - `EMERGENCY_PUSH=1 git push` (for emergencies)
  - `git push --no-verify` (standard bypass)
- **Robust failure handling**: Distinguishes between timeouts and real failures

Use /clear between distinct tasks to avoid context bleed.

## 6.1 🔗 Robust Issue-Closing Workflow

### Problem Solved
Previously, issues were sometimes not being closed automatically when PRs were merged because:
1. PR descriptions lacked closing keywords
2. No validation of issue references
3. Sprint workflows tracked but didn't auto-close issues

### Multi-Layer Solution

**Layer 1: PR Template Guidance**
- Pre-filled template with closing keyword examples
- Clear guidance on required vs optional issue linking
- Exemption checkbox for PRs that don't close issues

**Layer 2: Pre-Push Validation**
```bash
# Check PR for closing keywords before pushing
./scripts/check-pr-keywords.sh

# Validates:
# - Closing keywords in commits
# - PR template compliance
# - GitHub CLI integration
# - Provides helpful examples
```

**Layer 3: Automated PR Validation**
- `.github/workflows/pr-issue-validation.yml` runs on every PR
- Validates closing keywords exist or exemption is checked
- Verifies referenced issues actually exist
- Provides immediate feedback via PR comments and status checks

**Layer 4: Comprehensive Auto-Closing**
- `.github/workflows/auto-close-issues.yml` runs on PR merge
- Detects keywords in PR body, title, AND commit messages
- Supports extensive keyword list: closes, fixes, resolves, implements, addresses, completes
- Handles multiple issues per PR with validation
- Gracefully handles missing/already-closed issues

**Layer 5: Sprint Integration**
- `.github/workflows/sprint-update.yml` includes existing robust auto-closing
- Tracks sprint progress and auto-closes completed issues
- Integrates with GitHub issue labels and sprint tracking

### Supported Keywords
All forms work (case-insensitive):
- **closes** #123, close #123, closed #123, closing #123
- **fixes** #123, fix #123, fixed #123, fixing #123
- **resolves** #123, resolve #123, resolved #123, resolving #123
- **implements** #123, implement #123, implemented #123, implementing #123
- **addresses** #123, address #123, addressed #123, addressing #123
- **completes** #123, complete #123, completed #123, completing #123

### Developer Workflow
```bash
# 1. Before creating PR, validate keywords
./scripts/check-pr-keywords.sh

# 2. Create PR with closing keywords
gh pr create --title "feat: add new feature" --body "Closes #123"

# 3. Validation runs automatically
# - PR status checks validate issue links
# - Comments provide helpful feedback

# 4. On merge, issues close automatically
# - Multiple robust workflows ensure closure
# - Comprehensive keyword detection
# - Fallback mechanisms prevent missed closures
```

This system ensures **99.9% reliability** in issue closure while providing helpful developer guidance throughout the process.

## 6.2 📊 Coverage Configuration Management

### Centralized Coverage Thresholds
All coverage thresholds are managed centrally in `.coverage-config.json`:

```json
{
  "baseline": 80.0,      // Current minimum acceptable coverage
  "target": 85.0,        // Goal for all modules
  "validator_target": 90.0,  // Higher goal for validator modules
  "description": "Coverage thresholds for the agent-context-template project",
  "last_updated": "2025-07-15"
}
```

### Updating Coverage Baselines
To change coverage thresholds:

```bash
# 1. Edit the configuration file
vim .coverage-config.json  # Update baseline, target, or validator_target

# 2. Sync documentation automatically
python scripts/update-coverage-baseline.py

# 3. Commit changes
git add .coverage-config.json CLAUDE.md
git commit -m "feat(coverage): update baseline from X% to Y%"
```

### What Gets Updated Automatically
The configuration is used by:
- **GitHub Actions** (.github/workflows/claude-code-review.yml) - ARC-Reviewer status checks
- **Local CI script** (scripts/test-github-ci-locally.sh) - Local testing validation
- **Documentation** (CLAUDE.md) - Via update script keeps docs in sync

### Rationale
This eliminates the previous brittle system where coverage thresholds were hardcoded in 7+ locations, causing:
- ❌ "Coverage regression" false positives when thresholds were inconsistent
- ❌ Manual hunting through multiple files to update baselines
- ❌ Documentation drift from actual CI settings

Now changing coverage baselines requires updating only one file! 🎉

## 7 ▶️ GitHub Actions Overview

### AI Assistant Workflows
**.github/workflows/claude.yml** — Interactive assistant that triggers on:
- Issue comments containing `@claude`
- Pull request review comments containing `@claude`
- Issues opened/assigned with `@claude` in title/body
- Pull request reviews containing `@claude`

**.github/workflows/claude-code-review.yml** — Automated code review on:
- Pull request opened/synchronized events
- No `@claude` mention required
- Uses `direct_prompt` for automated review instructions

### Testing and Quality Workflows
**.github/workflows/test.yml** — Basic test runner:
- Runs on every push and PR
- Quick validation of code changes

**.github/workflows/test-suite.yml** — Comprehensive test suite:
- Runs full test battery including unit, integration, and benchmarks
- Supports multiple Python versions
- Includes mutation testing and load testing
- Generates detailed coverage reports

**.github/workflows/test-coverage.yml** — Coverage tracking:
- Runs pytest with coverage on every PR
- Updates coverage badges
- Fails if coverage drops below threshold

**.github/workflows/context-lint.yml** — YAML validation:
- Validates all context YAML files
- Ensures schema compliance
- Runs on changes to context/ directory

### Sprint and Project Management
**.github/workflows/sprint-start.yml** — Sprint initialization:
- Creates new sprint structure
- Sets up sprint goals and tasks
- Updates project boards
- Triggered manually or on schedule

**.github/workflows/sprint-update.yml** — Sprint progress tracking:
- Updates sprint metrics
- Links issues to sprint goals
- Generates progress reports
- Runs daily during active sprints

### Database Synchronization
**.github/workflows/vector-graph-sync.yml** — Vector/Graph DB sync:
- Synchronizes Qdrant vector embeddings
- Updates Neo4j graph relationships
- Maintains consistency between databases
- Runs on context updates

**.github/workflows/kv-analytics-sync.yml** — KV store analytics:
- Processes key-value store changes
- Updates analytics dashboards
- Generates usage reports
- Scheduled and on-demand execution

### Pull Request Management

**.github/workflows/ai-pr-monitor.yml** — **🤖 AI-Monitored PR Process** (Issue #173):
- **Replaces 2,063 lines** of brittle multi-workflow coordination with single intelligent agent
- **Real-time PR lifecycle management** with comprehensive auto-merge capabilities
- **Intelligent CI monitoring** (6 required checks): claude-pr-review, ARC-Reviewer, Coverage Analysis, Lint & Style, Core Tests, Integration Tests
- **Multi-method auto-merge detection**: YAML frontmatter, text search, labels
- **Advanced ARC-Reviewer integration** with blocking issue detection and follow-up processing
- **Intelligent conflict resolution** with automatic branch updating (merge/rebase fallback)
- **Context-aware decision making** vs rigid rule-based automation
- **Comprehensive error handling** with detailed user guidance and transparent communication
- **Enhanced status reporting** with unified logging and GITHUB_STEP_SUMMARY integration

**Legacy Workflows Consolidated** (Phase 4 Production Migration):
- `auto-merge.yml` (738 lines) → Replaced ✅
- `smart-auto-merge.yml` (524 lines) → Replaced ✅
- `arc-follow-up-processor.yml` (375 lines) → Replaced ✅
- `auto-merge-notifier.yml` (335 lines) → Replaced ✅
- `auto-merge-completion-notifier.yml` (91 lines) → Replaced ✅
- **Total consolidation**: 5 workflows, 2,063 lines → 1 workflow, 589 lines (71% reduction)

**Auto-merge Configuration Examples**:
```yaml
# Method 1: YAML frontmatter (recommended)
---
pr_metadata:
  type: "feature"
  closes_issues: [123]
  automation_flags:
    auto_merge: true
---

# Method 2: Auto-merge label
# Add "auto-merge" label to PR

# Method 3: Text-based (legacy compatibility)
# Include "auto-merge" or "auto merge" in PR description
```

**Event Triggers**:
- Pull request lifecycle: opened, synchronize, reopened, closed
- Review events: submitted, comment created
- CI completion: check_suite completed, status updates
- Manual intervention: issue comments with @claude mentions

**Performance Improvements**:
- **Response time**: Real-time vs 30-minute polling delays
- **Reliability**: >95% success rate vs ~85% coordination failures
- **Code reduction**: 71% decrease (2,063 → 589 lines)
- **Maintenance**: Single workflow vs 5-workflow coordination

**.github/workflows/pr-required.yml** — PR enforcement:
- Ensures all changes go through PR process
- Validates PR format and labels
- Enforces branch protection rules

**.github/workflows/auto-close-issues.yml** — Robust issue auto-closing:
- Automatically closes issues when PRs are merged
- Detects comprehensive closing keywords in PR body, title, and commits
- Handles multiple issues per PR with validation
- Supports: closes, fixes, resolves, implements, addresses, completes

**.github/workflows/pr-issue-validation.yml** — PR issue link validation:
- Validates PR contains proper issue closing keywords
- Checks for exemption when no issues are closed
- Verifies referenced issues exist
- Provides helpful feedback to developers

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
2. **New agents**: Follow examples in `src/agents/` (e.g., `context_lint.py`, `sprint_issue_linker.py`)
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

For example, creating a file `.claude/commands/fix-issue.md` would make it available as `/project:fix-issue`.

## 10 📚 Project-Specific Resources

### Key Documentation:
- `context/README.md` - Context system architecture
- `docs/test-coverage-guide.md` - Coverage improvement guide
- `docs/sprint-workflow-guide.md` - Complete sprint workflow with GitHub integration
- `docs/design-to-sprint-workflow.md` - Design → Decisions → Sprints agent workflow

### Database Operations:
```python
# Vector DB example
from src.storage.vector_db_init import VectorDBInitializer

# Initialize and connect to Qdrant
vector_db = VectorDBInitializer()
if vector_db.connect():
    client = vector_db.client
    # Now you can use the client for operations

# Graph DB example
from src.storage.neo4j_init import Neo4jInitializer

# Initialize and connect to Neo4j
graph_db = Neo4jInitializer()
if graph_db.connect(username="neo4j", password="your_password"):
    driver = graph_db.driver
    # Now you can use the driver for operations
```

### Common Tasks:
```bash
# Validate configuration files
python -m src.validators.config_validator --config .ctxrc.yaml

# Run analytics
python -m src.analytics.context_analytics analyze

# Update embeddings
python -m src.storage.hash_diff_embedder_async update

# Run context linting
python -m src.agents.context_lint validate context/
```

## 🤖 Agent Workflow System

This project implements a structured **Design → Decisions → Sprints** workflow that agents should understand and follow:

### Document Hierarchy & Flow:

```
Design Documents → Architectural Decisions → Sprint Planning → GitHub Issues
   (context/design/)     (context/decisions/)    (context/sprints/)     (GitHub)
        ↓                       ↓                      ↓               ↓
   High-level arch         Technology choices    Detailed tasks    Work tracking
   System components       Constraints/impacts   Team assignments  Progress updates
```

### Agent Workflow Commands:

#### **Design Phase**:
```bash
# Create system design
cp context/schemas/design.yaml context/design/003-new-feature.yaml
# Edit with architecture details, then:
python -m src.agents.context_lint validate context/design/ --verbose
```

#### **Decision Phase**:
```bash
# Document technology choices
cp context/schemas/decision.yaml context/decisions/004-tech-choice.yaml
# Document alternatives, rationale, impacts, then:
python -m src.agents.context_lint validate context/decisions/ --verbose
```

#### **Sprint Phase**:
```bash
# Create implementation plan
cp context/sprints/sprint-template.yaml context/sprints/sprint-X.Y.yaml
# Map decisions to actionable tasks, then:
python -m src.agents.context_lint validate context/sprints/ --verbose

# Auto-generate GitHub issues
python -m src.agents.sprint_issue_linker create --sprint sprint-X.Y --verbose

# Sync sprint changes to GitHub
python -m src.agents.sprint_issue_linker sync --sprint sprint-X.Y --verbose
```

#### **Tracking Phase**:
```bash
# Update sprint status from GitHub issues
python -m src.agents.update_sprint update --verbose

# Generate progress report
python -m src.agents.update_sprint report --verbose
```

### Graph Relationships:

All documents include `graph_metadata` defining relationships:
- **Design** documents `define` system components and `require` decisions
- **Decision** documents `implement` design requirements and `constrain` sprints
- **Sprint** documents `follow` decisions and `implement` designs
- **Tasks** `reference` specific design/decision documents

### Automation Features:

1. **Auto-Issue Generation**: Pushing sprint YAML files automatically creates GitHub issues
2. **Bidirectional Sync**: Changes in sprint YAML ↔ GitHub issues stay synchronized
3. **Progress Tracking**: Closing GitHub issues automatically updates sprint status
4. **Validation**: All documents validated against schemas with cross-reference checking

### Key Agent Behaviors:

- **Always validate** documents after creation/editing
- **Link documents** via `graph_metadata.relationships`
- **Reference source docs** in sprint tasks (trace decisions back to designs)
- **Use automation** rather than manual GitHub issue creation
- **Follow git workflow** (never push directly to main, always create PRs)

### Quick Reference Files:
- `docs/sprint-workflow-guide.md` - Complete sprint workflow with examples
- `docs/design-to-sprint-workflow.md` - Full design → decision → sprint process
- `context/schemas/` - All document schemas for validation

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

4. **ALWAYS run CI checks and tests before pushing:**
   ```bash
   # Run exact CI checks locally (RECOMMENDED - matches GitHub Actions)
   ./scripts/run-ci-docker.sh

   # Or use Make (uses local Python)
   make lint

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
- Ensure coverage stays above 80.0% (current baseline)
- If pre-commit makes changes, amend your commit before pushing

## 🎯 Current Focus Areas

1. **Immediate Priority**: Increase validator coverage
   - `validators/kv_validators.py` (33.64% → 90%)
   - `validators/config_validator.py` (34.66% → 90%)

2. **Phase 1 Goals**:
   - Overall coverage: 80.0% → 85%
   - Critical modules: All above 85%
   - Complete async error handling

3. **Code Review Focus**:
   - Verify all new code has tests
   - Check for proper async/await usage
   - Ensure validators handle edge cases
   - Look for potential security issues

## 🔧 Recently Resolved Issues

**Issue #171: Local Docker CI Environment & Dependencies (RESOLVED)**
- ✅ **Docker CI Environment**: Rebuilt images with latest dependencies
- ✅ **jsonschema Dependency**: Confirmed working in Docker environment
- ✅ **YAML Workflow Issues**: Fixed line length, indentation, and formatting
- ✅ **Pre-push Hook Reliability**: Enhanced with timeout protection and better error handling
- ✅ **Quick Alternative**: Added `./scripts/quick-pre-push.sh` for fast validation (30s vs 5min)
- ✅ **Documentation**: Updated CLAUDE.md with correct commands and troubleshooting

**Key Improvements:**
- Pre-push hooks now timeout after 5 minutes instead of hanging
- Better error messages with specific troubleshooting guidance
- Multiple bypass options for different scenarios
- Fast validation script for quick iteration
