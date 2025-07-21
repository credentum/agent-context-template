# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1084-coverage-configuration
# Generated from GitHub Issue #1084
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1084-coverage-configuration-conflict`

## 🎯 Goal (≤ 2 lines)
> Fix branch coverage configuration conflict that causes "Can't combine statement coverage data with branch data" error in all CI runs

## 🧠 Context
- **GitHub Issue**: #1084 - [Coverage] Fix branch coverage configuration conflict causing CI failures
- **Sprint**: Not specified
- **Phase**: Not specified
- **Component**: CI (from labels)
- **Priority**: HIGH (from labels)
- **Why this matters**: This blocks ALL PRs with test changes - critical infrastructure issue
- **Dependencies**: None
- **Related**: PR #1069 (discovered during investigation), commits 01caf4d (removed --cov-branch flag)

## 🛠️ Subtasks
Based on the issue, we need to disable branch coverage in configuration files to match the workflow changes.

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| pyproject.toml | modify | Direct Edit | Change `branch = true` to `branch = false` on line 30 | Low |
| pytest.ini | modify | Direct Edit | Change `branch = True` to `branch = False` on line 35 | Low |
| .coverage-config.json | verify | Read Only | Ensure no branch coverage settings conflict | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing a critical CI infrastructure issue.

**Context**
GitHub Issue #1084: Coverage configuration conflict causing CI failures
- Branch coverage is enabled in pyproject.toml (line 30) and pytest.ini (line 35)
- Recent commit 01caf4d removed --cov-branch from workflows
- This mismatch causes: "coverage.exceptions.DataError: Can't combine statement coverage data with branch data"
- Affects ALL PRs with test changes

**Instructions**
1. **Primary Objective**: Disable branch coverage in configuration files to match workflow behavior
2. **Scope**: Update only coverage configuration settings
3. **Constraints**:
   - Maintain all other coverage settings unchanged
   - Keep coverage thresholds as-is
   - Preserve formatting and structure of config files
4. **Prompt Technique**: Direct Edit - Simple boolean value changes
5. **Testing**: Must verify with Docker CI after changes
6. **Documentation**: Update inline comments if they reference branch coverage

**Technical Constraints**
• Expected diff ≤ 4 LoC, ≤ 2 files
• Context budget: ≤ 5k tokens
• Performance budget: Immediate - no computation needed
• Code quality: Maintain existing formatting
• CI compliance: All Docker CI checks must pass

**Output Format**
Return minimal diffs changing only the branch coverage settings.
Use conventional commit: fix(ci): disable branch coverage in config files

## 🔍 Verification & Testing
- Clear existing coverage: `find . -name ".coverage*" -delete && find . -name "htmlcov" -type d -exec rm -rf {} +`
- `pytest --cov=src --cov-report=term-missing` (verify no branch coverage errors)
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Verify coverage combines without errors
- **Integration tests**: Run a workflow that previously failed

## ✅ Acceptance Criteria
- [x] Coverage configuration is consistent across all files
- [x] CI tests pass without coverage data combination errors
- [x] Docker CI (`./scripts/run-ci-docker.sh`) passes locally
- [x] Coverage reports generate successfully

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 2000 (minimal file changes)
├── time_budget: 15 minutes
├── cost_estimate: $0.02
├── complexity: Low - configuration change only
└── files_affected: 2

Actuals (to be filled):
├── tokens_used: ~15000
├── time_taken: 10 minutes
├── cost_actual: $0.05
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1084
sprint: null
phase: null
component: ci
priority: high
complexity: low
dependencies: []
```
