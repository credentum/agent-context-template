# Sprint Workflow Guide

This guide documents the complete workflow for managing sprints using YAML files and automated GitHub issue generation.

## Overview

The sprint system provides a **bidirectional workflow** between structured sprint planning (YAML files) and GitHub issue tracking:

```
Sprint YAML ↔ GitHub Issues ↔ Automated Tracking ↔ Sprint Updates
```

## Table of Contents

1. [Creating Sprint Files](#creating-sprint-files)
2. [Generating GitHub Issues](#generating-github-issues)
3. [Issue → Sprint Tracking](#issue-sprint-tracking)
4. [Bidirectional Synchronization](#bidirectional-synchronization)
5. [Automation Setup](#automation-setup)
6. [Best Practices](#best-practices)

## Creating Sprint Files

### 1. Use the Template

Start with the sprint template:

```bash
cp context/sprints/sprint-template.yaml context/sprints/sprint-5.1.yaml
```

### 2. Fill in Sprint Details

```yaml
schema_version: 1.0.0
document_type: sprint
id: sprint-5.1
title: "Sprint 5.1: MCP Implementation"
status: planning
created_date: '2025-07-15'
sprint_number: 5.1
start_date: '2025-07-15'
end_date: '2025-07-29'

goals:
  - "Implement core MCP server functionality"
  - "Create contract definitions and validation"
  - "Set up hybrid retrieval system"

phases:
  - phase: "5.1-1"
    name: "MCP Foundation"
    status: pending
    priority: blocking
    component: mcp
    description: "Core MCP server and contract setup"

    tasks:
      - title: "5.1-1 Create MCP contract schema"
        description: |
          Define JSON schema for MCP contracts covering store_context, retrieve_context, get_agent_state.

          ## Acceptance Criteria
          - [ ] Contract passes yamale validation
          - [ ] Contract frozen for Sprint 5.1
          - [ ] Examples included for each tool

          ## Implementation Notes
          - Use jsonschema draft-07
          - Include comprehensive examples

        labels:
          - sprint-current
          - "phase:5.1"
          - "component:mcp"
          - "priority:blocking"

        dependencies: []
        estimate: "4 hours"
```

### 3. Define Task Structure

Each task should include:

- **title**: Clear, actionable title (becomes GitHub issue title)
- **description**: Detailed description with acceptance criteria (becomes issue body)
- **labels**: Array of GitHub labels to apply
- **dependencies**: Array of task titles or issue numbers this depends on
- **estimate**: Time estimate for planning
- **assignee**: Optional GitHub username

## Generating GitHub Issues

### Manual Generation

```bash
# Preview what issues would be created
python -m src.agents.sprint_issue_linker create --sprint sprint-5.1 --dry-run --verbose

# Create the issues
python -m src.agents.sprint_issue_linker create --sprint sprint-5.1 --verbose
```

### What Happens

1. **Reads sprint YAML file** → Parses phases and tasks
2. **Checks existing issues** → Avoids duplicates by title matching
3. **Creates GitHub issues** → Using title, description, and labels from YAML
4. **Updates sprint file** → Adds `github_issue: 123` to each created task
5. **Saves changes** → Sprint YAML now tracks which GitHub issues correspond to tasks

### Example Output

```
Processing Sprint 5.1: MCP Implementation from sprint-5.1.yaml
✓ Created issue #49: 5.1-1 Create MCP contract schema
✓ Created issue #50: 5.1-2 Implement minimal MCP server
✓ Updated sprint-5.1.yaml with issue numbers

Summary: Created 2 new issues
```

## Issue → Sprint Tracking

### How Issues Update Sprint Files

The sprint-update workflow (`.github/workflows/sprint-update.yml`) automatically monitors GitHub issues and updates sprint files:

#### Triggers
- Issue opened/closed/labeled/unlabeled
- Pull request closed
- Scheduled runs (daily)

#### Update Logic

1. **Issue State Changes**:
   ```
   Issue #49 closed → Task marked as completed in sprint YAML
   Issue #50 labeled "in-progress" → Task/phase status updated
   Issue #51 labeled "blocked" → Task marked as blocked
   ```

2. **Phase Status Calculation**:
   ```
   All tasks in phase completed → Phase marked as "completed"
   Any task in phase in-progress → Phase marked as "in_progress"
   Any task blocked → Phase could be marked as "blocked"
   ```

3. **Sprint Status Calculation**:
   ```
   All phases completed → Sprint marked as "completed"
   Any phase in-progress → Sprint marked as "in_progress"
   ```

### Matching Logic

The system matches GitHub issues to sprint tasks using:

1. **Issue Number**: Direct match via `github_issue: 123` in task
2. **Title Matching**: Fuzzy matching on issue title vs task title
3. **Sprint Labels**: Issues with `sprint-X.Y` labels

### Example Sprint Update

```yaml
# Before issue work
- title: "5.1-1 Create MCP contract schema"
  github_issue: 49
  status: pending

# After issue #49 is closed
- title: "5.1-1 Create MCP contract schema"
  github_issue: 49
  status: completed
  completed_date: '2025-07-16'
```

## Bidirectional Synchronization

### Sprint YAML → GitHub Issues

When you **update the sprint YAML file**:

```bash
# After modifying sprint-5.1.yaml
python -m src.agents.sprint_issue_linker sync --sprint sprint-5.1
```

This will:
- Create new GitHub issues for new tasks
- Update existing issue titles/descriptions if changed
- Apply new labels to existing issues
- Close issues for removed tasks (with confirmation)

### GitHub Issues → Sprint YAML

The **sprint-update workflow** automatically:
- Updates task status based on issue state
- Updates phase status based on task completion
- Updates sprint status based on phase completion
- Tracks timestamps for completed items
- Creates auto-merge PRs with changes

## Automation Setup

### Option 1: Auto-Generate Issues on Sprint Creation

Add to `.github/workflows/sprint-update.yml`:

```yaml
  - name: Auto-generate issues for new sprints
    if: github.event_name == 'push' && contains(github.event.head_commit.added, 'context/sprints/')
    run: |
      # Find newly added sprint files
      for file in $(git diff --name-only --diff-filter=A HEAD~1 HEAD | grep 'context/sprints/sprint-.*\.yaml'); do
        sprint_id=$(basename "$file" .yaml)
        echo "Auto-generating issues for $sprint_id"
        python -m src.agents.sprint_issue_linker create --sprint "$sprint_id" --verbose
      done
```

### Option 2: Manual Workflow Trigger

Create `.github/workflows/generate-sprint-issues.yml`:

```yaml
name: Generate Sprint Issues

on:
  workflow_dispatch:
    inputs:
      sprint_id:
        description: 'Sprint ID (e.g., sprint-5.1)'
        required: true
        type: string
      dry_run:
        description: 'Dry run (preview only)'
        required: false
        type: boolean
        default: false

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: pip install click pyyaml

    - name: Generate issues
      env:
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
          python -m src.agents.sprint_issue_linker create --sprint ${{ github.event.inputs.sprint_id }} --dry-run --verbose
        else
          python -m src.agents.sprint_issue_linker create --sprint ${{ github.event.inputs.sprint_id }} --verbose
        fi
```

### Option 3: File Watch Automation

For automatic issue generation when sprint files are created/updated:

```yaml
# Add to sprint-update.yml
on:
  push:
    paths:
      - 'context/sprints/sprint-*.yaml'
  # ... existing triggers

jobs:
  update:
    # ... existing job

  generate-issues:
    if: github.event_name == 'push' && contains(github.event.head_commit.modified, 'context/sprints/')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: pip install click pyyaml

    - name: Generate issues for modified sprints
      env:
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        # Check for modified sprint files
        git diff --name-only HEAD~1 HEAD | grep 'context/sprints/sprint-.*\.yaml' | while read file; do
          if [ -f "$file" ]; then
            sprint_id=$(basename "$file" .yaml)
            echo "Checking sprint file: $sprint_id"

            # Only generate if sprint is in planning or in_progress
            status=$(python -c "
import yaml
with open('$file', 'r') as f:
    data = yaml.safe_load(f)
print(data.get('status', 'unknown'))
")

            if [ "$status" = "planning" ] || [ "$status" = "in_progress" ]; then
              echo "Auto-generating issues for $sprint_id (status: $status)"
              python -m src.agents.sprint_issue_linker create --sprint "$sprint_id" --verbose
            else
              echo "Skipping $sprint_id (status: $status)"
            fi
          fi
        done
```

## Best Practices

### 1. Sprint File Management

- **One sprint file per version**: `sprint-4.1.yaml`, `sprint-4.2.yaml`, etc.
- **Use semantic versioning**: Major.Minor for sprint numbers
- **Keep completed sprints**: Don't delete, mark as `status: completed`
- **Version control**: Always commit sprint files to git

### 2. Task Definition

- **Clear titles**: Use format "X.Y-Z Task Description"
- **Detailed descriptions**: Include acceptance criteria and implementation notes
- **Proper labels**: Include component, priority, and phase labels
- **Track dependencies**: List dependencies by task title or issue number

### 3. Issue Management

- **Don't manually edit generated issues**: Changes may be overwritten
- **Use sprint labels**: Always include `sprint-X.Y` labels
- **Link related PRs**: Reference sprint issues in PR descriptions
- **Update sprint YAML**: For major changes, update the source sprint file

### 4. Automation

- **Enable auto-generation**: Set up workflow triggers for new sprint files
- **Monitor sprint-update workflow**: Ensure it's running and creating PRs
- **Review auto-merge PRs**: Check sprint status updates are accurate
- **Regular sync**: Periodically run manual sync for large changes

## Troubleshooting

### Issues Not Generated

1. **Check sprint file format**: Validate YAML syntax
2. **Verify GitHub CLI**: Ensure `gh auth status` works
3. **Check permissions**: Workflow needs `issues: write` permission
4. **Review logs**: Check workflow run logs for errors

### Sprint Status Not Updating

1. **Check issue labels**: Ensure issues have correct `sprint-X.Y` labels
2. **Verify workflow triggers**: Check if sprint-update workflow is running
3. **Review matching logic**: Confirm issue titles match task titles
4. **Check permissions**: Workflow needs `pull-requests: write` permission

### Sync Issues

1. **Manual sync**: Run `sprint_issue_linker sync` command manually
2. **Check GitHub API limits**: May hit rate limits with many issues
3. **Verify sprint file**: Ensure `github_issue` numbers are correct
4. **Review dependencies**: Check if dependency tasks exist

## Usage Examples

### Creating a New Sprint

```bash
# 1. Create sprint file from template
cp context/sprints/sprint-template.yaml context/sprints/sprint-6.1.yaml

# 2. Edit the sprint file with your specific tasks
# Include detailed acceptance criteria and implementation notes

# 3. Commit to git (triggers automatic issue generation)
git add context/sprints/sprint-6.1.yaml
git commit -m "feat(sprint): add Sprint 6.1 for MCP implementation"
git push origin main

# 4. Issues are automatically created via GitHub workflow
# Check GitHub Issues tab to see created issues with proper labels
```

### Manual Commands

```bash
# Preview what issues would be created (dry run)
python -m src.agents.sprint_issue_linker create --sprint sprint-6.1 --dry-run --verbose

# Manually create issues if auto-generation didn't work
python -m src.agents.sprint_issue_linker create --sprint sprint-6.1 --verbose

# Update sprint labels from "sprint-current" to "sprint-6.1"
python -m src.agents.sprint_issue_linker update-labels --sprint sprint-6.1 --verbose

# Sync sprint YAML changes to GitHub issues (bidirectional)
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --verbose

# Preview sync changes without making them
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --dry-run --verbose

# Generate sprint progress report
python -m src.agents.update_sprint report --sprint sprint-6.1 --verbose
```

### Manual Workflow Triggers

```bash
# Manually trigger issue generation workflow
gh workflow run generate-sprint-issues.yml -f sprint_id=sprint-6.1 -f dry_run=false

# Manually trigger sprint update workflow
gh workflow run sprint-update.yml -f sprint_id=sprint-6.1

# Check workflow status
gh run list --workflow=generate-sprint-issues.yml
gh run list --workflow=sprint-update.yml
```

### Working with Issues

```bash
# View all issues for current sprint
gh issue list --label "sprint-6.1" --state all

# Close an issue (triggers sprint update automatically)
gh issue close 45 --comment "Completed MCP contract schema implementation"

# Add labels to track progress
gh issue edit 46 --add-label "in-progress"
gh issue edit 47 --add-label "blocked"

# Link pull requests to sprint issues
gh pr create --title "feat: implement MCP server" --body "Closes #45, #46"
```

### Monitoring and Reporting

```bash
# Check sprint progress
python -m src.agents.update_sprint report --verbose

# View specific sprint status
cat context/sprints/sprint-6.1.yaml | grep -A 5 "status:"

# Check recent sprint update PRs
gh pr list --label "sprint-update" --state all

# View workflow logs
gh run view --log
```

## Example Complete Workflow

```bash
# === Phase 1: Planning ===
# 1. Create sprint file from template
cp context/sprints/sprint-template.yaml context/sprints/sprint-6.1.yaml

# 2. Edit sprint-6.1.yaml with your tasks
vim context/sprints/sprint-6.1.yaml

# 3. Commit and push (triggers auto-issue-generation)
git add context/sprints/sprint-6.1.yaml
git commit -m "feat(sprint): add Sprint 6.1 for MCP implementation"
git push origin main

# === Phase 2: Development ===
# 4. Work on GitHub issues (automatic tracking via workflows)
# Developers close issues, add labels, create PRs

# 5. Monitor progress automatically
# Sprint status updates via PRs every time issues change

# === Phase 3: Maintenance ===
# 6. If you update sprint YAML, sync to issues
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1

# 7. Generate final sprint report
python -m src.agents.update_sprint report --sprint sprint-6.1 --verbose

# === Phase 4: Completion ===
# 8. Mark sprint as completed
sed -i 's/status: in_progress/status: completed/' context/sprints/sprint-6.1.yaml
git add context/sprints/sprint-6.1.yaml
git commit -m "chore(sprint): mark Sprint 6.1 as completed"
```

## Troubleshooting Common Scenarios

### Sprint File Updated But Issues Not Synced

```bash
# Check what would be synced
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --dry-run --verbose

# Force sync
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --verbose

# Check for GitHub API limits
gh api rate_limit
```

### Issues Created But Not Linked to Sprint File

```bash
# Find unlinked issues
gh issue list --label "sprint-6.1" --json number,title

# Manually update sprint YAML with issue numbers
# Then run sync to establish bidirectional links
python -m src.agents.sprint_issue_linker sync --sprint sprint-6.1 --verbose
```

### Auto-Generation Not Working

```bash
# Check workflow logs
gh run list --workflow=generate-sprint-issues.yml
gh run view [RUN_ID] --log

# Manually trigger workflow
gh workflow run generate-sprint-issues.yml -f sprint_id=sprint-6.1

# Fallback to manual creation
python -m src.agents.sprint_issue_linker create --sprint sprint-6.1 --verbose
```

This workflow provides complete **sprint planning → issue tracking → automated updates** with full traceability and automation.
