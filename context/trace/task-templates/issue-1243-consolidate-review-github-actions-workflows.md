# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1243-consolidate-review-github-actions-workflows
# Generated from GitHub Issue #1243
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1243-consolidate-review-github-actions-workflows`

## 🎯 Goal (≤ 2 lines)
> Audit, consolidate, and clean up 29 GitHub Actions workflows to eliminate redundancy, conflicts, and false errors while maintaining CI coverage and functionality.

## 🧠 Context
- **GitHub Issue**: #1243 - [SPRINT-4.2] Consolidate and Review GitHub Actions Workflows
- **Sprint**: sprint-4-2
- **Phase**: Phase 2: Implementation
- **Component**: ci-workflows
- **Priority**: enhancement
- **Why this matters**: 29 workflows with significant redundancy causing maintenance burden and false errors
- **Dependencies**: Related to Issue #1063 (GitHub Actions alignment), PR #1242
- **Related**: MIGRATION.md shows ongoing consolidation work, Issue #1063 scratchpad available

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/*.yml | audit/consolidate | systematic-analysis | Identify duplicates and conflicts | Medium |
| .github/workflows/MIGRATION.md | update | documentation-driven | Track consolidation status | Low |
| ci-optimized*.yml | consolidate | merge-pattern | Combine overlapping CI workflows | High |
| test*.yml | consolidate | merge-pattern | Unify test runners | Medium |
| *.disabled files | remove | cleanup-pattern | Remove obsolete workflows | Low |
| Branch protection rules | update | configuration-review | Ensure no regressions | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in GitHub Actions workflow optimization and CI/CD pipeline consolidation.

**Context**
GitHub Issue #1243: [SPRINT-4.2] Consolidate and Review GitHub Actions Workflows
Current state: 29 total workflows (8 disabled, 21 active) with significant redundancy
- Duplicate CI functionality: ci-optimized.yml, ci-unified.yml, ci-optimized-unified.yml
- Duplicate testing: test.yml, test-suite.yml, test-coverage.yml
- Disabled legacy workflows: auto-merge*.yml, smart-auto-merge.yml
- Related work: Issue #1063 alignment efforts, existing MIGRATION.md tracking

Current codebase follows unified CI pattern with claude-ci.sh delegation.
Related files: .github/workflows/* (29 files), MIGRATION.md, scripts/claude-ci.sh

**Instructions**
1. **Primary Objective**: Consolidate redundant workflows while maintaining CI coverage and functionality
2. **Scope**: Audit all 29 workflows, identify consolidation opportunities, remove obsolete files
3. **Constraints**:
   - Follow existing consolidation patterns from Issue #1063 work
   - Maintain backward compatibility for active PR status checks
   - Preserve security permissions and proper workflow triggers
4. **Prompt Technique**: systematic-analysis because requires methodical review of all workflow files
5. **Testing**: Validate CI functionality remains intact after consolidation
6. **Documentation**: Update MIGRATION.md with consolidation results

**Technical Constraints**
• Expected diff ≤ 1500 LoC, ≤ 15 files (cleanup/consolidation)
• Context budget: ≤ 8k tokens (workflow file review + consolidation)
• Performance budget: Maintain or improve CI execution time
• Code quality: Preserve workflow security, triggers, and permissions
• CI compliance: All consolidated workflows must pass validation

**Output Format**
Return complete consolidation plan and implementation addressing issue requirements.
Use conventional commits: feat(ci): consolidate redundant GitHub Actions workflows

## 🔍 Verification & Testing
- Review all 29 workflow files for redundancy and conflicts
- Validate branch protection rules compatibility
- Test consolidated workflows on feature branch
- Ensure no regression in CI coverage or functionality
- Update documentation to reflect changes

## ✅ Acceptance Criteria
- [ ] Audit all 29 GitHub Actions workflows for redundancy and conflicts
- [ ] Identify and remove obsolete/duplicate workflows showing false errors
- [ ] Consolidate overlapping functionality into unified workflows
- [ ] Document active vs deprecated workflows in MIGRATION.md
- [ ] Ensure no regression in CI coverage or functionality
- [ ] Update branch protection rules to use consolidated workflows

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 8000 (workflow file review + consolidation)
├── time_budget: 2-3 hours (systematic review + implementation)
├── cost_estimate: ~$12 (moderate complexity workflow work)
├── complexity: Medium (workflow consolidation + documentation)
└── files_affected: ~15 (workflow files + documentation)

Actuals:
├── tokens_used: ~5,200 (lower than estimated due to efficient workflow analysis)
├── time_taken: ~90 minutes (faster than estimated 2-3 hours)
├── cost_actual: ~$8 (under budget)
├── iterations_needed: 1 (systematic approach worked well)
└── context_clears: 0 (stayed within context budget)
```

## 🏷️ Metadata
```yaml
github_issue: 1243
sprint: sprint-4-2
phase: Phase 2: Implementation
component: ci-workflows
priority: enhancement
complexity: Medium
dependencies: [1063, 1242]
```
