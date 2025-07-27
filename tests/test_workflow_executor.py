#!/usr/bin/env python3
"""
Comprehensive unit tests for WorkflowExecutor class.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_executor import WorkflowExecutor  # noqa: E402


class TestWorkflowExecutor(unittest.TestCase):
    """Test WorkflowExecutor class methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.issue_number = 1234
        self.executor = WorkflowExecutor(self.issue_number)
        self.temp_dir = Path(tempfile.mkdtemp())
        self.executor.workspace_root = self.temp_dir

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_execute_investigation_clear_scope(self, mock_run):
        """Test investigation with clear scope."""
        context = {"scope_is_clear": True}

        result = self.executor.execute_investigation(context)

        self.assertTrue(result["investigation_completed"])
        self.assertEqual(result["scope_clarity"], "clear")
        self.assertTrue(result["skipped"])

    @patch("subprocess.run")
    def test_execute_investigation_with_issue_data(self, mock_run):
        """Test investigation with real issue data."""
        # Mock gh issue view response
        issue_data = {
            "title": "Test Issue",
            "body": "## Problem Statement\nTest problem\n## Root Cause\nTest cause",
            "labels": [{"name": "bug"}, {"name": "high"}],
        }
        mock_run.return_value = MagicMock(stdout=json.dumps(issue_data), returncode=0)

        context = {"scope_is_clear": False}
        result = self.executor.execute_investigation(context)

        self.assertTrue(result["investigation_completed"])
        self.assertTrue(result["root_cause_identified"])
        self.assertIn("investigation_report", result)

        # Verify investigation report was created
        investigations_dir = self.temp_dir / "context" / "trace" / "investigations"
        self.assertTrue(investigations_dir.exists())

    @patch("subprocess.run")
    def test_execute_investigation_gh_error(self, mock_run):
        """Test investigation with GitHub CLI error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        context = {"scope_is_clear": False}
        result = self.executor.execute_investigation(context)

        self.assertFalse(result["investigation_completed"])
        self.assertIn("error", result)

    def test_execute_planning_existing_files(self):
        """Test planning phase with existing template and scratchpad."""
        # Create existing files
        template_dir = self.temp_dir / "context" / "trace" / "task-templates"
        template_dir.mkdir(parents=True)
        template_file = template_dir / f"issue-{self.issue_number}-test.md"
        template_file.write_text("# Test Template")

        scratchpad_dir = self.temp_dir / "context" / "trace" / "scratchpad"
        scratchpad_dir.mkdir(parents=True)
        scratchpad_file = scratchpad_dir / f"2025-01-01-issue-{self.issue_number}-test.md"
        scratchpad_file.write_text("# Test Scratchpad")

        with patch("subprocess.run") as mock_run:
            # Mock gh issue view
            mock_run.return_value = MagicMock(
                stdout=json.dumps({"title": "test issue"}), returncode=0
            )

            context: Dict[str, Any] = {}
            result = self.executor.execute_planning(context)

            self.assertTrue(result["task_template_created"])
            self.assertTrue(result["scratchpad_created"])
            self.assertTrue(result["execution_plan_complete"])

    @patch("subprocess.run")
    def test_execute_implementation_new_branch(self, mock_run):
        """Test implementation with branch creation."""
        # Mock git commands
        mock_run.side_effect = [
            MagicMock(stdout="main", returncode=0),  # git branch --show-current
            MagicMock(returncode=0),  # git checkout -b
            MagicMock(stdout="", returncode=0),  # git log
        ]

        context: Dict[str, Any] = {}
        result = self.executor.execute_implementation(context)

        self.assertTrue(result["implementation_complete"])
        self.assertTrue(result["branch_created"])
        self.assertNotEqual(result["branch_name"], "main")

    @patch("subprocess.run")
    def test_execute_implementation_existing_branch(self, mock_run):
        """Test implementation on existing feature branch."""
        mock_run.side_effect = [
            MagicMock(stdout="feature/test-branch", returncode=0),  # git branch
            MagicMock(stdout="commit1\ncommit2", returncode=0),  # git log
        ]

        context: Dict[str, Any] = {}
        result = self.executor.execute_implementation(context)

        self.assertTrue(result["implementation_complete"])
        self.assertEqual(result["branch_name"], "feature/test-branch")
        self.assertTrue(result["commits_made"])

    @patch("subprocess.run")
    def test_execute_validation_with_ci_script(self, mock_run):
        """Test validation with CI script available."""
        # Create CI script
        ci_script = self.temp_dir / "scripts" / "run-ci-docker.sh"
        ci_script.parent.mkdir(parents=True)
        ci_script.write_text("#!/bin/bash\necho 'CI passed'")
        ci_script.chmod(0o755)

        # Mock pre-commit check
        mock_run.return_value = MagicMock(returncode=0)

        context: Dict[str, Any] = {}
        result = self.executor.execute_validation(context)

        self.assertTrue(result["tests_run"])
        self.assertTrue(result["ci_passed"])
        self.assertTrue(result["pre_commit_passed"])
        self.assertTrue(result["coverage_maintained"])

    @patch("subprocess.run")
    def test_execute_validation_no_precommit(self, mock_run):
        """Test validation without pre-commit available."""
        mock_run.side_effect = FileNotFoundError("pre-commit not found")

        context: Dict[str, Any] = {}
        result = self.executor.execute_validation(context)

        self.assertTrue(result["tests_run"])
        self.assertFalse(result["pre_commit_passed"])

    @patch("subprocess.run")
    def test_execute_pr_creation_success(self, mock_run):
        """Test successful PR creation."""
        mock_run.side_effect = [
            MagicMock(stdout="feature/test", returncode=0),  # git branch
            MagicMock(returncode=1),  # git rev-parse (branch not on remote)
            MagicMock(returncode=0),  # git push
            MagicMock(returncode=1),  # git diff --cached --quiet (no changes)
            MagicMock(
                stdout="https://github.com/owner/repo/pull/123", returncode=0
            ),  # gh pr create
        ]

        # Create logs directory
        logs_dir = self.temp_dir / "context" / "trace" / "logs"
        logs_dir.mkdir(parents=True)

        context: Dict[str, Any] = {}
        result = self.executor.execute_pr_creation(context)

        self.assertTrue(result["pr_created"])
        self.assertTrue(result["branch_pushed"])
        self.assertEqual(result["pr_number"], "123")

    @patch("subprocess.run")
    def test_execute_pr_creation_on_main(self, mock_run):
        """Test PR creation fails when on main branch."""
        mock_run.return_value = MagicMock(stdout="main", returncode=0)

        context: Dict[str, Any] = {}
        result = self.executor.execute_pr_creation(context)

        self.assertFalse(result["pr_created"])
        self.assertIn("error", result)

    @patch("subprocess.run")
    def test_execute_pr_creation_push_failure(self, mock_run):
        """Test PR creation with push failure."""
        mock_run.side_effect = [
            MagicMock(stdout="feature/test", returncode=0),  # git branch
            MagicMock(returncode=1),  # git rev-parse (branch not on remote)
            subprocess.CalledProcessError(1, "git push"),  # git push fails
        ]

        context: Dict[str, Any] = {}
        result = self.executor.execute_pr_creation(context)

        self.assertFalse(result["pr_created"])
        self.assertEqual(result["error"], "Push failed")

    def test_execute_monitoring_success(self):
        """Test monitoring setup."""
        context = {"pr_number": "123"}
        result = self.executor.execute_monitoring(context)

        self.assertTrue(result["pr_monitoring_active"])
        self.assertTrue(result["workflow_completed"])
        self.assertIn("monitoring_file", result)

        # Verify monitoring file was created
        monitor_file = self.temp_dir / ".pr-monitor-123.json"
        self.assertTrue(monitor_file.exists())

        # Verify monitor file contents
        monitor_data = json.loads(monitor_file.read_text())
        self.assertEqual(monitor_data["pr_number"], "123")
        self.assertEqual(monitor_data["issue_number"], self.issue_number)

    def test_execute_monitoring_no_pr_number(self):
        """Test monitoring with missing PR number."""
        context: Dict[str, Any] = {}
        result = self.executor.execute_monitoring(context)

        self.assertFalse(result["pr_monitoring_active"])
        self.assertIn("error", result)

    def test_extract_section_found(self):
        """Test extracting existing section from text."""
        text = """# Title
