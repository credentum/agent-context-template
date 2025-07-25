# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1295-github-label-cleanup
# Generated from GitHub Issue #1295
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1295-github-label-cleanup`

## 🎯 Goal (≤ 2 lines)
> Standardize GitHub label system from 30 labels to a consistent naming convention, ensure all template-referenced labels exist, and add label validation to workflows.

## 🧠 Context
- **GitHub Issue**: #1295 - [SPRINT-4.3] GitHub Label System Cleanup and Standardization
- **Sprint**: sprint-4.3
- **Phase**: Infrastructure Cleanup
- **Component**: github-management
- **Priority**: medium
- **Why this matters**: Inconsistent labels cause confusion, missing labels break workflows, and duplicate labels waste time
- **Dependencies**: GitHub API, gh CLI, existing issues/PRs with labels
- **Related**: PRs #80, #72 (label batching work)

## 🛠️ Subtasks
Analysis reveals we have 30 labels (not 60+), but still have issues:
- Missing labels: `claude-ready`, `investigation`, `needs-scope`
- Inconsistent phase format: `phase:4.1` vs templates expecting `phase:?`
- Workflow creating labels without checking: claude-code-review.yml line 823
- Need to standardize categories and naming

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/claude-code-review.yml | modify | Chain-of-Thought | Add label validation before creation | Medium |
| .github/ISSUE_TEMPLATE/sprint-task.md | modify | Direct | Update to use existing labels | Low |
| .github/ISSUE_TEMPLATE/investigation.md | modify | Direct | Update to use existing labels | Low |
| scripts/migrate-labels.sh | create | Template-Based | Automate label migration | Low |
| docs/github-label-guidelines.md | create | Few-Shot | Document label system | Low |
| scripts/validate-labels.py | create | Chain-of-Thought | Validation utility | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in GitHub workflow automation and repository management.

**Context**
GitHub Issue #1295: [SPRINT-4.3] GitHub Label System Cleanup and Standardization
Current state: 30 labels with inconsistent naming, missing template-referenced labels, and workflows that create labels without validation.
Target state: Standardized label system with validation, all templates working, and clear guidelines.
Related files: claude-code-review.yml creates labels at line 823, issue templates reference non-existent labels.

**Instructions**
1. **Primary Objective**: Standardize label system and add validation to prevent future issues
2. **Scope**: Update workflows, templates, create migration script and documentation
3. **Constraints**:
   - Keep existing good labels (component:*, priority:*, etc.)
   - Don't break existing issues/PRs
   - Maintain backward compatibility during migration
4. **Prompt Technique**: Chain-of-Thought for complex workflow logic, Direct for simple updates
5. **Testing**: Dry-run mode for migration, validation before actual changes
6. **Documentation**: Clear guidelines for future label usage

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 6 files
• Context budget: ≤ 15k tokens
• Performance budget: Migration script should handle 1000+ issues
• Code quality: shellcheck for bash, Black for Python
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation with:
- Updated workflow with label validation
- Fixed issue templates
- Migration script with dry-run mode
- Label guidelines documentation
Use conventional commits: fix(labels): standardize GitHub label system

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `shellcheck scripts/migrate-labels.sh` (bash validation)
- `python scripts/validate-labels.py --dry-run` (test validation)
- **Manual testing**: Create test issue with new templates
- **Migration testing**: Run migration in dry-run mode first

## ✅ Acceptance Criteria
- [x] Current label audit shows 30 labels (not 60+)
- [ ] Missing labels created: `claude-ready`, `investigation`, `needs-scope`
- [ ] Workflows check for existing labels before creating
- [ ] All template-referenced labels exist and work
- [ ] Migration script with dry-run mode
- [ ] Documentation of label usage guidelines
- [ ] No disruption to existing issues/PRs

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 2 hours
├── cost_estimate: $0.75
├── complexity: medium
└── files_affected: 6

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1295
sprint: sprint-4.3
phase: infrastructure-cleanup
component: github-management
priority: medium
complexity: medium
dependencies: [github-api, gh-cli]
```
