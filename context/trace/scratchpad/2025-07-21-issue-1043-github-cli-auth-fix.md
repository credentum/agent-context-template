# Scratchpad: Issue 1043 - GitHub CLI Authentication Fix

## Issue Link
- GitHub Issue: #1043
- Sprint: sprint-5-2
- Task Template: context/trace/task-templates/issue-1043-fix-github-cli-authentication.md

## Token Budget & Complexity
- Estimated: 2k tokens (trivial change)
- Complexity: Trivial - single line move in YAML file

## Implementation Plan

### Step 1: Create feature branch
- Branch name: `fix/1043-github-cli-authentication`

### Step 2: Make the fix
- Remove `env:` section from workflow level (lines 207-208)
- Add `env:` section to the `validate-conflicts` job
- Place it after the `permissions:` section for clarity

### Step 3: Verify changes
- Ensure YAML syntax is valid
- Confirm GH_TOKEN will be available to all steps in the job

### Step 4: Test locally
- Run yamllint on the file
- Verify the workflow structure

### Step 5: Commit and push
- Commit message: `fix(ci): move GH_TOKEN to job level for proper authentication`

### Step 6: Create PR
- Reference issue #1043
- Note this is part 1/3 of the larger fix

## Key Details
- Current location: Workflow level (line 207-208)
- Target location: Inside `validate-conflicts` job, after `permissions:` block
- Token value remains: `${{ secrets.GITHUB_TOKEN }}`

## Notes
This is a simple configuration fix that will enable GitHub CLI commands in the workflow to authenticate properly, preventing fallback to unauthenticated API calls.
