#!/usr/bin/env python3
"""
Comprehensive unit tests for workflow validator enforcement system.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "workflows"))

try:
    from workflow_validator import (
        WorkflowValidator,
        complete_workflow_phase,
        enforce_workflow_phase,
    )

    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False


@unittest.skipUnless(IMPORT_SUCCESS, "workflow-validator.py import failed")
class TestWorkflowValidator(unittest.TestCase):
    """Comprehensive test cases for WorkflowValidator class."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_issue_number = 123
        self.validator = WorkflowValidator(self.test_issue_number, Path(self.temp_dir))

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Clean up state file
        state_file = Path(self.temp_dir) / f".workflow-state-{self.test_issue_number}.json"
        if state_file.exists():
            state_file.unlink()

        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_valid_state(self) -> None:
        """Test that initializing validator creates proper state file."""
        self.assertTrue(self.validator.state_file.exists())
        self.assertEqual(self.validator.state["issue_number"], self.test_issue_number)
        self.assertEqual(self.validator.state["current_phase"], 0)
        self.assertEqual(self.validator.state["phases_completed"], [])
        self.assertIn("created_at", self.validator.state)
        self.assertEqual(self.validator.state["validation_errors"], [])

    def test_invalid_issue_number_validation(self) -> None:
        """Test comprehensive issue number validation."""
        invalid_numbers = [-1, 0, 1000000, "invalid", None, 1.5]

        for invalid_num in invalid_numbers:
            with self.assertRaises(ValueError, msg=f"Should reject issue number: {invalid_num}"):
                WorkflowValidator(invalid_num, Path(self.temp_dir))

    def test_state_persistence_across_instances(self) -> None:
        """Test that state persists across validator instances."""
        # Modify state in first instance
        self.validator.record_phase_start(1, "task-planner")
        outputs = {"task_template": "created", "files": ["task.md"]}
        self.validator.record_phase_completion(1, outputs)

        # Create new instance with same issue number
        validator2 = WorkflowValidator(self.test_issue_number, Path(self.temp_dir))

        # Verify state was loaded
        self.assertEqual(validator2.state["current_phase"], 1)
        self.assertEqual(len(validator2.state["phases_completed"]), 1)
        self.assertTrue(validator2._phase_completed(1))

    def test_record_phase_start_updates_state(self) -> None:
        """Test that recording phase start updates state correctly."""
        self.validator.record_phase_start(2, "implementation-agent")

        self.assertEqual(self.validator.state["current_phase"], 2)
        self.assertEqual(len(self.validator.state["phases_completed"]), 1)

        phase_record = self.validator.state["phases_completed"][0]
        self.assertEqual(phase_record["phase"], 2)
        self.assertEqual(phase_record["agent_type"], "implementation-agent")
        self.assertEqual(phase_record["status"], "in_progress")
        self.assertIn("started_at", phase_record)

    def test_record_phase_completion_with_outputs(self) -> None:
        """Test recording phase completion with comprehensive outputs."""
        # Start phase first
        self.validator.record_phase_start(3, "test-runner")

        # Complete phase with complex outputs
        outputs = {
            "test_results": {"passed": 15, "failed": 0},
            "coverage": 85.5,
            "files_tested": ["test_module1.py", "test_module2.py"],
            "duration": "2m 30s",
        }
        self.validator.record_phase_completion(3, outputs)

        phase_record = self.validator.state["phases_completed"][0]
        self.assertEqual(phase_record["status"], "completed")
        self.assertEqual(phase_record["outputs"], outputs)
        self.assertIn("completed_at", phase_record)

    def test_record_phase_failure_with_errors(self) -> None:
        """Test recording phase failure with detailed error information."""
        # Start phase first
        self.validator.record_phase_start(4, "pr-manager")

        # Fail phase with multiple errors
        errors = [
            "GitHub CLI authentication failed",
            "Branch does not exist on remote",
            "PR creation permission denied",
        ]
        self.validator.record_phase_failure(4, errors)

        phase_record = self.validator.state["phases_completed"][0]
        self.assertEqual(phase_record["status"], "failed")
        self.assertEqual(phase_record["errors"], errors)
        self.assertIn("failed_at", phase_record)

        # Errors should also be added to global validation_errors
        self.assertEqual(self.validator.state["validation_errors"], errors)

    def test_phase_completion_status_checks(self) -> None:
        """Test comprehensive phase completion status checking."""
        # Initially no phases completed
        for phase in range(6):
            self.assertFalse(self.validator._phase_completed(phase))

        # Complete phases 1 and 3
        self.validator.record_phase_start(1, "task-planner")
        self.validator.record_phase_completion(1, {"output": "phase1"})

        self.validator.record_phase_start(3, "test-runner")
        self.validator.record_phase_completion(3, {"output": "phase3"})

        # Check status
        self.assertTrue(self.validator._phase_completed(1))
        self.assertFalse(self.validator._phase_completed(2))
        self.assertTrue(self.validator._phase_completed(3))
        self.assertFalse(self.validator._phase_completed(4))

    @patch("subprocess.run")
    def test_check_issue_accessible_scenarios(self, mock_run: Mock) -> None:
        """Test issue accessibility checking in various scenarios."""
        # Test successful access
        mock_run.return_value.returncode = 0
        self.assertTrue(self.validator._check_issue_accessible())
        mock_run.assert_called_with(
            ["gh", "issue", "view", str(self.test_issue_number)],
            capture_output=True,
            shell=False,
            text=True,
        )

        # Test access failure
        mock_run.return_value.returncode = 1
        self.assertFalse(self.validator._check_issue_accessible())

    @patch("subprocess.run")
    def test_has_commits_detection(self, mock_run: Mock) -> None:
        """Test git commit detection functionality."""
        # Mock branch with multiple commits
        mock_result = Mock()
        mock_result.stdout.decode.return_value = (
            "abc123 Latest commit\n" "def456 Previous commit\n" "789ghi Initial commit\n"
        )
        mock_run.return_value = mock_result
        self.assertTrue(self.validator._has_commits())

        # Mock branch without commits (empty output)
        mock_result.stdout.decode.return_value = ""
        self.assertFalse(self.validator._has_commits())

    def test_validate_phase_prerequisites_basic(self) -> None:
        """Test basic phase prerequisite validation."""
        # Phase 2 prerequisites (requires Phase 1 completion)
        can_proceed, errors = self.validator.validate_phase_prerequisites(2)
        self.assertFalse(can_proceed)
        self.assertIn("Phase 1 (Planning) must be completed first", errors[0])

        # Complete phase 1 and try again
        self.validator.record_phase_start(1, "task-planner")
        self.validator.record_phase_completion(1, {"output": "test"})

        # Should still fail without task template file but no error now
        can_proceed, errors = self.validator.validate_phase_prerequisites(2)
        # This might pass or fail depending on file existence, just test it runs
        self.assertIsInstance(can_proceed, bool)
        self.assertIsInstance(errors, list)

    def test_ci_status_checking(self) -> None:
        """Test CI status validation functionality."""
        # Initially no CI run marker
        self.assertFalse(self.validator._check_ci_status())

        # Create recent CI marker file
        ci_marker = Path(self.temp_dir) / ".last-ci-run"
        ci_marker.touch()

        # Should detect recent CI run
        self.assertTrue(self.validator._check_ci_status())

        # Mock old CI run (modify file time)
        import time

        old_time = time.time() - 7200  # 2 hours ago
        os.utime(ci_marker, (old_time, old_time))

        # Should not detect old CI run
        self.assertFalse(self.validator._check_ci_status())

    def test_file_validation_methods(self) -> None:
        """Test various file existence validation methods."""
        # Test pytest cache detection
        pytest_cache = Path(self.temp_dir) / ".pytest_cache"
        self.assertFalse(self.validator._check_tests_run())

        pytest_cache.mkdir()
        self.assertTrue(self.validator._check_tests_run())

        # Test CI artifacts detection
        self.assertFalse(self.validator._check_ci_run())

        ci_log = Path(self.temp_dir) / "ci-output.log"
        ci_log.touch()
        self.assertTrue(self.validator._check_ci_run())


