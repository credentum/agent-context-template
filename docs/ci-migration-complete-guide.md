# CI Migration Phase 3: Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Background](#background)
3. [Migration Strategy](#migration-strategy)
4. [Installation](#installation)
5. [Git Hooks Setup](#git-hooks-setup)
6. [Workflow Migration](#workflow-migration)
7. [Migration Modes](#migration-modes)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)
11. [Team Migration](#team-migration)
12. [FAQ](#faq)

## Overview

This guide covers the complete migration from GitHub-only CI to a hybrid local/GitHub CI system. The migration enables developers to run CI checks locally before pushing, reducing CI failures and improving development velocity.

### Goals
- **Zero downtime**: Gradual migration with fallback options
- **Developer friendly**: Multiple bypass mechanisms for emergencies
- **Performance**: 10x faster feedback loop (30s local vs 5min GitHub)
- **Reliability**: Parallel execution for validation during migration

### Components
1. **Git Hooks**: Pre-push validation running local CI
2. **Workflow Converter**: Automated migration to verifier pattern
3. **Monitoring Dashboard**: Real-time migration tracking
4. **Quick Validation**: Fast local checks before push

## Background

### Phase 1 (PR #1290)
- Created `post-ci-results.py` for posting CI results to GitHub
- Enhanced `claude-ci.sh` with `--output` and `--post-results` flags
- Created `ci-local-verifier.yml` workflow
- Basic proof of concept working

### Phase 2 (Issue #1291)
- Added GPG signing for CI results
- Implemented retry logic with exponential backoff
- Enhanced security and reliability
- Successfully completed and merged

### Phase 3 (This Migration)
- Full production rollout
- Git hooks for automatic local CI
- Workflow conversion tools
- Monitoring and rollback capabilities

## Migration Strategy

### Three-Mode Approach

1. **Traditional Mode**: GitHub CI only (current state)
2. **Parallel Mode**: Both local and GitHub CI run (validation phase)
3. **Verifier-Only Mode**: Local CI with GitHub verification (target state)

### Phased Rollout

```
Week 1: Foundation
├── Days 1-2: Git hook infrastructure
├── Days 3-4: Workflow converter
├── Days 5-6: Migration infrastructure
└── Days 7-8: Documentation

Week 2: Deployment
├── Days 9-10: Test repository validation
├── Days 11-12: Team-by-team migration
└── Days 13-14: Production cutover
```

## Installation

### Prerequisites
- Git 2.9+ (for hooks)
- Python 3.8+ (for scripts)
- GitHub CLI (`gh`) authenticated
- Docker (optional, for full CI)

### Quick Start

```bash
# 1. Install git hooks
./scripts/install-git-hooks.sh

# 2. Test the setup
./scripts/quick-pre-push.sh

# 3. Try pushing (will run local CI)
git push
```

## Git Hooks Setup

### Installation

The installer script sets up enhanced git hooks while preserving existing functionality:

```bash
./scripts/install-git-hooks.sh
```

This creates:
- `.git-hooks/pre-push`: Enhanced pre-push hook
- `.git-hooks/pre-commit`: Quick format checks
- `.git-hooks/config`: Configuration file

### Features

#### Pre-Push Hook
- Runs before every push to remote
- Preserves existing Git LFS functionality
- Progressive validation based on branch:
  - Temporary branches (wip/*, tmp/*): Skip CI
  - Feature branches: Quick validation (30s)
  - Protected branches (main, release/*): Comprehensive validation

#### Bypass Options
```bash
# Skip CI checks only
SKIP_CI=1 git push

# Skip all hooks
SKIP_HOOKS=1 git push

# Git native bypass
git push --no-verify
```

#### Configuration
Edit `.git-hooks/config` to customize:
- Timeout settings
- Branch patterns
- Protected branch definitions

### Uninstalling

To remove hooks:
```bash
# Remove symbolic links
rm .git/hooks/pre-push
rm .git/hooks/pre-commit

# Restore backups if needed
cp .git/hooks/pre-push.backup.* .git/hooks/pre-push
```

## Workflow Migration

### Automated Migration

Convert workflows to verifier pattern:

```bash
# Dry run to see changes
python -m src.tools.migrate_workflow --dry-run

# Migrate specific workflows
python -m src.tools.migrate_workflow --workflows test lint-verification

# Migrate all priority workflows
python -m src.tools.migrate_workflow

# Create verifier action
python -m src.tools.migrate_workflow --create-action
```

### Manual Migration

If you need to migrate a workflow manually:

1. Add environment variable:
   ```yaml
   env:
     CI_MIGRATION_MODE: ${{ vars.CI_MIGRATION_MODE || 'parallel' }}
   ```

2. Make CI jobs conditional:
   ```yaml
   jobs:
     test:
       if: env.CI_MIGRATION_MODE != 'verifier-only'
       # ... existing job config
   ```

3. Add verifier job:
   ```yaml
   verify-ci-results:
     name: Verify Local CI Results
     runs-on: ubuntu-latest
     if: github.event_name == 'pull_request'
     needs: [test, lint]  # List all CI jobs
     steps:
       - uses: actions/checkout@v4
       - uses: ./.github/actions/verify-ci-results
         with:
           mode: ${{ env.CI_MIGRATION_MODE || 'parallel' }}
   ```

### Priority Workflows

Migrate in this order for maximum impact:
1. `test.yml` - Core unit tests
2. `lint-verification.yml` - Code quality
3. `test-coverage.yml` - Coverage tracking
4. `ci-unified.yml` - Main CI pipeline
5. `claude-code-review.yml` - AI review
6. `context-lint.yml` - Context validation

## Migration Modes

### Setting Migration Mode

#### Repository-Wide (Recommended)
```bash
# Using GitHub CLI
gh variable set CI_MIGRATION_MODE --body "parallel"
```

#### Per-Developer
```bash
# In shell profile
export CI_MIGRATION_MODE="parallel"
```

#### Per-Push
```bash
CI_MIGRATION_MODE=traditional git push
```

### Mode Behaviors

| Mode | Local CI | GitHub CI | Use Case |
|------|----------|-----------|----------|
| traditional | ❌ | ✅ | Current state, fallback |
| parallel | ✅ | ✅ | Validation phase |
| verifier-only | ✅ | 🔍 | Target state |

🔍 = Verification only, not full CI run

## Monitoring

### Real-Time Dashboard

Monitor migration progress:

```bash
./scripts/monitor-ci-migration.sh
```

Features:
- Live workflow status
- Performance comparison
- Issue tracking
- Migration statistics

### Dashboard Commands
- `m` - Change migration mode
- `r` - Rollback to traditional
- `s` - Save report
- `q` - Quit

### Metrics Tracked
- Success rate per workflow
- Performance improvement
- Migration percentage
- Recent issues

## Troubleshooting

### Common Issues

#### 1. Pre-push hook timeout
**Symptom**: Push hangs for >5 minutes

**Solution**:
```bash
# Use quick validation instead
SKIP_CI=1 git push
# Then run CI manually
./scripts/claude-ci.sh all
```

#### 2. CI results not found
**Symptom**: GitHub workflow fails with "No CI results found"

**Solution**:
```bash
# Ensure local CI ran
./scripts/claude-ci.sh all --post-results
# Then push again
```

#### 3. Permission denied on hooks
**Symptom**: "Permission denied" when pushing

**Solution**:
```bash
chmod +x .git-hooks/pre-push
chmod +x scripts/claude-ci.sh
```

#### 4. Different results between local and GitHub
**Symptom**: Local passes but GitHub fails

**Solution**:
```bash
# Run with Docker for exact match
./scripts/run-ci-docker.sh
# Compare environments
./scripts/debug-ci-diff.sh
```

### Debug Mode

Enable detailed logging:
```bash
# For git hooks
DEBUG_HOOKS=1 git push

# For CI scripts
DEBUG_CI=1 ./scripts/claude-ci.sh all
```

## Rollback Procedures

### Quick Rollback (Individual)
```bash
# Bypass hooks temporarily
SKIP_HOOKS=1 git push

# Or use traditional mode
CI_MIGRATION_MODE=traditional git push
```

### Team Rollback
```bash
# Set repository variable
gh variable set CI_MIGRATION_MODE --body "traditional"

# Notify team
./scripts/notify-rollback.sh "Reason for rollback"
```

### Full Rollback
```bash
# 1. Restore workflow backups
find .github/workflows/backup -name "*.backup.*" -exec cp {} .github/workflows/ \;

# 2. Remove monitoring files
rm .github/workflows/.*.monitoring.json

# 3. Uninstall hooks
rm .git/hooks/pre-push .git/hooks/pre-commit

# 4. Commit changes
git add .github/workflows
git commit -m "revert: rollback CI migration to traditional mode"
git push
```

## Team Migration

### Preparation
1. Schedule migration window
2. Ensure all team members have:
   - Updated repository
   - GitHub CLI installed
   - Docker (optional)

### Migration Steps

#### Step 1: Team Notification
```bash
./scripts/notify-team.sh "CI Migration starting at 2pm PST"
```

#### Step 2: Install Hooks (Each Developer)
```bash
# Each team member runs:
git pull origin main
./scripts/install-git-hooks.sh
```

#### Step 3: Test in Parallel Mode
```bash
# Repository owner sets:
gh variable set CI_MIGRATION_MODE --body "parallel"

# Team validates:
./scripts/test-team-migration.sh
```

#### Step 4: Monitor Together
```bash
# One person shares screen with:
./scripts/monitor-ci-migration.sh
```

#### Step 5: Gradual Cutover
```bash
# After validation period:
gh variable set CI_MIGRATION_MODE --body "verifier-only"
```

### Training Materials

Share these resources:
- This guide
- Quick reference card (docs/ci-migration-quick-ref.pdf)
- Troubleshooting guide (docs/ci-migration-troubleshooting.md)
- Video walkthrough (if available)

## FAQ

### Q: Will this slow down my development?
**A**: No, it speeds it up! Local CI runs in 30 seconds vs 5+ minutes on GitHub.

### Q: What if I need to push urgently?
**A**: Use `SKIP_CI=1 git push` or `git push --no-verify` for emergencies.

### Q: Can I still use GitHub CI only?
**A**: Yes, set `CI_MIGRATION_MODE=traditional` to use GitHub CI only.

### Q: What happens if local and GitHub CI disagree?
**A**: In parallel mode, both must pass. Check the monitoring dashboard to debug differences.

### Q: Do I need Docker?
**A**: No, quick validation works without Docker. Docker is only needed for exact CI matching.

### Q: How do I know if migration is working?
**A**: Run `./scripts/monitor-ci-migration.sh` to see real-time status.

### Q: Can I customize which checks run locally?
**A**: Yes, edit `.git-hooks/config` to customize validation levels.

### Q: What about CI for automated PRs?
**A**: Automated PRs (like Dependabot) continue using GitHub CI only.

### Q: How do I report issues?
**A**: Use `./scripts/report-ci-issue.sh` or create a GitHub issue with the `ci-migration` label.

### Q: When will migration be complete?
**A**: Target is 2 weeks from start, but we'll maintain parallel mode until stability is confirmed.

## Summary

The CI migration provides:
- ✅ Faster feedback (30s vs 5min)
- ✅ Fewer broken builds
- ✅ Cost savings on CI minutes
- ✅ Better developer experience
- ✅ Gradual, safe migration path

For support, contact the DevOps team or post in #ci-migration Slack channel.
