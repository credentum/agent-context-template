# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1660-phase-0-validation-logic
# Generated from GitHub Issue #1660
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1660-phase-0-validation-logic`

## 🎯 Goal (≤ 2 lines)
> Add missing Phase 0 (Investigation) validation logic to workflow-validator.py to ensure consistency with other phases and proper enforcement of investigation prerequisites and outputs.

## 🧠 Context
- **GitHub Issue**: #1660 - Add missing Phase 0 (Investigation) validation logic to workflow system
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: High (bug fix)
- **Why this matters**: Phase 0 validation is missing, creating inconsistency in the workflow enforcement system
- **Dependencies**: None
- **Related**: #1659 (Phase 1 validation fix)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-validator.py | Modify | Zero-shot | Add Phase 0 validation logic | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on the workflow automation system.

**Context**
GitHub Issue #1660: Add missing Phase 0 (Investigation) validation logic to workflow system
Phase 0 is currently executed in workflow_executor.py but has no validation rules in workflow-validator.py
Current codebase follows the established validation pattern for other phases (1-4).
Related files: workflow-validator.py (needs update), workflow_executor.py (reference for outputs)

**Instructions**
1. **Primary Objective**: Add Phase 0 validation logic to workflow-validator.py
2. **Scope**: Add prerequisite and output validation for Phase 0 while maintaining consistency
3. **Constraints**:
   - Follow existing validation patterns from phases 1-4
   - Maintain backward compatibility
   - Keep validation logic consistent with workflow_executor.py outputs
4. **Prompt Technique**: Zero-shot - straightforward addition following existing patterns
5. **Testing**: Ensure validation works for both skipped and executed investigation phases
6. **Documentation**: Code is self-documenting following existing patterns

**Technical Constraints**
• Expected diff ≤ 50 LoC, 1 file
• Context budget: ≤ 5k tokens
• Performance budget: Minimal (validation checks)
• Code quality: Follow existing patterns, no new dependencies
• CI compliance: Must pass all existing checks

**Output Format**
Return implementation adding Phase 0 validation to workflow-validator.py.
Use conventional commits: fix(workflow): add missing Phase 0 validation logic

## 🔍 Verification & Testing
- Manual testing of Phase 0 validation logic
- Ensure validation works when investigation is skipped
- Ensure validation works when investigation is performed
- Check that existing phases still validate correctly
- Run pre-commit hooks to ensure code quality

## ✅ Acceptance Criteria
- [ ] Add Phase 0 validation logic to `workflow-validator.py`
- [ ] Prerequisites check that issue is accessible via GitHub API
- [ ] Output validation checks for investigation artifacts when phase is executed
- [ ] Output validation allows skipping when scope is clear
- [ ] Consistent with other phase validation patterns
- [ ] Tests added for Phase 0 validation logic

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000
├── time_budget: 30 minutes
├── cost_estimate: $0.10
├── complexity: Low
└── files_affected: 1

Actuals (to be filled):
├── tokens_used: ~4000
├── time_taken: 15 minutes
├── cost_actual: $0.08
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1660
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: high
complexity: low
dependencies: []
```
