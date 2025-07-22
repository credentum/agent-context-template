# Issue #1132 - Implement Coverage Checking Matching GitHub

**Issue Link**: https://github.com/anthropics/agent-context-template/issues/1132
**Sprint**: investigation-1060 decomposition
**Task Template**: context/trace/task-templates/issue-1132-implement-coverage-checking.md

## Token Budget & Complexity
- **Estimated tokens**: 12,000
- **Complexity**: Medium (bash scripting, CI process matching)
- **Files affected**: 3 (simulate-pr-review.sh, helpers, docs)

## Implementation Plan

### Phase 1: Analysis
1. ✅ Understand GitHub Actions coverage workflow (.github/workflows/test-coverage.yml)
2. ✅ Analyze existing coverage scripts (coverage_summary.py, get_coverage_threshold.py)
3. ✅ Review current PR simulation implementation (simulate-pr-review.sh)

### Phase 2: Implementation
1. **Modify simulate-pr-review.sh**:
   - Add coverage calculation function that matches GitHub CI exactly
   - Use same pytest commands as GitHub Actions
   - Integrate threshold checking using .coverage-config.json
   - Add coverage results to simulation output

2. **Create/enhance helper functions**:
   - Extract coverage logic to reusable functions
   - Ensure error handling matches GitHub CI behavior
   - Add verbose output for debugging

3. **Update documentation**:
   - Document GitHub CI matching approach
   - Add usage examples for coverage checking

### Phase 3: Testing
1. Run local simulation and compare with GitHub Actions results
2. Verify coverage percentages match exactly
3. Test threshold validation works correctly
4. Ensure all acceptance criteria are met

## Key Technical Requirements
- Use exact same pytest commands as GitHub Actions:
  ```bash
  python -m pytest --cov=src --cov-report=term-missing:skip-covered --cov-report=xml --cov-report=json -v
  ```
- Use centralized threshold from .coverage-config.json:
  ```bash
  THRESHOLD=$(python scripts/get_coverage_threshold.py)
  python -m coverage report --fail-under=$THRESHOLD
  ```
- Match output format and error handling of GitHub CI

## Success Criteria
- [ ] Coverage calculation matches GitHub CI exactly
- [ ] Baseline threshold checking implemented
- [ ] Target threshold validation included
- [ ] Module-specific coverage requirements handled
- [ ] Output format matches GitHub Actions
- [ ] Local and GitHub results are identical

## Next Steps
1. Start implementation with coverage function in simulate-pr-review.sh
2. Test against known coverage values
3. Refine until results match GitHub Actions exactly
