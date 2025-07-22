# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1204-yaml-linting-mypy-errors
# Generated from GitHub Issue #1204
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1204-comprehensive-ci-linting-type-errors`

## 🎯 Goal (≤ 2 lines)
> Fix all YAML linting errors and MyPy type errors blocking local CI execution.
> Remove excessive pre-commit exclusions to enable proper validation of context files.

## 🧠 Context
- **GitHub Issue**: #1204 - [SPRINT-4.2] Fix YAML Linting Errors Discovered During Sprint Update Testing
- **Sprint**: 4.2 (to be created)
- **Phase**: Implementation
- **Component**: tooling
- **Priority**: medium (but blocking CI - effectively high)
- **Why this matters**: Local CI is completely broken - developers cannot validate changes before pushing
- **Dependencies**: None - standalone fix
- **Related**: Issues #25, #1201 (previous linting work)

## 🛠️ Subtasks
Based on complexity analysis and prioritization:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| context/schemas/decision.yaml:7 | Fix critical syntax error | Direct Edit | Unblock YAML parsing | High |
| .pre-commit-config.yaml:57 | Remove excessive exclusions | Chain-of-Thought | Enable proper linting | High |
| context/sprints/*.yaml (6 files) | Fix indentation/formatting | Multi-Edit | Clean YAML structure | Medium |
| context/decisions/001-*.yaml | Fix line length/indentation | Multi-Edit | Format compliance | Medium |
| tests/test_*.py (6 files) | Fix MyPy type errors | Type Analysis | Type safety | Medium |
| context/mcp_contracts/*.yaml | Fix line length | Edit | Minor formatting | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer specializing in CI/CD tooling and code quality enforcement.

**Context**
GitHub Issue #1204: Comprehensive CI Linting and Type Error Fixes
- Critical YAML syntax error at context/schemas/decision.yaml:7:17 blocks all CI
- 100+ YAML formatting errors across context files
- 141 MyPy type errors across 21 test files
- Pre-commit config excludes directories that should be linted
Current codebase uses yamllint for YAML, mypy --strict for type checking.
Related files: .pre-commit-config.yaml, context/*, tests/*.py

**Instructions**
1. **Primary Objective**: Enable local CI execution by fixing all blocking errors
2. **Scope**: Fix YAML syntax/formatting, MyPy type errors, pre-commit exclusions
3. **Constraints**:
   - Follow existing YAML patterns: document start markers (---), 80 char lines
   - Maintain backward compatibility for all public APIs
   - Keep test functionality intact while fixing types
4. **Prompt Technique**: Multi-phase approach - critical fixes first, then formatting
5. **Testing**: Must pass ./scripts/run-ci-docker.sh after all fixes
6. **Documentation**: Update any changed configuration explanations

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 15 files
• Context budget: ≤ 40k tokens (many files to fix)
• Performance budget: No runtime impact (linting config only)
• Code quality: yamllint compliance, mypy --strict passing
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete fixes for all identified issues.
Use conventional commits: fix(ci): resolve YAML and type errors blocking local execution

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance - MUST PASS)
- `yamllint context/` (all YAML files valid)
- `mypy --strict tests/` (all type errors resolved)
- `pre-commit run --all-files` (hooks work on all files)
- **Issue-specific tests**:
  - Verify decision.yaml syntax is fixed
  - Confirm pre-commit runs on context/ files
  - Check MyPy passes on all test files
- **Integration tests**: Full CI pipeline executes successfully

## ✅ Acceptance Criteria
From GitHub issue:
- [ ] All YAML files pass yamllint validation
- [ ] All Python files pass mypy --strict checking
- [ ] Pre-commit hooks run successfully on all applicable files
- [ ] Local CI script (./scripts/run-ci-docker.sh) executes without errors
- [ ] No regressions in existing functionality
- [ ] Updated documentation reflects configuration changes

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 40000 (many files to process)
├── time_budget: 2-3 hours
├── cost_estimate: $8-12
├── complexity: High (multi-file, multi-format)
└── files_affected: 15

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1204
sprint: 4.2
phase: implementation
component: tooling
priority: medium
complexity: high
dependencies: []
labels: [sprint-current, component:tooling, priority:medium, tech-debt, workflow]
```