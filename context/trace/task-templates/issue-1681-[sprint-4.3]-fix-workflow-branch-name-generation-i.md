# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1681-[sprint-4.3]-fix-workflow-branch-name-generation-i
# Generated from GitHub Issue #1681
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1681-[sprint-4.3]-fix-workflow-branch-name-generation-i`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.3] Fix workflow branch name generation in workflow executor

## 🧠 Context
- **GitHub Issue**: #1681 - [SPRINT-4.3] Fix workflow branch name generation in workflow executor
- **Labels**: bug, sprint-current, claude-ready
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
**Component**: workflow-automation

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation
- [ ] **Scope needs investigation** - Create investigation issue first (use investigation.md template)
- [ ] **Partially clear** - Some aspects need investigation (note below)

**Investigation Notes**: Root cause has been identified through code analysis

## Acceptance Criteria
- [ ] Workflow executor generates meaningful branch names based on issue title
- [ ] Branch type (fix/feature/chore) is determined from issue labels or title
- [ ] Implementation phase reuses title_slug logic from planning phase
- [ ] Clear error messages guide users when on main branch
- [ ] Resume capability works after manual branch creation

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (docs, specs, related PRs)
- [x] **File scope estimated** (< 4 files, < 400 LoC expected)
- [x] **Dependencies mapped** (external APIs, config, other services)
- [x] **Test strategy defined** (unit, integration, edge cases)
- [x] **Breaking change assessment** (backward compatibility)

## Pre-Execution Context
**Key Files**: 
- `scripts/workflow_executor.py` (line 296 - hardcoded branch name)
- `scripts/workflow_cli.py` (workflow state management)
- `scripts/hybrid_workflow_executor.py` (if using same pattern)

**External Dependencies**: 
- GitHub CLI (gh) for issue data fetching
- Git for branch operations

**Configuration**: None required

**Related Issues/PRs**: 
- #1677 (Issue where workflow broke due to branch naming)
- This was discovered while implementing two-phase CI architecture

## Implementation Notes
### Root Cause
The workflow executor hardcodes branch names as `fix/{issue_number}-workflow-persistence` instead of generating meaningful names from issue titles. This causes:
1. Uninformative branch names
2. Always uses 'fix/' prefix regardless of issue type
3. Inconsistency with planning phase which properly generates title_slug

### Solution Approach
1. **Extract common issue fetching**: Create shared method to get issue details
2. **Generate proper branch names**: 
   - Use title_slug generation (same as planning phase)
   - Determine prefix from labels (bug→fix, enhancement→feature, etc.)
   - Handle special characters and length limits
3. **Improve error messages**: When on main branch, show what branch will be created
4. **Add resume awareness**: Guide users on manual branch creation + --resume option

### Code Locations
- Line 296 in workflow_executor.py: `branch_name = f"fix/{self.issue_number}-workflow-persistence"`
- Line 195 in workflow_executor.py: Has proper title_slug generation logic
- Line 138-142 in workflow_cli.py: State reset logic

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: ~8000 tokens
**Completion Target**: 30-45 minutes

_This issue will be updated during Claude Code execution with progress and results._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
