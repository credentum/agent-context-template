# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1201-fix-flake8-errors-blocking-pre-push-hooks
# Generated from GitHub Issue #1201
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1201-fix-flake8-errors-blocking-pre-push-hooks`

## 🎯 Goal (≤ 2 lines)
> Fix Docker CI configuration to respect .flake8 exclude settings, preventing test_formatting_issues.py from blocking pre-push hooks

## 🧠 Context
- **GitHub Issue**: #1201 - [SPRINT-4.2] Fix flake8 errors blocking pre-push hooks
- **Sprint**: sprint-4-2
- **Phase**: Phase 2: Implementation
- **Component**: testing
- **Priority**: high (blocking pre-push hooks)
- **Why this matters**: Developers cannot push code without SKIP_HOOKS=1, bypassing quality checks
- **Dependencies**: None - configuration fix only
- **Related**: Pre-commit hooks work correctly, Docker CI does not

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/test-comprehensive-ci.sh | modify | Direct fix | Use .flake8 config instead of inline params | Low |
| docker-compose.ci.yml | modify | Direct fix | Mount .flake8 config file | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD pipeline configuration.

**Context**
GitHub Issue #1201: Fix flake8 errors blocking pre-push hooks
The tests/test_formatting_issues.py file is intentionally designed with formatting issues for testing formatters. It has proper exclusion in .flake8 config file but Docker CI environment ignores this configuration and uses inline parameters instead. Pre-commit hooks work correctly because they respect .flake8 config.

Current problem: Docker CI runs `flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503` instead of using the .flake8 config file that excludes tests/test_formatting_issues.py.

Related files:
- .flake8 (has proper exclude on line 21)
- scripts/test-comprehensive-ci.sh (line 54 - uses inline params)
- docker-compose.ci.yml (lines 89-91 - uses inline params)

**Instructions**
1. **Primary Objective**: Make Docker CI respect .flake8 configuration file exclude settings
2. **Scope**: Fix CI configuration without modifying the intentionally broken test file
3. **Constraints**:
   - Do NOT modify tests/test_formatting_issues.py (it's intentionally broken for testing)
   - Maintain all existing flake8 settings (max-line-length=100, extend-ignore=E203,W503)
   - Keep the same behavior for all other files
4. **Prompt Technique**: Direct configuration fix because this is a straightforward config issue
5. **Testing**: Verify Docker CI no longer fails on test_formatting_issues.py
6. **Documentation**: Update if needed to clarify CI behavior

**Technical Constraints**
• Expected diff ≤ 10 LoC, ≤ 2 files
• Context budget: ≤ 5k tokens
• Performance budget: Configuration change only
• Code quality: Must maintain existing CI behavior for all other files
• CI compliance: Docker CI must pass after changes

**Output Format**
Return complete implementation addressing CI configuration issue.
Use conventional commits: fix(ci): use .flake8 config instead of inline parameters

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance - must pass)
- `pre-commit run flake8 --all-files` (verify pre-commit still works)
- Verify tests/test_formatting_issues.py is properly excluded from CI
- Verify other files still get proper flake8 checking

## ✅ Acceptance Criteria
- [ ] All flake8 errors in Docker CI environment are resolved
- [ ] Pre-push hooks execute successfully without requiring SKIP_HOOKS=1
- [ ] No regressions in existing functionality (other files still checked)
- [ ] Code follows project formatting standards
- [ ] tests/test_formatting_issues.py remains excluded from flake8 checks
- [ ] Docker CI respects .flake8 configuration file

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000 (simple config fix)
├── time_budget: 15 minutes (straightforward change)
├── cost_estimate: $0.05
├── complexity: Low (configuration change only)
└── files_affected: 2

Actuals (to be filled):
├── tokens_used: ~15,000 (estimated)
├── time_taken: 25 minutes
├── cost_actual: $0.15 (estimated)
├── iterations_needed: 1 (solution worked on first try)
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1201
sprint: sprint-4-2
phase: "Phase 2: Implementation"
component: testing
priority: high
complexity: low
dependencies: []
```
