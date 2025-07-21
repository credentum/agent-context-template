# Execution Plan: Issue #1084 - Fix Coverage Configuration Conflict

## Issue Link
- GitHub Issue: https://github.com/credentum/agent-context-template/issues/1084
- Priority: HIGH - Blocks ALL PRs with test changes

## Task Template Reference
- Template: `context/trace/task-templates/issue-1084-coverage-configuration.md`
- Complexity: Low (configuration change only)
- Estimated time: 15 minutes

## Token Budget & Complexity Assessment
- Token budget: 2,000 tokens (minimal changes)
- Complexity: Low - Only changing boolean values in 2 files
- Risk: Low - Well-understood configuration change

## Step-by-Step Implementation Plan

### 1. Create feature branch
```bash
git checkout -b fix/1084-coverage-configuration
```

### 2. Update pyproject.toml
- Change line 30: `branch = true` → `branch = false`

### 3. Update pytest.ini
- Change line 35: `branch = True` → `branch = False`

### 4. Verify no other branch coverage settings
- Check .coverage-config.json
- Search for any other coverage configuration files

### 5. Clear existing coverage data
```bash
find . -name ".coverage*" -delete
find . -name "htmlcov" -type d -exec rm -rf {} +
```

### 6. Test locally
```bash
# Run pytest without branch coverage
pytest --cov=src --cov-report=term-missing

# Run Docker CI
./scripts/run-ci-docker.sh
```

### 7. Commit changes
```bash
git add pyproject.toml pytest.ini
git commit -m "fix(ci): disable branch coverage in config files

Fixes coverage.exceptions.DataError that was blocking all CI runs.
Branch coverage was disabled in workflows (commit 01caf4d) but still
enabled in config files, causing incompatible coverage data.

Fixes #1084"
```

### 8. Create PR
- Title: fix(ci): disable branch coverage configuration to fix CI failures
- Body: Reference issue #1084, explain the fix, show test results

## Success Criteria
- [ ] Both config files updated
- [ ] No coverage combination errors
- [ ] Docker CI passes
- [ ] PR created and CI passes

## Notes
- This is a critical fix blocking all PRs
- Simple configuration change with high impact
- Should be merged quickly once tests pass
