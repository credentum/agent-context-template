# Issue #39: Test Coverage Uplift to 80% Line / 60% Branch

**Issue Link**: https://github.com/credentum/agent-context-template/issues/39
**Sprint**: sprint-5, Phase 5
**Branch**: fix/39-test-coverage-uplift

## Problem Analysis

Issue #39 requires increasing coverage targets and enforcing thresholds in CI:
- Target: ≥ 80% line coverage, 60% branch coverage
- Mutation baseline: ≥ 20%
- Use coverage-py XML & pytest-cov-threshold

## Current State Analysis

### Current Coverage Configuration:
- **Current baseline**: 78.5% (from .coverage-config.json)
- **Current target**: 85.0% for all modules, 90.0% for validators
- **Coverage is already configured** with:
  - pytest.ini: Coverage config in lines 31-49
  - pyproject.toml: Coverage tool config in lines 28-78
  - .github/workflows/test-coverage.yml: CI coverage workflow

### Existing Infrastructure:
1. **Coverage Config**: `.coverage-config.json` centralized configuration
2. **Coverage Workflows**:
   - `test-coverage.yml` runs coverage with thresholds
   - `claude-code-review.yml` includes coverage checks
3. **Scripts**:
   - `scripts/generate_coverage_matrix.py` - coverage analysis
   - `scripts/update-coverage-baseline.py` - sync config to docs
4. **Coverage Tools**:
   - pytest-cov for line/branch coverage
   - mutmut for mutation testing (configured in pyproject.toml)

## Implementation Plan

### Phase 1: Update Coverage Thresholds
1. **Update .coverage-config.json**:
   - Set baseline to 80% (line coverage target)
   - Add branch_target: 60% for branch coverage
   - Add mutation_baseline: 20% for mutation testing

2. **Update CI Workflows**:
   - Modify test-coverage.yml to use new thresholds
   - Add branch coverage enforcement
   - Add mutation testing baseline check

### Phase 2: Implement Coverage Enforcement
1. **Add pytest-cov-threshold plugin**:
   - Add to requirements-test.txt
   - Configure thresholds in pytest.ini or pyproject.toml

2. **Update test scripts**:
   - Modify scripts/coverage_summary.py to check new thresholds
   - Update CI to fail if thresholds not met

### Phase 3: Documentation and Validation
1. **Update documentation**:
   - Run scripts/update-coverage-baseline.py to sync CLAUDE.md
   - Update coverage section with new targets

2. **Test the implementation**:
   - Run ./scripts/run-ci-docker.sh to verify CI compatibility
   - Ensure coverage reports include branch coverage
   - Validate mutation testing baseline

## Technical Implementation Details

### Files to Modify:
1. `.coverage-config.json` - Add branch_target and mutation_baseline
2. `.github/workflows/test-coverage.yml` - Update threshold checks
3. `requirements-test.txt` - Add pytest-cov-threshold if needed
4. `scripts/coverage_summary.py` - Update to handle branch/mutation thresholds
5. `CLAUDE.md` - Update via script

### Coverage Enforcement Strategy:
- Line coverage: 80% (enforced by CI)
- Branch coverage: 60% (enforced by CI)
- Mutation baseline: 20% (informational/warning initially)

### Validation Steps:
1. Verify current coverage meets 80% line requirement
2. Check if branch coverage meets 60% requirement
3. Run mutation testing to establish baseline
4. Update CI to enforce new thresholds

## Dependencies and Risks

### Dependencies:
- Current coverage must be near 80% line coverage (currently 78.5%)
- Branch coverage support in pytest-cov (already configured)
- Mutation testing infrastructure (mutmut already configured)

### Risks:
- If current coverage < 80%, need to improve tests first
- Branch coverage might be significantly lower than line coverage
- Mutation testing baseline might be < 20%

### Mitigation:
- Start with current coverage assessment
- Implement thresholds gradually if needed
- Use fail-soft approach for mutation testing initially

## Success Criteria

- [ ] CI enforces ≥ 80% line coverage
- [ ] CI enforces ≥ 60% branch coverage
- [ ] Mutation testing baseline ≥ 20% established
- [ ] pytest-cov-threshold integrated
- [ ] Coverage configuration centralized and documented
- [ ] All existing tests pass with new thresholds

## Next Steps

1. Assess current coverage levels (run quick coverage check)
2. Update .coverage-config.json with new targets
3. Implement CI threshold enforcement
4. Test and validate changes
5. Update documentation
