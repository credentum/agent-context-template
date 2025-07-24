# Execution Plan: Issue #1334 - Fix Phase 4 CI Optimization Runtime Failures

**Date**: 2025-07-24
**Issue**: #1334 - [SPRINT-4.3] Fix Phase 4 CI Optimization Script Runtime Failures
**Sprint**: sprint-4.3
**Task Template**: context/trace/task-templates/issue-1334-fix-phase-4-ci-optimization-runtime-failures.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 20,000
- **Complexity**: HIGH - 4 interconnected runtime failures
- **Time Estimate**: 4-6 hours
- **Files to Modify**: 4

## Step-by-Step Implementation Plan

### 1. Hardware Detector Fix (scripts/ci_hardware_detector.py)
**Problem**: Script called without required subcommand causing `unrecognized arguments: --output`
**Solution**:
- Review argparse setup to ensure subcommands are properly defined
- Check all call sites in CI workflows to use correct syntax
- Add default behavior if no subcommand provided
- Validate with: `python scripts/ci_hardware_detector.py detect --output /tmp/test.json`

### 2. Incremental Build Analyzer Fix (scripts/incremental_build_analyzer.py)
**Problem**: `AttributeError: 'list' object has no attribute 'add'` in `_build_reverse_dependencies`
**Root Cause**: `__post_init__` converts sets to lists for JSON serialization but runtime expects sets
**Solution**:
- Separate runtime data structures from serialization
- Keep sets during runtime operations
- Convert to lists only during JSON export
- Add proper type hints to clarify expectations

### 3. ARC Reviewer Enhancement (src/agents/arc_reviewer.py)
**Problem**: Only performs static analysis, missing runtime validation
**Solution**:
- Add `--runtime-test` flag to enable runtime validation mode
- Implement subprocess execution of scripts with error capture
- Parse runtime errors and include in review output
- Ensure backward compatibility with existing static-only mode

### 4. Bidirectional Sync Test Fix (tests/test_bidirectional_sync.py)
**Problem**: `AssertionError: Sync should not try to create issue #116 again`
**Solution**:
- Analyze the sync logic to understand why duplicate creation attempted
- Either fix the sync logic or update test expectations
- Ensure test reflects actual desired behavior

## Execution Order
1. Start with hardware detector (simplest fix)
2. Fix incremental build analyzer (dataclass issue)
3. Enhance ARC reviewer (most complex)
4. Fix bidirectional sync test (isolated test issue)

## Risk Mitigation
- Test each fix individually before moving to next
- Ensure backward compatibility maintained
- Run full CI suite after each major change
- Keep changes minimal and focused

## Success Metrics
- All 4 scripts execute without runtime errors
- CI pipeline passes completely
- Local development catches runtime issues
- No regression in existing functionality
