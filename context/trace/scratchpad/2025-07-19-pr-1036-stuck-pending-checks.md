# PR #1036 Stuck with Pending Checks - Root Cause Analysis

**Date**: 2025-07-19
**PR**: #1036 - chore: automated sprint status update
**Status**: BLOCKED - No CI checks running

## Problem Summary

PR #1036 was stuck with no pending checks running, preventing auto-merge. After 10+ attempts to resolve, thorough investigation revealed the root cause.

## Root Cause

GitHub has a security feature that prevents CI workflows from triggering on PRs created by bots using `GITHUB_TOKEN`. This is to prevent recursive workflow runs.

**Evidence**:
- PR #1036 `statusCheckRollup: []` (empty array)
- `mergeStateStatus: "BLOCKED"`
- Created by `github-actions[bot]` using `GITHUB_TOKEN`
- sprint-update.yml line 257-260 documented this limitation

## Solution Implemented

Replace `GITHUB_TOKEN` with `GH_TOKEN` (Personal Access Token) in sprint-update.yml workflow.

### Changes Made:

1. **Updated sprint-update.yml**:
   - Changed checkout token from `GITHUB_TOKEN` to `GH_TOKEN`
   - Updated all GH CLI environment variables to use `GH_TOKEN`
   - Modified create-pull-request action to use `GH_TOKEN`
   - Updated PR body message to reflect CI will run

2. **Updated CLAUDE.md documentation**:
   - Added `GH_TOKEN` to required secrets list
   - Created new section 6.3 "GitHub Token Usage Guide"
   - Documented when to use `GH_TOKEN` vs `GITHUB_TOKEN`

## Key Learnings

1. **Always use GH_TOKEN for PR creation**: Any workflow that creates PRs must use a PAT or GitHub App token
2. **GITHUB_TOKEN is fine for read operations**: Comments, status checks, and reads work with default token
3. **Check workflow comments**: GitHub Actions often documents these limitations in workflow files
4. **Empty statusCheckRollup**: This is the key indicator that CI isn't running due to token restrictions

## Prevention

To prevent this issue in the future:
- Always review workflows that create PRs
- Use `GH_TOKEN` for any PR creation operations
- Document token usage clearly in CLAUDE.md
- Consider using GitHub App tokens for more complex scenarios

## Related Issues

- Issue #173: AI-monitored PR process implementation
- This issue revealed the importance of proper token usage for automated workflows

## Resolution

With the implementation of GH_TOKEN in sprint-update.yml, future automated sprint update PRs will:
- Have CI checks run automatically
- Be eligible for auto-merge when checks pass
- Not get stuck in a BLOCKED state

The fix ensures the automated sprint workflow functions as intended without manual intervention.
