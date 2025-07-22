# Issue #1201 Execution Plan - Fix flake8 errors blocking pre-push hooks

**Issue Link**: https://github.com/droter/agent-context-template/issues/1201
**Sprint**: sprint-4-2
**Task Template**: context/trace/task-templates/issue-1201-fix-flake8-errors-blocking-pre-push-hooks.md

## Problem Analysis
- `tests/test_formatting_issues.py` is intentionally broken for testing formatters
- `.flake8` config excludes this file on line 21
- Pre-commit hooks work correctly (respect .flake8 config)
- Docker CI uses inline flake8 parameters, ignoring .flake8 exclude settings
- This causes CI failures that force developers to use SKIP_HOOKS=1

## Root Cause
Two locations use inline flake8 parameters instead of .flake8 config:
1. `scripts/test-comprehensive-ci.sh:54` - inline parameters
2. `docker-compose.ci.yml:89-91` - inline parameters

## Solution Strategy
Replace inline flake8 parameters with simple `flake8` command to use .flake8 config file.

## Token Budget & Complexity
- **Estimated tokens**: 5,000 (simple config fix)
- **Estimated time**: 15 minutes
- **Files to modify**: 2
- **Complexity**: Low (configuration change only)

## Implementation Steps
1. Create feature branch
2. Modify scripts/test-comprehensive-ci.sh line 54 to use `flake8` without inline params
3. Modify docker-compose.ci.yml lines 89-91 to use `flake8` without inline params
4. Ensure .flake8 config file is mounted in Docker containers
5. Test with Docker CI
6. Verify tests/test_formatting_issues.py is properly excluded

## Verification Plan
- Run `./scripts/run-ci-docker.sh` - must pass
- Run `./scripts/run-ci-docker.sh flake8` - must pass
- Verify no flake8 errors on test_formatting_issues.py
- Verify other files still get checked by flake8
