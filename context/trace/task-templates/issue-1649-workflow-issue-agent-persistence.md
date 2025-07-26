# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1649-workflow-issue-agent-persistence
# Generated from GitHub Issue #1649
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1649-workflow-issue-agent-persistence`

## 🎯 Goal (≤ 2 lines)
> Fix /workflow-issue command to properly delegate to sub-agents with persistent changes
> Enable agents to make actual repository changes that persist across agent boundaries

## 🧠 Context
- **GitHub Issue**: #1649 - Fix /workflow-issue command to properly delegate to sub-agents with persistent changes
- **Sprint**: sprint-4.3
- **Phase**: Phase 3: Testing & Refinement
- **Component**: workflow-automation
- **Priority**: high
- **Why this matters**: The workflow-issue command is non-functional because agents run in isolated environments
- **Dependencies**: Task tool behavior, agent execution environment
- **Related**: #1644 (failed execution), #1647 (previous fix attempt)

## 🛠️ Subtasks
Based on root cause analysis, we need to modify the workflow execution model:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/workflow_cli.py | modify | Chain-of-Thought | Implement direct execution instead of agent delegation | High |
| .claude/commands/workflow-issue.md | modify | Direct | Update command to use direct execution | Low |
| scripts/workflow_executor.py | create | Few-Shot | Create new executor for direct phase execution | High |
| context/trace/logs/workflow-enforcement.log | modify | Direct | Track workflow execution | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer specializing in workflow automation and agent coordination systems.

**Context**
GitHub Issue #1649: The /workflow-issue command fails because sub-agents execute in isolated environments where changes don't persist. When using Task(subagent_type="workflow-coordinator"), all file operations, git commands, and GitHub CLI operations are lost when the agent completes.

Current implementation:
- workflow_cli.py delegates to agents using Task() tool
- Agents run in temporary contexts
- Changes (files, git operations) are discarded
- Workflow enforcement state doesn't persist

**Instructions**
1. **Primary Objective**: Make /workflow-issue command functional by ensuring changes persist
2. **Scope**: Modify execution model to avoid isolated agent environments
3. **Constraints**:
   - Maintain workflow enforcement validation
   - Keep phase structure intact
   - Ensure state persistence works
   - Don't break existing CLI functionality
4. **Prompt Technique**: Chain-of-Thought for complex refactoring
5. **Testing**: Verify with actual issue execution
6. **Documentation**: Update command documentation

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: Immediate execution
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return implementation that executes workflow phases directly in main context.
Use conventional commits: fix(workflow): enable persistent changes in workflow-issue command

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Execute /workflow-issue with test issue
  - Verify task template creation persists
  - Verify git branch creation persists
  - Verify PR is actually created
- **Integration tests**: Test workflow state persistence

## ✅ Acceptance Criteria
- [ ] `/workflow-issue` command successfully completes the full workflow from issue to PR
- [ ] Sub-agents can make persistent changes to the repository when delegated from main Claude
- [ ] Workflow enforcement (`enforce_workflow_phase`, `complete_workflow_phase`) works across agent boundaries
- [ ] State persistence (`.workflow-state-{issue_number}.json`) is maintained across all agents
- [ ] Each phase properly delegates to its designated agent
- [ ] All required documentation artifacts are created in the actual repository
- [ ] Git operations (branch, commit, push) persist in the actual repository
- [ ] PR is successfully created and visible on GitHub

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 45 minutes
├── cost_estimate: $0.75
├── complexity: High (architectural change)
└── files_affected: 4

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1649
sprint: sprint-4.3
phase: 3-testing-refinement
component: workflow-automation
priority: high
complexity: high
dependencies:
  - Task tool behavior
  - Agent execution environment
```
