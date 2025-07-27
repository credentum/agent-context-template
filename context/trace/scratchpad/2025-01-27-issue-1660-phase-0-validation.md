# Execution Plan: Issue #1660 - Phase 0 Validation Logic

**Date**: 2025-01-27
**Issue**: #1660 - Add missing Phase 0 (Investigation) validation logic to workflow system
**Sprint**: sprint-current
**Task Template**: context/trace/task-templates/issue-1660-phase-0-validation-logic.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 5,000
- **Complexity**: Low (single file modification)
- **Time Estimate**: 30 minutes

## Step-by-Step Implementation Plan

### 1. Add Phase 0 to validate_phase_prerequisites()
- Add case for `phase == 0` around line 60
- Check that issue is accessible using existing `_check_issue_accessible()` method
- Follow pattern from Phase 1 validation

### 2. Add Phase 0 to validate_phase_outputs()
- Add case for `phase == 0` around line 98 (after `if phase == 1:` block)
- Handle two scenarios:
  - If investigation was skipped: validate scope_clarity is "clear"
  - If investigation was performed: check for investigation report file
- Check for required outputs based on workflow_executor.py behavior

### 3. Implementation Details
Based on workflow_executor.py analysis:
- Investigation can be skipped if scope is clear
- If performed, creates report at: `context/trace/investigations/issue-{number}-investigation.md`
- Required outputs when skipped: `scope_clarity="clear"`, `skipped=True`
- Required outputs when performed: `investigation_completed=True`, `root_cause_identified=True`

### 4. Testing Strategy
- Test Phase 0 validation with skipped investigation
- Test Phase 0 validation with performed investigation
- Ensure no regression in other phase validations
- Run pre-commit hooks

## Code Changes Location
- File: `.claude/workflows/workflow-validator.py`
- Add Phase 0 case in `validate_phase_prerequisites()` method
- Add Phase 0 case in `validate_phase_outputs()` method
- No new helper methods needed (reuse existing ones)

## Verification Steps
1. Run workflow-validator.py manually for Phase 0
2. Test with both skipped and performed investigation scenarios
3. Ensure Phase 1 still requires Phase 0 completion
4. Run pre-commit hooks for code quality
