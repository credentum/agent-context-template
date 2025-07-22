# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1208-fix-local-ci-script
# Generated from GitHub Issue #1208
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1208-ci-script-run-all-checks`

## 🎯 Goal (≤ 2 lines)
> Modify local CI script to run ALL checks regardless of individual failures, collecting and reporting all errors at the end

## 🧠 Context
- **GitHub Issue**: #1208 - [SPRINT-4.2] Fix Local CI Script to Run All Checks Despite Failures
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: CI/Tooling Improvements
- **Component**: tooling
- **Priority**: high
- **Why this matters**: Developers are missing errors locally, causing fix-push-discover cycles
- **Dependencies**: None
- **Related**: PR #1207 (where issue was discovered)

## 🛠️ Subtasks
Based on analysis, this is a focused change to error handling logic

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/test-comprehensive-ci.sh | modify | Direct Patching | Remove `set -e` and refactor error handling | Low |
| scripts/run-ci-docker.sh | analyze | None | Understand integration with comprehensive script | Low |
| scripts/claude-ci.sh | verify | None | Ensure compatibility with changes | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD pipeline optimization and shell scripting.

**Context**
GitHub Issue #1208: Fix Local CI Script to Run All Checks Despite Failures
During PR #1207, the team discovered that `./scripts/run-ci-docker.sh` stops on first failure due to `set -e` in test-comprehensive-ci.sh. This caused a Black formatting error to hide a Flake8 line length error, only discovered after push.

Current codebase uses:
- Docker-based CI environment matching GitHub Actions
- Bash scripts for orchestration
- Multiple linting tools: Black, isort, Flake8, MyPy, yamllint

Related files:
- scripts/test-comprehensive-ci.sh (main logic with `set -e` issue)
- scripts/run-ci-docker.sh (wrapper that calls Docker services)
- docker-compose.ci.yml (defines CI services)

**Instructions**
1. **Primary Objective**: Modify test-comprehensive-ci.sh to run ALL checks even when individual checks fail
2. **Scope**: Focus on error collection and reporting logic
3. **Constraints**:
   - Preserve existing script structure and functionality
   - Exit code must still indicate overall failure if any check fails
   - Maintain clear, colored output for each check
   - Keep existing run_check() function pattern
4. **Prompt Technique**: Direct patching - remove `set -e` and enhance error collection
5. **Testing**: Script should handle multiple failures gracefully
6. **Documentation**: Update comments to explain new error handling approach

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 1 file primarily
• Context budget: ≤ 5k tokens
• Performance budget: No performance impact
• Code quality: Maintain existing bash style
• CI compliance: Must work in Docker environment

**Output Format**
Return the modified script with improved error handling.
Ensure the summary shows which checks passed/failed.
Example summary format already exists in script (lines 143-173).

## 🔍 Verification & Testing
- Manual test with intentional errors:
  - Create Black formatting error
  - Create Flake8 line length error
  - Verify BOTH errors are reported
- `./scripts/run-ci-docker.sh` (verify all checks run)
- `./scripts/run-ci-docker.sh black` (verify individual checks still work)
- `./scripts/claude-ci.sh all` (verify integration)

## ✅ Acceptance Criteria
- [x] Local CI script runs ALL checks regardless of failures
- [x] Script collects and reports ALL errors at the end
- [x] Exit code still indicates failure if any check fails
- [x] Clear summary showing which checks passed/failed
- [x] No fix-push-discover cycles due to hidden errors

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5k (single file modification)
├── time_budget: 30 minutes
├── cost_estimate: $0.10
├── complexity: Low (bash script refactoring)
└── files_affected: 1-2

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1208
sprint: sprint-4.2
phase: "Phase 2: CI/Tooling Improvements"
component: tooling
priority: high
complexity: low
dependencies: []
```