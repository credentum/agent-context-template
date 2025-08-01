# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1711-[sprint-4.2]-fix-workflow-validation-phase-timeout
# Generated from GitHub Issue #1711
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1711-[sprint-4.2]-fix-workflow-validation-phase-timeout`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.2] Fix workflow validation phase timeout for full CI execution

## 🧠 Context
- **GitHub Issue**: #1711 - [SPRINT-4.2] Fix workflow validation phase timeout for full CI execution
- **Labels**: bug, sprint-current, claude-ready
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Task Context
**Sprint**: sprint-4.2
**Phase**: Phase 3: Bug Fix & CI Improvement
**Component**: workflow-automation

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation

## Problem Description
The workflow validation phase (Phase 3) is timing out after 90 seconds when running full CI checks. The full CI suite requires approximately 12 minutes to complete, but the phase runner has a 90-second timeout configured in `WorkflowConfig.PHASE_TIMEOUT_SECONDS`.

## Root Cause Analysis
1. `workflow_phase_runner.py` uses a 90-second timeout for each phase
2. The validation phase attempts to run the full Docker CI suite via `run-ci-docker.sh all`
3. Full CI takes 10-12 minutes but times out after 90 seconds
4. This prevents proper validation of changes before PR creation

## Current CI Execution Times
Based on local testing:
- Pre-commit hooks: 2-3 minutes
- Individual lint checks: 3-4 minutes
- Unit tests: 1-2 minutes
- Integration tests: 2-3 minutes
- Coverage analysis: 2-3 minutes
- **Total: 10-12 minutes**

## Acceptance Criteria
- [ ] Modify validation phase to handle long-running CI operations
- [ ] Implement a validation-specific timeout of at least 15 minutes
- [ ] Ensure validation phase can complete full CI suite without timing out
- [ ] Add progress reporting during long CI operations
- [ ] Document the validation phase timeout configuration
- [ ] Ensure other phases maintain their shorter timeouts

## Implementation Strategy
1. **Option 1**: Increase `PHASE_TIMEOUT_SECONDS` for validation phase only
   - Add phase-specific timeout configuration
   - Keep other phases at 90 seconds for quick feedback

2. **Option 2**: Run CI validation asynchronously
   - Start CI in background process
   - Poll for completion with progress updates
   - Handle timeout gracefully

3. **Option 3**: Split validation into sub-phases
   - Quick validation (2 min) - essential checks
   - Full validation (15 min) - comprehensive CI

## Technical Details
Key files to modify:
- `scripts/workflow_phase_runner.py` - Add phase-specific timeout handling
- `scripts/workflow_config.py` - Add `VALIDATION_PHASE_TIMEOUT_SECONDS`
- `scripts/workflow_executor.py` - Update validation phase implementation

## Success Metrics
- Validation phase completes full CI without timeout
- No regression in other phase timeouts
- Clear progress feedback during long operations
- Proper error handling for actual CI failures vs timeouts

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (workflow files, CI scripts)
- [x] **File scope estimated** (3 files, ~100 LoC changes)
- [x] **Dependencies mapped** (subprocess, workflow components)
- [x] **Test strategy defined** (test timeout handling)
- [x] **Breaking change assessment** (backward compatible)

## Pre-Execution Context
**Key Files**:
- `scripts/workflow_phase_runner.py`
- `scripts/workflow_config.py`
- `scripts/workflow_executor.py`
- `scripts/run-ci-docker.sh`

**Related Issues/PRs**:
- #1708 (workflow test that exposed timeout issue)
- #1709 (verification improvements)
- #1710 (e2e test suite)

---

_This issue will fix the validation phase timeout to allow full CI execution._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
