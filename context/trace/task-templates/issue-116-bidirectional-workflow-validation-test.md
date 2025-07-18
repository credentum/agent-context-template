# ────────────────────────────────────────────────────────────────────────
# TASK: issue-116-bidirectional-workflow-validation-test
# Generated from GitHub Issue #116
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-116-bidirectional-workflow-validation-test`

## 🎯 Goal (≤ 2 lines)
> Test and validate bidirectional sync between sprint YAML and GitHub issues by completing all test scenarios and validation steps for issue #116.

## 🧠 Context
- **GitHub Issue**: #116 - [Sprint 41] Phase 8: Bidirectional Workflow Validation Test
- **Sprint**: Sprint 4.1: Infrastructure Bring-Up
- **Phase**: 8 - Bidirectional Workflow Testing
- **Component**: testing
- **Priority**: high
- **Why this matters**: Ensures the sprint automation system works correctly for future sprints and validates the bidirectional sync infrastructure
- **Dependencies**: None (self-contained test)
- **Related**: Issue #93 (original bidirectional workflow request), existing sprint-issue-linker.py

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| src/agents/sprint_issue_linker.py | test | Command execution | Verify sync functionality works | Low |
| context/sprints/sprint-4.1.yaml | modify | Direct edit | Update github_issue field | Low |
| tests/test_bidirectional_sync.py | create | Test-driven | Create validation test | Med |
| context/trace/logs/bidirectional-test-results.md | create | Documentation | Log test results | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on sprint automation and GitHub integration systems.

**Context**
GitHub Issue #116: [Sprint 41] Phase 8: Bidirectional Workflow Validation Test
This is a test task specifically designed to validate the bidirectional sync workflow between sprint YAML files and GitHub issues. The task already exists in sprint-4.1.yaml but needs to be properly linked to GitHub issue #116 and all test scenarios need to be completed.

Current codebase follows Python/pytest patterns with click CLI tools for automation.
Related files:
- src/agents/sprint_issue_linker.py (main sync logic)
- context/sprints/sprint-4.1.yaml (test sprint with this task)
- .github/workflows/sprint-update.yml (automated sync workflow)

**Instructions**
1. **Primary Objective**: Complete all test scenarios for bidirectional sync validation
2. **Scope**: Test YAML→GitHub and GitHub→YAML sync, validate all scenarios work correctly
3. **Constraints**:
   - Follow existing code patterns in sprint_issue_linker.py
   - Maintain backward compatibility with existing sprint system
   - Keep test temporary and removable after validation
4. **Prompt Technique**: Command execution because this is primarily testing existing functionality
5. **Testing**: Create comprehensive test to validate all bidirectional sync scenarios
6. **Documentation**: Log detailed test results for future reference

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 3 files
• Context budget: ≤ 5k tokens
• Performance budget: Fast execution (CLI tool testing)
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete test implementation and validation results.
Use conventional commits: test(sprint): validate bidirectional sync workflow

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Run `python -m src.agents.sprint_issue_linker sync --sprint sprint-4.1 --verbose`
  - Verify GitHub issue #116 gets linked to sprint task
  - Test status change sync in both directions
  - Verify label synchronization works
  - Test orphan handling (task removal)
- **Integration tests**: GitHub API functionality with real issue operations

## ✅ Acceptance Criteria
Based on GitHub Issue #116:
- [x] Task created in YAML generates GitHub issue (already done - issue #116 exists)
- [ ] GitHub issue status updates reflect in YAML
- [ ] Task completion in YAML closes GitHub issue
- [ ] Label changes sync bidirectionally
- [ ] Task removal from YAML closes GitHub issue
- [ ] Verification of issue creation and YAML update with issue number
- [ ] Test status changes in both directions
- [ ] Test label synchronization
- [ ] Test orphan handling when task is removed

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000 (testing existing functionality)
├── time_budget: 30 minutes (primarily CLI execution)
├── cost_estimate: $0.15 (minimal context usage)
├── complexity: Low (testing existing code)
└── files_affected: 3 (sprint yaml, test file, log file)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 116
sprint: sprint-4.1
phase: 8
component: testing
priority: high
complexity: low
dependencies: []
task_type: validation_test
temporary: true
```
