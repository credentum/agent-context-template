# Issue #93 Analysis: Test Bidirectional Sprint Workflow Validation

**Issue URL**: https://github.com/credentum/agent-context-template/issues/93
**Sprint**: sprint-4.1
**Date**: 2025-07-16
**Priority**: High

## Problem Analysis

### Objective
Create a comprehensive test to validate the bidirectional workflow between `context/sprints/sprint-4.1.yaml` and GitHub issues. The test should verify that:

1. **YAML → GitHub**: Updates to sprint YAML files automatically create/update GitHub issues
2. **GitHub → YAML**: Changes to GitHub issue status update the corresponding sprint YAML file
3. **Complex scenarios**: Handle multi-phase configurations with existing GitHub issues

### Current Infrastructure Analysis

From analyzing the codebase, the bidirectional workflow consists of:

**Key Components**:
- `src/agents/sprint_issue_linker.py` - Sprint → GitHub sync
- `src/agents/update_sprint.py` - GitHub → Sprint sync
- `.github/workflows/sprint-update.yml` - Automated GitHub Actions sync
- `.github/workflows/generate-sprint-issues.yml` - Issue creation automation
- `.github/workflows/auto-close-issues.yml` - PR-driven issue closure

**Existing sprint-4.1 configuration**:
- 7 phases with 8 total tasks
- GitHub issues: #28, #29, #30, #31, #32, #33, #79
- Complex multi-component structure (infra, ci, vector, dx, security, agents)

### Test Strategy

The test should validate the complete roundtrip workflow:

1. **Baseline**: Verify current sprint-4.1 state and existing issues
2. **YAML → GitHub**: Add new test task to sprint YAML, verify issue creation
3. **GitHub → YAML**: Modify GitHub issue status, verify YAML sync
4. **Bidirectional sync**: Test simultaneous changes in both directions
5. **Edge cases**: Test task removal, label changes, status changes

## Implementation Plan

### 1. Create Test Task in Sprint YAML

Add a new test task to sprint-4.1.yaml:
```yaml
- phase: 8
  name: Bidirectional Workflow Testing
  status: pending
  priority: high
  component: testing
  description: Test bidirectional sync between sprint YAML and GitHub issues
  tasks:
  - title: "Bidirectional Workflow Validation Test"
    description: |
      Test task to validate bidirectional sync between sprint YAML and GitHub issues.
      This task should be automatically created as a GitHub issue and then sync back.

      ## Test Scenarios
      - [x] Task created in YAML generates GitHub issue
      - [ ] GitHub issue status updates reflect in YAML
      - [ ] Task completion in YAML closes GitHub issue
      - [ ] Label changes sync bidirectionally

    labels:
    - sprint-current
    - phase:4.1
    - component:testing
    - priority:high
    - type:test
    dependencies: []
    estimate: 2 hours
    # github_issue: Will be populated automatically
```

### 2. Test Implementation Script

Create `tests/test_bidirectional_workflow.py`:

```python
#!/usr/bin/env python3
"""
Test script for bidirectional sprint workflow validation
"""

import json
import subprocess
import time
from pathlib import Path
import yaml

class BidirectionalWorkflowTest:
    def __init__(self):
        self.sprint_file = Path("context/sprints/sprint-4.1.yaml")
        self.test_task_title = "Bidirectional Workflow Validation Test"
        self.original_sprint_data = None
        self.test_issue_number = None

    def test_yaml_to_github_sync(self):
        """Test: Adding task to YAML creates GitHub issue"""

    def test_github_to_yaml_sync(self):
        """Test: Closing GitHub issue updates YAML status"""

    def test_bidirectional_consistency(self):
        """Test: Simultaneous changes maintain consistency"""
```

### 3. Validation Steps

**Step 1: Baseline Verification**
- Verify all existing issues in sprint-4.1 are correctly linked
- Confirm GitHub CLI authentication
- Check current sprint YAML structure

**Step 2: YAML → GitHub Test**
- Add test task to sprint-4.1.yaml
- Run `python -m src.agents.sprint_issue_linker sync --sprint sprint-4.1 --verbose`
- Verify new GitHub issue created with correct labels and content
- Verify sprint YAML updated with `github_issue` number

