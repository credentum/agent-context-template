# Issue #961: Fix failing sprint-update.yml workflow and resolve CI/YAML validation issues

**Date**: 2025-07-18
**Issue**: https://github.com/agent-context-template/issues/961
**Sprint**: sprint-4.1
**Phase**: Phase 4.1: Testing & Validation
**Task Template**: context/trace/task-templates/issue-961-fix-failing-sprint-update-yml-workflow.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 12,000 tokens
- **Complexity**: High (multiple interconnected failures)
- **Files affected**: ~15 files (workflows, tests, context YAML)
- **Time estimate**: 1-2 hours

## Step-by-Step Implementation Plan

### Phase 1: Analysis & Diagnosis
1. **Examine failing workflow**: `.github/workflows/sprint-update.yml`
   - Check conflict detection logic
   - Identify root cause of failure

2. **Analyze test failures**: `tests/test_workflow_feature_parity.py`
   - Review 5 failing tests
   - Understand what they're testing
   - Identify fixes needed

3. **YAML validation sweep**: Find all files with YAML issues
   - Check `context/sprints/sprint-4.1.yaml`
   - Validate all `context/schemas/*.yaml` files
   - Check workflow files for syntax issues

### Phase 2: Systematic Fixes
1. **Fix sprint-update.yml workflow**
   - Repair conflict detection logic
   - Ensure proper YAML syntax

2. **Fix test failures**
   - Address failing workflow feature parity tests
   - Update test expectations if needed

3. **YAML formatting fixes**
   - Fix indentation errors
   - Fix line length violations (>80 chars)
   - Add missing document start markers (`---`)
   - Fix syntax errors in context schemas

### Phase 3: Validation & Testing
1. **Local CI validation**
   - Run `./scripts/run-ci-docker.sh`
   - Ensure all Docker CI checks pass
   - Fix any remaining issues

2. **Pre-commit validation**
   - Run `pre-commit run --all-files`
   - Ensure all hooks pass in Docker environment

3. **Test suite validation**
   - Run `pytest --cov=src --cov-report=term-missing`
   - Ensure coverage maintained above 71.82%

## Context Window Management
- Monitor token usage proactively
- Use `/clear` if approaching 25k tokens
- Reference task template for consistency

## Success Metrics
- [ ] sprint-update.yml workflow passes conflict detection
- [ ] All 5 failing tests in test_workflow_feature_parity.py now pass
- [ ] All YAML files pass validation
- [ ] Pre-push hooks pass consistently in Docker environment
- [ ] All workflow files have proper YAML syntax

## Notes
- This is a critical sprint blocker - priority high
- Multiple interconnected failures suggest systematic approach needed
- Focus on root cause analysis before making changes
- Document any workflow behavior changes
