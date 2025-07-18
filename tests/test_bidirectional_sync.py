#!/usr/bin/env python3
"""
Test script for bidirectional sprint workflow validation
"""

import json
import subprocess
from pathlib import Path

import pytest
import yaml


class TestBidirectionalWorkflow:
    """Test bidirectional sync between sprint YAML and GitHub issues"""

    def setup_method(self):
        """Setup test fixtures"""
        self.sprint_file = Path("context/sprints/sprint-4.1.yaml")
        self.test_task_title = "Bidirectional Workflow Validation Test"
        self.test_issue_number = 116
        self.original_sprint_data = None

    def test_yaml_to_github_link_exists(self):
        """Test: Sprint YAML task is linked to GitHub issue #116"""
        # Load sprint data
        with open(self.sprint_file, "r") as f:
            sprint_data = yaml.safe_load(f)

        # Find the test task in Phase 8
        phase_8 = None
        for phase in sprint_data.get("phases", []):
            if phase.get("phase") == 8:
                phase_8 = phase
                break

        assert phase_8 is not None, "Phase 8 not found in sprint"

        # Find the test task
        test_task = None
        for task in phase_8.get("tasks", []):
            if task.get("title") == self.test_task_title:
                test_task = task
                break

        assert test_task is not None, "Test task not found in Phase 8"
        assert (
            test_task.get("github_issue") == self.test_issue_number
        ), f"Task not linked to issue #{self.test_issue_number}"

    def test_github_issue_exists_and_open(self):
        """Test: GitHub issue #116 exists and is open"""
        try:
            result = subprocess.run(
                ["gh", "issue", "view", str(self.test_issue_number), "--json", "state,title"],
                capture_output=True,
                text=True,
                check=True,
            )
            issue_data = json.loads(result.stdout)

            assert issue_data["state"] == "OPEN", "Issue should be open"
            assert (
                "Bidirectional Workflow Validation Test" in issue_data["title"]
            ), "Issue title should contain test task name"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("GitHub CLI not available (CI environment)")

    def test_issue_labels_match_task_labels(self):
        """Test: GitHub issue labels match task labels"""
        # Get issue labels
        try:
            result = subprocess.run(
                ["gh", "issue", "view", str(self.test_issue_number), "--json", "labels"],
                capture_output=True,
                text=True,
                check=True,
            )
            issue_data = json.loads(result.stdout)
            github_labels = {label["name"] for label in issue_data["labels"]}
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("GitHub CLI not available (CI environment)")

        # Get task labels from sprint YAML
        with open(self.sprint_file, "r") as f:
            sprint_data = yaml.safe_load(f)

        for phase in sprint_data.get("phases", []):
            if phase.get("phase") == 8:
                for task in phase.get("tasks", []):
                    if task.get("title") == self.test_task_title:
                        # Check that core labels are present
                        core_labels = {
                            "sprint-current",
                            "phase:4.1",
                            "component:testing",
                            "priority:high",
                            "type:test",
                            "automation",
                        }
                        missing_labels = core_labels - github_labels

                        assert (
                            len(missing_labels) == 0
                        ), f"Missing labels on GitHub issue: {missing_labels}"
                        break

    def test_sync_command_recognizes_linked_task(self):
        """Test: Sprint sync command recognizes task is already linked"""
        # Run sync in dry-run mode
        result = subprocess.run(
            [
                "python",
                "-m",
                "src.agents.sprint_issue_linker",
                "sync",
                "--sprint",
                "sprint-4.1",
                "--dry-run",
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        # Should not try to create issue #116 again
        assert result.returncode == 0, f"Sync command failed: {result.stderr}"
        assert (
            "Bidirectional Workflow Validation Test" not in result.stdout
        ), "Sync should not try to create issue #116 again"

    def test_validate_test_scenarios_structure(self):
        """Test: Validate that test scenarios are properly structured"""
        # Get issue body
        try:
            result = subprocess.run(
                ["gh", "issue", "view", str(self.test_issue_number), "--json", "body"],
                capture_output=True,
                text=True,
                check=True,
            )
            issue_data = json.loads(result.stdout)
            body = issue_data["body"]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("GitHub CLI not available (CI environment)")

        # Check that test scenarios are present
        expected_scenarios = [
            "Task created in YAML generates GitHub issue",
            "GitHub issue status updates reflect in YAML",
            "Task completion in YAML closes GitHub issue",
            "Label changes sync bidirectionally",
            "Task removal from YAML closes GitHub issue",
        ]

        for scenario in expected_scenarios:
            assert scenario in body, f"Missing test scenario: {scenario}"

    def test_bidirectional_sync_readiness(self):
        """Test: System is ready for bidirectional sync testing"""
        # Verify sprint issue linker is available
        result = subprocess.run(
            ["python", "-m", "src.agents.sprint_issue_linker", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Sprint issue linker not available"

        # Verify GitHub CLI is authenticated (skip in CI)
        try:
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if result.returncode != 0:
                pytest.skip("GitHub CLI not authenticated (CI environment)")
        except FileNotFoundError:
            pytest.skip("GitHub CLI not available (CI environment)")

        # Verify sprint file exists and is valid
        assert self.sprint_file.exists(), "Sprint file not found"

        with open(self.sprint_file, "r") as f:
            sprint_data = yaml.safe_load(f)

        assert sprint_data is not None, "Sprint file not valid YAML"
        assert "phases" in sprint_data, "Sprint file missing phases"


if __name__ == "__main__":
    # Run tests manually
    test = TestBidirectionalWorkflow()
    test.setup_method()

    print("Running bidirectional sync validation tests...")

    try:
        test.test_yaml_to_github_link_exists()
        print("✓ YAML to GitHub link exists")

        test.test_github_issue_exists_and_open()
        print("✓ GitHub issue exists and is open")

        test.test_issue_labels_match_task_labels()
        print("✓ Issue labels match task labels")

        test.test_sync_command_recognizes_linked_task()
        print("✓ Sync command recognizes linked task")

        test.test_validate_test_scenarios_structure()
        print("✓ Test scenarios properly structured")

        test.test_bidirectional_sync_readiness()
        print("✓ System ready for bidirectional sync")

        print("\n🎉 All bidirectional sync validation tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
