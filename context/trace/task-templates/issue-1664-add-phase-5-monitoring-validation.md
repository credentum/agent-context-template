# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1664-add-phase-5-monitoring-validation
# Generated from GitHub Issue #1664
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1664-add-phase-5-monitoring-validation`

## 🎯 Goal (≤ 2 lines)
> Add missing Phase 5 (Monitoring) validation logic to workflow-validator.py to ensure PR monitoring prerequisites and outputs are properly validated.

## 🧠 Context
- **GitHub Issue**: #1664 - Add missing Phase 5 (Monitoring) validation logic to workflow system
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: bug
- **Why this matters**: Phase 5 lacks validation, making workflow inconsistent and potentially allowing incomplete monitoring
- **Dependencies**: workflow-validator.py already has phases 0-4 implemented
- **Related**: #1659-1663 (other workflow validation fixes)

## 🛠️ Subtasks
Based on complexity analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-validator.py | modify | Implementation Pattern | Add Phase 5 validation logic | Low |
| tests/test_workflow_validator.py | create/modify | Test Generation | Add tests for Phase 5 validation | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation validation logic.

**Context**
GitHub Issue #1664: Add missing Phase 5 (Monitoring) validation logic to workflow system
Phase 5 is responsible for monitoring PR status through completion but lacks validation rules.
Current codebase has phases 0-4 implemented in workflow-validator.py.
Phase 5 outputs are defined in agent_hooks.py lines 191-193.

**Instructions**
1. **Primary Objective**: Add Phase 5 validation logic to ensure PR monitoring compliance
2. **Scope**: Add prerequisite and output validation for Phase 5 in workflow-validator.py
3. **Constraints**:
   - Follow existing validation patterns from phases 0-4
   - Maintain backward compatibility
   - Keep validation logic consistent with other phases
4. **Prompt Technique**: Implementation Pattern - follow existing phase patterns
5. **Testing**: Add unit tests for new Phase 5 validation logic
6. **Documentation**: Update inline comments as needed

**Technical Constraints**
• Expected diff ≤ 50 LoC in workflow-validator.py
• Context budget: ≤ 5k tokens
• Performance budget: Minimal (validation checks only)
• Code quality: Follow existing patterns, maintain test coverage
• CI compliance: All validation checks must pass

**Output Format**
Return implementation adding Phase 5 validation to both:
- validate_phase_prerequisites() method (after Phase 4)
- validate_phase_outputs() method (after Phase 4)
Use conventional commits: fix(workflow): add Phase 5 monitoring validation logic

## 🔍 Verification & Testing
- `python .claude/workflows/workflow-validator.py 1664 5` (test Phase 5 validation)
- `pytest tests/test_workflow_validator.py -k phase_5` (unit tests)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Verify PR exists check, monitoring activation check
- **Integration tests**: Test full workflow with Phase 5

## ✅ Acceptance Criteria
- [x] Add Phase 5 validation logic to workflow-validator.py
- [x] Prerequisites check that PR exists and is accessible
- [x] Prerequisites verify Phase 4 completion
- [x] Output validation checks monitoring was configured
- [x] Support for both completion and timeout scenarios
- [x] Consistent with other phase validation patterns
- [x] Tests added for Phase 5 validation logic

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000
├── time_budget: 30 minutes
├── cost_estimate: $0.15
├── complexity: low
└── files_affected: 2

Actuals (completed):
├── tokens_used: ~15000 (including conflict resolution)
├── time_taken: ~45 minutes (including merge conflict resolution)
├── cost_actual: ~$0.15
├── iterations_needed: 3 (implementation, testing, conflict resolution)
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1664
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: bug
complexity: low
dependencies: []
```