## Problem Statement
This is the problem.
Some more details.
## Next Section
Other content.
"""
        result = self.executor._extract_section(text, "Problem Statement")
        expected = "This is the problem.\nSome more details."
        self.assertEqual(result, expected)

    def test_extract_section_not_found(self):
        """Test extracting non-existing section from text."""
        text = "# Title\nSome content without the section."
        result = self.executor._extract_section(text, "Missing Section")
        self.assertEqual(result, "Not specified")

    def test_extract_section_multiple_names(self):
        """Test extracting section with multiple possible names."""
        text = """# Title
## Symptoms
These are symptoms.
## Other Section
Other content.
"""
        result = self.executor._extract_section(text, "Problem Statement", "Symptoms")
        self.assertEqual(result, "These are symptoms.")

    @patch("subprocess.run")
    def test_execute_planning_git_log_check(self, mock_run):
        """Test planning phase git log checking."""
        # Mock gh issue view and git log
        mock_run.side_effect = [
            MagicMock(stdout=json.dumps({"title": "test"}), returncode=0),  # gh issue
            MagicMock(
                stdout="docs(trace): add task template and execution plan for issue #1234",
                returncode=0,
            ),  # git log
        ]

        context: Dict[str, Any] = {}
        result = self.executor.execute_planning(context)

        self.assertTrue(result["documentation_committed"])

    @patch("subprocess.run")
    def test_execute_implementation_git_error(self, mock_run):
        """Test implementation with git error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        context: Dict[str, Any] = {}
        result = self.executor.execute_implementation(context)

        self.assertEqual(result["branch_name"], "unknown")
        self.assertFalse(result["commits_made"])

    @patch("subprocess.run")
    def test_execute_planning_creates_documents(self, mock_run):
        """Test planning phase creates task template and scratchpad when they don't exist."""
        mock_issue_data = {
            "title": "Fix validation error",
            "body": "Planning phase fails validation",
            "labels": [{"name": "bug"}, {"name": "workflow"}],
        }

        # Mock subprocess calls
        def side_effect(*args, **kwargs):
            cmd = args[0]
            if cmd[0] == "gh" and cmd[1] == "issue" and cmd[2] == "view":
                # Return mock issue data
                result = MagicMock()
                result.stdout = json.dumps(mock_issue_data)
                result.returncode = 0
                return result
            elif cmd[0] == "git" and cmd[1] == "log":
                # No existing commits
                result = MagicMock()
                result.stdout = ""
                result.returncode = 0
                return result
            elif cmd[0] == "git" and (cmd[1] == "add" or cmd[1] == "commit"):
                # Git operations succeed
                result = MagicMock()
                result.returncode = 0
                return result
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        context: Dict[str, Any] = {}
        result = self.executor.execute_planning(context)

        # Verify outputs
        self.assertTrue(result["task_template_created"])
        self.assertTrue(result["scratchpad_created"])
        self.assertTrue(result["documentation_committed"])

        # Verify files were created
        template_path = Path(result["task_template_path"])
        scratchpad_path = Path(result["scratchpad_path"])

        self.assertTrue(template_path.exists())
        self.assertTrue(scratchpad_path.exists())

        # Verify template content
        template_content = template_path.read_text()
        self.assertIn("Fix validation error", template_content)
        self.assertIn(f"#{self.issue_number}", template_content)
        self.assertIn("bug, workflow", template_content)

        # Verify scratchpad content
        scratchpad_content = scratchpad_path.read_text()
        self.assertIn("Fix validation error", scratchpad_content)
        self.assertIn(f"#{self.issue_number}", scratchpad_content)

    @patch("subprocess.run")
    @patch("datetime.datetime")
    def test_execute_planning_preserves_existing_files(self, mock_datetime, mock_run):
        """Test planning phase preserves existing documents and doesn't overwrite them."""
        # Fix date for consistent file naming
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-07-27"
        mock_now.isoformat.return_value = "2025-07-27T12:00:00"
        mock_datetime.now.return_value = mock_now

        # Create existing files
        template_dir = self.temp_dir / "context" / "trace" / "task-templates"
        template_dir.mkdir(parents=True)
        scratchpad_dir = self.temp_dir / "context" / "trace" / "scratchpad"
        scratchpad_dir.mkdir(parents=True)

        template_path = template_dir / f"issue-{self.issue_number}-fix-validation-error.md"
        template_path.write_text("Existing template content")
        scratchpad_path = (
            scratchpad_dir / f"2025-07-27-issue-{self.issue_number}-fix-validation-error.md"
        )
        scratchpad_path.write_text("Existing scratchpad content")

        # Mock issue data
        mock_run.side_effect = [
            MagicMock(
                stdout='{"title": "Fix validation error", "body": "Description", "labels": []}',
                returncode=0,
            ),
            MagicMock(stdout="abc123 docs(trace): add task template for issue #1234", returncode=0),
        ]

        context: Dict[str, Any] = {}
        result = self.executor.execute_planning(context)

        # Verify files weren't overwritten
        self.assertEqual(template_path.read_text(), "Existing template content")
        self.assertEqual(scratchpad_path.read_text(), "Existing scratchpad content")

        # Verify result indicates files exist and are committed
        self.assertTrue(result["task_template_created"])
        self.assertTrue(result["scratchpad_created"])
        self.assertTrue(result["documentation_committed"])


if __name__ == "__main__":
    unittest.main()
