# CI Migration Troubleshooting Guide

## Quick Diagnostics

Run this first for any issue:
```bash
./scripts/diagnose-ci-migration.sh
```

## Common Issues and Solutions

### 1. Installation Issues

#### Git hooks not installing
```bash
# Check git version (need 2.9+)
git --version

# Manually create hooks directory
mkdir -p .git/hooks
mkdir -p .git-hooks

# Re-run installer with debug
DEBUG=1 ./scripts/install-git-hooks.sh
```

#### Permission denied errors
```bash
# Fix script permissions
chmod +x scripts/*.sh
chmod +x .git-hooks/*

# Check file ownership
ls -la .git/hooks/
```

### 2. Pre-Push Hook Issues

#### Hook hanging/timeout
```bash
# Symptom: Git push hangs for >5 minutes
# Solution 1: Use quick bypass
SKIP_CI=1 git push

# Solution 2: Check what's hanging
ps aux | grep claude-ci
killall claude-ci.sh  # If needed

# Solution 3: Reduce timeout in config
echo "QUICK_TIMEOUT=15" >> .git-hooks/config
```

#### Hook not running at all
```bash
# Check if hook exists
ls -la .git/hooks/pre-push

# Check if it's a symlink
readlink .git/hooks/pre-push

# Test hook manually
.git/hooks/pre-push
```

#### CI checks failing locally but not on GitHub
```bash
# Run with Docker for exact match
./scripts/run-ci-docker.sh

# Compare Python versions
python --version
docker run python:3.11 python --version

# Check for missing dependencies
pip list | diff - requirements.txt
```

### 3. Workflow Migration Issues

#### Workflow already migrated error
```bash
# Check workflow status
grep verify-ci-results .github/workflows/*.yml

# Force re-migration
rm .github/workflows/.*.monitoring.json
./scripts/migrate-workflow.py --workflows test
```

#### Workflow not triggering
```yaml
# Check workflow conditions
# Should have:
env:
  CI_MIGRATION_MODE: ${{ vars.CI_MIGRATION_MODE || 'parallel' }}

jobs:
  your-job:
    if: env.CI_MIGRATION_MODE != 'verifier-only'
```

#### Verifier job failing
```bash
# Check for CI results file
ls -la ci-results.json.gpg

# Verify GPG signature manually
gpg --verify ci-results.json.gpg

# Check verifier script
python scripts/verify-ci-results.py --debug
```

### 4. Performance Issues

#### Local CI slower than expected
```bash
# Use quick mode
./scripts/quick-pre-push.sh

# Profile the slow parts
time ./scripts/claude-ci.sh all --quick

# Skip expensive checks
SKIP_COVERAGE=1 ./scripts/claude-ci.sh all
```

#### Memory issues
```bash
# Check available memory
free -h

# Limit pytest workers
export PYTEST_XDIST_WORKER_COUNT=2

# Use swap if needed
sudo swapon --show
```

### 5. Migration Mode Issues

#### Mode not changing
```bash
# Check current mode
echo $CI_MIGRATION_MODE
gh variable get CI_MIGRATION_MODE

# Force mode for single push
CI_MIGRATION_MODE=traditional git push

# Set globally
gh variable set CI_MIGRATION_MODE --body "parallel"
```

#### Parallel mode not comparing results
```bash
# Check monitoring files exist
ls -la .github/workflows/.*.monitoring.json

# Manually trigger comparison
./scripts/compare-ci-results.sh

# Check monitoring dashboard
./scripts/monitor-ci-migration.sh
```

### 6. Team Coordination Issues

#### Some developers not migrated
```bash
# Generate migration status report
./scripts/team-migration-status.sh

# Send reminder
./scripts/notify-team.sh "Reminder: Please run ./scripts/install-git-hooks.sh"
```

#### Inconsistent results across team
```bash
# Compare environments
./scripts/collect-team-env.sh > team-env.txt

# Check for differences
diff my-env.txt teammate-env.txt

# Standardize with Docker
echo "Please use ./scripts/run-ci-docker.sh for consistency"
```

### 7. Emergency Procedures

#### Need to push immediately
```bash
# Method 1: Skip all checks
git push --no-verify

# Method 2: Skip CI only
SKIP_CI=1 git push

# Method 3: Emergency mode
EMERGENCY_PUSH=1 git push
```

#### CI completely broken
```bash
# Rollback to traditional mode
CI_MIGRATION_MODE=traditional git push

# Notify team
./scripts/emergency-notification.sh "CI issues - use traditional mode"

# Create hotfix branch
git checkout -b hotfix/ci-emergency
```

#### Repository in bad state
```bash
# Full reset procedure
git stash
git checkout main
git pull origin main
rm -rf .git/hooks/pre-*
./scripts/install-git-hooks.sh
```

## Advanced Debugging

### Enable verbose logging
```bash
# For git operations
GIT_TRACE=1 git push

# For hook execution
DEBUG_HOOKS=1 git push

# For CI scripts
DEBUG_CI=1 VERBOSE=1 ./scripts/claude-ci.sh all
```

### Trace execution
```bash
# Trace shell execution
set -x
./scripts/claude-ci.sh all
set +x

# Profile performance
/usr/bin/time -v ./scripts/claude-ci.sh all
```

### Compare local vs GitHub
```bash
# Capture local results
./scripts/claude-ci.sh all --output local-results.json

# Capture GitHub results
gh run download --name ci-results

# Compare
diff local-results.json github-results.json
```

## Getting Help

### Self-Service
1. Run diagnostics: `./scripts/diagnose-ci-migration.sh`
2. Check FAQ: `docs/ci-migration-complete-guide.md#faq`
3. Search issues: `gh issue list --label ci-migration`

### Escalation Path
1. Team Slack channel: #ci-migration
2. Create issue: `gh issue create --label ci-migration,bug`
3. Emergency hotline: [DevOps on-call]

### Useful Commands Cheatsheet

```bash
# Bypass hooks
SKIP_CI=1 git push
git push --no-verify

# Change mode
export CI_MIGRATION_MODE=traditional
gh variable set CI_MIGRATION_MODE --body "parallel"

# Debug
DEBUG_HOOKS=1 git push
./scripts/monitor-ci-migration.sh

# Reset
rm .git/hooks/pre-push
./scripts/install-git-hooks.sh

# Status
./scripts/diagnose-ci-migration.sh
./scripts/team-migration-status.sh
```

## Prevention Tips

1. **Always pull latest main** before major operations
2. **Run diagnostics** weekly during migration
3. **Keep Docker updated** if using full CI
4. **Communicate** mode changes to team
5. **Document** any custom configurations
6. **Test** in parallel mode before switching to verifier-only
7. **Monitor** the dashboard during team migration
8. **Have rollback plan** ready

Remember: When in doubt, use `CI_MIGRATION_MODE=traditional` to fall back to the original behavior.
