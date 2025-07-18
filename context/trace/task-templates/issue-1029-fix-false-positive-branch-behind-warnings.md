# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1029-fix-false-positive-branch-behind-warnings
# Generated from GitHub Issue #1029
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1029-false-positive-branch-behind-warnings`

## 🎯 Goal (≤ 2 lines)
> Fix incorrect git rev-list syntax in pr-conflict-validator.yml that causes false positive "branch behind main" warnings when PR branches are actually ahead of main.

## 🧠 Context
- **GitHub Issue**: #1029 - [SPRINT-5.2] Fix false positive 'branch behind main' warnings in pr-conflict-validator
- **Sprint**: sprint-5-2
- **Phase**: Phase 2: Implementation
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: False positive warnings confuse developers and create unnecessary merge anxiety. Critical for CI/CD reliability.
- **Dependencies**: GitHub Actions, git commands
- **Related**: Auto-merge workflows rely on accurate conflict detection

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/pr-conflict-validator.yml | modify | Direct Fix | Fix git rev-list syntax on line 94 | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on GitHub Actions CI/CD workflows.

**Context**
GitHub Issue #1029: Fix false positive 'branch behind main' warnings in pr-conflict-validator
The pr-conflict-validator.yml workflow incorrectly uses `git rev-list --count pr-branch..base-branch` which counts how many commits base is behind PR, but reports this as "PR is behind base". When a PR is ahead of main (normal case), this creates false positive warnings.

Current incorrect code on line 94:
```bash
COMMITS_BEHIND=$(git rev-list --count pr-branch..base-branch)
```

Should be:
```bash
COMMITS_BEHIND=$(git rev-list --count base-branch..pr-branch)
```

Related files: .github/workflows/pr-conflict-validator.yml:94-95
Evidence: ai-pr-monitor.yml uses correct syntax: `git rev-list --count origin/$HEAD_REF..origin/$BASE_REF`

**Instructions**
1. **Primary Objective**: Fix the git rev-list syntax to eliminate false positive warnings
2. **Scope**: Single line change in pr-conflict-validator.yml
3. **Constraints**:
   - Maintain all existing functionality
   - Follow existing YAML formatting patterns
   - Do not modify any other logic or outputs
4. **Prompt Technique**: Direct fix because this is a simple syntax correction with clear evidence
5. **Testing**: Verify syntax matches proven working implementation in ai-pr-monitor.yml
6. **Documentation**: Update commit message to reference issue and explain the fix

**Technical Constraints**
• Expected diff ≤ 5 LoC, 1 file
• Context budget: ≤ 2k tokens
• Performance budget: No impact
• Code quality: Maintain YAML formatting, existing workflow patterns
• CI compliance: No new CI requirements

**Output Format**
Return single line fix addressing the git rev-list syntax error.
Use conventional commits: fix(ci): correct git rev-list syntax for branch behind calculation

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- Manually test git rev-list commands to verify correct syntax
- Check against ai-pr-monitor.yml for reference implementation
- **Issue-specific tests**: Test with current branch to confirm no false warnings
- **Integration tests**: Verify PR conflict validator still works correctly

## ✅ Acceptance Criteria
- [ ] Fix git rev-list syntax in pr-conflict-validator.yml line 94
- [ ] Verify ai-pr-monitor.yml uses correct syntax (already confirmed)
- [ ] Test fix with current PR to confirm no false warnings
- [ ] Update any related documentation about branch status checking

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 2000 tokens (simple syntax fix)
├── time_budget: 10 minutes (single line change)
├── cost_estimate: $0.006 (minimal context needed)
├── complexity: low (direct syntax correction)
└── files_affected: 1 (.github/workflows/pr-conflict-validator.yml)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1029
sprint: sprint-5-2
phase: 2
component: ci-workflows
priority: high
complexity: low
dependencies: ["GitHub Actions", "git commands"]
```
