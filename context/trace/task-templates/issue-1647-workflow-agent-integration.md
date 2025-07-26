# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1647-workflow-agent-integration
# Generated from GitHub Issue #1647
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1647-workflow-agent-integration`

## 🎯 Goal (≤ 2 lines)
> Integrate workflow enforcement system with sub-agents (issue-investigator, task-planner, test-runner, pr-manager) to ensure the /workflow-issue slash command enforces all workflow phases without skipping.

## 🧠 Context
- **GitHub Issue**: #1647 - [SPRINT-4.2] Integrate workflow enforcement with sub-agents for /workflow-issue command
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: Implementation
- **Component**: workflow-enforcement, agent-integration
- **Priority**: high
- **Why this matters**: PR #1646 implemented workflow enforcement but sub-agents need integration to prevent phase skipping
- **Dependencies**: Issue #1645 (workflow enforcement need), PR #1646 (enforcement implementation)
- **Related**: Workflow enforcement system already exists but not integrated with agents

## 🛠️ Subtasks
Integration of AgentHooks with each sub-agent and workflow coordinator

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/workflow_cli.py | modify | Chain-of-Thought | Add /workflow-issue slash command support | Medium |
| src/agents/base_agent.py | create | Template | Create base agent class with enforcement hooks | High |
| .claude/agents/workflow-coordinator.md | modify | Direct | Update to use WorkflowEnforcer | Medium |
| .claude/agents/issue-investigator.md | modify | Direct | Add pre/post phase hooks | Low |
| .claude/agents/task-planner.md | modify | Direct | Add pre/post phase hooks | Low |
| .claude/agents/test-runner.md | modify | Direct | Add pre/post phase hooks | Low |
| .claude/agents/pr-manager.md | modify | Direct | Add pre/post phase hooks | Low |
| tests/test_workflow_agent_integration.py | create | Test-Driven | Test agent enforcement integration | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation and agent orchestration systems.

**Context**
GitHub Issue #1647: Integrate workflow enforcement with sub-agents
- The workflow enforcement system (WorkflowEnforcer, AgentHooks) exists in scripts/
- Sub-agent definitions exist in .claude/agents/ as markdown files
- The /workflow-issue slash command should use these agents with enforcement
- State persistence across agent executions is required via .workflow-state-{issue_number}.json
- Each phase must be validated before and after execution

Current codebase follows:
- Agent definitions in .claude/agents/*.md
- Enforcement system in scripts/workflow_enforcer.py and scripts/agent_hooks.py
- Workflow CLI in scripts/workflow_cli.py

**Instructions**
1. **Primary Objective**: Enable /workflow-issue slash command to execute with full workflow enforcement
2. **Scope**:
   - Add slash command support to workflow_cli.py
   - Create base agent integration pattern
   - Update all agent markdown files to include enforcement hooks
   - Ensure state persistence works across agent boundaries
3. **Constraints**:
   - Maintain backward compatibility - enforcement should be configurable
   - Agent markdown files define behavior via prompts, not Python code
   - State must persist across different agent executions
   - No phase skipping allowed (except investigation when scope is clear)
4. **Prompt Technique**: Chain-of-Thought for complex integration, Direct modification for agent files
5. **Testing**: Create integration tests that verify enforcement across agent boundaries
6. **Documentation**: Update agent files with enforcement instructions

**Technical Constraints**
• Expected diff ≤ 600 LoC, ≤ 8 files
• Context budget: ≤ 20k tokens
• Performance budget: Minimal overhead on agent execution
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation with:
1. Updated workflow_cli.py with slash command support
2. Base agent integration pattern (if needed)
3. Modified agent markdown files with enforcement hooks
4. Integration tests
Use conventional commits: feat(workflow): integrate enforcement with sub-agents

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest tests/test_workflow_agent_integration.py` (new integration tests)
- `python scripts/workflow_cli.py workflow-issue --issue 1647` (manual test)
- **Issue-specific tests**:
  - Verify enforcement prevents phase skipping
  - Test state persistence across agents
  - Validate hook integration works
- **Integration tests**: Test complete workflow with mock agents

## ✅ Acceptance Criteria
- [ ] Sub-agents (issue-investigator, task-planner, test-runner, pr-manager) integrate with AgentHooks
- [ ] /workflow-issue slash command uses WorkflowEnforcer for phase validation
- [ ] All workflow phases are enforced - no skipping allowed (except investigation when scope is clear)
- [ ] State persistence works across sub-agent executions
- [ ] Workflow coordinator integrates with enforcement system
- [ ] Existing agent behavior is preserved with added enforcement

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 20,000
├── time_budget: 3 hours
├── cost_estimate: ~$1.50
├── complexity: Medium-High
└── files_affected: 8

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1647
sprint: sprint-4.2
phase: implementation
component: [workflow-enforcement, agent-integration]
priority: high
complexity: medium-high
dependencies: [1645, 1646]
```
