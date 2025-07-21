# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1085-pr-1069-merge-conflicts
# Generated from GitHub Issue #1085
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1085-pr-1069-merge-conflicts`

## 🎯 Goal (≤ 2 lines)
> Resolve merge conflicts in PR #1069, update branch with main, fix PR description,
> and ensure all CI checks pass so the PR can be merged.

## 🧠 Context
- **GitHub Issue**: #1085 - [PR #1069] Resolve merge conflicts and update branch with main
- **Sprint**: Not specified
- **Phase**: Not specified
- **Component**: tests
- **Priority**: bug
- **Why this matters**: PR #1069 is blocked from merging due to conflicts and failing CI checks
- **Dependencies**: Issue #1084 (coverage configuration) - RESOLVED
- **Related**: PR #1069, Issue #1057 (original issue being fixed)

## 🛠️ Subtasks
Branch update and conflict resolution tasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| PR #1069 branch | checkout & update | Direct Commands | Sync with main branch | High |
| Merge conflicts | resolve | Manual Resolution | Fix conflicts in test files | High |
| PR description | modify | GitHub CLI | Fix self-referential issue | Low |
| CI validation | verify | Test Execution | Ensure all checks pass | High |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer resolving merge conflicts and CI failures in a pull request.

**Context**
GitHub Issue #1085: [PR #1069] Resolve merge conflicts and update branch with main
- PR #1069 is trying to fix issue #1057 about auto-formatting Claude edits
- Branch `feature/1057-auto-format-claude-edits` is behind main and has conflicts
- Coverage configuration was fixed in issue #1084 (now resolved)
- PR incorrectly says "Closes #1069" (self-referential)
- CI checks are failing due to coverage and test issues

**Instructions**
1. **Primary Objective**: Resolve merge conflicts and update PR #1069 to be mergeable
2. **Scope**: Update branch, resolve conflicts, fix PR description, ensure CI passes
3. **Constraints**:
   - Preserve the intent of PR #1069's changes
   - Ensure all CI checks pass after update
   - Fix PR description to reference correct issue (#1057)
4. **Prompt Technique**: Direct command execution for git operations
5. **Testing**: Run Docker CI locally before pushing
6. **Documentation**: Update PR description with correct issue reference

**Technical Constraints**
• Expected diff ≤ 50 LoC (mostly conflict resolution)
• Context budget: ≤ 10k tokens
• Performance budget: Standard CI checks
• Code quality: All CI checks must pass
• CI compliance: Docker CI validation required

**Output Format**
Execute git commands to update branch and resolve conflicts.
Update PR description to reference issue #1057.

## 🔍 Verification & Testing
- `git status` (verify clean working directory)
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Verify bidirectional workflow tests pass
- **Integration tests**: Ensure no regression in test suite

## ✅ Acceptance Criteria
- Branch is up to date with main
- No merge conflicts remain
- All CI checks pass (coverage, tests, linting)
- PR description correctly references issue #1057 (not #1069)
- PR can be merged without blockers

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 10000
├── time_budget: 30 minutes
├── cost_estimate: $0.50
├── complexity: Medium (merge conflicts)
└── files_affected: ~5-10 (test files with conflicts)

Actuals (to be filled):
├── tokens_used: ~8000
├── time_taken: 15 minutes
├── cost_actual: $0.40
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1085
sprint: null
phase: null
component: tests
priority: bug
complexity: medium
dependencies: [1084]
```
