# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1659-fix-workflow-issue-hybrid-phase-1-validation
# Generated from GitHub Issue #1659
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1659-workflow-validation-logic`

## 🎯 Goal (≤ 2 lines)
> Fix the Phase 1 validation logic that incorrectly checks for documentation commits as prerequisites
> instead of outputs, preventing the workflow from executing successfully.

## 🧠 Context
- **GitHub Issue**: #1659 - Fix workflow-issue --hybrid Phase 1 validation logic error
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: bug
- **Why this matters**: The workflow cannot execute because Phase 1 validation expects documents to already exist before they are created
- **Dependencies**: Workflow enforcement system, state persistence
- **Related**: #1656 (issue that exposed this problem)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/workflow_executor.py | modify | chain-of-thought | Make planning phase actually create docs instead of just checking | High |
| scripts/workflow_enforcer.py | review | analysis | Understand validation timing but no changes needed | Low |
| scripts/agent_hooks.py | review | analysis | Understand output extraction but no changes needed | Low |
| tests/test_workflow_executor.py | modify | test-driven | Add tests for planning phase document creation | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on the workflow automation system.

**Context**
GitHub Issue #1659: The workflow-issue --hybrid command fails during Phase 1 because the validation checks for `documentation_committed` as if it should already exist, but Phase 1 is responsible for creating these documents. The workflow_executor.py planning phase only checks for existing files instead of creating them.

Current codebase follows:
- Workflow enforcement pattern with pre/post phase hooks
- State persistence in JSON files
- Clear separation between validation prerequisites and outputs

Related files:
- scripts/workflow_executor.py - execute_planning method needs to create docs
- scripts/workflow_enforcer.py - defines required outputs for phases
- scripts/agent_hooks.py - extracts outputs after phase completion

**Instructions**
1. **Primary Objective**: Fix workflow_executor.py to actually create planning documents
2. **Scope**: Make planning phase create task template, scratchpad, and commit them
3. **Constraints**:
   - Follow existing file naming patterns
   - Maintain backward compatibility with existing workflows
   - Keep validation logic unchanged (it's correct, just timing issue)
4. **Prompt Technique**: Chain-of-thought for implementation logic
5. **Testing**: Add tests to verify documents are created during planning
6. **Documentation**: Update inline comments to clarify create vs check behavior

**Technical Constraints**
• Expected diff ≤ 150 LoC, ≤ 2 files
• Context budget: ≤ 10k tokens
• Performance budget: Minimal - file operations only
• Code quality: Black formatting, existing patterns
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation fixing the planning phase.
Use conventional commits: fix(workflow): create planning docs instead of just checking

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest tests/test_workflow_executor.py -v` (new tests)
- `python scripts/workflow_cli.py workflow-issue 9999 --hybrid` (manual test)
- **Issue-specific tests**: Verify planning creates docs and commits them
- **Integration tests**: Full workflow should complete without validation errors

## ✅ Acceptance Criteria
- [ ] Phase 1 validation no longer fails with "Missing required outputs: documentation_committed"
- [ ] Planning phase creates task template if it doesn't exist
- [ ] Planning phase creates scratchpad if it doesn't exist
- [ ] Planning phase commits documentation files
- [ ] Workflow executes successfully from clean state
- [ ] Tests verify document creation behavior

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 10k
├── time_budget: 1 hour
├── cost_estimate: $0.15
├── complexity: medium
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
github_issue: 1659
sprint: sprint-current
phase: implementation
component: workflow-automation
priority: bug
complexity: medium
dependencies: []
```
