# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1652-fix-workflow-issue-command
# Generated from GitHub Issue #1652
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1652-fix-workflow-issue-command`

## 🎯 Goal (≤ 2 lines)
> Fix /workflow-issue command to use WorkflowExecutor directly instead of sub-agents to ensure stateful persistence across all 6 workflow phases

## 🧠 Context
- **GitHub Issue**: #1652 - [SPRINT-4.3] Fix /workflow-issue command to use WorkflowExecutor instead of sub-agents
- **Sprint**: sprint-4.3
- **Phase**: Phase 3: Testing & Refinement
- **Component**: workflow-automation
- **Priority**: high
- **Why this matters**: Sub-agents are stateless and cannot maintain workflow state, causing real operations to fail
- **Dependencies**: WorkflowExecutor class (already exists)
- **Related**: #1651 (failed workflow execution), #1650 (PR with WorkflowExecutor implementation)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/workflow_cli.py | modify | direct implementation | Remove sub-agent delegation logic | Low |
| /workflow-issue command | modify | direct execution | Ensure command uses WorkflowExecutor | Low |
| Test validation | test | validation run | Verify fix works on real issue | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation systems.

**Context**
GitHub Issue #1652: Fix /workflow-issue command to use WorkflowExecutor instead of sub-agents
Current issue: Sub-agents are stateless and isolated, cannot maintain workflow state across phases
Related files: scripts/workflow_cli.py (main command), scripts/workflow_executor.py (direct execution)
Architecture problem: Agent delegation breaks state persistence and real operations

**Instructions**
1. **Primary Objective**: Modify /workflow-issue command to use WorkflowExecutor directly for all 6 phases
2. **Scope**: Update workflow_cli.py to remove sub-agent delegation when use_agents=True
3. **Constraints**:
   - Follow existing code patterns in workflow_cli.py and workflow_executor.py
   - Maintain backward compatibility for direct CLI usage
   - Keep public APIs unchanged
4. **Prompt Technique**: Direct implementation because task scope is clear and architectural
5. **Testing**: Run /workflow-issue on a real issue to verify persistence works
6. **Documentation**: Update as needed for new execution model

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 2 files
• Context budget: ≤ 10k tokens
• Performance budget: Low complexity fix
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: fix(workflow): enable persistent changes in workflow-issue command

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Run /workflow-issue on real issue to verify all phases persist
- **Integration tests**: Verify git operations, file creation, PR creation work

## ✅ Acceptance Criteria
- [ ] /workflow-issue command executes all 6 phases using WorkflowExecutor directly
- [ ] All documentation artifacts are created and committed properly (task templates, scratchpads, logs)
- [ ] Real git operations (branch creation, commits, PR creation) work correctly
- [ ] Workflow state persists across all phases in .workflow-state-{issue}.json
- [ ] Phase enforcement validation works at each transition
- [ ] No fabricated outputs - all operations must be real and verifiable

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 10000 tokens
├── time_budget: 30 minutes
├── cost_estimate: $0.30
├── complexity: low (architectural fix)
└── files_affected: 2

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1652
sprint: sprint-4.3
phase: Phase 3: Testing & Refinement
component: workflow-automation
priority: high
complexity: low
dependencies: WorkflowExecutor
```
