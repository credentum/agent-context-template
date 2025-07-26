#!/usr/bin/env python3
"""
Test workflow agent integration with enforcement system.

This module tests that:
1. Agents integrate properly with enforcement hooks
2. State persists across agent executions
3. Phase validation prevents skipping
4. The workflow-issue command works correctly
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from agent_hooks import AgentHooks, WorkflowViolationError  # noqa: E402
from workflow_cli import WorkflowCLI  # noqa: E402
from workflow_enforcer import WorkflowEnforcer  # noqa: E402


class TestWorkflowAgentIntegration(unittest.TestCase):
    """Test workflow agent integration."""

    def setUp(self):
        """Set up test environment."""
        self.test_issue = 9999
        self.state_file = Path(f".workflow-state-{self.test_issue}.json")
        self.cleanup_files = [self.state_file]

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.cleanup_files:
            if file_path.exists():
                file_path.unlink()

    def test_workflow_cli_uses_executor_directly(self):
        """Test that workflow CLI uses WorkflowExecutor directly."""
        cli = WorkflowCLI()

        # Mock WorkflowExecutor to verify it's called
        with patch("workflow_cli.WorkflowExecutor") as mock_executor_class:
            mock_executor = mock_executor_class.return_value
            mock_executor.execute_investigation.return_value = {
                "scope_clarity": "clear",
                "investigation_completed": True,
                "root_cause_identified": True,
            }

            # Run investigation phase
            context = {"issue_number": self.test_issue, "use_agents": True}
            result = cli._execute_investigation(self.test_issue, context)

            # Verify WorkflowExecutor was instantiated and called
            mock_executor_class.assert_called_once_with(self.test_issue)
            mock_executor.execute_investigation.assert_called_once_with(context)

            # Verify correct result
            self.assertTrue(result["investigation_completed"])
            self.assertEqual(result["scope_clarity"], "clear")

    def test_workflow_issue_command(self):
        """Test the workflow-issue slash command."""
        cli = WorkflowCLI()

        # Test workflow-issue command parsing
        with patch("sys.argv", ["workflow", "workflow-issue", str(self.test_issue)]):
            args = cli.parser.parse_args()
            self.assertEqual(args.command, "workflow-issue")
            self.assertEqual(args.issue_number, self.test_issue)

    def test_agent_hooks_integration(self):
        """Test that agent hooks properly integrate with enforcement."""
        # Create an enforcer and initial state
        WorkflowEnforcer(self.test_issue)  # Initialize state
        hooks = AgentHooks(self.test_issue)

        # Test pre-phase hook for investigation
        can_proceed, message, context = hooks.pre_phase_hook(
            "investigation", "issue-investigator", {"issue_number": self.test_issue}
        )

        # Should be able to proceed with investigation as first phase
        self.assertTrue(can_proceed)
        self.assertIn("Starting", message)

        # Complete investigation
        outputs = {
            "scope_clarity": "clear",
            "investigation_completed": True,
            "root_cause_identified": True,
        }
        success, message = hooks.post_phase_hook("investigation", outputs)
        self.assertTrue(success)

        # Now test planning phase
        can_proceed, message, context = hooks.pre_phase_hook(
            "planning", "task-planner", {"issue_number": self.test_issue}
        )
        self.assertTrue(can_proceed)

    def test_phase_skipping_prevention(self):
        """Test that phases cannot be skipped without completing prerequisites."""
        hooks = AgentHooks(self.test_issue)

        # Try to skip to implementation without investigation/planning
        can_proceed, message, context = hooks.pre_phase_hook(
            "implementation", "main-claude", {"issue_number": self.test_issue}
        )

        # Should not be able to proceed
        self.assertFalse(can_proceed)
        self.assertIn("prerequisites", message.lower())

    def test_state_persistence(self):
        """Test that state persists across agent executions."""
        # First agent execution
        WorkflowEnforcer(self.test_issue)  # Initialize
        hooks1 = AgentHooks(self.test_issue)

        # Complete investigation
        hooks1.pre_phase_hook("investigation", "issue-investigator", {})
        outputs = {"scope_clarity": "clear", "investigation_completed": True}
        hooks1.post_phase_hook("investigation", outputs)

        # Verify state was saved
        self.assertTrue(self.state_file.exists())

        # Second agent execution - should load existing state
        enforcer2 = WorkflowEnforcer(self.test_issue)
        state = enforcer2.get_current_state()

        # Verify investigation is marked complete
        self.assertIn("investigation", state["phases"])
        self.assertEqual(state["phases"]["investigation"]["status"], "completed")

    def test_workflow_cli_with_enforcement(self):
        """Test workflow CLI with enforcement enabled."""
        # Create a mock subprocess to avoid actual command execution
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0

            cli = WorkflowCLI()
            # Test direct invocation without agents (simulation mode)
            result = cli.run(["issue", "--number", str(self.test_issue), "--skip-phases", "0"])

            # Should complete successfully
            self.assertEqual(result, 0)

    def test_agent_output_validation(self):
        """Test that agent outputs are validated."""
        hooks = AgentHooks(self.test_issue)

        # Complete investigation first
        hooks.pre_phase_hook("investigation", "issue-investigator", {})
        hooks.post_phase_hook(
            "investigation", {"scope_clarity": "clear", "investigation_completed": True}
        )

        # Try to complete planning with missing outputs
        hooks.pre_phase_hook("planning", "task-planner", {})

        # Missing required outputs
        incomplete_outputs = {"task_template_created": True}  # Missing other required outputs

        with self.assertRaises(WorkflowViolationError):
            success, message = hooks.post_phase_hook("planning", incomplete_outputs)

    def test_workflow_resume(self):
        """Test workflow resume functionality."""
        enforcer = WorkflowEnforcer(self.test_issue)

        # Simulate partial completion
        enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        enforcer.state["phases"]["planning"] = {
            "status": "completed",
            "outputs": {"task_template_created": True},
        }
        enforcer.state["current_phase"] = "implementation"
        enforcer._save_state()

        # Resume should identify implementation as next phase
        next_phase = enforcer.resume_workflow()
        self.assertEqual(next_phase, "implementation")


class TestWorkflowCLIExecutorIntegration(unittest.TestCase):
    """Test that workflow CLI integrates correctly with WorkflowExecutor."""

    def test_all_phases_use_executor(self):
        """Test all phases use WorkflowExecutor directly."""
        cli = WorkflowCLI()
        context = {"use_agents": True}
        issue_number = 123

        phases = [
            ("_execute_investigation", "execute_investigation"),
            ("_execute_planning", "execute_planning"),
            ("_execute_implementation", "execute_implementation"),
            ("_execute_validation", "execute_validation"),
            ("_execute_pr_creation", "execute_pr_creation"),
            ("_execute_monitoring", "execute_monitoring"),
        ]

        for method_name, executor_method in phases:
            with patch("workflow_cli.WorkflowExecutor") as mock_executor_class:
                mock_executor = mock_executor_class.return_value
                # Mock the executor method to return success
                getattr(mock_executor, executor_method).return_value = {
                    "success": True,
                    "phase_completed": True,
                }

                method = getattr(cli, method_name)
                result = method(issue_number, context)

                # Verify WorkflowExecutor was instantiated
                mock_executor_class.assert_called_once_with(issue_number)

                # Verify the correct executor method was called
                getattr(mock_executor, executor_method).assert_called_once_with(context)

                # Verify result indicates success
                self.assertTrue(result.get("success") or result.get("phase_completed"))

    def test_executor_instantiation_with_issue_number(self):
        """Test that WorkflowExecutor is instantiated with correct issue number."""
        cli = WorkflowCLI()
        test_issue = 456

        with patch("workflow_cli.WorkflowExecutor") as mock_executor_class:
            mock_executor = mock_executor_class.return_value
            mock_executor.execute_planning.return_value = {"planning_complete": True}

            cli._execute_planning(test_issue, {})

            # Verify WorkflowExecutor was called with the correct issue number
            mock_executor_class.assert_called_once_with(test_issue)


if __name__ == "__main__":
    unittest.main()
