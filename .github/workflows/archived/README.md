# Archived GitHub Workflows

**Archived Date**: 2025-07-31  
**Reason**: Migration to Local CI with Automatic Issue Fixing  
**Related Issues**: #173, #1291, #1694

## Overview

These workflows were archived as part of the migration from GitHub-only CI to a hybrid local/GitHub CI system that enables automatic issue fixing and provides 10x faster feedback loops.

## Archived Workflows

### CI/Testing Workflows (Replaced by Local CI)
- **ci-unified.yml** - Replaced by local CI execution via `claude-ci.sh`
- **test-coverage.yml** - Coverage now handled by local CI with posting to GitHub
- **lint-verification.yml** - Linting moved to local pre-push hooks
- **context-lint.yml** - Context validation integrated into local CI

These workflows are now replaced by:
- Local execution: `./scripts/claude-ci.sh`
- Git hooks: Automatic pre-push validation
- GitHub verification: `ci-local-verifier.yml`

### PR Management Workflows (Replaced by ai-pr-monitor.yml)
- **auto-close-issues.yml** - Issue closing integrated into ai-pr-monitor.yml
- **pr-issue-validation.yml** - PR/issue linking handled by ai-pr-monitor.yml
- **pr-required.yml** - Policy enforcement moved to ai-pr-monitor.yml
- **pr-review-unified.yml** - Redundant with claude-code-review.yml

These workflows achieved a 71% code reduction (2,063 lines → 589 lines) through consolidation into `ai-pr-monitor.yml`.

### Disabled Workflows (Removed)
- **ci-optimized.yml.disabled**
- **pr-conflict-validator.yml.disabled**
- **pr-validation.yml.disabled**
- **test-suite.yml.disabled**

## Benefits of Migration

1. **Speed**: 30 second local CI vs 5+ minute GitHub Actions
2. **Cost**: Reduced GitHub Actions minutes usage
3. **Developer Experience**: Immediate feedback before push
4. **Automatic Fixes**: Local CI can fix issues automatically
5. **Simplicity**: Fewer workflows to maintain

## Rollback Instructions

If you need to restore any of these workflows:

1. Copy the workflow from this archive back to `.github/workflows/`
2. Update any references to deprecated workflows
3. Consider if the functionality is already covered by:
   - `ai-pr-monitor.yml` for PR management
   - Local CI for testing/linting
   - `ci-local-verifier.yml` for GitHub verification

## Active Workflows

The following workflows remain active:
- `claude.yml` - Claude integration
- `claude-code-review.yml` - PR reviews
- `test.yml` - Basic GitHub testing fallback
- `ci-local-verifier.yml` - Local CI verification
- `ai-pr-monitor.yml` - Unified PR monitoring
- Sprint management workflows (3)
- Data sync workflows (2)

## Further Reading

- CI Migration Guide: `/docs/ci-migration-guide.md`
- CI Migration Complete Guide: `/docs/ci-migration-complete-guide.md`
- Workflow Deprecation Plan: `/docs/workflow-deprecation-plan.md`