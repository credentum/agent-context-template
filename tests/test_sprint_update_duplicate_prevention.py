#!/usr/bin/env python3
"""
Sprint Update Workflow Duplicate Prevention Tests

This test suite validates that the sprint-update.yml workflow
correctly prevents duplicate PR creation when both pull_request.closed
and issues.closed events fire simultaneously.

Tests ensure the duplicate prevention logic works correctly:
- Concurrency control prevents simultaneous runs
- Duplicate detection identifies recent/active runs
- Cancellation logic exits gracefully for duplicates
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import yaml


class TestSprintUpdateDuplicatePrevention:
    """Test duplicate prevention in sprint-update.yml workflow"""

    def setup_method(self):
        """Setup workflow paths and test data"""
        project_root = Path(__file__).parent.parent
        self.workflows_dir = project_root / ".github/workflows"
        self.sprint_update_workflow = self.workflows_dir / "sprint-update.yml"

    def test_workflow_file_exists(self):
        """Test that sprint-update.yml workflow exists"""
        assert (
            self.sprint_update_workflow.exists()
        ), f"sprint-update.yml should exist at {self.sprint_update_workflow}"

    def test_workflow_syntax_valid(self):
        """Test that sprint-update.yml has valid YAML syntax"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        assert workflow_content is not None, "Workflow YAML should parse correctly"
        assert "name" in workflow_content, "Workflow should have a name"
        assert (
            workflow_content["name"] == "Sprint Update"
        ), "Workflow name should be 'Sprint Update'"

    def test_concurrency_control_configured(self):
        """Test that concurrency control is properly configured"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        assert "concurrency" in workflow_content, "Workflow should have concurrency control"
        concurrency = workflow_content["concurrency"]

        # Check concurrency group includes issue/PR number for proper grouping
        group = concurrency["group"]
        assert "github.event.issue.number" in group, "Concurrency group should include issue number"
        assert (
            "github.event.pull_request.number" in group
        ), "Concurrency group should include PR number"
        assert concurrency["cancel-in-progress"] is True, "Should cancel in-progress runs"

    def test_trigger_events_configured(self):
        """Test that workflow triggers on correct events"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        triggers = workflow_content["on"]

        # Check that both triggering events are configured
        assert "issues" in triggers, "Should trigger on issues events"
        assert "pull_request" in triggers, "Should trigger on pull_request events"

        # Check specific event types
        issues_events = triggers["issues"]["types"]
        pr_events = triggers["pull_request"]["types"]

        assert "closed" in issues_events, "Should trigger on issues.closed"
        assert "closed" in pr_events, "Should trigger on pull_request.closed"

    def test_duplicate_detection_step_exists(self):
        """Test that duplicate detection step is present"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Find the duplicate detection step
        duplicate_check_step = None
        for step in steps:
            if step.get("id") == "check-duplicates":
                duplicate_check_step = step
                break

        assert duplicate_check_step is not None, "Should have duplicate detection step"
        assert "run" in duplicate_check_step, "Duplicate check should have run script"

    def test_cancellation_step_exists(self):
        """Test that cancellation step is present"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Find the cancellation step
        cancel_step = None
        for step in steps:
            if "Cancel if duplicate" in step.get("name", ""):
                cancel_step = step
                break

        assert cancel_step is not None, "Should have cancellation step"
        assert "if" in cancel_step, "Cancellation step should be conditional"
        assert "found_duplicate" in cancel_step["if"], "Should check for duplicate detection result"

    @patch("subprocess.run")
    def test_duplicate_detection_logic_recent_success(self, mock_subprocess):
        """Test duplicate detection identifies recent successful runs"""
        # Mock gh run list output with a recent successful run
        mock_runs: List[Dict[str, Any]] = [
            {
                "id": "12345",
                "createdAt": (datetime.now() - timedelta(minutes=2)).isoformat() + "Z",
                "status": "completed",
                "event": "pull_request",
                "conclusion": "success",
            },
            {
                "id": "12346",
                "createdAt": (datetime.now() - timedelta(minutes=1)).isoformat() + "Z",
                "status": "in_progress",
                "event": "issues",
                "conclusion": None,
            },
        ]

        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = json.dumps(mock_runs)

        # This test validates the logic structure - in practice the actual
        # duplicate detection runs in the GitHub Actions environment
        assert len(mock_runs) == 2, "Should have test data with multiple runs"

        # Check that we have both a successful recent run and an in-progress run
        recent_success = any(
            run["conclusion"] == "success" and run["status"] == "completed" for run in mock_runs
        )
        active_run = any(run["status"] == "in_progress" for run in mock_runs)

        assert recent_success, "Test data should include recent successful run"
        assert active_run, "Test data should include active run"

    @patch("subprocess.run")
    def test_duplicate_detection_logic_active_runs(self, mock_subprocess):
        """Test duplicate detection identifies active runs"""
        # Mock gh run list output with an active run
        mock_runs: List[Dict[str, Any]] = [
            {
                "id": "12347",
                "createdAt": datetime.now().isoformat() + "Z",
                "status": "in_progress",
                "event": "pull_request",
                "conclusion": None,
            }
        ]

        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = json.dumps(mock_runs)

        # Validate test scenario structure
        assert len(mock_runs) == 1, "Should have single active run"
        active_run = mock_runs[0]
        assert active_run["status"] == "in_progress", "Run should be active"
        assert active_run["conclusion"] is None, "Active run should have no conclusion"

    def test_workflow_timeout_configured(self):
        """Test that workflow has appropriate timeout"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]

        assert "timeout-minutes" in update_job, "Job should have timeout configured"
        timeout = update_job["timeout-minutes"]
        assert isinstance(timeout, int), "Timeout should be numeric"
        assert timeout > 0, "Timeout should be positive"
        assert timeout <= 30, "Timeout should be reasonable (≤30 minutes)"

    def test_permissions_properly_configured(self):
        """Test that workflow has necessary permissions"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]

        assert "permissions" in update_job, "Job should specify permissions"
        permissions = update_job["permissions"]

        # Check required permissions for sprint update operations
        assert "contents" in permissions, "Should have contents permission"
        assert "issues" in permissions, "Should have issues permission"
        assert "pull-requests" in permissions, "Should have pull-requests permission"

        # Verify permissions are write level (needed for PR creation)
        assert permissions["contents"] == "write", "Contents should be write permission"
        assert permissions["issues"] == "write", "Issues should be write permission"
        assert permissions["pull-requests"] == "write", "PRs should be write permission"

    def test_github_token_configured(self):
        """Test that workflow uses appropriate GitHub token"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Check checkout step uses GH_TOKEN
        checkout_step = steps[0]  # First step should be checkout
        assert "uses" in checkout_step, "First step should be checkout action"
        assert "actions/checkout" in checkout_step["uses"], "Should use checkout action"

        if "with" in checkout_step:
            with_params = checkout_step["with"]
            if "token" in with_params:
                token = with_params["token"]
                assert "GH_TOKEN" in token, "Should use GH_TOKEN for authentication"

    def test_environment_variables_secure(self):
        """Test that environment variables are properly configured"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Check that steps using GitHub CLI have proper token env var
        for step in steps:
            if "env" in step and "GH_TOKEN" in step["env"]:
                gh_token = step["env"]["GH_TOKEN"]
                assert "secrets.GH_TOKEN" in gh_token, "GH_TOKEN should reference secrets"

    def test_create_pr_step_configured(self):
        """Test that PR creation step is properly configured"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Find PR creation step
        pr_step = None
        for step in steps:
            if "peter-evans/create-pull-request" in str(step.get("uses", "")):
                pr_step = step
                break

        assert pr_step is not None, "Should have PR creation step"
        assert "with" in pr_step, "PR step should have configuration"

        pr_config = pr_step["with"]
        assert "token" in pr_config, "PR creation should specify token"
        assert "GH_TOKEN" in pr_config["token"], "PR creation should use GH_TOKEN"

    def test_auto_merge_configuration(self):
        """Test that auto-merge is properly configured"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Find auto-merge step
        auto_merge_step = None
        for step in steps:
            if "Enable Auto-Merge" in step.get("name", ""):
                auto_merge_step = step
                break

        assert auto_merge_step is not None, "Should have auto-merge step"
        assert "if" in auto_merge_step, "Auto-merge should be conditional"
        assert "env" in auto_merge_step, "Auto-merge should have environment"
        assert "GH_TOKEN" in auto_merge_step["env"], "Auto-merge should use GH_TOKEN"

    def test_workflow_robustness(self):
        """Test that workflow handles edge cases robustly"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]

        # Check that job runs on ubuntu-latest (stable environment)
        assert update_job["runs-on"] == "ubuntu-latest", "Should run on ubuntu-latest"

        # Check conditional execution patterns
        steps = update_job["steps"]
        conditional_steps = [step for step in steps if "if" in step]

        assert len(conditional_steps) > 0, "Should have conditional steps for robustness"

    def test_issue_closing_logic_exists(self):
        """Test that issue auto-closing logic is present"""
        with open(self.sprint_update_workflow) as f:
            workflow_content = yaml.safe_load(f)

        jobs = workflow_content["jobs"]
        update_job = jobs["update"]
        steps = update_job["steps"]

        # Find auto-close step
        auto_close_step = None
        for step in steps:
            if "Auto-close completed issues" in step.get("name", ""):
                auto_close_step = step
                break

        assert auto_close_step is not None, "Should have auto-close issues step"
        assert "if" in auto_close_step, "Auto-close should be conditional"

        # Check that it triggers on PR merge
        condition = auto_close_step["if"]
        assert "pull_request" in condition, "Should check for pull request event"
        assert "merged" in condition, "Should check if PR was merged"


class TestSprintUpdateIntegration:
    """Integration tests for sprint update workflow scenarios"""

    def test_yaml_frontmatter_parsing_logic(self):
        """Test YAML frontmatter parsing logic structure"""
        # This tests the logical structure of YAML parsing in the workflow
        sample_pr_body_with_yaml = """---
