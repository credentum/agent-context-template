# Execution Plan: Issue #1489 - Fix All Remaining CI Validation Issues

**Date**: 2025-07-25
**Issue**: #1489 - [SPRINT-4.1] Fix All Remaining CI Validation Issues - Complete CI Pipeline
**Sprint**: sprint-4.1 (Phase 3: Quality Assurance)
**Task Template**: context/trace/task-templates/issue-1489-fix-all-remaining-ci-validation-issues.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 35-40k (multiple files, iterative validation)
- **Complexity**: HIGH - 107+ YAML errors, 20 type errors, performance optimizations
- **Time Estimate**: 6-9 hours including validation
- **Risk Level**: Medium - no breaking changes, but extensive formatting fixes

## Step-by-Step Implementation Plan

### Phase 1: YAML Fixes (Highest Priority) - 2-3 hours
1. **Fix sprint-4.1.yaml formatting**:
   - [ ] Run yamllint to get specific line numbers for all 107+ errors
   - [ ] Fix indentation errors systematically (goals, phases, tasks sections)
   - [ ] Break long lines to stay under 80 characters
   - [ ] Validate with yamllint after each section fixed
   - [ ] Run full pre-commit to ensure no regressions

2. **Resolve schema file multi-document issues**:
   - [ ] Check each of 6 schema files for multi-document markers
   - [ ] Determine if multi-document format is intentional
   - [ ] Either fix format or configure check-yaml to allow it
   - [ ] Validate each file individually

### Phase 2: Type Annotations (Medium Priority) - 1-2 hours
1. **Fix test_config_validator.py**:
   - [ ] Check lines 100, 124 for type incompatibilities
   - [ ] Add proper type hints for config dictionaries
   - [ ] Test with mypy after fixes

2. **Fix test_ci_signing.py**:
   - [ ] Add null checks for importlib.util.spec_from_file_location
   - [ ] Handle Optional[ModuleSpec] properly
   - [ ] Verify no new mypy errors introduced

3. **Fix test_ci_analytics_metrics.py**:
   - [ ] Resolve import issues
   - [ ] Fix duplicate class definitions
   - [ ] Run specific tests to ensure functionality preserved

### Phase 3: Performance Optimization - 2-3 hours
1. **Docker CI Optimization**:
   - [ ] Profile current Docker CI to identify bottlenecks
   - [ ] Implement Docker layer caching in script
   - [ ] Consider parallelizing independent checks
   - [ ] Add progress indicators for long-running tasks
   - [ ] Test and verify <5 minute execution time

2. **ARC-Reviewer Configuration**:
   - [ ] Add configurable timeout parameter (default 120s)
   - [ ] Implement early termination for large diffs
   - [ ] Add progress indicators for transparency
   - [ ] Test with various PR sizes

### Phase 4: Final Validation - 1 hour
1. **Comprehensive Testing**:
   - [ ] Run full pre-commit suite
   - [ ] Execute ./scripts/run-ci-docker.sh (must be <5min)
   - [ ] Run python -m src.agents.arc_reviewer (must be <2min)
   - [ ] Verify coverage ≥78.0%
   - [ ] Document any configuration changes made

## Execution Notes
- Start with YAML fixes as they're blocking other validations
- Test incrementally - don't make all changes at once
- Keep semantic meaning intact while fixing formatting
- Use git commits after each successful phase
- Monitor context usage - may need /clear between phases

## Progress Tracking
- [ ] Phase 1: YAML Fixes - Started: ___ Completed: ___
- [ ] Phase 2: Type Annotations - Started: ___ Completed: ___
- [ ] Phase 3: Performance - Started: ___ Completed: ___
- [ ] Phase 4: Validation - Started: ___ Completed: ___

## Lessons Learned
(To be filled during execution)

## Final Results
(To be filled after completion)
