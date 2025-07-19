# Git PR Commands - Centralized Solution

This reusable action solves the recurring git command issues across workflows by providing tested, reliable git commands for PR analysis.

## Problem Solved

**Before**: Git commands scattered across 4+ workflows, each with potential failures:
```yaml
# ❌ Fragile - repeated in multiple workflows
COMMITS_BEHIND=$(git rev-list --count origin/$HEAD_REF..origin/$BASE_REF 2>/dev/null || echo "0")
```

**After**: Single source of truth with proper error handling:
```yaml
# ✅ Reliable - centralized and tested
- uses: ./.github/actions/git-pr-commands
  with:
    command: commits-behind
    head-sha: ${{ github.event.pull_request.head.sha }}
    base-sha: ${{ github.event.pull_request.base.sha }}
```

## Usage Examples

### Count Commits Behind
```yaml
- name: Check if branch is behind
  id: behind-check
  uses: ./.github/actions/git-pr-commands
  with:
    command: commits-behind
    head-sha: ${{ github.event.pull_request.head.sha }}
    base-sha: ${{ github.event.pull_request.base.sha }}

- name: Use result
  run: |
    echo "Branch is ${{ steps.behind-check.outputs.result }} commits behind"
```

### Get Changed Files
```yaml
- name: Get changed files
  id: changed-files
  uses: ./.github/actions/git-pr-commands
  with:
    command: diff-files
    head-sha: ${{ github.event.pull_request.head.sha }}
    base-sha: ${{ github.event.pull_request.base.sha }}
```

### Migration Guide

Replace these patterns in existing workflows:

| Old Pattern | New Pattern |
|-------------|-------------|
| `git rev-list --count origin/$HEAD_REF..origin/$BASE_REF` | `uses: ./.github/actions/git-pr-commands` with `command: commits-behind` |
| `git rev-list --count origin/$BASE_REF..origin/$HEAD_REF` | `uses: ./.github/actions/git-pr-commands` with `command: commits-ahead` |
| `git diff --name-only origin/main...HEAD` | `uses: ./.github/actions/git-pr-commands` with `command: diff-files` |
| `git log --oneline origin/main...HEAD` | `uses: ./.github/actions/git-pr-commands` with `command: log-commits` |

## Workflows to Update

1. **pr-conflict-validator.yml** - Lines 111-112
2. **ai-pr-monitor.yml** - Line 519
3. **claude-code-review.yml** - Lines 147-148
4. **Any future workflows** - Use this action instead of raw git commands

## Benefits

- ✅ **Single source of truth** - Fix once, works everywhere
- ✅ **Proper error handling** - No more silent failures
- ✅ **Consistent behavior** - Same logic across all workflows
- ✅ **Easy testing** - Test the action independently
- ✅ **Future-proof** - Add new git commands without workflow changes
