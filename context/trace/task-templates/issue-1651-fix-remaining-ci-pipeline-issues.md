# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1651-fix-remaining-ci-pipeline-issues
# Generated from GitHub Issue #1651
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1651-fix-remaining-ci-pipeline-issues`

## 🎯 Goal (≤ 2 lines)
> Fix remaining 5/16 failing CI pipeline checks to achieve complete Docker CI compliance
> Focus on MyPy type annotations, import resolution, security scanning, and YAML validation

## 🧠 Context
- **GitHub Issue**: #1651 - [SPRINT-4.3] Fix remaining CI pipeline issues to achieve 16/16 passing checks
- **Sprint**: sprint-4.3
- **Phase**: Phase 3: Testing & Refinement
- **Component**: ci-infrastructure
- **Priority**: high
- **Why this matters**: Complete CI pipeline compliance ensures code quality and prevents regressions
- **Dependencies**: None - standalone CI fixes
- **Related**: #1649 (original workflow issue), #1650 (WorkflowExecutor implementation PR)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| tests/test_workflow_executor.py | Add type annotations | Direct editing | Fix MyPy type checking | Low |
| tests/test_workflow_*.py | Fix import statements | Pattern matching | Resolve import-not-found errors | Low |
| scripts/__init__.py | Verify/create imports | Module structure | Enable proper module discovery | Low |
| .banditrc or pyproject.toml | Configure bandit | Config editing | Fix security scan issues | Low |
| scripts/validate-*.sh | Fix YAML syntax | Syntax correction | Resolve YAML validation errors | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD pipeline infrastructure.

**Context**
GitHub Issue #1651: Fix remaining CI pipeline issues to achieve 16/16 passing checks
Current status: 11/16 checks passing, 5 failing
Failing checks: MyPy (tests/), import resolution, bandit security, unit tests, YAML validation
Current codebase follows Python packaging standards with scripts/ as a module.
Related files: scripts/run-ci-docker.sh (CI runner), tests/test_workflow_*.py (failing tests)

**Instructions**
1. **Primary Objective**: Fix all 5 remaining CI check failures
2. **Scope**: Address specific CI compliance issues without changing functionality
3. **Constraints**:
   - Follow existing code patterns: Type annotations with Dict[str, Any] for context variables
   - Maintain backward compatibility - no breaking changes
   - Keep test functionality unchanged - only fix imports and types
4. **Prompt Technique**: Direct editing because issues are well-defined and isolated
5. **Testing**: Verify fixes with ./scripts/run-ci-docker.sh after each change
6. **Documentation**: Update completion status in task template

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 8 files
• Context budget: ≤ 15k tokens
• Performance budget: Minimal - configuration fixes only
• Code quality: All 16 Docker CI checks must pass
• CI compliance: Zero tolerance for failing checks

**Output Format**
Return complete implementation addressing all 5 failing CI checks.
Use conventional commits: fix(ci): description of specific fix

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance - must show 16/16 passing)
- `pytest tests/test_workflow_*.py` (verify imports work)
- `mypy tests/` (verify type annotations)
- `bandit -r scripts/` (verify security scan passes)
- `yamllint scripts/validate-*.sh` (verify YAML syntax if applicable)

## ✅ Acceptance Criteria
- [ ] All 16 Docker CI pipeline checks pass locally
- [ ] MyPy type checking passes for all test files
- [ ] Security scan (bandit) issues resolved
- [ ] All import-not-found errors fixed for scripts modules
- [ ] Test coverage maintains baseline (≥71.82%)
- [ ] Zero failing lint/format/type checks

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000 (well-defined fixes)
├── time_budget: 20-30 minutes
├── cost_estimate: $0.05-0.15
├── complexity: Low (configuration and type fixes)
└── files_affected: 5-8 files

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1651
sprint: sprint-4.3
phase: "Phase 3: Testing & Refinement"
component: ci-infrastructure
priority: high
complexity: low
dependencies: []
```
