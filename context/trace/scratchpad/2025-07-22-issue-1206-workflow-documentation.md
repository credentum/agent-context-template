# Execution Plan: Issue #1206 - Fix Workflow Documentation

**Date**: 2025-07-22
**Issue**: [#1206](https://github.com/anthropics/agent-context-template/issues/1206)
**Sprint**: sprint-4.2
**Task Template**: `context/trace/task-templates/issue-1206-fix-workflow-documentation.md`

## Problem Summary
The workflow documentation has a critical timing issue where completion logs are created in Phase 5 AFTER the PR is already pushed, causing these files to only exist locally and never be included in the actual PR.

## Token Budget & Complexity
- **Estimated Tokens**: 5,000
- **Complexity**: Low (documentation reordering)
- **Time Estimate**: 30 minutes
- **Files to Modify**: 1 (`.claude/workflows/workflow-issue.md`)

## Step-by-Step Implementation Plan

### 1. Analyze Current Workflow Structure
- Review Steps 9-12 in the workflow
- Understand current Phase 4 and Phase 5 separation
- Identify where completion logs are currently created (Step 12, Phase 5)

### 2. Reorder Phase 4 Steps
- Move completion log creation from Step 12 to Step 10 (before PR creation)
- Ensure all documentation is committed before `gh pr create` command
- Update Step 10 to include:
  - Task template updates with actuals
  - Completion log creation
  - Commit of all documentation files
  - Then PR creation

### 3. Update Phase 5 Focus
- Change Step 12 to focus on verification only
- Add checks to ensure all documentation is in the PR
- Remove documentation creation from Phase 5
- Keep only cleanup and archival tasks

### 4. Update Documentation Strategy Table
- Modify lines 50-57 to reflect new timing
- Phase 4: "Before PR creation" for completion logs
- Phase 5: "After PR creation" changes to verification only

### 5. Add Verification Steps
- Add command to verify documentation files are in PR
- Include example using `gh pr view --json files`
- Add troubleshooting section for missing documentation

### 6. Update Error Handling Section
- Add new error case: "Documentation Not in PR"
- Provide solution steps for adding missing documentation
- Emphasize prevention through proper workflow timing

## Implementation Notes
- Critical sections to modify:
  - Step 9: Pre-PR Preparation (needs completion log addition)
  - Step 10: PR Creation (must happen after all commits)
  - Step 12: Final Documentation (becomes verification only)
  - Documentation Strategy table (lines 47-59)
  - Error Handling section (add new case)

## Success Criteria
- Workflow prevents documentation gaps
- All artifacts included in PR automatically
- Clear timing guidance in documentation strategy
- Verification steps catch any missing files

## Next Actions
1. Create feature branch
2. Modify workflow file according to plan
3. Commit documentation before implementation
4. Implement changes
5. Create PR with all documentation included
