"""Comprehensive tests for UpdateSprintAgent to improve coverage"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import json
from typing import Dict, Any, List
import subprocess
import shutil

from src.agents.update_sprint import SprintUpdater


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "github": {"owner": "test-owner", "repo": "test-repo", "token": "test-token"},
        "agents": {
            "update_sprint": {
                "auto_transition_phases": True,
                "update_metrics": True,
                "create_issues": True,
                "sprint_duration_days": 14,
            }
        },
    }


@pytest.fixture
def sprint_data():
    """Sample sprint data for testing"""
    return {
        "schema_version": "1.1.0",
        "document_type": "sprint",
        "id": "sprint-001",
        "sprint_number": 1,
        "title": "Test Sprint",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "status": "active",
        "phases": [
            {
                "phase": 1,
                "name": "Planning",
                "status": "completed",
                "tasks": ["Define requirements", "Create design docs"],
                "duration_days": 3,
            },
            {
                "phase": 2,
                "name": "Implementation",
                "status": "in_progress",
                "tasks": ["Implement feature A", "Implement feature B", "Write tests"],
                "duration_days": 7,
            },
            {
                "phase": 3,
                "name": "Testing",
                "status": "pending",
                "tasks": ["Integration testing", "Performance testing"],
                "duration_days": 4,
            },
        ],
        "team": [
            {"agent": "code_agent", "role": "developer"},
            {"agent": "test_agent", "role": "tester"},
        ],
        "metrics": {"velocity": 0, "completion_rate": 0, "issues_closed": 0},
    }


@pytest.fixture
def update_agent(tmp_path, mock_config):
    """Create SprintUpdater instance with mocked config"""
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
        # Create agent (it will load .ctxrc.yaml from current directory)
        agent = SprintUpdater(verbose=True)
        # Override paths to use temp directory
        agent.context_dir = tmp_path / "context"
        agent.sprints_dir = tmp_path / "context" / "sprints"
        yield agent
    finally:
        os.chdir(original_cwd)


class TestUpdateSprintAgentCoverage:
    """Comprehensive tests for SprintUpdater"""

    def test_init_with_github_config(self, update_agent):
        """Test initialization with GitHub configuration"""
        # Check that config was loaded
        assert update_agent.config is not None
        assert "github" in update_agent.config
        assert update_agent.config["github"]["owner"] == "test-owner"

    def test_init_without_config(self, tmp_path):
        """Test initialization without configuration file"""
        original_cwd = Path.cwd()
        import os

        os.chdir(tmp_path)

        try:
            # Don't create .ctxrc.yaml - it should handle missing config
            agent = SprintUpdater(verbose=True)
            # Check attributes exist even without config
            assert hasattr(agent, "config")
        finally:
            os.chdir(original_cwd)

    def test_get_github_issues_success(self, update_agent):
        """Test successful GitHub issues retrieval"""
        # Mock gh CLI command
        mock_result = json.dumps(
            [
                {"number": 1, "title": "Issue 1", "state": "open"},
                {"number": 2, "title": "Issue 2", "state": "closed"},
            ]
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=mock_result)
            issues = update_agent._get_github_issues()
            assert len(issues) == 2
            assert issues[0]["number"] == 1

    def test_get_github_issues_failure(self, update_agent):
        """Test GitHub issues retrieval failure"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Error: Authentication failed")
            mock_run.side_effect = subprocess.CalledProcessError(1, "gh")
            issues = update_agent._get_github_issues()
            assert issues == []

    def test_get_github_issues_no_gh_cli(self, update_agent):
        """Test GitHub issues when gh CLI is not available"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            issues = update_agent._get_github_issues()
            assert issues == []

    def test_update_phase_status(self, update_agent, sprint_data):
        """Test phase status updates based on task completion"""
        # Mock GitHub issues
        issues = [
            {"number": 1, "title": "Define requirements", "state": "CLOSED"},
            {"number": 2, "title": "Create design docs", "state": "CLOSED"},
        ]

        # Ensure phase starts as in_progress
        phases = sprint_data["phases"]
        phases[0]["status"] = "in_progress"

        updated = update_agent._update_phase_status(phases, issues)

        # First phase should be marked completed (all tasks closed)
        assert phases[0]["status"] == "completed"
        assert updated is True

    def test_match_task_to_issue(self, update_agent):
        """Test task to issue matching logic"""
        # Exact match
        assert update_agent._match_task_to_issue("Write unit tests", "Write unit tests") is True

        # Case insensitive match
        assert update_agent._match_task_to_issue("write unit tests", "Write Unit Tests") is True

        # Partial match with extra words - needs exact word sequence
        assert (
            update_agent._match_task_to_issue(
                "Write unit tests", "[Sprint 1] Write unit tests for module"
            )
            is True
        )

        # No match - different words
        assert update_agent._match_task_to_issue("Deploy app", "Write tests") is False

        # No match - substring but not exact word sequence
        assert update_agent._match_task_to_issue("Write tests", "Write unit tests") is False

    def test_update_sprint_status(self, update_agent, sprint_data):
        """Test sprint status update functionality"""
        # Test with all phases completed
        for phase in sprint_data["phases"]:
            phase["status"] = "completed"

        updated = update_agent._update_sprint_status(sprint_data)
        assert sprint_data["status"] == "completed"
        assert updated is True

        # Test with phases in progress
        sprint_data["phases"][0]["status"] = "completed"
        sprint_data["phases"][1]["status"] = "in_progress"
        sprint_data["status"] = "active"

        updated = update_agent._update_sprint_status(sprint_data)
        assert sprint_data["status"] == "active"
        assert updated is False

    def test_check_gh_cli(self, update_agent):
        """Test GitHub CLI availability check"""
        # Test when gh is available
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            with patch("click.echo"):
                update_agent._check_gh_cli()  # Should not raise

        # Test when gh is not available
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("gh not found")
            with patch("click.echo"):
                update_agent._check_gh_cli()  # Should handle gracefully

    def test_get_current_sprint(self, update_agent, tmp_path, sprint_data):
        """Test getting current sprint file"""
        # Create sprint file
        sprint_file = tmp_path / "context" / "sprints" / "sprint-001.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)
        sprint_file.write_text(yaml.dump(sprint_data))

        # Test with specific sprint ID
        update_agent.sprint_id = "sprint-001"
        current = update_agent._get_current_sprint()
        assert current is not None
        assert current.name == "sprint-001.yaml"

    def test_get_current_sprint_auto(self, update_agent, tmp_path, sprint_data):
        """Test auto-detecting current sprint"""
        # Create multiple sprint files
        for i in range(1, 4):
            sprint_file = tmp_path / "context" / "sprints" / f"sprint-{i:03d}.yaml"
            data = sprint_data.copy()
            data["sprint_number"] = i
            data["status"] = "completed" if i < 3 else "active"
            sprint_file.write_text(yaml.dump(data))

        # Should find the active sprint
        update_agent.sprint_id = None
        current = update_agent._get_current_sprint()
        assert current is not None
        assert "sprint-003" in current.name

    def test_update_timestamps(self, update_agent, sprint_data):
        """Test updating timestamps in sprint data"""
        original_date = sprint_data.get("last_modified")

        updated = update_agent._update_timestamps(sprint_data)
        assert updated is True
        assert "last_modified" in sprint_data
        assert sprint_data["last_modified"] != original_date

    def test_update_sprint_full_workflow(self, update_agent, tmp_path, sprint_data):
        """Test complete sprint update workflow"""
        # Save initial sprint
        sprint_file = tmp_path / "context" / "sprints" / "sprint-001.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)
        sprint_file.write_text(yaml.dump(sprint_data))
        update_agent.sprint_id = "sprint-001"

        with patch.object(update_agent, "_get_github_issues") as mock_issues:
            mock_issues.return_value = [
                {"number": 1, "title": "Define requirements", "state": "CLOSED"},
                {"number": 2, "title": "Create design docs", "state": "CLOSED"},
                {"number": 3, "title": "Implement feature A", "state": "CLOSED"},
                {"number": 4, "title": "Implement feature B", "state": "CLOSED"},
                {"number": 5, "title": "Write tests", "state": "CLOSED"},
            ]

            with patch("click.echo"):
                result = update_agent.update_sprint()

        assert result is True
        assert len(update_agent.updates_made) > 0

    def test_create_next_sprint(self, update_agent, tmp_path, sprint_data):
        """Test creating next sprint when current completes"""
        # Set up completed sprint
        sprint_data["status"] = "completed"
        sprint_data["sprint_number"] = 1

        with patch("click.echo"):
            update_agent._create_next_sprint(sprint_data)

        # Check if next sprint file was created
        next_sprint = tmp_path / "context" / "sprints" / "sprint-002.yaml"
        assert next_sprint.exists()

        # Verify next sprint data
        with open(next_sprint) as f:
            next_data = yaml.safe_load(f)
        assert next_data["sprint_number"] == 2
        assert next_data["status"] == "planning"

    def test_generate_report(self, update_agent, tmp_path, sprint_data):
        """Test sprint report generation"""
        # Create sprint file
        sprint_file = tmp_path / "context" / "sprints" / "sprint-001.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)
        sprint_file.write_text(yaml.dump(sprint_data))
        update_agent.sprint_id = "sprint-001"

        report = update_agent.generate_report()

        assert "Test Sprint" in report
        assert "Planning" in report  # Phase name
        assert "Implementation" in report  # Phase name

    def test_error_handling_in_update(self, update_agent, tmp_path):
        """Test error handling during sprint update"""
        # Test with no sprint files
        update_agent.sprint_id = "nonexistent"

        with patch("click.echo"):
            result = update_agent.update_sprint()

        assert result is False

    def test_cli_command(self, tmp_path, sprint_data):
        """Test CLI command execution"""
        from src.agents.update_sprint import cli

        # Set up test environment
        config_path = tmp_path / ".ctxrc.yaml"
        config_path.write_text(yaml.dump({"agents": {"update_sprint": {}}}))

        sprint_file = tmp_path / "context" / "sprints" / "sprint-001.yaml"
        sprint_file.parent.mkdir(parents=True, exist_ok=True)
        sprint_file.write_text(yaml.dump(sprint_data))

        original_cwd = Path.cwd()
        import os

        os.chdir(tmp_path)

        try:
            with patch("subprocess.run") as mock_run:
                # Configure subprocess mock to return empty JSON list
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "[]"

                with patch("click.echo"):
                    # Test with sprint ID
                    from click.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(cli, ["update", "--sprint", "sprint-001"])
                    assert result.exit_code == 0
        finally:
            os.chdir(original_cwd)
