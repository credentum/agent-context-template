# Scratchpad: Issue #1647 - Workflow Agent Integration

**Date**: 2025-07-26
**Issue**: [#1647](https://github.com/owner/repo/issues/1647) - [SPRINT-4.2] Integrate workflow enforcement with sub-agents for /workflow-issue command
**Sprint**: sprint-4.2
**Task Template**: [issue-1647-workflow-agent-integration.md](../task-templates/issue-1647-workflow-agent-integration.md)

## Execution Plan

### Overview
Integrate the existing workflow enforcement system (WorkflowEnforcer, AgentHooks) with the sub-agent system to ensure the /workflow-issue slash command enforces all workflow phases without allowing skipping.

### Token Budget & Complexity Assessment
- **Estimated Tokens**: 20,000 (Medium-high complexity)
- **Estimated Time**: 3 hours
- **Complexity**: Medium-High - Requires coordinating enforcement across agent boundaries

### Implementation Steps

1. **Update workflow_cli.py for slash command** (45 minutes)
   - Add support for /workflow-issue slash command parsing
   - Integrate with existing workflow enforcement
   - Handle the command delegation to workflow coordinator

2. **Create base agent integration pattern** (30 minutes)
   - Design pattern for agents to communicate with enforcement system
   - Since agents are markdown-based, create helper functions that can be called
   - Document the integration pattern

3. **Update workflow-coordinator.md** (30 minutes)
   - Add enforcement integration to the coordinator
   - Update Task() calls to include enforcement context
   - Ensure state persistence between phases

4. **Update sub-agent markdown files** (45 minutes)
   - issue-investigator.md: Add enforcement hooks
   - task-planner.md: Add enforcement hooks
   - test-runner.md: Add enforcement hooks
   - pr-manager.md: Add enforcement hooks
   - Each agent needs instructions to check and update workflow state

5. **Create integration tests** (30 minutes)
   - Test enforcement across agent boundaries
   - Test state persistence
   - Test phase validation
   - Mock agent execution for testing

6. **Manual testing and validation** (30 minutes)
   - Test the complete workflow with a test issue
   - Verify enforcement prevents skipping
   - Check state file persistence

### Key Challenges
1. **Agent Integration**: Agents are defined as markdown files, not Python classes, so we need to embed enforcement instructions in their prompts
2. **State Persistence**: Need to ensure state file is accessible and updated across different agent executions
3. **Slash Command**: Need to integrate the slash command system with the workflow CLI

### Implementation Notes
- The enforcement system already exists from PR #1646
- AgentHooks provides pre_phase_hook and post_phase_hook methods
- State is stored in .workflow-state-{issue_number}.json
- Each agent execution is independent, so state must be explicitly loaded/saved

### Phase Tracking
- [ ] Create task template and scratchpad
- [ ] Commit documentation before implementation
- [ ] Update workflow_cli.py
- [ ] Update agent markdown files
- [ ] Create integration tests
- [ ] Run CI checks
- [ ] Manual testing

### Expected Outcomes
- /workflow-issue slash command works with full enforcement
- No phases can be skipped (except investigation when scope is clear)
- State persists across all agent executions
- Existing functionality is preserved with enforcement added
