# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1640-integrate-workflow-enforcement
# Generated from GitHub Issue #1640
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1640-integrate-workflow-enforcement`

## 🎯 Goal (≤ 2 lines)
> Integrate the existing workflow-validator.py enforcement system into the workflow-issue command so that sub-agents automatically use validation at phase start/end with state persistence and resume capability.

## 🧠 Context
- **GitHub Issue**: #1640 - [SPRINT-5.1] Integrate workflow enforcement system into workflow-issue command
- **Sprint**: sprint-5-1
- **Phase**: Phase 2: Implementation Enhancement
- **Component**: workflow-orchestration
- **Priority**: enhancement (sprint-current)
- **Why this matters**: Ensures workflow compliance and prevents agents from skipping required steps
- **Dependencies**: workflow-validator.py (exists), workflow-issue.md (current workflow)
- **Related**: #1634 (original workflow), #1639 (workflow enforcement docs)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-issue.md | modify | stepwise-integration | Add enforcement hooks to existing phases | Med |
| workflow coordinator code | identify/modify | code-analysis | Integrate validator calls into agent coordination | High |
| .claude/workflows/workflow-validator.py | review/extend | gap-analysis | Ensure all required validation is present | Low |
| test scripts | create | test-driven | Validate integration works end-to-end | Med |
| documentation | update | documentation-sync | Update workflow docs with enforcement details | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow orchestration systems.

**Context**
GitHub Issue #1640: Integrate workflow enforcement system into workflow-issue command
Current state: workflow-validator.py exists with phase validation but isn't integrated into the main workflow execution.
The workflow-issue.md defines 6 phases (0-5) but agents can skip phases without validation.
Related files: .claude/workflows/workflow-validator.py (enforcement system), .claude/workflows/workflow-issue.md (current workflow)

**Instructions**
1. **Primary Objective**: Integrate workflow-validator.py into workflow execution so sub-agents automatically use enforcement
2. **Scope**: Modify workflow coordination to call enforce_workflow_phase() before and complete_workflow_phase() after each agent execution
3. **Constraints**:
   - Follow existing code patterns in .claude/workflows/ directory
   - Maintain backward compatibility with current workflow-issue command
   - Keep public APIs unchanged unless specified in issue
4. **Prompt Technique**: stepwise-integration with code-analysis because this requires understanding existing integration points and modifying them systematically
5. **Testing**: Test phase prerequisite validation, output validation, state persistence, failure recovery, resume capability
6. **Documentation**: Update workflow-issue.md to document enforcement integration

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 5 files
• Context budget: ≤ 15k tokens
• Performance budget: minimal overhead per phase
• Code quality: Python best practices, error handling
• CI compliance: All validation checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(workflow): integrate enforcement system

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `python .claude/workflows/workflow-validator.py 1640 1` (test phase validation)
- Test workflow with intentional failures to verify enforcement
- Test resume capability from failed phases
- Verify state persistence across agent executions

## ✅ Acceptance Criteria
- [ ] Workflow coordinator integrates with workflow-validator.py
- [ ] Sub-agents automatically use enforcement at phase start/end
- [ ] State tracking persists across workflow execution
- [ ] Failed validations prevent phase progression
- [ ] Clear error messages when prerequisites not met
- [ ] Resume capability from any failed phase

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000 (moderate integration task)
├── time_budget: 2-3 hours (code analysis + integration + testing)
├── cost_estimate: $0.50-0.75 (estimated token usage)
├── complexity: medium (integration of existing systems)
└── files_affected: 3-5 files (workflow coordinator, docs, tests)

Actuals (filled during execution):
├── tokens_used: ~12,000 tokens
├── time_taken: ~2 hours
├── cost_actual: ~$0.60
├── iterations_needed: 1 (successful on first attempt)
└── context_clears: 0 (stayed within budget)
```

## 🏷️ Metadata
```yaml
github_issue: 1640
sprint: sprint-5-1
phase: implementation-enhancement
component: workflow-orchestration
priority: enhancement
complexity: medium
dependencies: ["workflow-validator.py", "workflow-issue.md"]
```
