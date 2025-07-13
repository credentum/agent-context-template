# Sprint Automation Guide

The Agent-First Context System includes comprehensive sprint automation capabilities that integrate with GitHub Issues and Actions.

## Overview

The sprint automation system provides:
- Automatic sprint status tracking based on GitHub issues
- Task-to-issue linking with labels
- Automated sprint transitions
- Progress reporting and metrics
- CI/CD integration via GitHub Actions

## Components

### 1. Sprint Documents (`context/sprints/`)

Sprint documents follow the schema defined in `context/schemas/sprint.yaml`:

```yaml
schema_version: "1.0.0"
document_type: "sprint"
id: "sprint-001"
title: "MVP Implementation Sprint"
status: "planning"  # planning, in_progress, completed
sprint_number: 1
start_date: "2025-07-11"
end_date: "2025-07-29"
phases:
  - phase: 0
    name: "Setup"
    status: "pending"  # pending, in_progress, completed, blocked
    tasks:
      - "Task description"
```

### 2. Update Sprint Script (`update_sprint.py`)

Updates sprint documents based on GitHub issue state:

```bash
# Update current active sprint
python update_sprint.py update --verbose

# Update specific sprint
python update_sprint.py update --sprint sprint-001

# Generate sprint report
python update_sprint.py report --verbose

# Watch mode for CI/CD
python update_sprint.py watch
```

Features:
- Automatically marks phases as completed when all tasks are closed
- Updates sprint status based on phase completion
- Creates next sprint when current is completed
- Updates timestamps automatically

### 3. Sprint Issue Linker (`sprint_issue_linker.py`)

Creates GitHub issues from sprint tasks:

```bash
# Create issues from active sprint
python sprint_issue_linker.py create --verbose

# Create issues from specific sprint
python sprint_issue_linker.py create --sprint sprint-001

# Dry run to see what would be created
python sprint_issue_linker.py create --dry-run

# Update labels on existing issues
python sprint_issue_linker.py update-labels
```

Features:
- Creates properly formatted issues with sprint context
- Applies appropriate labels (sprint-N, phase-N)
- Links issues to sprint tasks
- Avoids creating duplicate issues

### 4. GitHub Actions Integration

#### Sprint Update Workflow (`.github/workflows/sprint-update.yml`)

Triggers on:
- Issue events (opened, closed, labeled)
- Pull request closures
- Daily schedule (9 AM UTC weekdays)
- Manual dispatch

Actions:
- Updates sprint document based on issue state
- Generates sprint reports
- Commits changes automatically
- Posts sprint status to relevant issues

#### Sprint Start Workflow (`.github/workflows/sprint-start.yml`)

Triggers on:
- Manual dispatch with sprint number
- Creation of `start-sprint-N` label

Actions:
- Changes sprint status from `planning` to `in_progress`
- Creates GitHub issues for all sprint tasks
- Updates labels on existing issues
- Posts sprint kickoff announcement

## Usage Patterns

### Starting a New Sprint

1. **Manual Start**:
   ```bash
   # Via GitHub UI
   Actions → Sprint Start → Run workflow → Enter sprint number

   # Via label
   Create label "start-sprint-2" on any issue
   ```

2. **Automatic Creation**:
   When a sprint is marked as completed, the next sprint is automatically created in `planning` status.

### Tracking Sprint Progress

1. **Label Issues**:
   - Use `sprint-N` label for sprint association
   - Use `phase-N` label for phase tracking
   - Close issues to mark tasks as complete

2. **View Progress**:
   ```bash
   # Local report
   python update_sprint.py report --verbose

   # GitHub UI
   Issues → Labels → sprint-N
   ```

3. **Automated Updates**:
   - Sprint status updates automatically on issue closure
   - Daily scheduled updates ensure accuracy
   - Phase progression tracked automatically

### Integration with Development Workflow

1. **Issue Templates**:
   Use `.github/ISSUE_TEMPLATE/sprint-task.md` for consistent issue creation.

2. **PR Integration**:
   Reference sprint issues in PRs:
   ```
   Fixes #123 (Sprint 1, Phase 2)
   ```

3. **Automation Labels**:
   - `sprint-current`: Issues for current sprint (before numbering)
   - `sprint-N`: Issues for specific sprint
   - `phase-N`: Issues for specific phase
   - `blocked`: Blocked tasks

## Configuration

### Sprint Duration

Set in `.ctxrc.yaml`:
```yaml
agents:
  pm_agent:
    sprint_duration_days: 14  # Default sprint length
```

### Thresholds

Configure warning thresholds:
```yaml
linter:
  warning_days_old: 90
  warning_days_until_expire: 7
```

## Best Practices

1. **Sprint Planning**:
   - Define all tasks in sprint YAML before starting
   - Use clear, actionable task descriptions
   - Group related tasks in phases

2. **Issue Management**:
   - Create issues at sprint start using the linker
   - Keep issue titles consistent with sprint tasks
   - Close issues promptly when tasks complete

3. **Automation**:
   - Let automation handle status updates
   - Review sprint reports regularly
   - Use manual updates sparingly

4. **Sprint Transitions**:
   - Complete all tasks before marking sprint as done
   - Review and update next sprint during planning
   - Use sprint retrospectives to improve process

## Security Considerations

### Input Validation

The sprint automation system validates all user inputs:
- Sprint numbers must be numeric (1-999)
- Label names are sanitized before use
- File paths are validated to prevent traversal

### GitHub CLI Requirements

Both `update_sprint.py` and `sprint_issue_linker.py` require GitHub CLI:
- Checks authentication status on startup
- Provides clear error messages if not configured
- Dry-run mode bypasses GitHub CLI for testing

### Workflow Security

- Minimal permissions requested (contents: write, issues: read)
- Input sanitization for commit messages
- External scripts for complex operations

## Troubleshooting

### Issues Not Linking

- Ensure issue titles match sprint task text
- Check for correct sprint labels
- Verify GitHub token permissions

### Sprint Not Updating

- Check GitHub Actions logs
- Ensure .ctxrc.yaml is valid
- Verify sprint YAML follows schema

### Automation Not Triggering

- Check workflow permissions
- Verify event triggers match your usage
- Review GitHub Actions quotas

### GitHub CLI Errors

If you see "GitHub CLI not found" or "not authenticated":
```bash
# Install GitHub CLI
# See: https://cli.github.com/

# Authenticate
gh auth login
```

## Example Sprint Lifecycle

1. **Sprint Created**:
   - Status: `planning`
   - Define phases and tasks

2. **Sprint Started**:
   - Create label `start-sprint-1`
   - Status: `in_progress`
   - Issues created automatically

3. **Development**:
   - Work on issues
   - Close completed tasks
   - Phases progress automatically

4. **Sprint Completed**:
   - All tasks closed
   - Status: `completed`
   - Next sprint created

5. **Repeat**:
   - Plan next sprint
   - Start when ready
