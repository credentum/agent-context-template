# Execution Scratchpad: GitHub Label System Cleanup
**Date**: 2025-07-25
**Issue**: #1295 - [SPRINT-4.3] GitHub Label System Cleanup and Standardization
**Sprint**: sprint-4.3
**Task Template**: context/trace/task-templates/issue-1295-github-label-cleanup.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 15,000
- **Complexity**: Medium
- **Files to Modify**: 6
- **Risk Level**: Low (with dry-run testing)

## Execution Plan

### Current State Analysis (COMPLETED)
- Found 30 labels total (not 60+ as originally thought)
- Missing labels that templates reference:
  - `claude-ready`
  - `investigation`
  - `needs-scope`
- Workflow issue: claude-code-review.yml line 823 creates labels without checking
- Inconsistent naming: phase:4.1 format but templates use phase:?

### Step-by-Step Implementation Plan

1. **Create missing labels first** (5 min)
   - Add `claude-ready`, `investigation`, `needs-scope`
   - This unblocks templates immediately

2. **Create label validation utility** (20 min)
   - scripts/validate-labels.py
   - Check if label exists before use
   - Suggest closest match if not found

3. **Update claude-code-review.yml** (15 min)
   - Add label validation at line 823
   - Use validate-labels.py utility
   - Fallback to safe defaults

4. **Fix issue templates** (10 min)
   - sprint-task.md: Remove phase:?, use sprint-current
   - investigation.md: Ensure uses valid labels

5. **Create migration script** (30 min)
   - scripts/migrate-labels.sh
   - Map old to new labels
   - Dry-run mode by default
   - Progress reporting

6. **Write documentation** (20 min)
   - docs/github-label-guidelines.md
   - Label categories and usage
   - Naming conventions

7. **Test everything** (20 min)
   - Run migration in dry-run
   - Test template creation
   - Verify workflow changes

## Risk Mitigation
- Create new labels before removing old ones
- All changes are backward compatible
- Migration script has dry-run mode
- Can rollback label changes via GitHub UI

## Progress Tracking
- [ ] Missing labels created
- [ ] Validation utility written
- [ ] Workflow updated
- [ ] Templates fixed
- [ ] Migration script ready
- [ ] Documentation complete
- [ ] Testing done
- [ ] PR created

## Notes & Observations
- The issue description overestimated the problem (30 vs 60+ labels)
- Main issue is missing labels and lack of validation
- Current labels are actually well-organized (component:*, priority:*, etc.)
- Focus on adding validation to prevent future issues
