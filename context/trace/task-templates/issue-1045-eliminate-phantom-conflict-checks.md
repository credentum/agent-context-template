# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1045-eliminate-phantom-conflict-checks
# Generated from GitHub Issue #1045
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1045-eliminate-phantom-conflict-checks`

## 🎯 Goal (≤ 2 lines)
> Remove github.rest.checks.create API calls from pr-conflict-validator.yml to eliminate phantom "🔍 Conflict Detection" checks appearing in unrelated workflows

## 🧠 Context
- **GitHub Issue**: #1045 - [SPRINT-5.2] [MERGE-3/3] Eliminate phantom conflict detection checks across workflows
- **Sprint**: sprint-5-2
- **Phase**: Phase 2: Implementation
- **Component**: ci
- **Priority**: bug, enhancement
- **Why this matters**: Manual check creation causes phantom checks to appear in unrelated workflows (Lint, Tests, Coverage), creating confusion and false failures
- **Dependencies**: Requires #1043 (authentication) and #1044 (syntax fix) merged first
- **Related**: Parent issue #1029, combined PR #1034 (closed but not merged)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/pr-conflict-validator.yml | modify | Direct Replacement | Remove github.rest.checks.create API usage | High |
| docs/workflow-deprecation-plan.md | modify | Append Documentation | Document architectural decision to rely on job status | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer refactoring GitHub Actions workflows to eliminate cross-workflow attribution issues.

**Context**
GitHub Issue #1045: Eliminate phantom conflict detection checks across workflows
- Problem: github.rest.checks.create API calls create checks that get misattributed to other workflows
- Root cause: Manual check creation appears as phantom "🔍 Conflict Detection" in Lint, Tests, Coverage workflows
- Solution: Remove API check creation and rely on native GitHub Actions job status

Current implementation in pr-conflict-validator.yml (lines 114-165):
- Uses github.rest.checks.create to manually create a check run
- This check gets incorrectly attributed to other workflows
- Creates false failures and confusion

**Instructions**
1. **Primary Objective**: Remove all github.rest.checks.create API calls from pr-conflict-validator.yml
2. **Scope**:
   - Remove the "Update PR status check" step entirely (lines 114-165)
   - Keep the conflict detection logic intact
   - Keep the PR commenting functionality for conflicts
   - Let the job's success/failure status serve as the check
3. **Constraints**:
   - Do not modify the actual conflict detection logic
   - Preserve all existing functionality except manual check creation
   - Ensure job fails when conflicts are detected (exit 1)
4. **Prompt Technique**: Direct replacement - remove specific code block
5. **Testing**: Verify workflow syntax remains valid
6. **Documentation**: Update workflow-deprecation-plan.md with architectural decision

**Technical Constraints**
• Expected diff ≤ 50 LoC removal, 2 files
• Context budget: ≤ 3k tokens
• Performance budget: Immediate (removal only)
• Code quality: Valid YAML syntax
• CI compliance: Workflow must remain functional

**Output Format**
Return complete implementation removing API check creation.
Use conventional commits: fix(ci): eliminate phantom conflict detection checks

## 🔍 Verification & Testing
- Validate YAML syntax: `yamllint .github/workflows/pr-conflict-validator.yml`
- Check workflow runs successfully without creating phantom checks
- Verify conflict detection still works (job fails on conflicts)
- Confirm no "🔍 Conflict Detection" checks appear in other workflows
- PR comment functionality still works when conflicts detected

## ✅ Acceptance Criteria
- [x] Remove redundant github.rest.checks.create API calls from pr-conflict-validator
- [x] Ensure conflict detection relies only on job status (pass/fail)
- [x] Verify no phantom "🔍 Conflict Detection" checks appear in other workflows
- [x] Confirm conflict detection is centralized in pr-conflict-validator only
- [x] Update documentation to reflect architectural decision

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 3000
├── time_budget: 30 minutes
├── cost_estimate: $0.10
├── complexity: Low
└── files_affected: 2

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1045
sprint: sprint-5-2
phase: phase-2-implementation
component: ci
priority: high
complexity: low
dependencies: [1043, 1044]
```
