# ────────────────────────────────────────────────────────────────────────
# TASK: issue-961-fix-failing-sprint-update-yml-workflow
# Generated from GitHub Issue #961
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-961-fix-failing-sprint-update-yml-workflow`

## 🎯 Goal (≤ 2 lines)
> Fix failing sprint-update.yml workflow conflict detection and resolve CI/YAML validation issues across context files and workflow files

## 🧠 Context
- **GitHub Issue**: #961 - Fix failing sprint-update.yml workflow and resolve CI/YAML validation issues
- **Sprint**: sprint-4.1
- **Phase**: Phase 4.1: Testing & Validation
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: Critical CI workflow failing, blocking sprint progress and causing YAML validation issues
- **Dependencies**: Docker CI environment, yamllint, pre-commit hooks, GitHub Actions workflow syntax
- **Related**: #960, #760

## 🛠️ Subtasks
Analysis shows 5 failed tests in workflow feature parity and multiple YAML formatting issues

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/sprint-update.yml | debug/fix | Root cause analysis | Fix conflict detection failing | High |
| tests/test_workflow_feature_parity.py | analyze/fix | Error analysis | Fix 5 failing tests | High |
| context/sprints/sprint-4.1.yaml | format/fix | YAML formatting | Fix indentation and line length | Medium |
| context/schemas/*.yaml | validate/fix | Batch validation | Fix multiple document errors | Medium |
| .pre-commit-config.yaml | validate/fix | Configuration fix | Ensure hooks pass in Docker | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD workflows and YAML validation.

**Context**
GitHub Issue #961: Fix failing sprint-update.yml workflow and resolve CI/YAML validation issues
Sprint-4.1 is blocked by CI workflow failures. The sprint-update.yml workflow is failing on conflict detection, 5 tests are failing in workflow feature parity, and multiple YAML files have formatting issues including indentation errors, line length violations, and missing document start markers.

Current codebase follows GitHub Actions workflow patterns and uses yamllint for validation.
Related files: .github/workflows/sprint-update.yml, tests/test_workflow_feature_parity.py, context/sprints/sprint-4.1.yaml, context/schemas/*.yaml

**Instructions**
1. **Primary Objective**: Fix sprint-update.yml workflow conflict detection and resolve all CI/YAML validation issues
2. **Scope**: Address workflow failures while maintaining backward compatibility with existing sprint automation
3. **Constraints**:
   - Follow existing GitHub Actions workflow patterns
   - Maintain backward compatibility with sprint automation
   - Keep workflow APIs unchanged unless breaking change required
4. **Prompt Technique**: Root cause analysis followed by systematic fix because multiple interconnected failures need coordinated resolution
5. **Testing**: Fix 5 failing tests in test_workflow_feature_parity.py and ensure all Docker CI checks pass
6. **Documentation**: Update any workflow documentation if behavior changes

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 15 files
• Context budget: ≤ 15k tokens
• Performance budget: CI workflow fixes with no performance impact
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass, especially YAML validation

**Output Format**
Return complete implementation fixing workflow and YAML issues.
Use conventional commits: fix(ci): fix sprint-update workflow conflict detection

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Fix 5 failing tests in test_workflow_feature_parity.py
- **Integration tests**: Verify sprint-update.yml workflow runs without errors
- **YAML validation**: Ensure all context files pass yamllint validation

## ✅ Acceptance Criteria
- [ ] Fix failing sprint-update.yml workflow conflict detection
- [ ] Resolve Docker CI environment test failures (5 failed tests in workflow feature parity)
- [ ] Fix YAML validation issues across context files and workflow files
- [ ] Ensure pre-push hooks pass consistently in local Docker environment
- [ ] Verify all workflow files have proper YAML syntax and formatting

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12,000 tokens (workflow debugging + YAML fixes)
├── time_budget: 1-2 hours (systematic fix approach)
├── cost_estimate: $6-12 (Claude Code execution)
├── complexity: High (multiple interconnected failures)
└── files_affected: ~15 files (workflows, tests, context YAML)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 961
sprint: sprint-4.1
phase: Phase 4.1: Testing & Validation
component: ci-workflows
priority: high
complexity: high
dependencies: [docker-ci, yamllint, pre-commit, github-actions]
```
