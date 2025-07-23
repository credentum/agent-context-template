# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1258-run-precommit-fix-violations
# Generated from GitHub Issue #1258
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1258-run-precommit-fix-violations`

## 🎯 Goal (≤ 2 lines)
> Run pre-commit on entire codebase and fix all violations to unblock PR #1244 and ensure consistent code quality across the project.

## 🧠 Context
- **GitHub Issue**: #1258 - [SPRINT-4.2] Run Pre-commit on Entire Codebase and Fix All Violations
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: Implementation
- **Component**: codebase-quality / CI
- **Priority**: High
- **Why this matters**: PR #1244 is blocked due to pre-commit failures, preventing workflow consolidation
- **Dependencies**: Pre-commit hooks installed and configured
- **Related**: PR #1244 (blocked), Issue #1256 (partial fix), Issue #1243 (workflow consolidation)

## 🛠️ Subtasks
Based on expected violations from CI failures:

| File Pattern | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `**/*.py` | Run Black formatter | Tool automation | Fix formatting violations | Low |
| `**/*.py` | Run isort | Tool automation | Fix import ordering | Low |
| `**/*.py` | Fix flake8 issues | Chain-of-thought | Fix linting violations | Medium |
| `**/*.py` | Fix/ignore mypy issues | Few-shot learning | Type checking compliance | Medium |
| All files | Fix pre-commit-hooks | Tool automation | Trailing whitespace, EOF | Low |
| `.pre-commit-config.yaml` | Verify config | Direct inspection | Ensure all hooks configured | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer performing comprehensive code quality fixes across a Python codebase.

**Context**
GitHub Issue #1258: Run pre-commit on entire codebase and fix all violations
- PR #1244 is blocked due to pre-commit failures discovered in #1256
- YAML issues were fixed in #1256, but Python violations remain
- Project uses: Black (100-char lines), isort (Black profile), flake8, mypy, pre-commit-hooks
- Configuration files: .pre-commit-config.yaml, pyproject.toml, mypy.ini, .flake8

**Instructions**
1. **Primary Objective**: Fix all pre-commit violations across the codebase
2. **Scope**: Format/style fixes only - no functional changes
3. **Constraints**:
   - Preserve all existing functionality
   - Use `# type: ignore` sparingly and with justification
   - Follow existing project patterns for fixes
4. **Prompt Technique**: Tool automation for formatters, chain-of-thought for manual fixes
5. **Testing**: Run tests after fixes to ensure no regressions
6. **Documentation**: Document any files excluded from checks if necessary

**Technical Constraints**
• Expected diff ≤ 2000 LoC across multiple files
• Context budget: ≤ 15k tokens (may need multiple passes)
• Performance budget: 1-2 hours
• Code quality: All pre-commit hooks must pass
• CI compliance: Quick Validation and PR Review Simulation must pass

**Output Format**
Apply fixes systematically:
1. Run auto-formatters first (Black, isort)
2. Fix remaining issues manually
3. Verify with pre-commit and CI scripts
Use conventional commits: fix(formatting): apply pre-commit fixes across codebase

## 🔍 Verification & Testing
- `pre-commit run --all-files` (must pass completely)
- `./scripts/claude-ci.sh pre-commit` (structured validation)
- `./scripts/claude-ci.sh all --quick` (quick CI validation)
- `pytest --cov=src --cov-report=term-missing` (ensure tests still pass)
- `./scripts/run-ci-docker.sh` (full Docker CI compliance)

## ✅ Acceptance Criteria
- [X] Run pre-commit on entire codebase locally
- [ ] Fix all Black formatting violations
- [ ] Fix all isort import ordering issues
- [ ] Fix all flake8 linting violations
- [ ] Fix all mypy type checking issues (or add appropriate ignores with justification)
- [ ] Fix all pre-commit-hooks violations (trailing whitespace, EOF, etc.)
- [ ] All CI checks pass (Quick Validation, PR Review Simulation)
- [ ] PR #1244 becomes unblocked and can merge

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 1-2 hours
├── cost_estimate: $0.15
├── complexity: Medium (multiple files, various violation types)
└── files_affected: 50-100 (estimated)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1258
sprint: sprint-4.2
phase: "Phase 2: Implementation"
component: codebase-quality
priority: high
complexity: medium
dependencies: ["pre-commit-config", "PR-1244"]
```