**Step 3: GitHub → YAML Test**
- Manually update GitHub issue status (close/reopen)
- Run sprint update workflow or trigger manually
- Verify sprint YAML reflects the status change

**Step 4: Cleanup**
- Remove test task from sprint YAML
- Verify orphaned issue is closed automatically
- Restore original sprint state

### 4. GitHub Actions Integration Test

Test the automated workflows:

**Generate Sprint Issues Workflow**:
- Create PR that modifies sprint-4.1.yaml with test task
- Verify `.github/workflows/generate-sprint-issues.yml` triggers
- Confirm issue created automatically on PR merge

**Sprint Update Workflow**:
- Trigger issue status change
- Verify `.github/workflows/sprint-update.yml` triggers
- Confirm sprint YAML updated via automated PR

### 5. Edge Cases to Test

**Task Removal**:
- Remove task from sprint YAML
- Verify corresponding GitHub issue is closed with explanation
- Verify orphaned issue detection works

**Label Synchronization**:
- Change task labels in sprint YAML
- Verify GitHub issue labels updated
- Test preserving non-sprint labels

**Status Transitions**:
- Change phase status from `pending` → `in_progress` → `completed`
- Verify GitHub issues open/close appropriately
- Test reopening when phase status changes back

**Error Handling**:
- Test with invalid GitHub issue numbers
- Test with missing GitHub authentication
- Test with API rate limiting

## Technical Implementation Details

### Files to Create/Modify

1. **context/sprints/sprint-4.1.yaml** - Add test task temporarily
2. **tests/test_bidirectional_workflow.py** - Main test implementation
3. **scripts/test-bidirectional-sync.sh** - Shell script for manual testing
4. **context/trace/logs/bidirectional-test-results.md** - Test results log

### Test Commands

```bash
# Manual sync test
python -m src.agents.sprint_issue_linker sync --sprint sprint-4.1 --dry-run --verbose

# Manual issue creation test
python -m src.agents.sprint_issue_linker create --sprint sprint-4.1 --dry-run --verbose

# Sprint update test
python -m src.agents.update_sprint update --sprint sprint-4.1 --verbose

# Full integration test
./scripts/test-bidirectional-sync.sh
```

### GitHub API Operations to Test

1. **Issue Creation**: POST /repos/owner/repo/issues
2. **Issue Updates**: PATCH /repos/owner/repo/issues/{number}
3. **Label Management**: PUT /repos/owner/repo/issues/{number}/labels
4. **Issue Status**: PATCH /repos/owner/repo/issues/{number} (state: open/closed)
5. **Comments**: POST /repos/owner/repo/issues/{number}/comments

### Success Criteria

- [x] **Test task creation**: Adding task to YAML creates GitHub issue
- [ ] **Issue numbering**: Sprint YAML updated with correct GitHub issue number
- [ ] **Status sync**: Changing phase status updates GitHub issue state
- [ ] **Label sync**: Task label changes reflect in GitHub issue labels
- [ ] **Reverse sync**: GitHub issue changes update sprint YAML
- [ ] **Orphan handling**: Removing tasks closes corresponding GitHub issues
- [ ] **Workflow integration**: GitHub Actions trigger automatically
- [ ] **Error resilience**: Handles missing issues and API failures gracefully
- [ ] **Data preservation**: Non-sprint metadata preserved during sync
- [ ] **Performance**: Sync completes within reasonable time (< 30 seconds)

## Risk Mitigation

**GitHub API Rate Limits**:
- Use dry-run mode for initial testing
- Implement exponential backoff
- Test with small batches first

**Data Corruption**:
- Backup original sprint-4.1.yaml before testing
- Use git branches for testing changes
- Implement rollback procedures

**Workflow Conflicts**:
- Test during low-activity periods
- Coordinate with other automation
- Monitor for duplicate operations

## Dependencies

- GitHub CLI authenticated and working
- Sprint-4.1 existing issues (#28, #29, #30, #31, #32, #33, #79)
- GitHub Actions workflows enabled
- Python dependencies: click, pyyaml, subprocess
- Git access for creating test branches

---

*This test plan provides comprehensive validation of the bidirectional sprint workflow as requested in issue #93.*
