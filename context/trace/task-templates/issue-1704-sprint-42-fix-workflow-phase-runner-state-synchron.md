# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1704-[sprint-4.2]-fix-workflow-phase-runner-state-synch
# Generated from GitHub Issue #1704
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1704-[sprint-4.2]-fix-workflow-phase-runner-state-synch`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.2] Fix workflow phase runner state synchronization failure

## 🧠 Context
- **GitHub Issue**: #1704 - [SPRINT-4.2] Fix workflow phase runner state synchronization failure
- **Labels**: bug, sprint-current, claude-ready
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Task Context
**Sprint**: sprint-4-2
**Phase**: Phase 3: Bug Fix & CI Improvement
**Component**: workflow-automation

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation

## Problem Description
The workflow phase runner fails during phase execution even when actual work is completed successfully. This causes workflows to halt with "Phase failed with exit code: 1" errors, requiring manual intervention to continue.

## Root Cause
**State synchronization mismatch** between two parallel state management systems:
1. `PhaseRunner` uses `.workflow-phase-state-{issue_number}.json`
2. `WorkflowEnforcer` uses `.workflow-state-{issue_number}.json`

These systems don't communicate, causing the WorkflowEnforcer to reject phase execution because it doesn't know previous phases were completed.

## Failure Sequence
1. PhaseRunner attempts phase execution with: `workflow_cli.py workflow-issue 1234 --skip-phases 0 1 3 4 5`
2. WorkflowCLI creates fresh WorkflowEnforcer instance
3. WorkflowEnforcer reads its own state file and doesn't see previous phases completed
4. Enforcer fails with "Previous phase 'planning' not started"
5. Command exits with code 1
6. PhaseRunner interprets as phase failure even though work was done

## Acceptance Criteria
- [ ] PhaseRunner and WorkflowEnforcer use synchronized state management
- [ ] Workflows complete all phases without manual state file editing
- [ ] Phase completion is properly tracked across both systems
- [ ] No false failures when work is actually completed
- [ ] Backward compatibility with existing workflows

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (workflow scripts and state management)
- [x] **File scope estimated** (< 4 files: workflow_phase_runner.py, workflow_enforcer.py, workflow_cli.py, agent_hooks.py)
- [x] **Dependencies mapped** (state files, WorkflowConfig)
- [x] **Test strategy defined** (test state synchronization, phase transitions)
- [x] **Breaking change assessment** (ensure existing workflows continue to work)

## Pre-Execution Context
**Key Files**: 
- `scripts/workflow_phase_runner.py` - Phase execution orchestrator
- `scripts/workflow_enforcer.py` - Phase validation and state tracking
- `scripts/workflow_cli.py` - CLI interface that connects them
- `scripts/agent_hooks.py` - Pre/post phase hooks

**External Dependencies**: 
- JSON state files
- WorkflowConfig constants

**Configuration**: 
- PHASE_TIMEOUT_SECONDS = 90
- State file locations

**Related Issues/PRs**: 
- Discovered during #1702 workflow execution
- Affects all workflow-issue --hybrid executions

## Implementation Notes
### Proposed Solutions
1. **Option A**: Unified state management
   - Create single state file used by both systems
   - Migrate existing state on first run
   - Most robust but requires migration

2. **Option B**: State synchronization
   - PhaseRunner updates WorkflowEnforcer state after phase completion
   - Add hooks to sync between systems
   - Less invasive but more complex

3. **Option C**: Read from both state files
   - WorkflowEnforcer checks both state files
   - Consider phase complete if either shows completion
   - Simplest but maintains dual state

### Recommendation
Implement Option A (unified state management) for long-term maintainability.

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: Medium (focused state management changes)
**Completion Target**: 45-60 minutes

_This issue will be updated during Claude Code execution with progress and results._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
