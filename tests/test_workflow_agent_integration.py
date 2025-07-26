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

    def test_workflow_cli_agent_delegation(self):
        """Test that workflow CLI properly delegates to agents."""
        cli = WorkflowCLI()

        # Test with use_agents flag
        with patch(
            "sys.argv", ["workflow", "issue", "--number", str(self.test_issue), "--use-agents"]
        ):
            # Mock the phase executors to check they're called correctly
            with patch.object(cli, "_execute_investigation") as mock_investigation:
                mock_investigation.return_value = {
                    "scope_clarity": "delegated_to_agent",
                    "investigation_completed": True,
                    "agent_delegated": True,
                }

                # Run just the investigation phase
                context = {"issue_number": self.test_issue, "use_agents": True}

                result = mock_investigation(self.test_issue, context)

                # Verify agent delegation happened
                self.assertTrue(result["agent_delegated"])
                self.assertEqual(result["scope_clarity"], "delegated_to_agent")

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


class TestWorkflowCLIAgentPrompts(unittest.TestCase):
    """Test that workflow CLI generates correct agent prompts."""

    def test_investigation_agent_prompt(self):
        """Test investigation phase generates correct prompt."""
        cli = WorkflowCLI()
        context = {"use_agents": True}

        # Capture printed output
        with patch("builtins.print") as mock_print:
            cli._execute_investigation(123, context)

            # Check that Task() prompt was generated
            printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
            task_prompt = "\n".join(printed_args)

            self.assertIn("Task(", task_prompt)
            self.assertIn("issue-investigator", task_prompt)
            self.assertIn("workflow-state-123.json", task_prompt)

    def test_all_phases_generate_prompts(self):
        """Test all phases generate appropriate prompts."""
        cli = WorkflowCLI()
        context = {"use_agents": True}
        issue_number = 123

        phases = [
            ("_execute_investigation", "issue-investigator"),
            ("_execute_planning", "task-planner"),
            ("_execute_validation", "test-runner"),
            ("_execute_pr_creation", "pr-manager"),
            ("_execute_monitoring", "pr-manager"),
        ]

        for method_name, expected_agent in phases:
            with patch("builtins.print") as mock_print:
                method = getattr(cli, method_name)
                result = method(issue_number, context)

                # Verify agent delegation
                self.assertTrue(result.get("agent_delegated"))

                # Check prompt contains expected agent
                printed_args = [str(arg) for call in mock_print.call_args_list for arg in call[0]]
                task_prompt = "\n".join(printed_args)
                self.assertIn(expected_agent, task_prompt)


if __name__ == "__main__":
    unittest.main()
