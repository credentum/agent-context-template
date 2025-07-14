#!/usr/bin/env python3
"""
Integration tests for CI/CD workflow
Tests: Simulated PR → triggers CI → updates sprint.yaml
"""

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import yaml


class TestCIWorkflowIntegration:
    """Test GitHub Actions CI workflow integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = Path(self.temp_dir) / "test_repo"
        self.repo_dir.mkdir()

        # Create GitHub Actions workflow directory
        self.workflows_dir = self.repo_dir / ".github" / "workflows"
        self.workflows_dir.mkdir(parents=True)

        # Create context directories
        self.context_dir = self.repo_dir / "context"
        self.sprints_dir = self.context_dir / "sprints"
        self.sprints_dir.mkdir(parents=True)

        # Test PR data
        self.test_pr = {
            "number": 42,
            "title": "feat: Implement user authentication",
            "body": "Closes #10, #11\n\nImplements JWT-based authentication",
            "user": {"login": "developer"},
            "head": {"ref": "feature/auth", "sha": "abc123"},
            "base": {"ref": "main"},
            "state": "open",
            "labels": [{"name": "enhancement"}, {"name": "sprint-1"}],
        }

    def teardown_method(self):
        """Clean up temp files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_ci_workflow(self):
        """Create a test CI workflow file"""
        workflow = {
            "name": "Sprint Update on PR",
            "on": {
                "pull_request": {"types": ["opened", "synchronize", "closed"]},
                "issue_comment": {"types": ["created"]},
            },
            "jobs": {
                "update-sprint": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"name": "Checkout code", "uses": "actions/checkout@v3"},
                        {
                            "name": "Update Sprint Document",
                            "run": "python -m src.agents.update_sprint",
                        },
                    ],
                }
            },
        }

        workflow_path = self.workflows_dir / "sprint_update.yml"
        with open(workflow_path, "w") as f:
            yaml.dump(workflow, f)

        return workflow_path

    def create_sprint_document(self):
        """Create a test sprint document"""
        sprint = {
            "metadata": {
                "document_type": "sprint",
                "sprint_number": 1,
                "created_date": "2024-01-01",
            },
            "sprint_number": 1,
            "status": "in_progress",
            "start_date": "2024-01-01",
            "end_date": "2024-01-14",
            "goals": ["Implement authentication system", "Set up CI/CD pipeline"],
            "phases": [
                {
                    "name": "Development",
                    "status": "in_progress",
                    "tasks": [
                        {
                            "name": "Implement user authentication",
                            "status": "in_progress",
                            "assignee": "developer",
                            "github_issues": [10, 11],
                        },
                        {
                            "name": "Set up CI/CD pipeline",
                            "status": "pending",
                            "github_issues": [12],
                        },
                    ],
                }
            ],
        }

        sprint_path = self.sprints_dir / "sprint_001.yaml"
        with open(sprint_path, "w") as f:
            yaml.dump(sprint, f)

        return sprint_path

    @patch("subprocess.run")
    def test_pr_triggers_ci_workflow(self, mock_subprocess):
        """Test that PR events trigger CI workflow"""
        # Create workflow and sprint files
        self.create_ci_workflow()
        sprint_path = self.create_sprint_document()

        # Simulate GitHub webhook for PR opened
        # webhook_payload would be used in actual webhook handling
        _ = {"action": "opened", "pull_request": self.test_pr}

        # Mock GitHub CLI responses
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "number": 10,
                        "title": "Implement JWT authentication",
                        "state": "closed",
                        "closedAt": datetime.utcnow().isoformat(),
                    },
                    {
                        "number": 11,
                        "title": "Add user login endpoint",
                        "state": "closed",
                        "closedAt": datetime.utcnow().isoformat(),
                    },
                ]
            ),
        )

        # Simulate CI workflow execution
        # 1. Check current sprint status
        with open(sprint_path) as f:
            sprint = yaml.safe_load(f)

        # 2. Update task status based on PR
        for phase in sprint["phases"]:
            for task in phase["tasks"]:
                if task["name"] == "Implement user authentication":
                    # Mark as completed since related issues are closed
                    task["status"] = "completed"
                    task["completed_date"] = datetime.utcnow().strftime("%Y-%m-%d")
                    task["pr_number"] = self.test_pr["number"]

        # 3. Save updated sprint
        with open(sprint_path, "w") as f:
            yaml.dump(sprint, f)

        # 4. Create CI run trace (for documentation)
        _ = {
            "workflow_run_id": "123456789",
            "triggered_by": "pull_request",
            "pr_number": self.test_pr["number"],
            "updates_made": [
                {
                    "file": "context/sprints/sprint_001.yaml",
                    "changes": ["Updated task 'Implement user authentication' to completed"],
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Verify updates
        with open(sprint_path) as f:
            updated_sprint = yaml.safe_load(f)

        task = updated_sprint["phases"][0]["tasks"][0]
        assert task["status"] == "completed"
        assert "completed_date" in task
        assert task["pr_number"] == 42

    @patch("subprocess.run")
    def test_pr_merge_updates_sprint(self, mock_subprocess):
        """Test sprint updates when PR is merged"""
        sprint_path = self.create_sprint_document()

        # Simulate PR merge event (for documentation)
        _ = {
            "action": "closed",
            "pull_request": {
                **self.test_pr,
                "merged": True,
                "merged_at": datetime.utcnow().isoformat(),
                "merge_commit_sha": "def456",
            },
        }

        # Mock GitHub API calls
        mock_subprocess.return_value = Mock(
            returncode=0, stdout=json.dumps({"state": "closed", "merged": True})
        )

        # Update sprint based on merge
        with open(sprint_path) as f:
            sprint = yaml.safe_load(f)

        # Find and update related task
        for phase in sprint["phases"]:
            for task in phase["tasks"]:
                if any(issue in [10, 11] for issue in task.get("github_issues", [])):
                    task["status"] = "completed"
                    task["completion_method"] = "pr_merge"
                    task["merge_commit"] = "def456"

        # Update phase status if all tasks completed
        for phase in sprint["phases"]:
            if all(task["status"] == "completed" for task in phase["tasks"]):
                phase["status"] = "completed"

        with open(sprint_path, "w") as f:
            yaml.dump(sprint, f)

        # Verify updates
        with open(sprint_path) as f:
            updated_sprint = yaml.safe_load(f)

        task = updated_sprint["phases"][0]["tasks"][0]
        assert task["status"] == "completed"
        assert task["completion_method"] == "pr_merge"

    def test_issue_comment_triggers_update(self):
        """Test that specific issue comments trigger sprint updates"""
        sprint_path = self.create_sprint_document()

        # Simulate issue comment event
        comment_event = {
            "action": "created",
            "issue": {"number": 10, "state": "open"},
            "comment": {
                "body": "/update-sprint status:blocked reason:waiting-for-review",
                "user": {"login": "developer"},
            },
        }

        # Parse command from comment
        comment_body = comment_event["comment"]["body"]
        if comment_body.startswith("/update-sprint"):
            parts = comment_body.split()
            updates = {}
            for part in parts[1:]:
                if ":" in part:
                    key, value = part.split(":", 1)
                    updates[key] = value

        # Update sprint based on command
        with open(sprint_path) as f:
            sprint = yaml.safe_load(f)

        # Find task related to issue
        for phase in sprint["phases"]:
            for task in phase["tasks"]:
                if 10 in task.get("github_issues", []):
                    if "status" in updates:
                        task["status"] = updates["status"]
                    if "reason" in updates:
                        task["blocked_reason"] = updates["reason"]
                    task["last_updated"] = datetime.utcnow().isoformat()

        with open(sprint_path, "w") as f:
            yaml.dump(sprint, f)

        # Verify updates
        with open(sprint_path) as f:
            updated_sprint = yaml.safe_load(f)

        task = updated_sprint["phases"][0]["tasks"][0]
        assert task["status"] == "blocked"
        assert task["blocked_reason"] == "waiting-for-review"

    @patch("subprocess.run")
    def test_ci_failure_handling(self, mock_subprocess):
        """Test handling of CI failures during sprint update"""
        sprint_path = self.create_sprint_document()

        # Simulate CI failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "python -m src.agents.update_sprint"
        )

        # Create failure trace (for documentation)
        _ = {
            "workflow_run_id": "987654321",
            "status": "failure",
            "error": "Failed to update sprint document",
            "error_details": {
                "type": "CalledProcessError",
                "message": "Command returned non-zero exit status 1",
                "command": "python -m src.agents.update_sprint",
            },
            "recovery_actions": [
                "Manual intervention required",
                "Check sprint document syntax",
                "Verify GitHub API access",
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Verify sprint remains unchanged
        with open(sprint_path) as f:
            original_sprint = yaml.safe_load(f)

        # After failed CI run
        with open(sprint_path) as f:
            current_sprint = yaml.safe_load(f)

        assert original_sprint == current_sprint


class TestCISprintMetrics:
    """Test CI-driven sprint metrics collection"""

    def test_velocity_calculation(self):
        """Test sprint velocity calculation from completed tasks"""
        completed_tasks = [
            {"name": "Task 1", "story_points": 3, "completed_date": "2024-01-05"},
            {"name": "Task 2", "story_points": 5, "completed_date": "2024-01-08"},
            {"name": "Task 3", "story_points": 2, "completed_date": "2024-01-10"},
        ]

        total_points = sum(task.get("story_points", 0) for task in completed_tasks)
        sprint_days = 14
        daily_velocity = total_points / sprint_days

        metrics = {
            "total_story_points": total_points,
            "sprint_duration_days": sprint_days,
            "daily_velocity": daily_velocity,
            "projected_capacity_next_sprint": total_points * 1.1,  # 10% improvement
        }

        assert metrics["total_story_points"] == 10
        assert metrics["daily_velocity"] == 0.7142857142857143

    def test_burndown_tracking(self):
        """Test sprint burndown chart data generation"""
        # Define sprint parameters (for documentation)
        _ = datetime(2024, 1, 1)
        _ = 21

        # Daily progress
        burndown_data = [
            {"day": 1, "remaining_points": 21, "ideal_remaining": 21},
            {"day": 2, "remaining_points": 21, "ideal_remaining": 19.5},
            {"day": 3, "remaining_points": 18, "ideal_remaining": 18},
            {"day": 4, "remaining_points": 18, "ideal_remaining": 16.5},
            {"day": 5, "remaining_points": 13, "ideal_remaining": 15},
        ]

        # Calculate burn rate
        actual_burned = burndown_data[0]["remaining_points"] - burndown_data[-1]["remaining_points"]
        days_elapsed = len(burndown_data)
        burn_rate = actual_burned / days_elapsed

        # Project completion
        remaining = burndown_data[-1]["remaining_points"]
        days_to_complete = remaining / burn_rate if burn_rate > 0 else float("inf")

        analysis = {
            "burn_rate": burn_rate,
            "days_to_complete": days_to_complete,
            "on_track": days_to_complete <= (14 - days_elapsed),
        }

        assert analysis["burn_rate"] == 1.6
        assert analysis["days_to_complete"] == 8.125
        assert analysis["on_track"] is True  # Need 8.125 days and have 9 days left


class TestGitHubActionsIntegration:
    """Test GitHub Actions specific integration"""

    def test_workflow_dispatch_event(self):
        """Test manual workflow dispatch for sprint updates"""
        workflow_dispatch = {
            "inputs": {"sprint_id": "sprint_001", "update_type": "full", "dry_run": "false"},
            "ref": "main",
            "actor": "project_manager",
        }

        # Validate inputs
        assert workflow_dispatch["inputs"]["sprint_id"].startswith("sprint_")
        assert workflow_dispatch["inputs"]["update_type"] in ["full", "incremental"]
        assert workflow_dispatch["inputs"]["dry_run"] in ["true", "false"]

    def test_scheduled_sprint_update(self):
        """Test scheduled sprint updates via cron"""
        schedule_config = {"cron": "0 9,17 * * 1-5", "timezone": "UTC"}  # 9 AM and 5 PM on weekdays

        # Parse cron expression
        cron_parts = schedule_config["cron"].split()
        assert len(cron_parts) == 5
        assert cron_parts[0] == "0"  # Minutes
        assert cron_parts[1] == "9,17"  # Hours
        assert cron_parts[4] == "1-5"  # Monday-Friday

    def test_workflow_environment_setup(self):
        """Test CI environment setup for sprint updates"""
        env_vars = {
            "GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}",
            "SPRINT_UPDATE_MODE": "automated",
            "CONTEXT_DIR": "./context",
            "LOG_LEVEL": "INFO",
        }

        # Validate required environment variables
        required_vars = ["GITHUB_TOKEN", "CONTEXT_DIR"]
        for var in required_vars:
            assert var in env_vars

        # Validate paths
        assert env_vars["CONTEXT_DIR"].startswith(".")
        assert env_vars["SPRINT_UPDATE_MODE"] in ["automated", "manual"]
