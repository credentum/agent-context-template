# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1661-fix-phase-2-task-template-path-validation-mismatch
# Generated from GitHub Issue #1661
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1661-fix-phase-2-task-template-path-validation-mismatch`

## 🎯 Goal (≤ 2 lines)
> Fix Phase 2 validation in workflow-validator.py to check the correct task template file path pattern used by the actual workflow implementation.

## 🧠 Context
- **GitHub Issue**: #1661 - Fix Phase 2 task template path validation mismatch
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: bug
- **Why this matters**: Phase 2 validation always fails because it's looking for wrong file path, blocking workflow progression
- **Dependencies**: None
- **Related**: Issues #1659 (Phase 1 validation), #1660 (Phase 0 validation)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-validator.py | modify | direct fix | Fix line 71 path validation logic | Low |
| .claude/workflows/workflow-validator.py | add method | pattern implementation | Add _check_file_exists helper method | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation and validation systems.

**Context**
GitHub Issue #1661: Fix Phase 2 task template path validation mismatch
Current Phase 2 validation checks for `issue_{issue_number}_tasks.md` in root directory, but actual workflow creates templates at `context/trace/task-templates/issue-{issue_number}-*.md`.
Current codebase follows Python pathlib patterns and glob matching.
Related files:
- .claude/workflows/workflow-validator.py (line 71 needs fixing)
- scripts/workflow_enforcer.py (shows correct _check_file_exists implementation)
- scripts/agent_hooks.py (line 161 shows correct pattern usage)

**Instructions**
1. **Primary Objective**: Update Phase 2 validation to use correct task template path pattern
2. **Scope**: Fix path validation logic and add missing helper method
3. **Constraints**:
   - Follow existing code patterns: pathlib, glob matching, validation error format
   - Maintain backward compatibility unless breaking change approved
   - Keep public APIs unchanged unless specified in issue
4. **Prompt Technique**: Direct fix because this is a clear bug with specific solution
5. **Testing**: Add unit tests if test framework exists for validator
6. **Documentation**: Update comments to reflect correct path pattern

**Technical Constraints**
• Expected diff ≤ 15 LoC, ≤ 1 file
• Context budget: ≤ 2k tokens
• Performance budget: minimal impact
• Code quality: Follow existing validation patterns
• CI compliance: All validation checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: fix(workflow): correct Phase 2 task template path validation

## 🔍 Verification & Testing
- `python -c "from .claude.workflows.workflow_validator import WorkflowValidator; v = WorkflowValidator(1661); print(v.validate_phase_prerequisites(2))"` (manual test)
- Create test task template and verify validation passes
- Check existing test files pass validation
- **Issue-specific tests**: Test with actual task template pattern

## ✅ Acceptance Criteria
- [ ] Update Phase 2 validation to check the correct path pattern
- [ ] Use glob pattern matching to find task template files
- [ ] Ensure validation passes when task template exists in correct location
- [ ] Update any related documentation or comments
- [ ] Add tests to prevent regression

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 2000 (simple file fix)
├── time_budget: 15 minutes (straightforward bug fix)
├── cost_estimate: $0.01 (minimal context)
├── complexity: low (single file, clear solution)
└── files_affected: 1

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1661
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: bug
complexity: low
dependencies: none
```
