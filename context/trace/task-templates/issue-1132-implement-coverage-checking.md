# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1132-implement-coverage-checking
# Generated from GitHub Issue #1132
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1132-implement-coverage-checking`

## 🎯 Goal (≤ 2 lines)
> Implement coverage checking in local PR simulation that exactly matches GitHub Actions environment for accurate review simulation.

## 🧠 Context
- **GitHub Issue**: #1132 - [Component: CI] Implement coverage checking matching GitHub
- **Sprint**: investigation-1060 decomposition
- **Phase**: implementation
- **Component**: ci
- **Priority**: enhancement
- **Why this matters**: Local coverage calculations must exactly match GitHub Actions to provide accurate review simulation
- **Dependencies**: Depends on #1131 (PR simulation environment) - COMPLETED
- **Related**: Part of investigation #1060, uses .coverage-config.json configuration

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/simulate-pr-review.sh | modify | chain-of-thought | Add coverage calculation matching GitHub CI | Low |
| scripts/lib/pr-simulation-helpers.sh | create/modify | few-shot | Helper functions for coverage analysis | Low |
| scripts/coverage_summary.py | analyze | investigation | Understand current coverage logic | Med |
| scripts/get_coverage_threshold.py | analyze | investigation | Understand threshold retrieval | Low |
| .coverage-config.json | reference | documentation | Central coverage configuration source | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD pipeline consistency between local and GitHub Actions environments.

**Context**
GitHub Issue #1132: [Component: CI] Implement coverage checking matching GitHub
Current state: Local PR simulation exists but coverage checking doesn't match GitHub Actions exactly.
The PR simulation script uses extracted ARC-Reviewer module but needs accurate coverage validation.
GitHub Actions workflow (.github/workflows/test-coverage.yml) uses specific coverage commands:
- `python -m pytest --cov=src --cov-report=term-missing:skip-covered --cov-report=xml --cov-report=json -v`
- `python scripts/coverage_summary.py`
- `THRESHOLD=$(python scripts/get_coverage_threshold.py); python -m coverage report --fail-under=$THRESHOLD`

Related files: scripts/simulate-pr-review.sh, scripts/test-coverage-like-ci.sh, .coverage-config.json

**Instructions**
1. **Primary Objective**: Make local coverage calculation identical to GitHub CI environment
2. **Scope**: Modify PR simulation to use exact same coverage commands and thresholds as GitHub Actions
3. **Constraints**:
   - Follow existing script patterns in scripts/ directory
   - Use .coverage-config.json as single source of truth for thresholds
   - Maintain backward compatibility with existing simulate-pr-review.sh interface
   - Keep public APIs unchanged
4. **Prompt Technique**: Chain-of-thought for main implementation, investigation for understanding existing patterns
5. **Testing**: Ensure coverage results match between local and GitHub CI exactly
6. **Documentation**: Update script comments to explain GitHub CI matching

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 3 files
• Context budget: ≤ 15k tokens
• Performance budget: Coverage calculation should complete in <30 seconds
• Code quality: Follow bash best practices, proper error handling
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing coverage matching requirements.
Use conventional commits: fix(ci): implement coverage checking matching GitHub

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `./scripts/simulate-pr-review.sh --verbose` (test coverage calculation)
- `./scripts/test-coverage-like-ci.sh` (compare with CI-like execution)
- **Issue-specific tests**: Coverage percentages match between local and GitHub exactly
- **Integration tests**: PR simulation produces same coverage verdict as GitHub Actions

## ✅ Acceptance Criteria
- [ ] Coverage calculation matches GitHub CI exactly
- [ ] Baseline threshold checking implemented using .coverage-config.json
- [ ] Target threshold validation included
- [ ] Handles module-specific coverage requirements
- [ ] Outputs coverage data in same format as GitHub Actions
- [ ] Local simulation and GitHub Actions produce identical coverage results

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12000 (moderate complexity, existing patterns)
├── time_budget: 2 hours (modification of existing script)
├── cost_estimate: $0.15 (estimated token usage)
├── complexity: medium (bash scripting, CI process matching)
└── files_affected: 3 (simulate-pr-review.sh, helpers, documentation)

Actuals (completed):
├── tokens_used: ~8,000 (estimated based on conversation length)
├── time_taken: 1.5 hours
├── cost_actual: $0.10 (estimated)
├── iterations_needed: 2 (initial implementation + refinement)
└── context_clears: 0 (stayed within budget)
```

## 🏷️ Metadata
```yaml
github_issue: 1132
sprint: investigation-1060
phase: implementation
component: ci
priority: enhancement
complexity: medium
dependencies: [1131]
```
