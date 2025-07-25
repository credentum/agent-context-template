# Issue #1426 Fix Critical CI Validation Blocking Issues - Execution Plan
**Date**: 2025-07-25
**Issue**: #1426 - [SPRINT-4.1] Fix Critical CI Validation Blocking Issues
**Sprint**: sprint-4.1
**Component**: ci-cd
**Phase**: Phase 3: Quality Assurance

## Issue Context
Issue #1403 local CI validation revealed 4 critical blocking issues preventing successful PR submission. These failures would cause GitHub Actions to fail and block all development. This task fixes all identified issues to establish reliable CI pipeline.

## Task Template Reference
- **Template**: `context/trace/task-templates/issue-1426-fix-critical-ci-validation-blocking-issues.md`
- **Token Budget**: 15,000 tokens
- **Time Budget**: 3 hours (including full validation)
- **Complexity**: Medium (well-defined fixes)

## Critical Issues to Fix (Priority Order)
1. **YAML Syntax Error** - sprint-4.1.yaml line 367 (blocks all workflows)
2. **Missing Dependencies** - pytest-benchmark not installed (blocks tests)
3. **Type Errors** - 15 MyPy errors in test files (quality issues)
4. **Performance Issues** - Docker CI >7 min, ARC >2 min (UX problems)

## Execution Plan

### Phase 1: Analysis & Planning ✅
- [x] Analyzed issue #1426 and validation report
- [x] Created task template with clear fix strategy
- [x] Identified 8 files needing changes
- [x] Prioritized fixes by impact

### Phase 2: Implementation (Current)
1. **Fix YAML Syntax Error (CRITICAL)**
   - Check line 367 in sprint-4.1.yaml
   - Fix syntax error (likely missing colon or indentation)
   - Validate with context_lint

2. **Add Missing Dependencies**
   - Add pytest-benchmark to pyproject.toml
   - Update any related test configurations

3. **Fix MyPy Type Errors**
   - Review 15 type errors in tests/
   - Add minimal type annotations
   - Avoid over-engineering

4. **Fix Pre-commit/Flake8 Issues**
   - Add document start markers to schema files
   - Fix any line length violations
   - Ensure all hooks pass

5. **Optimize Performance**
   - Analyze Docker CI bottlenecks
   - Configure ARC-Reviewer timeout
   - Target: Docker <5 min, ARC <2 min

### Phase 3: Testing & Validation
1. Run each validation after its fix:
   - YAML: `python -m src.agents.context_lint validate context/`
   - Tests: `pytest --cov=src`
   - Pre-commit: `pre-commit run --all-files`
   - Docker CI: `./scripts/run-ci-docker.sh`

2. Full validation suite (matching issue #1403)

### Phase 4: PR Creation
1. Create PR with comprehensive documentation
2. Reference validation report showing all PASSED
3. Include performance improvements

## Progress Tracking
- [x] YAML syntax error fixed - Added document start marker to sprint-4.1.yaml
- [x] pytest-benchmark added - Already in requirements-test.txt, installed via pip
- [x] Document start markers added to schemas - All schema files already have markers
- [ ] MyPy errors resolved - 20 errors remain, mostly type annotations needed
- [x] Flake8 violations fixed - Pre-commit shows flake8 passing
- [ ] Docker CI optimized - Not yet addressed
- [ ] ARC-Reviewer configured - Not yet addressed
- [ ] Full validation passes - Partial success, YAML linting still failing

## Token Usage
- Analysis phase: ~2,000 tokens
- Implementation: (tracking)
- Testing: (tracking)
- Total: ___/15,000

## Notes
- Validation report shows clear, actionable issues
- Fixes are straightforward - no architectural changes
- Priority on unblocking development
