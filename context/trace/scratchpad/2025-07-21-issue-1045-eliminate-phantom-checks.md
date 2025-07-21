# Issue #1045: Eliminate Phantom Conflict Detection Checks

## Issue Link
https://github.com/droter/agent-context-template/issues/1045

## Sprint Reference
- Sprint: sprint-5-2
- Phase: Phase 2: Implementation
- Component: ci

## Task Template
- Template: context/trace/task-templates/issue-1045-eliminate-phantom-conflict-checks.md
- Token Budget: 3000 tokens
- Complexity: Low
- Estimated Time: 30 minutes

## Problem Summary
The pr-conflict-validator.yml workflow uses `github.rest.checks.create` API to manually create a "🔍 Conflict Detection" check. This check is getting misattributed to other workflows (Lint, Tests, Coverage), causing phantom checks to appear and creating false failures.

## Root Cause
- Manual check creation via GitHub API causes cross-workflow attribution issues
- The check shows up in unrelated workflows where it wasn't actually run
- Creates confusion and false failure notifications

## Solution Plan
1. Remove the entire "Update PR status check" step (lines 114-165)
2. Let the job's natural success/failure status serve as the check
3. Modify conflict detection to use exit codes:
   - Exit 1 when conflicts detected
   - Exit 0 when no conflicts
4. Keep PR commenting functionality intact
5. Update documentation

## Implementation Steps

### Step 1: Create Feature Branch
```bash
git checkout main
git pull origin main
git checkout -b fix/1045-eliminate-phantom-checks
```

### Step 2: Modify pr-conflict-validator.yml
- Remove lines 114-165 (the entire "Update PR status check" step)
- Modify the conflict detection step to exit with appropriate codes
- Ensure job fails when conflicts are detected

### Step 3: Update Documentation
- Update docs/workflow-deprecation-plan.md to document this architectural decision
- Explain why we rely on job status instead of manual check creation

### Step 4: Test Changes
- Validate YAML syntax
- Ensure workflow still functions correctly
- Verify no phantom checks appear

### Step 5: Create PR
- Create PR with proper closing keyword
- Reference issue #1045
- Document the architectural improvement

## Dependencies Check
- Issue #1043 (GitHub CLI authentication) - Status: Need to verify if merged
- Issue #1044 (git rev-list syntax) - Status: Need to verify if merged

## Expected Outcome
- No more phantom "🔍 Conflict Detection" checks in unrelated workflows
- Cleaner separation of concerns between workflows
- Simplified architecture relying on native GitHub Actions features
