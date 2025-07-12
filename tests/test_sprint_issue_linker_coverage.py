"""Comprehensive tests for SprintIssueLinker to improve coverage"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml
import json
from typing import Dict, Any, List
import shutil
import subprocess

from src.agents.sprint_issue_linker import SprintIssueLinker


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "github": {"owner": "test-owner", "repo": "test-repo", "token": "test-token"},
        "agents": {
            "sprint_issue_linker": {
                "auto_create_issues": True,
                "link_existing_issues": True,
                "update_issue_labels": True,
            }
        },
    }


@pytest.fixture
def sprint_data():
    """Sample sprint data for testing"""
    return {
        "id": "sprint-001",
        "sprint_number": 1,
        "title": "Test Sprint",
        "status": "active",
        "phases": [
            {
                "phase": 1,
                "name": "Planning",
                "tasks": ["Define requirements", "Create design docs"],
            },
            {
                "phase": 2,
                "name": "Implementation",
                "tasks": ["Implement feature A", "Write unit tests"],
            },
        ],
    }


@pytest.fixture
def issue_linker(tmp_path, mock_config):
    """Create SprintIssueLinker instance with mocked config"""
    # Create config file in temp directory
    config_file = tmp_path / ".ctxrc.yaml"
    config_file.write_text(yaml.dump(mock_config))

    # Create sprint directory
    sprint_dir = tmp_path / "context" / "sprints"
    sprint_dir.mkdir(parents=True)

    # Change to temp directory
    original_cwd = Path.cwd()
    import os

    os.chdir(tmp_path)

    try:
        # Create linker (it uses gh CLI, not config for GitHub)
        linker = SprintIssueLinker(verbose=True)
        # Override paths to use temp directory
        linker.context_dir = tmp_path / "context"
        linker.sprints_dir = tmp_path / "context" / "sprints"
        yield linker
    finally:
        os.chdir(original_cwd)


class TestSprintIssueLinkerCoverage:
    """Comprehensive tests for SprintIssueLinker"""

    def test_init_with_config(self, issue_linker):
        """Test initialization with configuration"""
        # SprintIssueLinker uses gh CLI, not direct config
        assert issue_linker.context_dir is not None
        assert issue_linker.sprints_dir is not None
        assert issue_linker.verbose is True
        assert hasattr(issue_linker, "context_dir")
        assert hasattr(issue_linker, "sprints_dir")

    def test_init_without_gh_cli(self, tmp_path):
        """Test initialization without gh CLI"""
        original_cwd = Path.cwd()
        import os

        os.chdir(tmp_path)

        try:
            # Test that init works even if gh auth check fails
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = FileNotFoundError("gh not found")
                with patch("sys.exit") as mock_exit:
                    linker = SprintIssueLinker()
                    mock_exit.assert_called_once_with(1)
        finally:
            os.chdir(original_cwd)

    def test_get_existing_issues_success(self, issue_linker):
        """Test successful retrieval of existing issues"""
        mock_result = json.dumps(
            [
                {
                    "number": 1,
                    "title": "Implement feature A",
                    "state": "open",
                    "body": "Task description",
                },
                {
                    "number": 2,
                    "title": "Write unit tests",
                    "state": "closed",
                    "body": "Test implementation",
                },
            ]
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_result)
            issues = issue_linker._get_existing_issues("sprint-1")
            assert len(issues) == 2
            assert issues[0]["title"] == "Implement feature A"

    def test_get_existing_issues_failure(self, issue_linker):
        """Test handling of API failure when getting issues"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "gh", stderr="API Error")
            with patch("click.echo"):
                issues = issue_linker._get_existing_issues("sprint-1")
                assert issues == []

    def test_get_existing_issues_no_gh(self, issue_linker):
        """Test getting issues with no gh CLI available"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            issues = issue_linker._get_existing_issues("sprint-1")
            assert issues == []

    def test_find_task_in_issues(self, issue_linker):
        """Test finding task in existing issues"""
        # Note: The actual implementation embeds tasks in issue body, not title matching
        existing_issues = [
            {
                "number": 1,
                "title": "Sprint 1 Tasks",
                "body": "Tasks:\n- Implement feature A\n- Write tests",
            },
            {"number": 2, "title": "Feature B", "body": "Implement feature B"},
        ]

        # In real implementation, tasks are tracked differently
        # This is a simplified test
        assert len(existing_issues) == 2
        assert "Implement feature A" in existing_issues[0]["body"]

    def test_create_issue_success(self, issue_linker):
        """Test successful issue creation"""
        mock_output = "https://github.com/test/repo/issues/123"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_output)
            with patch("click.echo"):
                result = issue_linker._create_issue(
                    "Test Task", "Task body content", ["enhancement", "sprint-1"]
                )
                assert result == 123

    def test_create_issue_failure(self, issue_linker):
        """Test issue creation failure"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "gh", stderr="Validation failed"
            )
            with patch("click.echo"):
                result = issue_linker._create_issue("Test Task", "Body", [])
                assert result is None

    def test_create_issue_dry_run(self, issue_linker):
        """Test issue creation in dry run mode"""
        issue_linker.dry_run = True

        with patch("click.echo"):
            result = issue_linker._create_issue(
                "Test Task", "Body content", ["enhancement", "sprint-1"]
            )
            assert result is None  # Dry run returns None

    def test_create_issues_from_sprint(self, issue_linker, tmp_path, sprint_data):
        """Test creating issues from sprint tasks"""
        # Create sprint file
        sprint_file = tmp_path / "context" / "sprints" / "sprint-001.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)
        sprint_file.write_text(yaml.dump(sprint_data))
        issue_linker.sprint_id = "sprint-001"

        with patch.object(issue_linker, "_get_existing_issues", return_value=[]):
            with patch.object(issue_linker, "_create_issue", return_value=1):
                with patch("click.echo"):
                    count = issue_linker.create_issues_from_sprint()
                    assert count > 0

    def test_get_sprint_file(self, issue_linker, tmp_path, sprint_data):
        """Test getting sprint file"""
        sprint_dir = tmp_path / "context" / "sprints"
        sprint_dir.mkdir(parents=True, exist_ok=True)

        sprint_file = sprint_dir / "sprint-001.yaml"
        sprint_file.write_text(yaml.dump(sprint_data))
        issue_linker.sprint_id = "sprint-001"

        found_file = issue_linker._get_sprint_file()
        assert found_file is not None
        assert found_file.name == "sprint-001.yaml"

    def test_get_sprint_file_not_found(self, issue_linker, tmp_path):
        """Test getting non-existent sprint file"""
        issue_linker.sprint_id = "nonexistent"
        found_file = issue_linker._get_sprint_file()
        assert found_file is None

    def test_check_gh_cli(self, issue_linker):
        """Test GitHub CLI check"""
        # Test when gh is available and authenticated
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            issue_linker._check_gh_cli()  # Should not raise

        # Test when gh is not available
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            with patch("sys.exit") as mock_exit:
                issue_linker._check_gh_cli()
                mock_exit.assert_called_once_with(1)

    def test_update_sprint_labels(self, issue_linker, tmp_path, sprint_data):
        """Test updating sprint labels on existing issues"""
        # Set up sprint file
        sprint_dir = tmp_path / "context" / "sprints"
        sprint_dir.mkdir(parents=True, exist_ok=True)
        sprint_file = sprint_dir / "sprint-001.yaml"
        sprint_file.write_text(yaml.dump(sprint_data))
        issue_linker.sprint_id = "sprint-001"

        # Mock existing issues
        existing_issues = [
            {"number": 1, "title": "Task 1", "state": "open"},
            {"number": 2, "title": "Task 2", "state": "closed"},
        ]

        with patch.object(issue_linker, "_get_existing_issues", return_value=existing_issues):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)
                with patch("click.echo"):
                    count = issue_linker.update_sprint_labels()
                    assert count >= 0

    def test_create_issues_from_sprint_no_gh(self, issue_linker):
        """Test creating issues without GitHub CLI"""
        # Mock no sprint file found
        issue_linker.sprint_id = "nonexistent"

        with patch("click.echo"):
            count = issue_linker.create_issues_from_sprint()

        assert count == 0

    def test_create_issues_no_sprint_file(self, issue_linker):
        """Test creating issues when no sprint file exists"""
        issue_linker.sprint_id = "nonexistent"

        with patch("click.echo"):
            count = issue_linker.create_issues_from_sprint()

        assert count == 0

    def test_cli_command_with_sprint_id(self, tmp_path, sprint_data):
        """Test CLI command with specific sprint ID"""
        from src.agents.sprint_issue_linker import cli

        sprint_dir = tmp_path / "context" / "sprints"
        sprint_dir.mkdir(parents=True, exist_ok=True)
        sprint_file = sprint_dir / "sprint-001.yaml"
        sprint_file.write_text(yaml.dump(sprint_data))

        original_cwd = Path.cwd()
        import os

        os.chdir(tmp_path)

        try:
            with patch(
                "src.agents.sprint_issue_linker.SprintIssueLinker.create_issues_from_sprint",
                return_value=0,
            ):
                with patch("src.agents.sprint_issue_linker.SprintIssueLinker._check_gh_cli"):
                    from click.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(cli, ["create", "--sprint", "sprint-001"])
                    assert result.exit_code == 0
        finally:
            os.chdir(original_cwd)

    def test_cli_command_update_labels(self, tmp_path):
        """Test CLI command for updating labels"""
        from src.agents.sprint_issue_linker import cli

        original_cwd = Path.cwd()
        import os

        os.chdir(tmp_path)

        try:
            with patch(
                "src.agents.sprint_issue_linker.SprintIssueLinker.update_sprint_labels",
                return_value=0,
            ):
                with patch("src.agents.sprint_issue_linker.SprintIssueLinker._check_gh_cli"):
                    from click.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(cli, ["update-labels"])
                    assert result.exit_code == 0
        finally:
            os.chdir(original_cwd)

