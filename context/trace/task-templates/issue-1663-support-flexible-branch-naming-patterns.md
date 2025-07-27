# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1663-support-flexible-branch-naming-patterns
# Generated from GitHub Issue #1663
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1663-support-flexible-branch-naming-patterns`

## 🎯 Goal (≤ 2 lines)
> Make PR validation flexible to support various branch naming patterns (fix/, feature/, hotfix/, etc.) instead of hardcoded patterns

## 🧠 Context
- **GitHub Issue**: #1663 - Support flexible branch naming patterns in Phase 4 PR validation
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: enhancement/bug
- **Why this matters**: Current workflow validator only checks fix/ and feature/ branches, missing PRs from other valid patterns
- **Dependencies**: GitHub CLI (gh)
- **Related**: #1659-1662 (other workflow validation fixes)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `.claude/workflows/workflow-validator.py` | modify | direct-implementation | Update `_check_pr_created()` method | Low |
| `.claude/config/workflow-enforcement.yaml` | create/modify | structured-config | Add branch pattern configuration | Low |
| tests for validator | create | test-driven | Test various branch patterns | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation and validation systems.

**Context**
GitHub Issue #1663: Support flexible branch naming patterns in Phase 4 PR validation
Current code in `.claude/workflows/workflow-validator.py` lines 327-339 hardcodes branch patterns to only check `fix/` and `feature/` prefixes.
The `_check_pr_created()` method needs to support configurable patterns for: fix, feature, hotfix, refactor, chore, docs, style, test branches.
Current codebase follows Python patterns with YAML configuration loading already implemented.
Related files: workflow-validator.py (main logic), workflow-enforcement.yaml (configuration)

**Instructions**
1. **Primary Objective**: Make PR detection flexible to support configurable branch naming patterns
2. **Scope**: Modify the `_check_pr_created()` method and add configuration support for branch patterns
3. **Constraints**:
   - Follow existing code patterns: subprocess calls, YAML config loading, security-conscious approach
   - Maintain backward compatibility with existing fix/ and feature/ patterns
   - Keep public APIs unchanged - this is internal validation logic
4. **Prompt Technique**: Direct implementation with security validation because task involves subprocess calls
5. **Testing**: Create tests for various branch naming patterns including edge cases
6. **Documentation**: Update method docstring to reflect new flexible behavior

**Technical Constraints**
• Expected diff ≤ 50 LoC, ≤ 2 files
• Context budget: ≤ 5k tokens
• Performance budget: Single method optimization
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass
• Security: Prevent command injection, validate inputs

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: fix(workflow): support flexible branch naming patterns

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Test various branch patterns: fix/, feature/, hotfix/, refactor/, chore/, docs/, style/, test/
- **Integration tests**: Test workflow validation with different branch types

## ✅ Acceptance Criteria
- [ ] Support configurable branch prefix patterns
- [ ] Check for all common branch prefixes by default
- [ ] Allow custom branch naming patterns via configuration
- [ ] Improve PR detection to be more flexible
- [ ] Maintain backward compatibility
- [ ] Add tests for various branch naming patterns

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000 (single method + config + tests)
├── time_budget: 30 minutes
├── cost_estimate: $0.05
├── complexity: low-medium (method modification + config)
└── files_affected: 2-3

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1663
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: enhancement
complexity: low-medium
dependencies: GitHub CLI
```
