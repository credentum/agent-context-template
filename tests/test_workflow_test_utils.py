#!/usr/bin/env python3
"""Unit tests for workflow_test_utils module."""

import unittest
from typing import Any, Dict

from src.utils.workflow_test_utils import (
    create_test_workflow_state,
    get_workflow_test_issue_number,
    verify_workflow_phase_outputs,
)


class TestWorkflowTestUtils(unittest.TestCase):
    """Test cases for workflow test utility functions."""

    def test_verify_workflow_phase_outputs_valid_investigation(self):
        """Test verification of valid investigation phase outputs."""
        outputs = {
            "investigation_completed": True,
            "scope_clarity": "clear",
            "extra_field": "ignored",
        }
        result = verify_workflow_phase_outputs("investigation", outputs)
        self.assertTrue(result)

    def test_verify_workflow_phase_outputs_missing_required(self):
        """Test verification fails when required outputs are missing."""
        # Missing scope_clarity
        outputs = {"investigation_completed": True}
        result = verify_workflow_phase_outputs("investigation", outputs)
        self.assertFalse(result)

    def test_verify_workflow_phase_outputs_invalid_phase(self):
        """Test verification fails for unknown phase names."""
        outputs = {"some_field": True}
        result = verify_workflow_phase_outputs("unknown_phase", outputs)
        self.assertFalse(result)

    def test_verify_workflow_phase_outputs_all_phases(self):
        """Test verification for all defined phases."""
        test_cases = {
            "investigation": {
                "valid": {"investigation_completed": True, "scope_clarity": "clear"},
                "invalid": {"investigation_completed": True},  # missing scope_clarity
            },
            "planning": {
                "valid": {
                    "task_template_created": True,
                    "scratchpad_created": True,
                    "documentation_committed": True,
                },
                "invalid": {
                    "task_template_created": True,
                    "scratchpad_created": True,
                },  # missing documentation_committed
            },
            "implementation": {
                "valid": {
                    "branch_created": True,
                    "commits_made": True,
                    "implementation_complete": True,
                },
                "invalid": {
                    "branch_created": True,
                    "commits_made": True,
                },  # missing implementation_complete
            },
            "validation": {
                "valid": {
                    "tests_run": True,
                    "ci_passed": True,
                    "quality_checks_passed": True,
                },
                "invalid": {"tests_run": True, "ci_passed": True},  # missing quality_checks_passed
            },
            "pr_creation": {
                "valid": {
                    "pr_created": True,
                    "branch_pushed": True,
                    "labels_applied": True,
                },
                "invalid": {"pr_created": True, "branch_pushed": True},  # missing labels_applied
            },
            "monitoring": {
                "valid": {
                    "documentation_verified": True,
                    "workflow_completed": True,
                },
                "invalid": {"documentation_verified": True},  # missing workflow_completed
            },
        }

        for phase, cases in test_cases.items():
            with self.subTest(phase=phase, case="valid"):
                result = verify_workflow_phase_outputs(phase, cases["valid"])
                self.assertTrue(result, f"Valid {phase} outputs should pass")

            with self.subTest(phase=phase, case="invalid"):
                result = verify_workflow_phase_outputs(phase, cases["invalid"])
                self.assertFalse(result, f"Invalid {phase} outputs should fail")

    def test_get_workflow_test_issue_number(self):
        """Test getting the test issue number."""
        issue_number = get_workflow_test_issue_number()
        self.assertEqual(issue_number, 9999)
        self.assertIsInstance(issue_number, int)

    def test_create_test_workflow_state_planning_phase(self):
        """Test creating workflow state for planning phase."""
        issue_number = 1234
        state = create_test_workflow_state(issue_number, "planning")

        # Check basic structure
        self.assertEqual(state["schema_version"], "1.0")
        self.assertEqual(state["issue_number"], issue_number)
        self.assertEqual(state["current_phase"], "planning")

        # Check phases exist
        self.assertIn("phases", state)
        self.assertIn("investigation", state["phases"])
        self.assertIn("planning", state["phases"])

        # Check investigation is completed
        self.assertEqual(state["phases"]["investigation"]["status"], "completed")
        self.assertIn("investigation_completed", state["phases"]["investigation"]["outputs"])
        self.assertTrue(state["phases"]["investigation"]["outputs"]["investigation_completed"])

        # Check planning is in_progress
        self.assertEqual(state["phases"]["planning"]["status"], "in_progress")

    def test_create_test_workflow_state_other_phase(self):
        """Test creating workflow state for non-planning phase."""
        issue_number = 5678
        state = create_test_workflow_state(issue_number, "implementation")

        # Both investigation and planning should be completed
        self.assertEqual(state["phases"]["investigation"]["status"], "completed")
        self.assertEqual(state["phases"]["planning"]["status"], "completed")

        # Check planning outputs are all present
        planning_outputs = state["phases"]["planning"]["outputs"]
        self.assertTrue(planning_outputs["task_template_created"])
        self.assertTrue(planning_outputs["scratchpad_created"])
        self.assertTrue(planning_outputs["documentation_committed"])

    def test_create_test_workflow_state_structure(self):
        """Test the complete structure of created workflow state."""
        state = create_test_workflow_state(123, "validation")

        # Verify all required top-level keys
        required_keys = ["schema_version", "issue_number", "current_phase", "phases"]
        for key in required_keys:
            self.assertIn(key, state, f"Missing required key: {key}")

        # Verify phase structure
        for phase_name in ["investigation", "planning"]:
            phase = state["phases"][phase_name]
            self.assertIn("phase_name", phase)
            self.assertIn("status", phase)
            self.assertIn("outputs", phase)
            self.assertEqual(phase["phase_name"], phase_name)

    def test_verify_workflow_phase_outputs_empty_outputs(self):
        """Test verification with empty outputs dictionary."""
        result = verify_workflow_phase_outputs("investigation", {})
        self.assertFalse(result)

    def test_verify_workflow_phase_outputs_none_values(self):
        """Test verification handles None values correctly."""
        outputs = {
            "investigation_completed": None,
            "scope_clarity": "clear",
        }
        # Should pass because keys are present (values can be None)
        result = verify_workflow_phase_outputs("investigation", outputs)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
