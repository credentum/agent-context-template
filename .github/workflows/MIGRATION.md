# GitHub Actions Migration Plan
## Issue #1063: Align GitHub Actions with Claude Local CI

### Migration Strategy: Gradual Transition

This document outlines the migration from legacy GitHub Actions workflows to the new unified workflows that use claude-ci scripts.

## Phase 1: Parallel Execution (Current)
**Status**: In Progress  
**Duration**: 1-2 weeks

### New Unified Workflows (Active):
- `ci-unified.yml` - New unified CI pipeline  
- `pr-review-unified.yml` - PR review using claude-ci delegation
- `ci-optimized-unified.yml` - Simplified replacement for ci-optimized.yml

### Legacy Workflows (Still Active):
- `ci-optimized.yml` - Complex embedded logic (802 lines)
- `test.yml` - Basic test runner (82 lines)  
- `test-suite.yml` - Comprehensive test suite (200+ lines)
- `lint-verification.yml` - Lint checks (102 lines)

### Verification Plan:
1. **Results Comparison**: Compare outputs between legacy and unified workflows
2. **Performance Monitoring**: Track execution time improvements
3. **Reliability Testing**: Ensure identical CI results for identical code

## Phase 2: Validation (After 1 week)
**Status**: Planned  
**Duration**: 3-5 days

### Actions:
1. **Analyze Results**: Compare legacy vs unified workflow outcomes
2. **Performance Review**: Validate expected improvements (60-70% time reduction)
3. **Issue Resolution**: Fix any discrepancies discovered
4. **Team Approval**: Get team sign-off on unified approach

## Phase 3: Legacy Deprecation (After Validation)
**Status**: Planned  
**Duration**: 1 week

### Actions:
1. **Disable Legacy Workflows**: Add `.legacy` suffix to old workflow files
2. **Update Default Branch Protection**: Switch to require unified workflow checks
3. **Documentation Update**: Update CLAUDE.md and README with new approach
4. **Team Communication**: Notify team of cutover completion

## Phase 4: Cleanup (Final)
**Status**: Planned  
**Duration**: 2-3 days

### Actions:
1. **Archive Legacy Files**: Move old workflows to `.archive/` directory
2. **Simplify Checks**: Remove redundant status checks from branch protection
3. **Update Documentation**: Final documentation cleanup
4. **Success Metrics**: Document achieved improvements

## Benefits Tracking

### Expected Improvements:
- **90% YAML complexity reduction**: 802 lines → ~150 lines
- **60-70% execution time improvement**: Parallel execution + caching
- **100% consistency**: Identical local/GitHub behavior
- **Single source of truth**: All CI logic in claude-ci.sh

### Success Metrics:
- [ ] All new workflows passing consistently
- [ ] Performance improvements achieved  
- [ ] Zero discrepancies in CI results
- [ ] Team satisfaction with new approach
- [ ] Reduced CI maintenance burden

## Rollback Plan

If issues are discovered:

1. **Immediate**: Re-enable legacy workflows by removing `.disabled` suffix
2. **Branch Protection**: Revert to legacy workflow requirements  
3. **Investigation**: Analyze and fix unified workflow issues
4. **Re-attempt**: Resume migration after fixes

## Current Status

### Completed:
✅ Created unified workflows  
✅ Enhanced claude-ci.sh with --github-output  
✅ Added structured review output capture  
✅ Fixed lint and import sorting issues  

### In Progress:
🟡 Running parallel execution for validation  
🟡 Monitoring performance and reliability  

### Pending:
⏳ Results comparison and team review  
⏳ Legacy workflow deprecation  
⏳ Final cleanup and documentation