# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1489-fix-all-remaining-ci-validation-issues
# Generated from GitHub Issue #1489
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1489-complete-ci-pipeline-validation`

## 🎯 Goal (≤ 2 lines)
> Fix all remaining CI validation issues including 107+ YAML errors, 20 MyPy type errors in tests,
> and optimize Docker CI/ARC-Reviewer performance to achieve 100% CI compliance.

## 🧠 Context
- **GitHub Issue**: #1489 - [SPRINT-4.1] Fix All Remaining CI Validation Issues - Complete CI Pipeline
- **Sprint**: sprint-4.1
- **Phase**: Phase 3: Quality Assurance
- **Component**: ci-cd
- **Priority**: high
- **Why this matters**: PR #1448 fixed critical blockers but many CI issues remain, preventing clean CI pipeline
- **Dependencies**: Parent issue #1426 (partially resolved), PR #1448 (merged)
- **Related**: validation-report-1403.yaml details all issues

## 🛠️ Subtasks
Based on comprehensive issue analysis and validation report:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| context/sprints/sprint-4.1.yaml | modify | Few-shot examples | Fix 107+ YAML indentation/line length errors | High |
| context/schemas/*.yaml (6 files) | modify | Pattern matching | Resolve multi-document YAML issues | Medium |
| tests/test_config_validator.py | modify | Type annotation guide | Add MyPy type annotations (lines 100, 124) | Low |
| tests/test_ci_signing.py | modify | Type annotation guide | Fix Optional[ModuleSpec] handling | Low |
| tests/test_ci_analytics_metrics.py | modify | Error correction | Fix imports and duplicate definitions | Low |
| scripts/run-ci-docker.sh | modify | Performance optimization | Add caching, reduce time to <5min | High |
| src/agents/arc_reviewer.py | modify | Configuration | Add timeout config (default 120s) | Medium |
| .pre-commit-config.yaml | review | Configuration analysis | Verify/adjust YAML validation settings | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD pipeline optimization and code quality enforcement.

**Context**
GitHub Issue #1489: [SPRINT-4.1] Fix All Remaining CI Validation Issues - Complete CI Pipeline
- PR #1448 fixed critical blockers but 100+ validation issues remain
- Validation report 1403 documents all specific failures
- Current state: YAML syntax errors, type checking failures, performance timeouts
- Files affected: sprint-4.1.yaml (107+ errors), 6 schema files, 3-4 test files, CI scripts
- Performance issues: Docker CI >7min, ARC-Reviewer >2min timeouts

**Instructions**
1. **Primary Objective**: Fix ALL remaining CI validation issues to achieve 100% compliance
2. **Scope**: Address YAML formatting, type annotations, and performance optimization
3. **Constraints**:
   - Maintain YAML semantic meaning while fixing formatting
   - Follow existing MyPy type annotation patterns
   - Keep Docker CI under 5 minutes execution time
   - Keep ARC-Reviewer under 2 minutes execution time
   - No breaking changes to CI functionality
4. **Prompt Technique**: Use targeted fixes based on error type:
   - YAML: Few-shot examples of correct formatting
   - Types: Type annotation guides with Optional handling
   - Performance: Profiling-based optimization
5. **Testing**: Each fix must pass its specific validation tool
6. **Documentation**: Update relevant configurations if needed

**Technical Constraints**
• Expected diff ≤ 500 LoC across ~10 files
• Context budget: ≤ 40k tokens
• Performance budget: Docker CI <5min, ARC <2min
• Code quality: All pre-commit hooks must pass
• CI compliance: ./scripts/run-ci-docker.sh must complete successfully

**Output Format**
Return incremental fixes for each category:
1. YAML formatting fixes (test after each file)
2. Type annotation additions (test with mypy)
3. Performance optimizations (benchmark before/after)
Use conventional commits: fix(ci): [specific fix description]

## 🔍 Verification & Testing
- `yamllint context/sprints/sprint-4.1.yaml` (YAML validation)
- `yamllint context/schemas/*.yaml` (schema validation)
- `mypy tests/test_*.py` (type checking specific files)
- `pre-commit run --all-files` (comprehensive validation)
- `./scripts/run-ci-docker.sh` (full Docker CI - must be <5min)
- `python -m src.agents.arc_reviewer` (ARC timeout test - must be <2min)
- `pytest --cov=src --cov-report=term-missing` (maintain ≥78.0% coverage)

## ✅ Acceptance Criteria
From GitHub issue #1489:
- [ ] All 107+ YAML indentation errors in sprint-4.1.yaml fixed
- [ ] All line length violations (>80 characters) in sprint-4.1.yaml resolved
- [ ] Multi-document YAML issues in 6 schema files resolved
- [ ] All YAML files pass both check-yaml and yamllint hooks
- [ ] All 20 MyPy type errors in test files fixed
- [ ] Docker CI execution time optimized to <5 minutes
- [ ] ARC-Reviewer configured with timeout to prevent >2 minute hangs
- [ ] All pre-commit hooks pass
- [ ] Coverage remains above 78.0% baseline
- [ ] Zero validation errors in final CI run

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 35-40k (multiple files, iterative fixes)
├── time_budget: 6-9 hours
├── cost_estimate: ~$2-3
├── complexity: High (many distinct issues)
└── files_affected: ~10 files

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1489
sprint: sprint-4.1
phase: 3
component: ci-cd
priority: high
complexity: high
dependencies: [1426, 1448]
validation_report: validation-report-1403.yaml
```
