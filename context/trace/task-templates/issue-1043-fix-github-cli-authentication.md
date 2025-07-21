# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1043-fix-github-cli-authentication
# Generated from GitHub Issue #1043
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1043-github-cli-authentication`

## 🎯 Goal (≤ 2 lines)
> Move GH_TOKEN environment variable from workflow level to job level in pr-conflict-validator.yml to fix GitHub CLI authentication failures.

## 🧠 Context
- **GitHub Issue**: #1043 - [SPRINT-5.2] [MERGE-1/3] Fix GitHub CLI authentication in pr-conflict-validator
- **Sprint**: sprint-5-2
- **Phase**: Phase 2: Implementation
- **Component**: ci
- **Priority**: bug
- **Why this matters**: Without proper authentication, GitHub CLI falls back to unauthenticated API calls with severe rate limits
- **Dependencies**: Part of larger issue #1029, extracted from PR #1034
- **Related**: PR #1034 (closed, not merged)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/pr-conflict-validator.yml | modify | Direct Edit | Move GH_TOKEN to job level | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing GitHub Actions workflow authentication issues.

**Context**
GitHub Issue #1043: Fix GitHub CLI authentication in pr-conflict-validator
The workflow currently defines GH_TOKEN at the workflow level (lines 207-208), but it needs to be at the job level for GitHub CLI commands to authenticate properly.
Current workflow uses `gh pr view` command that requires authentication.

**Instructions**
1. **Primary Objective**: Move GH_TOKEN from workflow-level env to job-level env
2. **Scope**: Only modify the environment variable placement, no other changes
3. **Constraints**:
   - Maintain exact same token value: ${{ secrets.GITHUB_TOKEN }}
   - Place in the validate-conflicts job
   - Remove from workflow level
4. **Prompt Technique**: Direct Edit - simple configuration change
5. **Testing**: Verify syntax is correct and placement follows GitHub Actions best practices
6. **Documentation**: No documentation updates needed for this change

**Technical Constraints**
• Expected diff ≤ 10 LoC, 1 file
• Context budget: ≤ 2k tokens
• Performance budget: No performance impact
• Code quality: YAML syntax must be valid
• CI compliance: Workflow must pass validation

**Output Format**
Return the modified workflow with GH_TOKEN moved to job level.
Use conventional commits: fix(ci): move GH_TOKEN to job level for proper authentication

## 🔍 Verification & Testing
- `yamllint .github/workflows/pr-conflict-validator.yml` (YAML syntax)
- Verify GH_TOKEN is accessible in job context
- Ensure `gh pr view` command will authenticate properly
- Check no other workflows are affected

## ✅ Acceptance Criteria
- [x] Move GH_TOKEN from workflow env to job env in pr-conflict-validator.yml
- [ ] Verify GitHub CLI commands authenticate properly
- [ ] Ensure no fallback to unauthenticated API calls
- [ ] Test that merge_state conflict detection works correctly

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 2000
├── time_budget: 15 minutes
├── cost_estimate: $0.10
├── complexity: trivial
└── files_affected: 1

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1043
sprint: sprint-5-2
phase: 2
component: ci
priority: bug
complexity: trivial
dependencies: [1029, 1034]
```
