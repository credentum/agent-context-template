# 2025-07-27 Issue #1661 Fix Phase 2 Task Template Path Validation Mismatch

**GitHub Issue**: [#1661](https://github.com/owner/repo/issues/1661) - Fix Phase 2 task template path validation mismatch
**Sprint**: sprint-current
**Priority**: bug
**Component**: workflow-automation

**Task Template**: context/trace/task-templates/issue-1661-fix-phase-2-task-template-path-validation-mismatch.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 2000 (simple file fix)
- **Estimated Time**: 15 minutes
- **Complexity**: Low - single file bug fix with clear solution
- **Files Affected**: 1 (.claude/workflows/workflow-validator.py)

## Execution Plan

### Problem Analysis
Phase 2 validation in workflow-validator.py:71 checks for wrong task template path:
- **Current (broken)**: `issue_{issue_number}_tasks.md` in root
- **Should be**: `context/trace/task-templates/issue-{issue_number}-*.md` pattern

Evidence from codebase:
- All scratchpad files reference `context/trace/task-templates/issue-{number}-*.md` pattern
- scripts/agent_hooks.py:161 uses correct pattern: `context/trace/task-templates/issue-{self.issue_number}-*.md`
- scripts/workflow_enforcer.py has working `_check_file_exists` method using glob

### Implementation Steps
1. **Add glob import** to workflow-validator.py (if not present)
2. **Add _check_file_exists helper method** (copy from workflow_enforcer.py)
3. **Replace line 71** with correct pattern validation
4. **Test with actual task template** to verify fix works

### Code Changes Required
```python
# Add to imports
import glob

# Add helper method (copy from workflow_enforcer.py)
def _check_file_exists(self, pattern: str) -> bool:
    """Check if a file matching the pattern exists."""
    files = glob.glob(pattern)
    return len(files) > 0

# Replace lines 71-73
# OLD:
task_template = self.workflow_dir / f"issue_{self.issue_number}_tasks.md"
if not task_template.exists():
    errors.append(f"Task template not found: {task_template}")

# NEW:
task_template_pattern = f"context/trace/task-templates/issue-{self.issue_number}-*.md"
if not self._check_file_exists(task_template_pattern):
    errors.append(f"Task template not found matching pattern: {task_template_pattern}")
```

### Verification Plan
1. Create test task template in correct location
2. Run Phase 2 validation to confirm it passes
3. Test with missing template to confirm error handling
4. Check that existing task templates validate correctly

## Execution Log
- **Started**: 2025-07-27
- **Phase 1 Complete**: Task template and scratchpad created
- **Phase 2**: Implementation in progress...

## Actual Results (to be filled)
- **Tokens Used**: ___
- **Time Taken**: ___
- **Files Modified**: ___
- **Tests Added**: ___
- **Validation Results**: ___
