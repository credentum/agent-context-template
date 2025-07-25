# ARC Reviewer Performance Issue Investigation
**Date**: 2025-07-25
**Issue**: ARC reviewer times out due to running full test suite

## Problem Summary
ARC reviewer is timing out in the local CI pipeline because it runs the **full pytest test suite with coverage** every time it's invoked. The test suite alone takes 2-3+ minutes to complete, causing timeouts and CI failures.

## Root Cause
In `src/agents/arc_reviewer.py`, the `_check_coverage()` method runs:
```python
cmd = [
    "python", "-m", "pytest",
    "--cov=src",
    "--cov-report=json",
    "--cov-report=term-missing",
    "-m", "not integration and not e2e",
    "-x", "-q"
]
```

This runs the entire test suite to get coverage data, which is:
- Time-consuming (2-3+ minutes)
- Resource-intensive
- Unnecessary for every PR review

## Impact
1. Local CI takes 5+ minutes even for small changes
2. Developers experience timeouts and false failures
3. CI pipeline becomes unreliable
4. Blocks rapid development iteration

## Temporary Fix Applied
Updated `scripts/claude-ci.sh`:
- Increased default timeout from 60s to 300s (5 minutes)
- Added proper handling for timeout scenarios
- Improved error messages to indicate the root cause

## Recommended Permanent Solutions

### Option 1: Cache Coverage Data (Preferred)
- Run coverage once and cache results
- Only re-run if Python files changed
- Use file hashes to detect changes

### Option 2: Use Existing Coverage Reports
- Check if recent coverage.json exists
- Use timestamp to determine freshness
- Only run tests if data is stale

### Option 3: Separate Coverage from Review
- Make coverage a separate CI step
- ARC reviewer reads pre-computed coverage
- Parallelize CI stages

### Option 4: Incremental Coverage
- Only test changed modules
- Use pytest-cov's `--cov-context=test` feature
- Calculate coverage delta instead of absolute

## Performance Metrics
- Current: 2-3+ minutes per ARC review
- Target: <30 seconds for code review (excluding coverage)
- Coverage can run separately in parallel

## Next Steps
1. Create issue for ARC reviewer performance optimization
2. Implement coverage caching mechanism
3. Consider moving to incremental testing strategy
4. Profile test suite to identify slow tests

## Related Issues
- Original issue: #1426 (CI validation blocking issues)
- Follow-up issue: #1489 (remaining CI issues)
- Performance optimization needed for sustainable CI
