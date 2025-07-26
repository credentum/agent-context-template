# Execution Plan: Issue #1652 - Fix /workflow-issue command

**Date**: 2025-07-26
**Issue**: #1652 - [SPRINT-4.3] Fix /workflow-issue command to use WorkflowExecutor instead of sub-agents
**Sprint**: sprint-4.3
**Task Template**: context/trace/task-templates/issue-1652-fix-workflow-issue-command.md

## 🎯 Objective
Fix the /workflow-issue command to use WorkflowExecutor directly instead of sub-agent delegation to ensure stateful persistence across all workflow phases.

## 🧠 Context Analysis
- **Root Cause**: Sub-agents are stateless and isolated, cannot maintain workflow state
- **Current Issue**: Lines 324-327, 348-351, 399-402, 434-437, 459-462, 484-487 in workflow_cli.py use agent delegation
- **Solution**: These should call WorkflowExecutor methods directly when use_agents=True

## 📋 Token Budget & Complexity Assessment
- **Estimated Tokens**: 10,000 tokens
- **Estimated Time**: 30 minutes
- **Complexity**: Low (architectural fix, clear scope)
- **Files to Modify**: scripts/workflow_cli.py

## 🔧 Step-by-Step Implementation Plan

### Phase 1: Code Analysis (5 mins)
1. ✅ Identify exact lines where sub-agent delegation occurs
2. ✅ Understand WorkflowExecutor interface
3. ✅ Plan modification strategy

### Phase 2: Implementation (15 mins)
1. Modify workflow_cli.py to remove sub-agent delegation
2. Update each phase execution method to use WorkflowExecutor directly
3. Ensure backward compatibility for direct CLI usage

### Phase 3: Testing (10 mins)
1. Run /workflow-issue on a test issue
2. Verify all phases execute and persist state
3. Confirm git operations work
4. Run CI checks

## 🎯 Success Criteria
- [ ] All 6 workflow phases execute using WorkflowExecutor directly
- [ ] Real git operations (branch, commits, PR) work correctly
- [ ] Documentation artifacts persist across phases
- [ ] CI checks pass
- [ ] No fabricated outputs - all operations are real

## 📝 Implementation Notes
The fix involves changing the conditional logic in each phase execution method from:
```python
if context.get("use_agents", False):
    # Use direct executor instead of agent delegation
    executor = WorkflowExecutor(issue_number)
    return executor.execute_[phase](context)
```

This should be the primary execution path, not the fallback.

## 🔍 Validation Plan
1. Test with a real issue number
2. Verify .workflow-state-{issue}.json persists
3. Confirm all documentation files are created
4. Check git operations create real branches and commits
5. Validate PR creation works end-to-end
