# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1303-fix-local-ci-pipeline
# Generated from GitHub Issue #1303
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1303-fix-local-ci-pipeline`

## 🎯 Goal (≤ 2 lines)
> Fix local CI pipeline to properly detect ARC Reviewer blocking issues and test failures before PRs are created, ensuring local CI matches GitHub CI behavior exactly.

## 🧠 Context
- **GitHub Issue**: #1303 - [URGENT] Fix Local CI Pipeline - ARC Reviewer & Test Failures Not Caught
- **Sprint**: sprint-current
- **Phase**: Active Development
- **Component**: CI/CD
- **Priority**: CRITICAL
- **Why this matters**: Broken PRs being created with blocking issues, undermining local-first CI strategy from Phase 3
- **Dependencies**: PR #1298 (ARC-Reviewer integration) already merged
- **Related**: #1297, #1063, #1131, #1208, #1299

## 🛠️ Subtasks
Based on complexity analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-ci.sh | modify | Chain-of-Thought | Fix ARC reviewer integration and test failure propagation | High |
| scripts/claude-test-changed.sh | modify | Few-Shot | Ensure test failures properly exit with non-zero code | Medium |
| src/agents/arc_reviewer.py | verify/modify | Analytical | Ensure ARC reviewer returns proper exit codes for blocking issues | Medium |
| scripts/run-ci-docker.sh | verify | Systematic | Ensure Docker CI environment runs all checks | Low |
| scripts/claude-pre-commit.sh | verify | Systematic | Ensure pre-commit properly blocks on failures | Low |
| tests/test_ci_integration.py | create | Test-Driven | Add integration tests for CI pipeline | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD pipelines and Python tooling.

**Context**
GitHub Issue #1303: [URGENT] Fix Local CI Pipeline - ARC Reviewer & Test Failures Not Caught
- Local CI is failing to catch critical issues before PRs are created
- ARC Reviewer blocking issues not detected locally
- Test failures not properly blocking CI pipeline
- Issues only surface after pushing to GitHub

Current codebase has:
- `scripts/claude-ci.sh` - Unified CI command hub
- `scripts/claude-test-changed.sh` - Smart test runner
- `src/agents/arc_reviewer.py` - ARC reviewer implementation (extracted from GitHub Actions)
- Integration with Docker CI environment

**Instructions**
1. **Primary Objective**: Fix local CI to catch all issues that GitHub CI would catch
2. **Scope**:
   - Fix ARC Reviewer exit code handling in claude-ci.sh
   - Fix test failure propagation in test runners
   - Ensure all blocking issues prevent PR creation
   - Add integration tests to prevent regression
3. **Constraints**:
   - Maintain backward compatibility with existing scripts
   - Keep execution time under 5 minutes for comprehensive mode
   - Ensure quick mode stays under 30 seconds
   - Match GitHub Actions behavior exactly
4. **Prompt Technique**: Chain-of-Thought for systematic debugging and fixing
5. **Testing**: Add integration tests that verify CI properly blocks on failures
6. **Documentation**: Update any changed command behaviors in script help text

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 6 files
• Context budget: ≤ 50k tokens
• Performance budget: Quick mode < 30s, Comprehensive < 5min
• Code quality: Black formatting, coverage ≥ 78.0%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation fixing all CI pipeline issues.
Use conventional commits: fix(ci): ensure local CI catches all blocking issues

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Verify ARC Reviewer blocks on REQUEST_CHANGES verdict
  - Verify test failures exit with non-zero code
  - Verify comprehensive mode catches all issues
  - Test integration between all CI components
- **Manual verification**:
  - Create a test branch with failing tests
  - Run `claude-ci all` and verify it fails
  - Create code that would trigger ARC Reviewer issues
  - Run `claude-ci review` and verify it blocks

## ✅ Acceptance Criteria
- [x] ARC Reviewer runs locally and blocks on same issues as GitHub
- [x] All test failures caught locally before push
- [x] Local CI matches GitHub CI behavior exactly
- [x] Blocking issues prevent PR creation with clear error messages
- [x] Quick validation available for fast feedback (< 30 seconds)
- [x] Comprehensive validation catches all issues (< 5 minutes)
- [x] Documentation updated with correct local CI workflow
- [x] Regression testing ensures fixes don't break existing functionality

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 50k
├── time_budget: 2-4 hours
├── cost_estimate: $2.50
├── complexity: HIGH (critical infrastructure)
└── files_affected: 6

Actuals (to be filled):
├── tokens_used: ~45k
├── time_taken: 50 minutes
├── cost_actual: $2.25
├── iterations_needed: 2
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1303
sprint: sprint-current
phase: active-development
component: ci-cd
priority: critical
complexity: high
dependencies: [1298]
```
