# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1063-align-github-actions-claude-local-ci
# Generated from GitHub Issue #1063
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1063-align-github-actions-claude-local-ci`

## 🎯 Goal (≤ 2 lines)
> Consolidate GitHub Actions workflows to use the same claude-ci scripts that Claude uses locally, ensuring identical behavior between local and GitHub CI runs.

## 🧠 Context
- **GitHub Issue**: #1063 - Align GitHub Actions with Claude Local CI
- **Sprint**: Not specified in current sprint-5
- **Phase**: Enhancement/Infrastructure
- **Component**: CI/CD workflows
- **Priority**: Medium (important for maintainability but not blocking)
- **Why this matters**: Currently have 20+ GitHub workflows with different logic than local CI, causing inconsistent results and maintenance burden
- **Dependencies**: Depends on existing claude-ci.sh script (#1061)
- **Related**: Simplifies all existing GitHub workflows

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/ci-unified.yml | create | Implementation Pattern | New unified CI pipeline | Low |
| .github/workflows/pr-review-unified.yml | create | Implementation Pattern | PR review using local simulator | Low |
| .github/workflows/ci-optimized.yml | modify | Refactoring | Update to use claude-ci commands | Med |
| scripts/claude-ci.sh | modify | Enhancement | Add --github-output flag for Actions | Low |
| .github/workflows/*.yml | modify | Mass Refactoring | Simplify multiple workflows | High |
| scripts/post-review-comment.py | create | Implementation Pattern | Parse review results for GitHub | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in GitHub Actions and CI/CD pipeline optimization.

**Context**
GitHub Issue #1063: Align GitHub Actions with Claude Local CI
Current situation: 20+ GitHub workflows with embedded CI logic that differs from local claude-ci.sh commands, causing:
- Different results between local and GitHub CI
- Duplicate maintenance of CI logic  
- Complex workflows that are hard to debug
- Confusion when local checks pass but GitHub fails

The existing claude-ci.sh script provides unified commands:
- claude-ci check <file> - Validate single file
- claude-ci test - Smart test selection
- claude-ci pre-commit - Pre-commit validation  
- claude-ci all - Complete CI pipeline
- claude-ci review - PR review simulation

Current workflows like ci-optimized.yml (802 lines) embed complex logic that should delegate to claude-ci scripts.

**Instructions**
1. **Primary Objective**: Create unified workflows that call claude-ci scripts instead of embedding CI logic
2. **Scope**: Refactor existing workflows to use single source of truth for CI logic
3. **Constraints**:
   - Follow existing code patterns: YAML workflows, bash script delegation
   - Maintain backward compatibility with existing PR checks
   - Keep same security permissions and job isolation
   - Preserve caching and parallel execution benefits
4. **Prompt Technique**: Implementation Pattern - consolidate complex embedded logic into simple script calls
5. **Testing**: Ensure identical results between old and new workflows during transition
6. **Documentation**: Update workflow documentation and migration guides

**Technical Constraints**
• Expected diff ≤ 500 LoC across multiple workflow files
• Context budget: ≤ 15k tokens (mainly workflow YAML changes)  
• Performance budget: Maintain or improve current CI performance
• Code quality: YAML validation, consistent job names, proper error handling
• CI compliance: All Docker CI checks must continue to pass

**Output Format**
Return complete implementation with:
1. New unified workflow files that delegate to claude-ci
2. Enhanced claude-ci script with --github-output support
3. Migration strategy for transitioning workflows
4. Use conventional commits: feat(ci): consolidate workflows to use claude-ci scripts

## 🔍 Verification & Testing
- `./scripts/claude-ci.sh all --github-output` (GitHub Actions compatibility)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)  
- **Issue-specific tests**: Compare old vs new workflow results during parallel execution
- **Integration tests**: Verify GitHub Actions can parse claude-ci JSON output properly

## ✅ Acceptance Criteria
**From GitHub Issue #1063:**
- [ ] GitHub workflows use claude-ci scripts instead of embedded logic
- [ ] Identical results between local and GitHub runs
- [ ] Simplified workflow YAML files (reduce from 20+ to core set)
- [ ] Single source of truth for CI logic in claude-ci.sh
- [ ] Reduced workflow maintenance burden
- [ ] Clear mapping between local commands and GitHub checks

**Additional Criteria:**
- [ ] New ci-unified.yml replaces complex embedded logic
- [ ] claude-ci.sh supports --github-output for Actions integration
- [ ] Legacy workflows can run in parallel during migration
- [ ] All existing CI checks continue to pass
- [ ] Documentation updated with new architecture

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: ~8000 (moderate YAML refactoring)
├── time_budget: 2-3 hours (workflow consolidation)
├── cost_estimate: ~$12-15 in tokens
├── complexity: Medium (workflow refactoring + script enhancement)
└── files_affected: ~8-10 workflow files + 1 script + docs

Actuals (completed):
├── tokens_used: ~12,000 (above estimate due to YAML troubleshooting)
├── time_taken: ~3 hours (within estimate range)
├── cost_actual: ~$18 in tokens (slightly above due to complexity)
├── iterations_needed: 3 (main implementation + 2 rounds of fixes)
└── context_clears: 0 (stayed within context window)
```

## 🏷️ Metadata
```yaml
github_issue: 1063
sprint: not-assigned
phase: enhancement
component: ci
priority: medium
complexity: medium
dependencies: ["claude-ci.sh script"]
```