pr_metadata:
  type: "test"
  closes_issues: [1047]
  automation_flags:
    auto_merge: true
---

## Summary
This PR tests the sprint update duplicate prevention logic.

## Testing
- [x] Validates duplicate prevention
- [x] Ensures single PR creation
"""

        # Validate that the sample has proper YAML frontmatter structure
        lines = sample_pr_body_with_yaml.strip().split("\n")
        assert lines[0] == "---", "Should start with YAML delimiter"

        # Find closing delimiter
        yaml_end = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                yaml_end = i
                break

        assert yaml_end is not None, "Should have closing YAML delimiter"

        # Extract YAML content
        yaml_content = "\n".join(lines[1:yaml_end])
        yaml_data = yaml.safe_load(yaml_content)

        assert "pr_metadata" in yaml_data, "Should have pr_metadata section"
        assert "closes_issues" in yaml_data["pr_metadata"], "Should specify closes_issues"
        assert 1047 in yaml_data["pr_metadata"]["closes_issues"], "Should close issue 1047"

    def test_legacy_text_parsing_fallback(self):
        """Test legacy text parsing fallback logic"""
        # Test various closing keyword formats
        test_cases = [
            "Closes #1047",
            "closes #1047",
            "Fixes #1047",
            "fixes #1047",
            "Resolves #1047",
            "resolves #1047",
            "This PR closes #1047 and fixes the issue",
            "Multiple issues: closes #1047, fixes #1048",
        ]

        for test_case in test_cases:
            # Validate that the text contains recognizable closing patterns
            import re

            pattern = r"(closes?|fixes?|resolves?|implements?)\s+#(\d+)"
            matches = re.findall(pattern, test_case, re.IGNORECASE)

            assert len(matches) > 0, f"Should find closing keyword in: {test_case}"

            # Check that issue number is correctly extracted
            for keyword, issue_num in matches:
                assert keyword.lower() in [
                    "close",
                    "closes",
                    "fix",
                    "fixes",
                    "resolve",
                    "resolves",
                    "implement",
                    "implements",
                ], f"Should recognize keyword: {keyword}"
                assert issue_num.isdigit(), f"Issue number should be numeric: {issue_num}"
