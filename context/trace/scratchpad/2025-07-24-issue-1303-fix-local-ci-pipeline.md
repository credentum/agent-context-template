# Execution Plan: Issue #1303 - Fix Local CI Pipeline

## Issue Link
- GitHub Issue: #1303 - [URGENT] Fix Local CI Pipeline - ARC Reviewer & Test Failures Not Caught
- Sprint: sprint-current
- Priority: CRITICAL

## Task Template Reference
- Template: `context/trace/task-templates/issue-1303-fix-local-ci-pipeline.md`
- Token Budget: 50k
- Complexity: HIGH

## Analysis Summary

### Root Cause Analysis
1. **ARC Reviewer Integration**:
   - `claude-ci.sh` has ARC reviewer integration (line 313: `run_arc_reviewer()`)
   - BUT: Exit codes not properly propagated when ARC verdict is REQUEST_CHANGES
   - The function returns exit code but doesn't fail the overall review

2. **Test Failure Propagation**:
   - `claude-test-changed.sh` returns proper exit codes (line 329, 482, 485)
   - BUT: `claude-ci.sh` cmd_test() doesn't propagate failures properly
   - Test failures are captured but don't fail the overall CI pipeline

3. **Overall Status Logic**:
   - Individual check failures don't always set overall_status to FAILED
   - Some checks use `|| true` which swallows exit codes

## Implementation Plan

### Step 1: Fix ARC Reviewer Exit Code Handling
- In `claude-ci.sh`, modify `cmd_review()` to fail when ARC verdict is REQUEST_CHANGES
- Ensure arc_exit_code propagates to overall status
- Remove any `|| true` that might swallow ARC failures

### Step 2: Fix Test Failure Propagation
- In `claude-ci.sh`, modify `cmd_test()` to properly return non-zero on test failures
- Ensure test exit codes propagate through the pipeline
- Fix cmd_all() to fail if any stage fails

### Step 3: Fix Overall Pipeline Logic
- Review all `run_stage` calls in cmd_all()
- Remove `|| true` where failures should block
- Ensure EXIT_CODE is properly set and returned

### Step 4: Add Integration Tests
- Create `tests/test_ci_integration.py`
- Test that CI fails on:
  - Test failures
  - ARC Reviewer REQUEST_CHANGES
  - Pre-commit violations
- Test that exit codes propagate correctly

### Step 5: Verify Docker CI Environment
- Check `run-ci-docker.sh` for similar issues
- Ensure it also propagates failures correctly

## Execution Steps

1. Create feature branch
2. Fix exit code handling in claude-ci.sh
3. Verify test failure propagation
4. Add integration tests
5. Test manually with failing scenarios
6. Run full CI validation
7. Create PR with comprehensive description

## Success Metrics
- Local CI blocks on test failures
- Local CI blocks on ARC Reviewer issues
- Exit codes properly propagated
- Clear error messages provided
- CI time within performance budget
