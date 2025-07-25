# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1426-fix-critical-ci-validation-blocking-issues
# Generated from GitHub Issue #1426
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1426-critical-ci-validation-blocking-issues`

## 🎯 Goal (≤ 2 lines)
> Fix 4 critical CI validation blocking issues identified in issue #1403 to enable successful PR submission and establish reliable CI pipeline.

## 🧠 Context
- **GitHub Issue**: #1426 - [SPRINT-4.1] Fix Critical CI Validation Blocking Issues
- **Sprint**: sprint-4.1
- **Phase**: Phase 3: Quality Assurance
- **Component**: ci-cd
- **Priority**: high (blocking all PRs)
- **Why this matters**: Issue #1403 validation revealed critical failures that prevent PR submission and GitHub Actions success
- **Dependencies**: validation-report-1403.yaml, PR #1402, issue #1403
- **Related**: Local CI validation improvements, sprint-4.1 goals

## 🛠️ Subtasks
Based on validation report analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| context/sprints/sprint-4.1.yaml | modify | Direct Fix | Fix YAML syntax error line 367 | High |
| context/schemas/*.yaml | modify | Pattern Match | Add missing document start markers (---) | Medium |
| pyproject.toml | modify | Dependency Add | Add pytest-benchmark to test dependencies | Medium |
| tests/test_benchmarks.py | modify | Error Fix | Update benchmark fixture usage | Low |
| tests/test_*.py | modify | Type Annotation | Fix 15 MyPy type errors | Medium |
| scripts/run-ci-docker.sh | analyze/optimize | Performance | Reduce execution time <5 min | High |
| src/agents/arc_reviewer.py | modify | Config Update | Add timeout configuration | Medium |
| .pre-commit-config.yaml | verify | Validation | Ensure all hooks configured correctly | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior CI/CD engineer fixing critical validation failures that block all PR submissions.

**Context**
GitHub Issue #1426: Fix Critical CI Validation Blocking Issues
- Validation report (validation-report-1403.yaml) identified 4 critical failures
- YAML syntax error in sprint-4.1.yaml line 367 blocks all workflows
- Missing pytest-benchmark dependency causes test suite failures
- 15 MyPy type errors in test files need resolution
- Docker CI performance exceeds 7 minutes (target: <5 minutes)
- Pre-commit hooks failing on YAML validation
Current codebase uses: Python 3.11, Docker CI, pre-commit hooks, pytest
Related files: sprint files, schema files, test files, CI scripts

**Instructions**
1. **Primary Objective**: Fix all 4 critical blocking issues from validation report
2. **Scope**: Address only the specific failures listed in acceptance criteria
3. **Constraints**:
   - Fix YAML syntax error at line 367 in sprint-4.1.yaml first (blocks everything)
   - Add pytest-benchmark to pyproject.toml test dependencies
   - Fix MyPy errors with minimal type annotations (no over-engineering)
   - Maintain all existing functionality - fixes only, no refactoring
4. **Prompt Technique**: Direct Fix with validation because issues are well-defined
5. **Testing**: Verify each fix with appropriate validation command
6. **Documentation**: Update only if CI process changes significantly

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 8 files
• Context budget: ≤ 15k tokens
• Performance budget: Docker CI <5 min, ARC <2 min
• Code quality: All pre-commit hooks must pass
• CI compliance: Full validation suite must show PASSED

**Output Format**
Fix issues in priority order:
1. YAML syntax error (blocks all)
2. Missing dependencies (blocks tests)
3. Type errors (quality issues)
4. Performance optimization (UX improvement)
Use conventional commits: fix(ci): specific issue description

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (must complete <5 minutes)
- `pytest --cov=src --cov-report=term-missing` (must run without fixture errors)
- `pre-commit run --all-files` (all hooks must pass)
- **YAML validation**: `python -m src.agents.context_lint validate context/`
- **MyPy check**: `mypy tests/` (should report 0 errors)
- **ARC validation**: `python -m src.agents.arc_reviewer` (should complete <2 min)
- **Full validation**: Re-run all checks from issue #1403

## ✅ Acceptance Criteria
From issue #1426:
- [x] Fix YAML syntax error in `context/sprints/sprint-4.1.yaml` line 367
- [x] Add missing document start markers (---) to all schema files
- [x] Install pytest-benchmark dependency and verify test suite runs completely
- [x] Resolve 15 MyPy type checking errors in tests/ directory
- [x] Fix flake8 violations and ensure pre-commit hooks pass
- [x] Optimize Docker CI performance from 7+ minutes to <5 minutes
- [x] Configure ARC-Reviewer timeout and performance settings
- [x] Re-run full validation with all stages showing PASSED status

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15,000 (focused fixes, minimal context)
├── time_budget: 3 hours (including validation)
├── cost_estimate: $0.75 (15k tokens @ $0.05/1k)
├── complexity: Medium (well-defined fixes)
└── files_affected: 8 (YAML, Python, config files)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1426
sprint: sprint-4.1
phase: "Phase 3: Quality Assurance"
component: ci-cd
priority: high
complexity: medium
dependencies: [1403, 1402]
blocking: true
```
