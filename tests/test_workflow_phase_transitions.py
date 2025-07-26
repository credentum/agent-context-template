#!/usr/bin/env python3
"""
Unit tests for workflow phase transitions.
"""


# Add scripts directory to path
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from agent_hooks import AgentHooks  # noqa: E402
from workflow_enforcer import WorkflowEnforcer  # noqa: E402


class TestWorkflowPhaseTransitions(unittest.TestCase):
    """Test workflow phase transitions and state management."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.issue_number = 9999
        self.state_file = Path(self.temp_dir) / f".workflow-state-{self.issue_number}.json"

        # Store reference for mock
        test_case = self

        # Create mock init function
        def mock_init(enforcer_self, issue_number, config_path=None):
            """Mock WorkflowEnforcer.__init__ to use temp directory."""
            enforcer_self.issue_number = issue_number
            enforcer_self.state_file = test_case.state_file
            enforcer_self.config_path = Path(
                config_path or ".claude/config/workflow-enforcement.yaml"
            )
            enforcer_self.config = enforcer_self._load_config()
            enforcer_self.state = enforcer_self._load_state()

        # Patch the init
        self.original_init = WorkflowEnforcer.__init__
        WorkflowEnforcer.__init__ = mock_init

    def tearDown(self):
        """Clean up test environment."""
        WorkflowEnforcer.__init__ = self.original_init
        if self.state_file.exists():
            self.state_file.unlink()

    def test_skip_phase_functionality(self):
        """Test the new skip_phase method."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Test skipping investigation phase
        success, message = enforcer.skip_phase("investigation", "Scope is clear")
        self.assertTrue(success)
        self.assertIn("skipped", message)

        # Verify phase is marked as completed with skipped flag
        self.assertIn("investigation", enforcer.state["phases"])
        phase_state = enforcer.state["phases"]["investigation"]
        self.assertEqual(phase_state["status"], "completed")
        self.assertTrue(phase_state["outputs"]["skipped"])
        self.assertEqual(phase_state["outputs"]["reason"], "Scope is clear")

    def test_skip_phase_already_completed(self):
        """Test skipping a phase that's already completed."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # First skip the phase
        enforcer.skip_phase("investigation", "Scope is clear")

        # Try to skip it again
        success, message = enforcer.skip_phase("investigation", "Another reason")
        self.assertFalse(success)
        self.assertIn("already completed", message)

    def test_skip_phase_in_progress(self):
        """Test skipping a phase that's in progress."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Start the phase
        enforcer.enforce_phase_entry("investigation", "issue-investigator")

        # Try to skip it
        success, message = enforcer.skip_phase("investigation", "Scope is clear")
        self.assertFalse(success)
        self.assertIn("already in_progress", message)

    def test_investigation_skip_with_hooks(self):
        """Test investigation phase skipping via agent hooks."""
        hooks = AgentHooks(self.issue_number)
        context = {"scope_is_clear": True}

        # Pre-phase hook should handle skipping
        can_proceed, message, context_updates = hooks.pre_phase_hook(
            "investigation", "issue-investigator", context
        )

        self.assertTrue(can_proceed)
        self.assertIn("skipped", message)
        self.assertTrue(context_updates.get("investigation_skipped", False))

        # Verify investigation phase is marked as completed
        enforcer = hooks.enforcer
        self.assertIn("investigation", enforcer.state["phases"])
        self.assertEqual(enforcer.state["phases"]["investigation"]["status"], "completed")

    def test_post_phase_hook_with_skipped_phase(self):
        """Test post-phase hook handling of skipped phases."""
        hooks = AgentHooks(self.issue_number)

        # Simulate a skipped phase output
        outputs = {"skipped": True, "scope_clarity": "clear", "investigation_completed": True}

        # Post-phase hook should handle skipped phase
        success, message = hooks.post_phase_hook("investigation", outputs)

        self.assertTrue(success)
        self.assertIn("skipped", message)

    def test_phase_transition_normal_flow(self):
        """Test normal phase transitions without skipping."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Start investigation phase
        can_proceed, message, _ = enforcer.enforce_phase_entry(
            "investigation", "issue-investigator"
        )
        self.assertTrue(can_proceed)

        # Complete investigation
        outputs = {"scope_clarity": "clear", "investigation_completed": True}
        success, message = enforcer.complete_phase("investigation", outputs)
        self.assertTrue(success)

        # Start planning phase
        can_proceed, message, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        self.assertTrue(can_proceed)

    def test_phase_dependency_enforcement(self):
        """Test that phases enforce proper dependencies."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Investigation can be skipped, so planning should be allowed
        can_proceed, message, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        self.assertTrue(can_proceed)  # Investigation is optional

        # But implementation should require planning to be completed
        can_proceed, message, _ = enforcer.enforce_phase_entry("implementation", "main-claude")
        self.assertFalse(can_proceed)
        self.assertIn("not completed", message)

    def test_phase_dependency_with_skip(self):
        """Test phase dependencies when investigation is skipped."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Skip investigation
        enforcer.skip_phase("investigation", "Scope is clear")

        # Now planning should be allowed
        can_proceed, message, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        self.assertTrue(can_proceed)

    def test_state_persistence(self):
        """Test that state persists across enforcer instances."""
        enforcer1 = WorkflowEnforcer(self.issue_number)

        # Skip investigation
        enforcer1.skip_phase("investigation", "Scope is clear")

        # Create new enforcer instance
        enforcer2 = WorkflowEnforcer(self.issue_number)

        # Verify state was loaded
        self.assertIn("investigation", enforcer2.state["phases"])
        self.assertEqual(enforcer2.state["phases"]["investigation"]["status"], "completed")

    def test_resume_workflow_with_skip(self):
        """Test resuming workflow when a phase was skipped."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Skip investigation
        enforcer.skip_phase("investigation", "Scope is clear")

        # Resume should return planning phase
        next_phase = enforcer.resume_workflow()
        self.assertEqual(next_phase, "planning")

    def test_complete_phase_validation(self):
        """Test phase completion validation."""
        enforcer = WorkflowEnforcer(self.issue_number)

        # Start planning phase
        enforcer.skip_phase("investigation", "Scope is clear")
        enforcer.enforce_phase_entry("planning", "task-planner")

        # Try to complete with missing outputs
        outputs = {
            "task_template_created": True,
            # Missing scratchpad_created and documentation_committed
        }

        success, message = enforcer.complete_phase("planning", outputs)
        self.assertFalse(success)
        self.assertIn("Missing required outputs", message)

    @patch("subprocess.run")
    def test_workflow_cli_integration(self, mock_run):
        """Test workflow CLI integration with phase transitions."""
        from workflow_cli import WorkflowCLI

        # Mock git and gh commands
        mock_run.return_value = MagicMock(
            stdout='{"body": "[x] Scope is clear"}', stderr="", returncode=0
        )

        cli = WorkflowCLI()

        # Test workflow-issue command
        cli.run(["workflow-issue", str(self.issue_number)])

        # Check that subprocess.run was called for scope check
        mock_run.assert_called()


if __name__ == "__main__":
    unittest.main()
