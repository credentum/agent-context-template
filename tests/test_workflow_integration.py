#!/usr/bin/env python3
"""
Integration tests for complete workflow execution.
"""

import json
import os
import subprocess

# Add scripts directory to path
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from hybrid_workflow_executor import HybridWorkflowExecutor  # noqa: E402
from workflow_async_executor import AsyncWorkflowExecutor  # noqa: E402
from workflow_cli import WorkflowCLI  # noqa: E402
from workflow_enforcer import WorkflowEnforcer  # noqa: E402
from workflow_executor import WorkflowExecutor  # noqa: E402
from workflow_phase_runner import PhaseRunner  # noqa: E402


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete workflow execution."""

    def setUp(self):
        """Set up test environment."""
        self.test_issue = 9999
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        # Create necessary directories
        (Path(self.temp_dir) / "context" / "trace" / "task-templates").mkdir(parents=True)
        (Path(self.temp_dir) / "context" / "trace" / "scratchpad").mkdir(parents=True)
        (Path(self.temp_dir) / "context" / "trace" / "logs").mkdir(parents=True)
        (Path(self.temp_dir) / ".claude" / "config").mkdir(parents=True)
        (Path(self.temp_dir) / "scripts").mkdir(parents=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("subprocess.run")
    def test_complete_workflow_with_clear_scope(self, mock_run):
        """Test complete workflow execution when scope is clear."""

        # Mock responses for various commands
        def mock_subprocess_run(cmd, *args, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd

            # Mock gh issue view
            if "gh issue view" in cmd_str:
                return MagicMock(
                    stdout=json.dumps(
                        {
                            "title": "Test Issue",
                            "body": "[x] Scope is clear - Requirements are well-defined",
                            "labels": [{"name": "bug"}, {"name": "priority:high"}],
                        }
                    ),
                    stderr="",
                    returncode=0,
                )

            # Mock git commands
            elif "git branch --show-current" in cmd_str:
                return MagicMock(stdout="main\n", stderr="", returncode=0)
            elif "git checkout -b" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=0)
            elif "git add" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=0)
            elif "git commit" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=0)
            elif "git push" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=0)
            elif "git log" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=0)
            elif "git diff" in cmd_str:
                return MagicMock(stdout="", stderr="", returncode=1)  # No changes

            # Mock test/CI commands
            elif "pre-commit" in cmd_str:
                return MagicMock(stdout="All checks passed", stderr="", returncode=0)
            elif "pytest" in cmd_str:
                return MagicMock(stdout="TOTAL    100    20    80%", stderr="", returncode=0)

            # Mock gh pr create
            elif "gh pr create" in cmd_str:
                return MagicMock(
                    stdout="https://github.com/user/repo/pull/123\n", stderr="", returncode=0
                )

            # Default response
            return MagicMock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_subprocess_run

        # Execute workflow
        cli = WorkflowCLI()
        result = cli.run(["workflow-issue", str(self.test_issue)])

        # Workflow should complete successfully
        self.assertEqual(result, 0)

        # Verify state file was created
        state_file = Path(f".workflow-state-{self.test_issue}.json")
        self.assertTrue(state_file.exists())

        # Load and verify state
        with open(state_file, "r") as f:
            state = json.load(f)

        # Investigation should be skipped but marked complete
        self.assertIn("investigation", state["phases"])
        self.assertEqual(state["phases"]["investigation"]["status"], "completed")
        self.assertTrue(state["phases"]["investigation"]["outputs"]["skipped"])

    def test_workflow_executor_phases(self):
        """Test individual phase execution in workflow executor."""
        executor = WorkflowExecutor(self.test_issue)

        # Test investigation with clear scope
        context = {"scope_is_clear": True, "investigation_skipped": True}
        result = executor.execute_investigation(context)

        self.assertTrue(result["skipped"])
        self.assertEqual(result["scope_clarity"], "clear")
        self.assertTrue(result["investigation_completed"])

        # Test planning phase
        context = {}
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout='{"title": "Test Issue", "body": "Test body"}', stderr="", returncode=0
            )
            result = executor.execute_planning(context)

            self.assertTrue(result["task_template_created"])
            self.assertEqual(result["next_phase"], 2)

    def test_hybrid_workflow_executor(self):
        """Test hybrid workflow executor with specialist support."""
        executor = HybridWorkflowExecutor(self.test_issue, enable_specialists=True)

        # Test investigation with skipped phase
        context = {"investigation_skipped": True}
        result = executor.execute_investigation(context)

        self.assertTrue(result["skipped"])
        self.assertEqual(result["scope_clarity"], "clear")

    @patch("subprocess.run")
    def test_workflow_state_transitions(self, mock_run):
        """Test proper state transitions through workflow phases."""
        # Set up basic mocks
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        enforcer = WorkflowEnforcer(self.test_issue)

        # Test phase transition: skip investigation -> planning
        success, message = enforcer.skip_phase("investigation", "Scope is clear")
        self.assertTrue(success)

        # Should be able to enter planning
        can_proceed, message, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        self.assertTrue(can_proceed)

        # Complete planning
        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }
        success, message = enforcer.complete_phase("planning", outputs)
        self.assertTrue(success)

        # Should be able to enter implementation
        can_proceed, message, _ = enforcer.enforce_phase_entry("implementation", "main-claude")
        self.assertTrue(can_proceed)

    @patch("subprocess.run")
    def test_workflow_error_handling(self, mock_run):
        """Test workflow error handling and recovery."""

        # Simulate a git command failure
        def mock_failing_command(cmd, *args, **kwargs):
            if "git push" in " ".join(cmd):
                raise subprocess.CalledProcessError(1, cmd, stderr="Permission denied")
            return MagicMock(stdout="", stderr="", returncode=0)

        mock_run.side_effect = mock_failing_command

        cli = WorkflowCLI()

        # This should handle the error gracefully
        with patch("builtins.print") as mock_print:
            result = cli.run(["issue", "--number", str(self.test_issue)])

            # Should fail but with proper error message
            self.assertNotEqual(result, 0)

            # Check that error was printed
            error_printed = False
            for call in mock_print.call_args_list:
                if call[0][0] and "Command failed" in str(call[0][0]):
                    error_printed = True
                    break
            self.assertTrue(error_printed)

    def test_workflow_resume_capability(self):
        """Test workflow resume functionality."""
        enforcer = WorkflowEnforcer(self.test_issue)

        # Simulate a partially completed workflow
        enforcer.skip_phase("investigation", "Scope is clear")
        enforcer.enforce_phase_entry("planning", "task-planner")

        # Get resume point
        next_phase = enforcer.resume_workflow()
        self.assertEqual(next_phase, "planning")  # Should resume at in-progress phase

        # Complete planning
        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }
        enforcer.complete_phase("planning", outputs)

        # Now resume should return implementation
        next_phase = enforcer.resume_workflow()
        self.assertEqual(next_phase, "implementation")

    def test_workflow_compliance_report(self):
        """Test workflow compliance report generation."""
        enforcer = WorkflowEnforcer(self.test_issue)

        # Skip investigation and complete planning
        enforcer.skip_phase("investigation", "Scope is clear")
        enforcer.enforce_phase_entry("planning", "task-planner")
        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }
        enforcer.complete_phase("planning", outputs)

        # Generate report
        report = enforcer.generate_compliance_report()

        # Verify report content
        self.assertIn("COMPLIANT", report)
        self.assertIn("Investigation", report)
        self.assertIn("completed", report)
        self.assertIn("Planning", report)
        self.assertIn("completed", report)
        self.assertIn("Implementation", report)
        self.assertIn("Not started", report)

    def test_async_executor_error_handling(self):
        """Test async executor error handling paths."""
        executor = AsyncWorkflowExecutor(999)

        # Test get_logs with subprocess error
        executor.log_file.touch()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")
            result = executor.get_logs()
            self.assertIn("Error reading logs", result)

    def test_async_executor_windows_support(self):
        """Test async executor Windows-specific code paths."""
        executor = AsyncWorkflowExecutor(444)

        # Test Windows process termination
        with patch("platform.system") as mock_platform:
            mock_platform.return_value = "Windows"

            # Create test PID file
            with open(executor.pid_file, "w") as f:
                f.write("12345")

            with patch.object(executor, "_is_running", return_value=True):
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = subprocess.CalledProcessError(1, "taskkill")
                    result = executor.stop_workflow()
                    self.assertFalse(result)

                    # Verify taskkill was called
                    mock_run.assert_called_with(
                        ["taskkill", "/F", "/PID", "12345", "/T"], check=True, capture_output=True
                    )

    def test_async_executor_windows_start(self):
        """Test async executor Windows-specific start functionality."""
        executor = AsyncWorkflowExecutor(333)

        with patch("platform.system") as mock_platform:
            mock_platform.return_value = "Windows"

            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.pid = 54321
                mock_popen.return_value = mock_process

                result = executor.start_workflow(hybrid=True)
                self.assertTrue(result)

                # Verify Windows-specific flags were used
                _, kwargs = mock_popen.call_args
                self.assertIn("creationflags", kwargs)
                # Should use the correct process group creation flag
                self.assertEqual(kwargs["creationflags"], 0x00000200)

    def test_phase_runner_edge_cases(self):
        """Test phase runner edge cases and error paths."""
        runner = PhaseRunner(666, hybrid=True)

        # Test with pre-existing completed phases
        runner.completed_phases = [0, 1, 2]
        runner._save_state()

        # Create new runner and load state
        runner2 = PhaseRunner(666, hybrid=False)
        self.assertEqual(runner2.completed_phases, [])
        runner2._load_state()
        self.assertEqual(runner2.completed_phases, [0, 1, 2])

    def test_phase_runner_subprocess_stderr(self):
        """Test phase runner handling of subprocess stderr."""
        runner = PhaseRunner(99)

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = None  # No stderr
            mock_run.return_value = mock_result

            result = runner._run_single_phase(3)
            self.assertFalse(result)

    def test_concurrent_execution_handling(self):
        """Test handling of concurrent executions."""
        executor1 = AsyncWorkflowExecutor(66)
        executor2 = AsyncWorkflowExecutor(66)

        # Simulate first executor running
        with open(executor1.pid_file, "w") as f:
            f.write(str(os.getpid()))  # Current process PID

        # Second executor should detect it's already running
        result = executor2.start_workflow()
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
