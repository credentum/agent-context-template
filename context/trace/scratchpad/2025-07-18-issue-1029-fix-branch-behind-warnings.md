# Issue #1029 - Fix False Positive Branch Behind Warnings

**Sprint**: sprint-5-2 (current)
**Issue**: https://github.com/user/repo/issues/1029
**Task Template**: context/trace/task-templates/issue-1029-fix-false-positive-branch-behind-warnings.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 2,000 (simple syntax fix)
- **Complexity**: Low - single line change
- **Files affected**: 1 (.github/workflows/pr-conflict-validator.yml)
- **Risk level**: Low - syntax correction with clear evidence

## Step-by-Step Implementation Plan

### 1. Branch Creation
- Create fix branch: `fix/1029-branch-behind-warnings`
- Single commit with conventional commit message

### 2. Implementation
- Fix line 94 in pr-conflict-validator.yml:
  - FROM: `COMMITS_BEHIND=$(git rev-list --count pr-branch..base-branch)`
  - TO: `COMMITS_BEHIND=$(git rev-list --count base-branch..pr-branch)`

### 3. Verification Steps
- Compare with working syntax in ai-pr-monitor.yml
- Test git rev-list commands manually to confirm correct behavior
- Run CI checks to ensure no regressions

### 4. PR Creation
- Title: `fix(ci): correct git rev-list syntax for branch behind calculation`
- Reference issue #1029 with "Fixes #1029"
- Include verification commands in PR description

## Evidence & Justification

**Current Bug (line 94)**:
```bash
COMMITS_BEHIND=$(git rev-list --count pr-branch..base-branch)
```
This counts how many commits base-branch is behind pr-branch, but reports it as commits_behind.

**Correct Implementation (from ai-pr-monitor.yml:518)**:
```bash
COMMITS_BEHIND=$(git rev-list --count origin/$HEAD_REF..origin/$BASE_REF)
```
This counts how many commits HEAD_REF is behind BASE_REF.

**Expected Fix**:
```bash
COMMITS_BEHIND=$(git rev-list --count base-branch..pr-branch)
```

## Success Criteria
- [x] Issue analyzed and root cause identified
- [x] Task template created
- [x] Fix implemented in single commit
- [x] CI checks pass locally
- [x] PR created with proper documentation
- [ ] PR merged successfully (monitoring #1034)

**Execution Start**: 2025-07-18T23:35:00Z
