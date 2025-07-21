# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1044-git-rev-list-syntax-fix
# Generated from GitHub Issue #1044
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1044-git-rev-list-syntax`

## 🎯 Goal (≤ 2 lines)
> Fix inverted git rev-list syntax in pr-conflict-validator.yml that causes false "PR is behind" warnings by swapping the branch order from `pr-branch..base-branch` to `base-branch..pr-branch`.

## 🧠 Context
- **GitHub Issue**: #1044 - [SPRINT-5.2] [MERGE-2/3] Fix git rev-list syntax for branch behind calculation
- **Sprint**: sprint-5-2
- **Phase**: Phase 2: Implementation
- **Component**: ci
- **Priority**: bug
- **Why this matters**: Current syntax causes false positive warnings about PRs being behind when they're actually ahead
- **Dependencies**: Issue #1043 (prerequisite for API authentication)
- **Related**: Issue #1029 (parent), PR #1034 (combined PR), ai-pr-monitor.yml:518 (working example)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/pr-conflict-validator.yml:97 | modify | Direct Edit | Fix git rev-list syntax | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing a git command syntax error in GitHub Actions workflows.

**Context**
GitHub Issue #1044: Fix git rev-list syntax for branch behind calculation
The git rev-list command on line 97 of pr-conflict-validator.yml is inverted, causing it to count how many commits the base branch is behind the PR branch, but reporting this as "PR is behind base".

Current code (line 97):
```bash
COMMITS_BEHIND=$(git rev-list --count pr-branch..base-branch)
```

Working example from ai-pr-monitor.yml:518:
```bash
COMMITS_BEHIND=$(git rev-list --count origin/$HEAD_REF..origin/$BASE_REF)
```

**Instructions**
1. **Primary Objective**: Fix the git rev-list syntax by swapping branch order
2. **Scope**: Change only line 97 in pr-conflict-validator.yml
3. **Constraints**:
   - Maintain variable names (COMMITS_BEHIND, pr-branch, base-branch)
   - Do not modify line 98 (COMMITS_AHEAD calculation is already correct)
   - Preserve exact formatting and spacing
4. **Prompt Technique**: Direct Edit - single line syntax fix
5. **Testing**: Verify the logic aligns with git rev-list semantics
6. **Documentation**: No documentation changes needed

**Technical Constraints**
• Expected diff ≤ 1 LoC, 1 file
• Context budget: ≤ 1k tokens
• Performance budget: Immediate
• Code quality: Maintain GitHub Actions YAML standards
• CI compliance: No workflow syntax errors

**Output Format**
Return the corrected line 97 with proper git rev-list syntax.
Use conventional commits: fix(ci): correct git rev-list syntax for branch behind calculation

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- Manual verification: Create test branches ahead/behind main
- Compare behavior with ai-pr-monitor.yml implementation
- Ensure no false "branch is behind" warnings for branches ahead of main

## ✅ Acceptance Criteria
- [x] Fix git rev-list syntax on line 94 of pr-conflict-validator.yml
- [x] Change from `pr-branch..base-branch` to `base-branch..pr-branch`
- [x] Verify COMMITS_AHEAD calculation on line 95 is correct
- [x] Test with branches that are ahead of main to confirm no false warnings
- [x] Compare implementation with working version in ai-pr-monitor.yml

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 1k
├── time_budget: 10 minutes
├── cost_estimate: $0.001
├── complexity: trivial (1 line fix)
└── files_affected: 1

Actuals (to be filled):
├── tokens_used: ~30k
├── time_taken: 8 minutes
├── cost_actual: $0.005
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1044
sprint: sprint-5-2
phase: phase-2-implementation
component: ci
priority: bug
complexity: trivial
dependencies: [1043]
```
