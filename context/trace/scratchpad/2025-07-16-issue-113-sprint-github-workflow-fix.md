# Issue #113: Sprint-to-GitHub Issue Creation Workflow Fix

**Date**: 2025-07-16
**Issue**: [#113](https://github.com/credentum/agent-context-template/issues/113)
**Sprint**: sprint-4.1
**Status**: In Progress

## Problem Analysis

The automated workflow that creates GitHub issues from sprint plan updates is failing. After investigating the GitHub Actions logs, I found the root cause:

### Root Cause
The workflow `.github/workflows/generate-sprint-issues.yml` is failing on line 79-82 with a "bad object" error:

```bash
fatal: bad object f1dd22611be725df414fbc0534713de797412468
```

The issue is in the git diff command that uses invalid commit references:
```bash
git diff --name-only \
  ${{ github.event.pull_request.base.sha }} \
  ${{ github.event.pull_request.head.sha }}
```

### Analysis of the Issue

1. **Invalid Git References**: The workflow is trying to use PR event commit SHAs that are not available in the checkout context
2. **Checkout Depth**: The workflow only fetches depth=2, which may not include the referenced commits
3. **Workflow Trigger**: The issue occurs when the workflow runs on `pull_request.closed` events

### Current Failed Tasks

Looking at `context/sprints/sprint-4.1.yaml`, there are two tasks that should have been automatically created as GitHub issues:

1. **Phase 8**: "Bidirectional Workflow Validation Test" (line 288-323)
   - Has comment: `# github_issue: Will be populated automatically by sprint issue linker`
   - Missing `github_issue` number

2. **Phase 9**: "Test Sprint Update Workflow Duplicate Prevention" (line 331-378)
   - Has comment: `# github_issue: Will be populated automatically by sprint issue linker`
   - Missing `github_issue` number

## Solution Plan

### 1. Fix the Git Diff Command
Replace the problematic git diff with a more robust approach:
- Use `HEAD~1` to compare with the previous commit
- Increase fetch depth to ensure we have the necessary commits
- Add better error handling for git operations

### 2. Improve Workflow Reliability
- Add validation to ensure git references exist before using them
- Implement fallback mechanisms for different trigger scenarios
- Add better logging for debugging

### 3. Test the Fix
- Create a test branch with the fix
- Update sprint-4.1.yaml to trigger the workflow
- Verify that the two missing issues are created

### 4. Validate Bidirectional Sync
- Test that created issues sync back to the sprint YAML
- Verify that issue status changes reflect in the sprint
- Confirm that the workflow handles all edge cases

## Implementation Details

### Files to Modify:
- `.github/workflows/generate-sprint-issues.yml` - Main workflow fix
- `context/sprints/sprint-4.1.yaml` - Remove comment lines and test

### Key Changes:
1. Replace git diff command with a more reliable approach
2. Increase fetch-depth from 2 to a higher number or use 0 for full history
3. Add error handling and validation
4. Improve logging for better debugging

### Testing Strategy:
1. Test with a manual workflow dispatch first
2. Create a PR that modifies sprint-4.1.yaml to trigger automatic workflow
3. Verify that both pending tasks get GitHub issues created
4. Test bidirectional sync functionality

## Dependencies
- GitHub Actions workflow permissions (already configured)
- Access to modify sprint YAML files
- Ability to test workflow changes safely

## Next Steps
1. ✅ Complete investigation and create scratchpad
2. 🔄 Fix the git diff command in generate-sprint-issues.yml
3. 🔄 Test the workflow fix with sprint-4.1.yaml
4. 🔄 Verify bidirectional sync works correctly
5. 🔄 Update CLAUDE.md if needed for future reference

## Risk Assessment
- **Low Risk**: The fix is isolated to the workflow file
- **Backup**: Original workflow is preserved in git history
- **Rollback**: Easy to revert if issues occur
- **Testing**: Can be tested in feature branch before merging

---
*Investigation completed: 2025-07-16*
*Next: Implement the workflow fix*
