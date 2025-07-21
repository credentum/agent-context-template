# Scratchpad: Issue #1044 - Git Rev-List Syntax Fix

## Issue Link
https://github.com/anthropics/agent-context-template/issues/1044

## Sprint Reference
- Sprint: sprint-5-2
- Phase: Phase 2: Implementation
- Component: ci

## Task Template
Reference: `/workspaces/agent-context-template/context/trace/task-templates/issue-1044-git-rev-list-syntax-fix.md`

## Token Budget & Complexity
- Estimated tokens: 1k (trivial single-line fix)
- Complexity: Trivial
- Time estimate: 10 minutes

## Implementation Plan

### Step 1: Create Feature Branch
- Branch name: `fix/1044-git-rev-list-syntax`
- Base: main (after ensuring it's up to date)

### Step 2: Make the Fix
- File: `.github/workflows/pr-conflict-validator.yml`
- Line: 97
- Change: `pr-branch..base-branch` → `base-branch..pr-branch`

### Step 3: Verify Logic
- Confirm line 98 (COMMITS_AHEAD) remains unchanged
- Compare with working implementation in ai-pr-monitor.yml:518

### Step 4: Testing
- Run CI checks locally
- Create test branches to verify behavior

### Step 5: Create PR
- Title: "fix(ci): correct git rev-list syntax for branch behind calculation"
- Body: Reference issue #1044, explain the fix
- Labels: bug, component:ci, sprint-current

## Git Command Reference
- `git rev-list --count A..B` = commits in B that are not in A
- To find how many commits PR is behind base: `base..pr`
- Current bug: using `pr..base` which gives opposite result

## Related Context
- Parent issue: #1029 (larger workflow fixes)
- Sibling issues: #1043 (API fix), #1045 (phantom checks)
- Working example: ai-pr-monitor.yml line 518
