# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1403-local-ci-validation-before-pr
# Generated from GitHub Issue #1403
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1403-local-ci-validation-before-pr`

## 🎯 Goal (≤ 2 lines)
> Run comprehensive local CI validation suite for PR #1402 to ensure all quality gates pass before submission, preventing CI failures and establishing proper validation workflow for future PRs.

## 🧠 Context
- **GitHub Issue**: #1403 - [SPRINT-4.1] Run Full Local CI Validation Before PR Submission
- **Sprint**: sprint-4.1
- **Phase**: Phase 3: Quality Assurance
- **Component**: ci-cd
- **Priority**: Current (from sprint-current label)
- **Why this matters**: PR #1402 was submitted without complete local validation, creating risk of CI failures. This establishes comprehensive validation process.
- **Dependencies**: Docker, pytest, pre-commit tools, ARC-Reviewer
- **Related**: PR #1402 (merged), Issue #1377 (closed), Issue #1303 (local CI pipeline issues)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/run-ci-docker.sh | execute | Direct execution | Run comprehensive Docker CI matching GitHub Actions | Low |
| scripts/claude-ci.sh | execute | Unified CI interface | Run complete validation pipeline | Low |
| src/agents/arc_reviewer.py | execute | Code review automation | Generate local ARC review report | Medium |
| .coverage-config.json | read | Configuration analysis | Verify coverage thresholds | Low |
| PR #1402 | analyze | Context gathering | Post validation report as comment | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD pipeline validation and quality assurance.

**Context**
GitHub Issue #1403: [SPRINT-4.1] Run Full Local CI Validation Before PR Submission
PR #1402 for issue #1377 was submitted without running complete local CI validation suite. This creates risk of CI failures and requires comprehensive local validation process before any PR submission.

Current codebase follows these CI patterns:
- Docker-based CI environment matching GitHub Actions exactly
- Unified claude-ci.sh command hub for all CI operations
- ARC-Reviewer integration for automated code review
- Coverage thresholds managed centrally in .coverage-config.json
- Pre-commit hooks for linting and formatting

Related files:
- scripts/run-ci-docker.sh: Comprehensive CI matching GitHub Actions
- scripts/claude-ci.sh: Unified CI command interface
- src/agents/arc_reviewer.py: Local ARC-Reviewer execution
- .pre-commit-config.yaml: Linting configuration
- .coverage-config.json: Coverage threshold configuration

**Instructions**
1. **Primary Objective**: Execute complete local CI validation suite and generate agent-readable YAML report
2. **Scope**: Validate existing PR #1402 retrospectively and establish process for future PRs
3. **Constraints**:
   - Follow existing CI patterns: Docker-based validation, unified command interface
   - Maintain backward compatibility with existing validation scripts
   - Keep validation report format machine-readable for agents
4. **Prompt Technique**: Direct execution with structured reporting because this is operational validation task
5. **Testing**: Run all validation stages: Docker CI, unit tests, ARC-Reviewer, pre-commit hooks
6. **Documentation**: Generate YAML validation report for red team review and post to PR

**Technical Constraints**
• Expected execution time: 10-15 minutes for complete validation
• Context budget: ≤ 20k tokens for validation and reporting
• Performance budget: Full CI suite (5-7 min) + tests (3-5 min) + review (2-3 min)
• Code quality: No code changes required, only validation execution
• CI compliance: All Docker CI checks must pass, coverage ≥ 79.8%

**Output Format**
Return structured YAML validation report with PASSED/FAILED status for each stage.
Include specific issue counts, failure details, and remediation steps.
Post final report as comment to PR #1402.

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance - matches GitHub Actions exactly)
- `pytest --cov=src --cov-report=term-missing` (full test suite with coverage report)
- `python -m src.agents.arc_reviewer` (local ARC review execution)
- `pre-commit run --all-files` (complete linting suite)
- **Validation-specific tests**: Verify all stages return PASSED status
- **Integration tests**: Ensure validation report format is agent-readable

## ✅ Acceptance Criteria
- [ ] Run complete local linting suite (Black, isort, flake8, mypy, yamllint) and fix all issues
- [ ] Execute full unit test suite locally (pytest --cov=src) and achieve >79.8% coverage
- [ ] Run ARC-Reviewer locally and address all REQUEST_CHANGES feedback
- [ ] Execute Docker CI validation (`./scripts/run-ci-docker.sh`) to match GitHub Actions exactly
- [ ] Generate agent-readable YAML validation report for red team review
- [ ] Post validation report to PR #1402 as comment
- [ ] Fix any issues found during validation process
- [ ] Re-run validation after fixes to ensure clean state

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000-20000 tokens (execution + reporting)
├── time_budget: 20-30 minutes (including full CI validation)
├── cost_estimate: $0.50-0.75 (primarily execution, minimal generation)
├── complexity: Medium (operational validation, no code changes)
└── files_affected: 0 (execution only, validation report generation)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1403
sprint: sprint-4.1
phase: Phase 3: Quality Assurance
component: ci-cd
priority: current
complexity: medium
dependencies: [docker, pytest, pre-commit, arc-reviewer]
```
