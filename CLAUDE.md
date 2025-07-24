# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Table of Contents
1. [Repository Context](#repository-context)
2. [Security & Secrets](#1-️-security--secrets-first-things-first)
3. [Quick Start](#2--quick-start)
4. [Project Structure & Key Files](#3--project-structure--key-files)
5. [CLI Cheat-Sheet](#4-️-cli-cheat-sheet-keep-nearby)
6. [Coding & Review Guidelines](#5--coding--review-guidelines)
7. [Recommended Workflows](#6--recommended-workflows)
8. [GitHub Actions Overview](#7-️-github-actions-overview)
9. [Tokens & Cost Control](#8--tokens--cost-control)
10. [Extending Claude](#9--extending-claude)
11. [Project-Specific Resources](#10--project-specific-resources)
12. [Agent Workflow System](#-agent-workflow-system)
13. [Critical Git Workflow Rules](#-critical-git-workflow-rules)
14. [Current Focus Areas](#-current-focus-areas)
15. [Recently Resolved Issues](#-recently-resolved-issues)

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
  - `GH_TOKEN` - Personal Access Token for GitHub API operations (enables CI on bot-created PRs)

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

**Project-specific CI commands:**
- `claude-ci check <file>` – Validate single file (with --fix for auto-correction)
- `claude-ci test` – Run smart test selection (--all for full suite)
- `claude-ci pre-commit` – Pre-commit validation (--fix to auto-fix)
- `claude-ci review` – Local PR review simulation
- `claude-ci all` – Complete validation (--quick or --comprehensive modes)
- `claude-ci help` – Show all CI commands and options

**Other project scripts:**
- `./scripts/check-pr-keywords.sh` – Validate PR has proper issue closing keywords
- `./scripts/claude-test-changed.sh` – Smart test runner (called by claude-ci)
- `./scripts/claude-post-edit.sh` – Post-edit validation
- `./scripts/claude-pre-commit.sh` – Pre-commit wrapper

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

**🚀 Quick CI-First Approach (Recommended):**
```bash
# After making code changes, run smart tests
claude-ci test

# Before committing, validate and auto-fix
claude-ci pre-commit --fix

# Final check before PR
claude-ci all --comprehensive
```

**📋 Traditional Approach (when needed):**
```bash
# Run exact CI checks locally (Docker - matches GitHub Actions exactly!)
./scripts/run-ci-docker.sh

# Alternative: Run CI checks with Make (uses local Python)
make lint

# Run full test suite with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Update coverage metrics
python scripts/update_coverage_metrics.py

# Check specific module
pytest tests/test_validators.py -v

# If pre-commit made changes:
git add -A && git commit --amend --no-edit
```

**⚡ Speed Comparison:**
- `claude-ci test`: 10-30 seconds (smart selection)
- `pytest` full suite: 3-5 minutes
- `claude-ci all --quick`: 30 seconds
- `./scripts/run-ci-docker.sh`: 5+ minutes

### NEW: Unified Claude CI Command Hub
Single command interface for all CI operations with consistent output:

```bash
# Quick file validation after edits
./scripts/claude-ci.sh check src/module.py

# Auto-fix formatting issues
./scripts/claude-ci.sh check src/module.py --fix

# Run smart test selection
./scripts/claude-ci.sh test

# Run full test suite
./scripts/claude-ci.sh test --all

# Pre-commit validation
./scripts/claude-ci.sh pre-commit

# Pre-commit with auto-fix
./scripts/claude-ci.sh pre-commit --fix

# Local PR review simulation
./scripts/claude-ci.sh review

# Complete CI pipeline (standard mode)
./scripts/claude-ci.sh all

# Quick validation (seconds)
./scripts/claude-ci.sh all --quick

# Comprehensive validation (full suite)
./scripts/claude-ci.sh all --comprehensive

# Human-readable output
./scripts/claude-ci.sh all --pretty
```

**Unified CI Features:**
- **Single interface**: One command for all CI operations
- **Consistent output**: JSON format by default for Claude integration
- **Progressive validation**: Quick → Standard → Comprehensive modes
- **Auto-fixing**: Built-in support for fixable issues
- **Integration**: Leverages existing claude-*.sh scripts
- **Help system**: `./scripts/claude-ci.sh help` for full documentation

**Recommended Usage:**
- **After edits**: `claude-ci check <file> --fix`
- **Before commit**: `claude-ci all`
- **Quick validation**: `claude-ci all --quick`
- **PR preparation**: `claude-ci all --comprehensive`

### NEW: Smart Test Runner for Claude Code
Run only tests relevant to your recent changes for faster feedback:

```bash
# After making code changes, run smart test detection
./scripts/claude-test-changed.sh

# Output shows which tests were run and why
# JSON format for easy parsing by Claude

# Run with human-readable output
./scripts/claude-test-changed.sh --format text

# Show what tests would run without executing
./scripts/claude-test-changed.sh --dry-run

# Force full test suite when needed
./scripts/claude-test-changed.sh --all

# Verbose mode for debugging test mapping
./scripts/claude-test-changed.sh --verbose
```

**Smart Test Runner Features:**
- **Automatic detection**: Finds changed files using git diff
- **Intelligent mapping**: Maps source files to their test files
- **Import detection**: Finds tests that import changed modules
- **Fast feedback**: 10-30 seconds vs 3-5 minutes for full suite
- **Structured output**: JSON format with recommendations
- **Coverage tracking**: Module-specific coverage information

**Example Output (JSON):**
```json
{
  "files_changed": ["src/agents/claude_helper.py"],
  "tests_run": ["tests/test_agents.py"],
  "test_results": {
    "passed": 5,
    "failed": 0,
    "skipped": 1
  },
  "coverage": {
    "percentage": 87,
    "modules": ["src.agents.claude_helper"]
  },
  "duration": "2.3s",
  "recommendation": "All tests passed. Coverage is good."
}
```

### NEW: Auto-Format After Claude Edits
When Claude uses Edit/MultiEdit/Write tools, formatting errors can be caught immediately:

```bash
# After editing Python files, validate formatting
./scripts/claude-post-edit.sh src/module.py src/another.py

# Automatically fix formatting issues
./scripts/claude-post-edit.sh src/module.py --fix

# Use the hook functions
source .claude/hooks/post-edit.sh
claude_validate_edits file1.py file2.py  # Check only
claude_format_edits file1.py file2.py    # Check and fix
```

**Claude Workflow Integration:**
1. After using Edit/MultiEdit/Write on Python files, run validation
2. Parse the structured output to understand issues
3. Use --fix flag to automatically resolve formatting problems
4. Stage fixed files before committing

**Structured Output Format:**
```
CLAUDE_FORMAT_CHECK:START
status: success|warning|error
file: <filepath>
issues_found: <count>
auto_fixed: <count>
remaining_issues: <count>
details:
  - type: black|isort|flake8
    message: <issue description>
CLAUDE_FORMAT_CHECK:END
```

This prevents formatting errors from accumulating and reduces CI failures.

### NEW: Pre-Commit Integration for Claude
When working with pre-commit checks, use the Claude-friendly wrapper for structured feedback:

```bash
# Check all files with structured JSON output
./scripts/claude-pre-commit.sh

# Auto-fix all fixable issues
./scripts/claude-pre-commit.sh --fix

# Check specific files
./scripts/claude-pre-commit.sh src/module.py tests/test_module.py

# Human-readable output
./scripts/claude-pre-commit.sh --text

# Use the hook functions
source .claude/hooks/pre-commit.sh
claude_pre_commit_check           # Check all files
claude_pre_commit_fix            # Auto-fix issues
claude_safe_commit "message"     # Commit with pre-commit validation
```

**Claude Workflow Integration:**
1. Before committing, run `claude_pre_commit_check` for structured feedback
2. Parse JSON output to understand specific failures
3. Use `claude_pre_commit_fix` for auto-fixable issues
4. Follow fix guidance for manual corrections
5. Use `claude_safe_commit` for validated commits

**Structured Output Format:**
```json
{
  "overall_status": "FAILED",
  "checks": [
    {
      "hook": "black",
      "status": "FAILED",
      "files_failed": ["src/module.py"],
      "auto_fixable": true
    },
    {
      "hook": "flake8",
      "status": "FAILED",
      "issues": [
        {
          "file": "src/module.py",
          "line": 45,
          "code": "E501",
          "message": "line too long",
          "fix_guidance": "Break line at logical point"
        }
      ],
      "auto_fixable": false
    }
  ],
  "recommendation": "Run with --fix to auto-fix 1 issue(s), then manually fix remaining issues"
}
```

This provides clear, actionable feedback for resolving pre-commit failures efficiently.

### Development Workflow:
When | Ask Claude to...
---|---
After file edit | `claude-ci check <file>` → fix issues → continue
Small fix | read files → plan → patch → `claude-ci test` → `claude-ci pre-commit` → /review → commit
New feature | TDD: write failing tests → commit → implement → `claude-ci all --quick` → iterate
High coverage | `claude-ci test --all` → analyze uncovered lines → write tests → verify >85%
Refactor | `claude-ci all` baseline → refactor → `claude-ci all` → compare results
Debug | reproduce → add logging → `claude-ci test` → fix → add regression test
Before commit | `claude-ci pre-commit --fix` → review changes → commit
Before PR | `claude-ci all --comprehensive` → `claude-ci review` → create PR

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

**🚀 Quick Method (Recommended):**
```bash
# Single command that does everything
claude-ci all

# Or for comprehensive validation
claude-ci all --comprehensive
```

**📋 Manual Method (for understanding):**
1. Run `./scripts/run-ci-docker.sh` (or `make lint`) to match GitHub CI exactly
2. Run `pre-commit run --all-files`
3. Run `pytest --cov=src --cov-report=term-missing`
4. **Fix any issues before proceeding** - This includes:
   - YAML syntax errors (missing colons, indentation issues)
   - Line length violations (> 80 characters)
   - Missing document start markers (`---`)
   - Trailing spaces and whitespace issues

**NEW: CI Migration Phase 3 - Local CI Before Push:**
- **Git hooks installation**: Run `./scripts/install-git-hooks.sh` to enable local CI
- **Automatic pre-push validation**: CI runs locally before allowing push (30s vs 5min on GitHub)
- **Migration modes**:
  - `traditional`: GitHub CI only (current default)
  - `parallel`: Both local and GitHub CI (validation phase)
  - `verifier-only`: Local CI with GitHub verification (target state)
- **Quick validation**: `./scripts/quick-pre-push.sh` for essential checks only
- **Bypass options**:
  - `SKIP_CI=1 git push` (skip CI checks only)
  - `SKIP_HOOKS=1 git push` (skip all hooks)
  - `git push --no-verify` (standard git bypass)
- **Workflow migration**: `python -m src.tools.migrate_workflow` converts workflows to verifier pattern
- **Real-time monitoring**: `./scripts/monitor-ci-migration.sh` tracks migration progress
- **Full documentation**: See `docs/ci-migration-complete-guide.md`

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

## 6.3 🔑 GitHub Token Usage Guide

### When to Use GH_TOKEN vs GITHUB_TOKEN

**Use `GH_TOKEN` (Personal Access Token) when:**
- Creating PRs from workflows (e.g., sprint-update.yml)
- Need CI workflows to run on bot-created PRs
- Updating protected branches
- Triggering other workflows

**Use `GITHUB_TOKEN` (default) when:**
- Reading repository data
- Posting comments on issues/PRs
- Running checks and status updates
- General CI operations that don't create PRs

**Example:**
```yaml
# For PR creation (use GH_TOKEN)
- uses: peter-evans/create-pull-request@v6
  with:
    token: ${{ secrets.GH_TOKEN }}  # ✅ CI will run on created PR

# For reading/commenting (GITHUB_TOKEN is fine)
env:
  GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # ✅ Sufficient for gh CLI read operations
```

## 6.4 🔧 CI Integration for Claude Code

Claude Code has specialized CI tools that catch errors early and provide structured feedback. Use these commands throughout your development workflow.

### Quick Reference

| Command | Purpose | When to Use | Typical Duration |
|---------|---------|-------------|------------------|
| `claude-ci check <file>` | Validate single file | After editing any Python file | ~1 second |
| `claude-ci check <file> --fix` | Auto-fix formatting | When validation shows fixable issues | ~2 seconds |
| `claude-ci test` | Run smart test selection | Before committing changes | 10-30 seconds |
| `claude-ci test --all` | Run full test suite | When smart selection insufficient | 3-5 minutes |
| `claude-ci pre-commit` | Pre-commit validation | Before git commit | 30-60 seconds |
| `claude-ci pre-commit --fix` | Auto-fix + validate | When pre-commit fails | 45-90 seconds |
| `claude-ci review` | Local PR review | Before creating PR | 2-3 minutes |
| `claude-ci all` | Complete validation | Final check before PR | 3-5 minutes |
| `claude-ci all --quick` | Quick validation | Rapid iteration | 30 seconds |
| `claude-ci all --comprehensive` | Full validation | Critical changes | 10+ minutes |

### CI Commands in Detail

#### Check Individual Files
After editing any Python file, validate immediately:
```bash
claude-ci check src/module.py
```

Expected output:
```json
{
  "status": "PASSED",
  "checks": {
    "black": "PASSED",
    "isort": "PASSED",
    "flake8": "PASSED",
    "mypy": "PASSED"
  },
  "duration": "0.8s",
  "next_action": "File is clean, proceed with development"
}
```

If issues are found:
```json
{
  "status": "FAILED",
  "checks": {
    "black": "FAILED",
    "isort": "PASSED",
    "flake8": "FAILED",
    "mypy": "PASSED"
  },
  "auto_fixable": true,
  "fix_command": "claude-ci check src/module.py --fix",
  "issues": [
    {
      "tool": "black",
      "message": "File would be reformatted"
    },
    {
      "tool": "flake8",
      "line": 45,
      "code": "E501",
      "message": "line too long (92 > 88 characters)"
    }
  ]
}
```

#### Smart Test Runner
Run only tests affected by your changes:
```bash
claude-ci test
```

Output shows intelligent test selection:
```json
{
  "mode": "smart",
  "files_changed": ["src/storage/vector_db.py"],
  "tests_selected": [
    "tests/test_storage/test_vector_db.py",
    "tests/integration/test_vector_search.py"
  ],
  "reason": "Direct test mapping + import detection",
  "test_results": {
    "passed": 23,
    "failed": 0,
    "skipped": 2
  },
  "coverage": {
    "percentage": 89,
    "changed_files": 92
  },
  "duration": "12.3s",
  "recommendation": "All tests passed. Good coverage on changes."
}
```

#### Pre-Commit Validation
Before committing, ensure all checks pass:
```bash
claude-ci pre-commit
```

Structured output for parsing:
```json
{
  "overall_status": "FAILED",
  "checks": [
    {
      "hook": "black",
      "status": "FAILED",
      "files_failed": ["src/module.py"],
      "auto_fixable": true
    },
    {
      "hook": "flake8",
      "status": "FAILED",
      "issues": [
        {
          "file": "src/module.py",
          "line": 45,
          "code": "E501",
          "message": "line too long",
          "fix_guidance": "Break line at logical point or use parentheses"
        }
      ],
      "auto_fixable": false
    }
  ],
  "fix_command": "claude-ci pre-commit --fix",
  "recommendation": "Run fix command for auto-fixable issues, then manually fix remaining"
}
```

#### Local PR Review
Simulate full PR review before pushing:
```bash
claude-ci review
```

Comprehensive review output:
```json
{
  "verdict": "REQUEST_CHANGES",
  "summary": {
    "files_changed": 5,
    "lines_added": 127,
    "lines_removed": 43
  },
  "issues": {
    "blocking": [
      {
        "severity": "high",
        "file": "src/api/handler.py",
        "line": 67,
        "issue": "Missing error handling for database connection",
        "suggestion": "Add try-except block around connection.execute()"
      }
    ],
    "non_blocking": [
      {
        "severity": "low",
        "file": "tests/test_api.py",
        "issue": "Test coverage below target (82% < 85%)",
        "suggestion": "Add tests for error conditions"
      }
    ]
  },
  "ci_checks": {
    "lint": "PASSED",
    "tests": "PASSED",
    "coverage": "WARNING",
    "type_check": "PASSED"
  },
  "next_action": "Fix blocking issues before creating PR"
}
```

### Progressive Validation Strategy

Use progressive validation for efficiency:

#### 1. Quick Check (seconds)
```bash
claude-ci all --quick
```
- Basic format and syntax validation
- Import checks
- Fast type checking
- Use during active development

#### 2. Standard Check (1-2 minutes)
```bash
claude-ci all
```
- Full linting suite
- Smart test selection
- Pre-commit hooks
- Coverage analysis
- Use before commits

#### 3. Comprehensive Check (5+ minutes)
```bash
claude-ci all --comprehensive
```
- Everything in standard
- Full test suite
- Integration tests
- Performance benchmarks
- PR review simulation
- Use before creating PR

### Integration with Development Workflow

Updated workflow with CI checkpoints:

| When | Claude Command Sequence |
|------|------------------------|
| After file edit | `claude-ci check <file>` → fix issues → continue |
| After multiple edits | `claude-ci all --quick` → address failures |
| Before testing | `claude-ci test` → check coverage impact |
| Pre-commit | `claude-ci pre-commit --fix` → review changes |
| Pre-PR | `claude-ci all --comprehensive` → ensure clean |
| PR blocked | `claude-ci review` → fix blocking issues |

### CI Troubleshooting

#### Common Issues and Solutions

**Format errors after edit:**
```bash
# See what would change
claude-ci check src/module.py

# Auto-fix formatting
claude-ci check src/module.py --fix

# Verify fix worked
claude-ci check src/module.py
```

**Pre-commit keeps failing:**
```bash
# Get detailed error report
claude-ci pre-commit | jq '.checks[] | select(.status=="FAILED")'

# Try auto-fix first
claude-ci pre-commit --fix

# Check what remains
claude-ci pre-commit | jq '.issues'
```

**Coverage regression:**
```bash
# Check current coverage
claude-ci test --all | jq '.coverage'

# Find uncovered lines
pytest --cov=src --cov-report=term-missing | grep -A 10 "TOTAL"

# Run specific test file
pytest tests/test_module.py -v --cov=src.module
```

**Review shows REQUEST_CHANGES:**
```bash
# Get blocking issues only
claude-ci review | jq '.issues.blocking'

# Check specific file issues
claude-ci review | jq '.issues.blocking[] | select(.file=="src/module.py")'

# After fixes, verify
claude-ci review | jq '.verdict'
```

### CI Error Reference

| Error | Meaning | Fix |
|-------|---------|-----|
| `E501 line too long` | Line exceeds 88 chars | Break at logical point or use parentheses |
| `F401 imported but unused` | Unnecessary import | Remove the import |
| `E302 expected 2 blank lines` | Class/function spacing | Add blank line |
| `I001 import order` | Wrong import order | Run with --fix flag |
| `B008 function call in argument` | Dangerous default | Use `None` and check in function |
| `type: ignore` needed | MyPy can't infer type | Add type annotation or ignore with comment |

### Best Practices

1. **Run checks immediately** after edits to catch issues early
2. **Use --fix flags** for automatic corrections
3. **Parse JSON output** for specific error details
4. **Follow progressive validation** to save time
5. **Address blocking issues first** in review feedback
6. **Keep coverage above baseline** (currently 78.0%)

### Performance Tips

- Use `claude-ci test` instead of `claude-ci test --all` when possible (80% faster)
- Run `claude-ci all --quick` frequently during development
- Save `claude-ci all --comprehensive` for final validation
- Cache Docker images locally for faster `claude-ci review`
- Use parallel execution when checking multiple files

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

   **🚀 Quick Method with claude-ci (RECOMMENDED):**
   ```bash
   # Run comprehensive validation
   claude-ci all --comprehensive

   # If issues found, auto-fix what's possible
   claude-ci pre-commit --fix
   git add -A
   git commit --amend --no-edit
   ```

   **📋 Traditional Method:**
   ```bash
   # Run exact CI checks locally (matches GitHub Actions)
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

**Issue #1303: Local CI Pipeline - ARC Reviewer & Test Failures (RESOLVED)**
- ✅ **ARC Reviewer Integration**: Fixed exit code handling - now exits with code 1 on REQUEST_CHANGES
- ✅ **Test Failure Propagation**: Verified test failures properly exit with non-zero codes
- ✅ **CI Pipeline Logic**: All stages run for complete diagnostics, but overall exit code reflects failures
- ✅ **Clear Error Messages**: Structured JSON output shows exactly which checks failed
- ✅ **Performance**: Quick mode < 30s, Comprehensive mode < 5min as required
- ✅ **Integration Tests**: Added tests to verify CI properly blocks on failures

**What was fixed:**
- `src/agents/arc_reviewer.py` now calls `sys.exit(1)` when verdict is REQUEST_CHANGES
- `scripts/claude-ci.sh` already had correct exit code propagation (verified)
- Local CI now matches GitHub CI behavior exactly
- Blocking issues prevent PR creation with clear error messages
