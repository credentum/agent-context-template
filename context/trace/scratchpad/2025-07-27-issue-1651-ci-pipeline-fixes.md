# Issue #1651 CI Pipeline Fixes - Execution Plan
**Date**: 2025-07-27
**Issue**: [#1651 - Fix remaining CI pipeline issues](https://github.com/repo/issues/1651)
**Sprint**: sprint-4.3
**Task Template**: context/trace/task-templates/issue-1651-fix-remaining-ci-pipeline-issues.md

## Token Budget & Complexity
- **Estimated**: 15k tokens, 20-30 minutes
- **Complexity**: Low (configuration and type fixes)
- **Files affected**: 5-8 files expected

## Current Status: 11/16 CI Checks Passing

### ✅ Passing Checks (11/16):
1. Black formatting
2. isort import sorting
3. Flake8 linting
4. MyPy type checking (src/)
5. Integration tests
6. Coverage analysis
7. End-to-end tests
8. Auto-merge detection tests
9. Workflow feature parity tests
10. Dependency checks
11. Performance optimizations

### ❌ Failing Checks (5/16):
1. **MyPy type checking (tests/)** - Missing type annotations in test_workflow_executor.py
2. **Import resolution** - Cannot find workflow_executor, agent_hooks, workflow_enforcer modules
3. **Security scan (bandit)** - Command not found or configuration issues
4. **Unit tests** - Some test failures due to import issues
5. **YAML validation** - Syntax error in validation script

## Step-by-Step Implementation Plan

### Step 1: Diagnose Current CI Failures
```bash
./scripts/run-ci-docker.sh
# Capture exact error messages for each failing check
```

### Step 2: Fix MyPy Type Issues (Priority 1)
- File: `tests/test_workflow_executor.py`
- Action: Add type annotations to `context = {}` variables
- Pattern: `context: Dict[str, Any] = {}`

### Step 3: Fix Import Resolution (Priority 2)
- Files: `tests/test_workflow_*.py`
- Action: Fix import statements for scripts modules
- Check: Ensure `scripts/__init__.py` exists and exports needed modules

### Step 4: Configure Security Scanner (Priority 3)
- Action: Install/configure bandit
- Files: Create `.banditrc` or update `pyproject.toml`
- Goal: Make bandit command available and passing

### Step 5: Fix YAML Validation (Priority 4)
- Files: Scripts with YAML validation syntax errors
- Action: Fix syntax in validation scripts

### Step 6: Verify All Fixes
```bash
./scripts/run-ci-docker.sh
# Should show 16/16 passing
```

## Expected Outcome
- All 16 Docker CI pipeline checks passing
- Zero import or type errors
- Clean security scan results
- Maintained test coverage ≥71.82%

## Notes
- Work incrementally, testing each fix
- Use conventional commits for each change
- Document any unexpected discoveries
