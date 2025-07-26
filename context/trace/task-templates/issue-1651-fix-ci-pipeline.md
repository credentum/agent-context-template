# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1651-fix-ci-pipeline
# Generated from GitHub Issue #1651
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1651-ci-pipeline-checks`

## 🎯 Goal (≤ 2 lines)
> Fix remaining 5 failing Docker CI pipeline checks to achieve 16/16 passing status by resolving MyPy type issues, import errors, security scan configuration, and validation scripts.

## 🧠 Context
- **GitHub Issue**: #1651 - [SPRINT-4.3] Fix remaining CI pipeline issues to achieve 16/16 passing checks
- **Sprint**: sprint-4.3
- **Phase**: Phase 3: Testing & Refinement
- **Component**: ci-infrastructure
- **Priority**: high
- **Why this matters**: CI pipeline integrity is critical for development workflow and code quality
- **Dependencies**: MyPy, Bandit, Docker CI pipeline
- **Related**: PR #1650 (WorkflowExecutor implementation)

## 🛠️ Subtasks
Based on failing checks analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| tests/test_workflow_executor.py | modify | Type annotation | Add type hints to context variables | Low |
| tests/test_workflow_*.py | modify | Import fix | Fix module import paths | Low |
| scripts/__init__.py | create | Module init | Enable proper module imports | Low |
| .bandit | create | Config file | Configure security scanner | Low |
| scripts/run-ci-docker.sh | analyze | Debug | Understand YAML validation error | Low |
| mypy.ini | modify | Config update | Ensure test files are properly checked | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer fixing CI pipeline issues to ensure code quality standards.

**Context**
GitHub Issue #1651: Fix remaining CI pipeline issues
Current status: 11/16 checks passing, 5 failing:
1. MyPy type checking for tests (missing annotations)
2. Import resolution errors for workflow modules
3. Bandit security scan configuration issues
4. Unit test failures due to imports
5. YAML validation script syntax error

**Instructions**
1. **Primary Objective**: Fix all 5 failing CI checks while maintaining existing passing checks
2. **Scope**: Address type annotations, import structure, and tool configuration
3. **Constraints**:
   - Maintain test coverage ≥ 71.82%
   - Keep all existing tests passing
   - No changes to core functionality
4. **Prompt Technique**: Direct fixes with systematic validation
5. **Testing**: Run Docker CI after each fix to verify progress
6. **Documentation**: Update configuration files as needed

**Technical Constraints**
• Expected diff ≤ 150 LoC, ≤ 8 files
• Context budget: ≤ 8k tokens
• Performance budget: Immediate fixes
• Code quality: All CI checks must pass
• CI compliance: 16/16 Docker CI checks

**Output Format**
Return fixes in order of priority, testing after each change.
Use conventional commits: fix(ci): specific description

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Full Docker CI pipeline)
- `./scripts/run-ci-docker.sh debug` (Debug specific failures)
- `pytest --cov=src --cov-report=term-missing` (coverage check)
- `mypy tests/` (type checking for test files)
- `bandit -r src/` (security scan)

## ✅ Acceptance Criteria
- All 16 Docker CI pipeline checks pass locally
- MyPy type checking passes for all test files
- Security scan (bandit) issues resolved
- All import-not-found errors fixed for scripts modules
- Test coverage maintains baseline (≥71.82%)
- Zero failing lint/format/type checks

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 8000
├── time_budget: 30 minutes
├── cost_estimate: $0.40
├── complexity: medium
└── files_affected: 6-8

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
complexity: medium
dependencies: [mypy, bandit, docker]
```
