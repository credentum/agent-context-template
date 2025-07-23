# GitHub Actions Migration Plan
## Issue #1063: Align GitHub Actions with Claude Local CI
## Issue #1243: Consolidate and Review GitHub Actions Workflows

### Migration Strategy: Gradual Transition

This document outlines the migration from legacy GitHub Actions workflows to the new unified workflows that use claude-ci scripts, and the comprehensive consolidation effort to eliminate redundancy.

## Phase 1: Parallel Execution (Current)
**Status**: In Progress
**Duration**: 1-2 weeks

### Active Unified Workflows:
- `ci-unified.yml` - New unified CI pipeline (replaces 5 legacy CI/testing workflows)
- `pr-review-unified.yml` - PR review using claude-ci delegation
- `ai-pr-monitor.yml` - AI-managed PR lifecycle (replaces 5 auto-merge workflows)

### Removed Workflows:
- `ci-optimized-unified.yml` - ✅ **REMOVED** (transitional, no longer needed)
- `ai-pr-monitor-minimal.yml` - ✅ **REMOVED** (test version)
- `auto-merge*.yml.disabled` - ✅ **REMOVED** (5 obsolete files)

### Legacy Workflows (Now Disabled):
- `ci-optimized.yml.disabled` - Complex embedded logic (802 lines) - ✅ **DISABLED**
- `test.yml.disabled` - Basic test runner (82 lines) - ✅ **DISABLED**
- `test-suite.yml.disabled` - Comprehensive test suite (200+ lines) - ✅ **DISABLED**
- `test-coverage.yml.disabled` - Coverage analysis (171 lines) - ✅ **DISABLED**
- `lint-verification.yml.disabled` - Lint checks (102 lines) - ✅ **DISABLED**
- `pr-validation.yml.disabled` - PR format validation (131 lines) - ✅ **DISABLED**
- `pr-conflict-validator.yml.disabled` - Conflict detection (169 lines) - ✅ **DISABLED**

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

## Issue #1243 Consolidation Results

### ✅ Completed (2025-07-22):
- **Workflow count reduced**: 29 → 16 workflows (45% reduction)
- **Disabled legacy workflows**: 7 redundant CI/testing/PR workflows
- **Removed obsolete files**: 8 .disabled files + 2 transitional workflows
- **Lines of YAML reduced**: ~1,950 lines removed (35% reduction)

### Active Workflows After Consolidation:
1. **CI/Testing**: `ci-unified.yml`, `pr-review-unified.yml`
2. **PR Management**: `ai-pr-monitor.yml`, `pr-issue-validation.yml`, `pr-required.yml`, `auto-close-issues.yml`
3. **Sprint/Project**: `sprint-start.yml`, `sprint-update.yml`, `generate-sprint-issues.yml`
4. **Data Sync**: `vector-graph-sync.yml`, `kv-analytics-sync.yml`
5. **Utilities**: `context-lint.yml`, `claude.yml`, `claude-code-review.yml`

## Migration Status Update

### Completed:
✅ Created unified workflows
✅ Enhanced claude-ci.sh with --github-output
✅ Added structured review output capture
✅ Fixed lint and import sorting issues
✅ **Consolidated redundant workflows (Issue #1243)**
✅ **Removed obsolete .disabled files**
✅ **Updated MIGRATION.md documentation**

### In Progress:
🟡 Monitoring unified workflow performance
🟡 Validating branch protection compatibility

### Pending:
⏳ Final archive of .disabled files to .archive/ directory
⏳ Branch protection rule optimization
⏳ Performance metrics documentation
