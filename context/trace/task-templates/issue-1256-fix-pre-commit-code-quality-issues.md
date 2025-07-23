# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1256-fix-pre-commit-code-quality-issues
# Generated from GitHub Issue #1256
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1256-pre-commit-code-quality`

## 🎯 Goal (≤ 2 lines)
> Fix all pre-commit check failures in CI pipeline to unblock PR #1244 and restore CI functionality.

## 🧠 Context
- **GitHub Issue**: #1256 - [SPRINT-4.2] Fix Pre-commit Code Quality Issues Blocking CI
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: Implementation
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: CI pipeline is broken, blocking PR #1244 which consolidates GitHub Actions workflows
- **Dependencies**: Pre-commit hooks, linting tools (Black, isort, flake8, mypy, yamllint)
- **Related**: PR #1244 (blocked), #1243 (workflow consolidation), #1118 (coverage target)

## 🛠️ Subtasks
Based on CI failures analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/ci-unified.yml | Fix YAML | Direct fix | Remove syntax errors, trailing spaces | Low |
| .github/workflows/*.yml | Fix formatting | Pattern matching | Apply yamllint rules consistently | Low |
| Python files (if any) | Format code | Tool usage | Apply Black/isort formatting | Low |
| .pre-commit-config.yaml | Verify config | Analysis | Ensure hooks are properly configured | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing CI pipeline issues related to code quality checks.

**Context**
GitHub Issue #1256: Fix Pre-commit Code Quality Issues Blocking CI
- The Unified CI Pipeline is failing at Quick Validation stage
- Pre-commit checks are preventing PR #1244 from merging
- YAML syntax errors were already partially fixed but more issues remain
- Need to ensure all pre-commit hooks pass

Current pre-commit hooks configured:
- Black (Python formatter)
- isort (Import sorter)
- flake8 (Linter)
- mypy (Type checker)
- yamllint (YAML linter)
- Various pre-commit-hooks (trailing whitespace, EOF, etc.)

**Instructions**
1. **Primary Objective**: Make all pre-commit checks pass in CI
2. **Scope**: Fix formatting/linting issues without changing functionality
3. **Constraints**:
   - Use existing tool configurations (pyproject.toml, .flake8, etc.)
   - Don't modify pre-commit configuration unless necessary
   - Maintain all existing functionality
4. **Prompt Technique**: Direct tool usage - run pre-commit with auto-fix
5. **Testing**: Verify all checks pass locally before pushing
6. **Documentation**: Update any affected documentation

**Technical Constraints**
• Expected diff ≤ 200 LoC (mostly formatting changes)
• Context budget: ≤ 10k tokens
• Performance budget: N/A (formatting only)
• Code quality: All pre-commit checks must pass
• CI compliance: Docker CI and GitHub Actions must succeed

**Output Format**
Apply formatting fixes and commit with conventional commits.
Verify all checks pass before creating PR.

## 🔍 Verification & Testing
- `pre-commit run --all-files` (must pass completely)
- `./scripts/claude-ci.sh pre-commit` (structured output validation)
- `./scripts/run-ci-docker.sh` (full Docker CI validation)
- `yamllint .github/workflows/*.yml` (YAML validation)
- Verify PR #1244 becomes unblocked after fixes

## ✅ Acceptance Criteria
From issue #1256:
- [X] All pre-commit checks pass in CI pipeline
- [X] Quick Validation job in Unified CI Pipeline succeeds
- [X] PR Review Simulation workflow passes
- [X] No YAML syntax errors in workflow files
- [X] Code meets project quality standards (Black, isort, flake8, mypy)

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5,000
├── time_budget: 30-60 minutes
├── cost_estimate: ~$0.15
├── complexity: Low (formatting fixes)
└── files_affected: ~10-20 (workflows + Python files)

Actuals (to be filled):
├── tokens_used: ~35,000
├── time_taken: 45 minutes
├── cost_actual: ~$1.05
├── iterations_needed: 2
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1256
sprint: sprint-4.2
phase: Phase 2: Implementation
component: ci-workflows
priority: high
complexity: low
dependencies: [pre-commit, linting-tools]
```