# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1299-fix-github-ci-failures
# Generated from GitHub Issue #1299
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1299-github-ci-failures`

## 🎯 Goal (≤ 2 lines)
> Fix GitHub CI failures preventing PR merges after ARC-Reviewer integration, specifically coverage showing 0% and verdict "UNKNOWN"

## 🧠 Context
- **GitHub Issue**: #1299 - [SPRINT-4.3] Fix GitHub CI failures preventing PR merges
- **Sprint**: sprint-4.3
- **Phase**: Phase 4.2: Critical Bug Fix
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: Blocking all PR merges and development velocity
- **Dependencies**: PR #1298 (ARC-Reviewer integration), GitHub Actions workflows
- **Related**: CI Migration Phase 3 (#1296), ARC-Reviewer integration (#1297)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/claude-code-review.yml | modify | debugging | Fix ARC-Reviewer integration | Medium |
| .github/workflows/test.yml | modify | debugging | Fix coverage calculation | Medium |
| scripts/claude-ci.sh | modify | debugging | Fix local CI issues | Low |
| .coverage-config.json | check | analysis | Verify coverage thresholds | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on GitHub Actions CI/CD pipelines.

**Context**
GitHub Issue #1299: [SPRINT-4.3] Fix GitHub CI failures preventing PR merges
After implementing ARC-Reviewer integration in PR #1298, GitHub CI checks are failing with:
- Coverage showing 0% (should be ~78%)
- ARC-Reviewer verdict "UNKNOWN" instead of APPROVE/REQUEST_CHANGES
- Lint and test checks failing
Current codebase uses GitHub Actions with pytest-cov for coverage, ARC-Reviewer for automated reviews.
Related files: .github/workflows/claude-code-review.yml, .github/workflows/test.yml, scripts/claude-ci.sh

**Instructions**
1. **Primary Objective**: Fix GitHub CI failures to restore PR merge capability
2. **Scope**: Address CI configuration issues without breaking existing local CI
3. **Constraints**:
   - Follow existing GitHub Actions patterns
   - Maintain backward compatibility with local CI tools
   - Keep coverage reporting accurate (should show ~78%)
4. **Prompt Technique**: Debugging approach because issue involves troubleshooting broken CI
5. **Testing**: Validate fixes by checking CI status on test PR
6. **Documentation**: Update workflow documentation if changes affect usage

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 3 files
• Context budget: ≤ 15k tokens
• Performance budget: CI fixes should not increase run time
• Code quality: YAML syntax validation, no workflow breaking changes
• CI compliance: All GitHub Actions checks must pass

**Output Format**
Return complete implementation addressing CI failures.
Use conventional commits: fix(ci): description

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Create test PR to validate CI fixes
- **Integration tests**: Verify ARC-Reviewer integration works properly

## ✅ Acceptance Criteria
- [ ] GitHub CI coverage reports accurate percentage (>= 78%)
- [ ] ARC-Reviewer provides clear APPROVE/REQUEST_CHANGES verdict
- [ ] Lint checks pass for non-infrastructure changes
- [ ] Test checks pass consistently
- [ ] PR #1298 can be merged successfully

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000 (moderate CI debugging)
├── time_budget: 45 minutes (focused troubleshooting)
├── cost_estimate: $0.45 (at current rates)
├── complexity: medium (CI configuration debugging)
└── files_affected: 3 (GitHub Actions workflows + scripts)

Actuals (filled after completion):
├── tokens_used: ~12000 (under budget)
├── time_taken: ~35 minutes (under budget)
├── cost_actual: $0.36 (under budget)
├── iterations_needed: 1 (single implementation cycle)
└── context_clears: 0 (stayed within limits)
```

## 🏷️ Metadata
```yaml
github_issue: 1299
sprint: sprint-4.3
phase: Phase 4.2
component: ci-workflows
priority: high
complexity: medium
dependencies: [1298, 1297, 1296]
```
