# Execution Plan: Issue #1133 - Generate review report in same format

**Issue Link**: https://github.com/droter/agent-context-template/issues/1133
**Sprint Reference**: Part of investigation #1060
**Task Template**: context/trace/task-templates/issue-1133-generate-review-report-in-same-format.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 8,000 (small script modifications)
- **Estimated time**: 30 minutes
- **Complexity**: Low (using existing ARC-Reviewer module)
- **Files affected**: 2-3 script files

## Step-by-Step Implementation Plan

### 1. Analysis Phase (5 minutes)
- [x] Understand current simulate-pr-review.sh structure
- [x] Verify ARC-Reviewer module format_yaml_output() method
- [x] Identify specific changes needed for YAML format consistency

### 2. Implementation Phase (20 minutes)
- [ ] Create feature branch: `feature/1133-review-report-format`
- [ ] Modify scripts/simulate-pr-review.sh to use ARC-Reviewer directly
- [ ] Update run_arc_reviewer_analysis() function to call format_yaml_output()
- [ ] Remove simulated YAML generation in favor of real ARC-Reviewer output
- [ ] Update helper functions if needed

### 3. Testing Phase (5 minutes)
- [ ] Test YAML output format matches GitHub ARC-Reviewer
- [ ] Verify all command-line options still work
- [ ] Run pre-commit hooks
- [ ] Run Docker CI checks

## Key Changes Required

1. **scripts/simulate-pr-review.sh**:
   - Modify `run_arc_reviewer_analysis()` to always use real ARC-Reviewer module
   - Remove `generate_simulated_review_with_coverage()` fallback for YAML format
   - Ensure YAML output is passed through format_yaml_output() method

2. **scripts/lib/pr-simulation-helpers.sh** (if needed):
   - Update any helper functions that generate review output
   - Ensure consistency with ARC-Reviewer format

## Expected Outcome
- Local simulate-pr-review.sh generates identical YAML format to GitHub Actions
- Claude Code can parse the output successfully
- All existing functionality preserved
- Reduced code duplication by using existing ARC-Reviewer module

## Risk Assessment
- **Low risk**: Changes are minimal and use existing validated code
- **Fallback**: Existing ARC-Reviewer module is well-tested
- **Testing**: Can validate against known GitHub output format