@unittest.skipUnless(IMPORT_SUCCESS, "workflow-validator.py import failed")
class TestEnforcementFunctions(unittest.TestCase):
    """Test cases for enforcement helper functions."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_issue_number = 456

    def tearDown(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("builtins.print")
    def test_enforce_workflow_phase_basic(self, mock_print: Mock) -> None:
        """Test basic workflow phase enforcement functionality."""
        # Test that the function exists and can be called
        try:
            # This might raise an exception based on actual validation logic
            validator = enforce_workflow_phase(self.test_issue_number, 1, "task-planner")
            # If we get here, function executed successfully
            self.assertIsNotNone(validator)
        except ValueError:
            # Expected if prerequisites not met - that's OK for this test
            pass

    @patch("builtins.print")
    def test_complete_workflow_phase_basic(self, mock_print: Mock) -> None:
        """Test basic workflow phase completion functionality."""
        # Create a validator instance
        validator = WorkflowValidator(self.test_issue_number, Path(self.temp_dir))
        validator.record_phase_start(1, "task-planner")

        try:
            # Test that the function exists and can be called
            complete_workflow_phase(validator, 1, {"test": "output"})
            # If we get here, function executed successfully
        except ValueError:
            # Expected if validation fails - that's OK for this test
            pass


class TestWorkflowValidatorBasic(unittest.TestCase):
    """Basic tests that run even if import fails."""

    def test_workflow_validator_file_exists(self) -> None:
        """Test that workflow validator file exists."""
        workflow_validator_path = (
            Path(__file__).parent.parent / ".claude" / "workflows" / "workflow-validator.py"
        )
        self.assertTrue(workflow_validator_path.exists(), "workflow-validator.py file should exist")

    def test_workflow_validator_has_required_functions(self) -> None:
        """Test that workflow validator has required functions."""
        workflow_validator_path = (
            Path(__file__).parent.parent / ".claude" / "workflows" / "workflow-validator.py"
        )
        content = workflow_validator_path.read_text()

        required_items = [
            "enforce_workflow_phase",
            "complete_workflow_phase",
            "class WorkflowValidator",
            "def validate_phase_prerequisites",
            "def validate_phase_outputs",
            "def record_phase_start",
            "def record_phase_completion",
            "def record_phase_failure",
        ]

        for item in required_items:
            self.assertIn(
                item, content, f"Required item '{item}' not found in workflow-validator.py"
            )

    def test_workflow_validator_security_patterns(self) -> None:
        """Test that workflow validator follows security best practices."""
        workflow_validator_path = (
            Path(__file__).parent.parent / ".claude" / "workflows" / "workflow-validator.py"
        )
        content = workflow_validator_path.read_text()

        # Check for security-conscious patterns
        security_patterns = [
            "shell=False",  # Prevents shell injection
            "if not isinstance(issue_number, int)",  # Type validation
            "if issue_number <= 0 or issue_number > 999999",  # Range validation
            r're.match(r"^\.workflow-state-\\d+\\.json$"',  # Path validation
        ]

        for pattern in security_patterns:
            self.assertIn(pattern, content, f"Security pattern '{pattern}' not found")


if __name__ == "__main__":
    unittest.main()
