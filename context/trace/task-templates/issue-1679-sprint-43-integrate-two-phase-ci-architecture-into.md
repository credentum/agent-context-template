# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1679-[sprint-4.3]-integrate-two-phase-ci-architecture-i
# Generated from GitHub Issue #1679
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1679-[sprint-4.3]-integrate-two-phase-ci-architecture-i`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.3] Integrate two-phase CI architecture into workflow command validation phase

## 🧠 Context
- **GitHub Issue**: #1679 - [SPRINT-4.3] Integrate two-phase CI architecture into workflow command validation phase
- **Labels**: enhancement, sprint-current, component:ci
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Task Context
**Sprint**: sprint-4.3
**Phase**: Phase 3: Testing & Refinement
**Component**: ci-infrastructure

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation
- [ ] **Scope needs investigation** - Create investigation issue first (use investigation.md template)
- [ ] **Partially clear** - Some aspects need investigation (note below)

**Investigation Notes**: N/A - Building on existing workflow command and two-phase CI design

## Acceptance Criteria
- [ ] Workflow Phase 3 (Testing & Validation) uses two-phase CI architecture
- [ ] Docker tests run first, generating coverage artifacts
- [ ] ARC reviewer runs separately in Claude Code with LLM mode
- [ ] Failed tests trigger return to Phase 2 (Implementation)
- [ ] ARC reviewer "REQUEST_CHANGES" verdict triggers return to Phase 2
- [ ] Workflow continues iterating until all validation passes
- [ ] State persistence tracks validation attempts and results

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (workflow docs, related issues)
- [x] **File scope estimated** (< 4 files, < 200 LoC expected)
- [x] **Dependencies mapped** (workflow_executor.py, validation scripts)
- [x] **Test strategy defined** (test workflow iteration)
- [x] **Breaking change assessment** (backward compatible)

## Pre-Execution Context
**Key Files**: 
- `.claude/workflows/workflow-issue.md` (Phase 3 section)
- `scripts/workflow_executor.py`
- `scripts/workflow_cli.py`
- `scripts/run-ci-docker.sh`
- `src/agents/arc_reviewer.py`

**External Dependencies**:
- Existing workflow command infrastructure
- Docker CI scripts
- ARC reviewer with LLM mode

**Configuration**: 
- Workflow state file: `.workflow-state-{issue_number}.json`
- Test artifacts directory for coverage sharing

**Related Issues/PRs**: 
- #1677 (Two-phase CI architecture implementation)
- #1678 (Fix ARC reviewer import issues)

## Implementation Notes
### Integration Points

1. **Update Phase 3 Step 3.1 (Local Testing)**:
   - Replace single `./scripts/run-ci-docker.sh` with:
     ```bash
     # Phase 1: Run Docker tests without ARC reviewer
     ./scripts/run-ci-docker.sh --no-arc-reviewer
     
     # Phase 2: Run ARC reviewer in Claude Code
     python -m src.agents.arc_reviewer --llm --coverage-file test-artifacts/coverage.json
     ```

2. **Enhanced Validation Loop**:
   ```python
   # In workflow_executor.py
   def execute_validation_phase():
       while True:
           # Run Docker tests
           docker_result = run_docker_tests()
           if not docker_result.passed:
               return Phase.IMPLEMENTATION  # Go back to fix tests
           
           # Run ARC reviewer with LLM
           arc_result = run_arc_reviewer_llm()
           if arc_result.verdict == "REQUEST_CHANGES":
               return Phase.IMPLEMENTATION  # Go back to fix issues
           elif arc_result.verdict == "APPROVE":
               break  # Continue to Phase 4
   ```

3. **State Tracking**:
   - Add validation attempts counter
   - Track which issues (test failures vs ARC feedback) caused iterations
   - Store coverage metrics in state file

4. **Error Handling**:
   - Handle Docker test failures gracefully
   - Provide clear feedback on what needs fixing
   - Support resuming validation after fixes

### Benefits
- Automated iteration until validation passes
- Clear separation of test execution and code review
- LLM-powered feedback integrated into workflow
- No manual intervention needed between phases

### Backward Compatibility
- Existing workflows continue to work
- New behavior only activates with appropriate flags
- Graceful fallback if LLM mode unavailable

---

## Claude Code Execution
**Session Started**: 2025-07-31T18:42:32
**Task Template Created**: context/trace/task-templates/issue-1679-sprint-43-integrate-two-phase-ci-architecture-into.md
**Token Budget**: 10000 (estimated)
**Completion Target**: 1 hour

_This integrates the two-phase CI architecture into the existing workflow command for seamless issue-to-PR automation._

## 💲 Budget & Performance Tracking
```
Actuals (filled during execution):
├── tokens_used: ~8000 (estimated)
├── time_taken: ~30 minutes
├── cost_actual: ~$0.50
├── iterations_needed: 1
├── context_clears: 0
└── files_modified: 1 (scripts/workflow_executor.py)

Implementation completed:
├── Two-phase CI architecture integrated
├── Docker tests phase implemented
├── ARC reviewer LLM phase implemented  
├── Validation loop with automatic iteration
├── State persistence for validation attempts
└── Backward compatibility maintained
```

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
