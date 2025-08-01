#!/usr/bin/env python3
"""Unit tests for two-phase CI implementation in workflow_executor.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, mock_open, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_executor import WorkflowExecutor  # noqa: E402


class TestWorkflowExecutorTwoPhaseCIExtended(unittest.TestCase):
    """Extended test cases for two-phase CI implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.issue_number = 123
        self.executor = WorkflowExecutor(self.issue_number)
        
        # Mock workspace root
        self.executor.workspace_root = Path("/test/workspace")
        
        # Create base context
        self.context = {
            "validation_attempts": 0,
            "phase_outputs": {},
        }

    @patch("workflow_executor.subprocess.run")
    @patch.object(WorkflowExecutor, "_cleanup_test_environment")
    def test_execute_validation_docker_ci_success(self, mock_cleanup, mock_run):
        """Test successful Docker CI phase."""
        # Setup
        ci_script = self.executor.workspace_root / "scripts" / "run-ci-docker.sh"
        
        # Mock script exists
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            
            # Mock successful Docker CI run
            mock_docker_result = MagicMock()
            mock_docker_result.returncode = 0
            mock_docker_result.stdout = "All tests passed\nCoverage: 85.5%"
            
            # Mock coverage file read
            mock_coverage_data = {
                "percentage": "85.5%",
                "maintained": True,
                "timestamp": "2025-08-01T10:00:00"
            }
            
            mock_run.return_value = mock_docker_result
            
            with patch("builtins.open", mock_open(read_data=json.dumps(mock_coverage_data))):
                with patch("pathlib.Path.exists", return_value=True):
                    result = self.executor.execute_validation(self.context)
            
            # Verify
            self.assertTrue(result["docker_tests_passed"])
            self.assertEqual(result["coverage_percentage"], "85.5%")
            self.assertTrue(result["coverage_maintained"])
            mock_cleanup.assert_called_once()

    @patch("workflow_executor.subprocess.run")
    @patch.object(WorkflowExecutor, "_cleanup_test_environment")
    def test_execute_validation_docker_ci_failure(self, mock_cleanup, mock_run):
        """Test Docker CI phase failure handling."""
        # Mock script exists
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            
            # Mock failed Docker CI run
            mock_docker_result = MagicMock()
            mock_docker_result.returncode = 1
            mock_docker_result.stdout = "Tests failed"
            mock_docker_result.stderr = "Error: Lint check failed"
            
            mock_run.return_value = mock_docker_result
            
            # Execute
            result = self.executor.execute_validation(self.context)
            
            # Verify
            self.assertFalse(result["docker_tests_passed"])
            self.assertEqual(result["coverage_percentage"], "unknown")
            self.assertFalse(result["coverage_maintained"])

    @patch("workflow_executor.subprocess.run")
    @patch.object(WorkflowExecutor, "_cleanup_test_environment")
    def test_execute_validation_coverage_file_missing(self, mock_cleanup, mock_run):
        """Test handling when coverage file is missing."""
        with patch("pathlib.Path.exists") as mock_exists:
            # Script exists but coverage file doesn't
            def side_effect(self):
                return str(self).endswith("run-ci-docker.sh")
            
            mock_exists.side_effect = side_effect
            
            # Mock successful Docker CI run
            mock_docker_result = MagicMock()
            mock_docker_result.returncode = 0
            
            mock_run.return_value = mock_docker_result
            
            # Execute
            result = self.executor.execute_validation(self.context)
            
            # Should still pass but with unknown coverage
            self.assertTrue(result["docker_tests_passed"])
            self.assertEqual(result["coverage_percentage"], "unknown")

    @patch("workflow_executor.subprocess.run")
    @patch.object(WorkflowExecutor, "_cleanup_test_environment")
    def test_execute_validation_coverage_json_invalid(self, mock_cleanup, mock_run):
        """Test handling of invalid coverage JSON."""
        with patch("pathlib.Path.exists", return_value=True):
            # Mock successful Docker CI
            mock_docker_result = MagicMock()
            mock_docker_result.returncode = 0
            mock_run.return_value = mock_docker_result
            
            # Mock invalid JSON in coverage file
            with patch("builtins.open", mock_open(read_data="invalid json")):
                result = self.executor.execute_validation(self.context)
            
            # Should handle gracefully
            self.assertTrue(result["docker_tests_passed"])
            self.assertEqual(result["coverage_percentage"], "unknown")

    @patch("workflow_executor.subprocess.run")
    def test_execute_validation_subprocess_timeout(self, mock_run):
        """Test handling of subprocess timeout."""
        with patch("pathlib.Path.exists", return_value=True):
            # Mock timeout
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=300)
            
            # Execute
            result = self.executor.execute_validation(self.context)
            
            # Should handle timeout gracefully
            self.assertFalse(result["docker_tests_passed"])
            self.assertIn("timed out", result.get("error", "").lower())

    @patch("workflow_executor.subprocess.run")
    def test_execute_validation_subprocess_error(self, mock_run):
        """Test handling of subprocess errors."""
        with patch("pathlib.Path.exists", return_value=True):
            # Mock subprocess error
            mock_run.side_effect = subprocess.CalledProcessError(1, ["test"])
            
            # Execute
            result = self.executor.execute_validation(self.context)
            
            # Should handle error gracefully
            self.assertFalse(result["docker_tests_passed"])

    def test_execute_validation_no_ci_script(self):
        """Test validation when CI script doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.executor.execute_validation(self.context)
            
            # Should skip Docker CI but still complete
            self.assertFalse(result.get("docker_tests_passed", False))

    @patch("workflow_executor.subprocess.run")
    def test_execute_validation_increments_attempts(self, mock_run):
        """Test that validation attempts are tracked."""
        with patch("pathlib.Path.exists", return_value=True):
            mock_run.return_value = MagicMock(returncode=0)
            
            # First attempt
            result = self.executor.execute_validation(self.context)
            self.assertEqual(result["validation_attempts"], 1)
            
            # Second attempt
            result = self.executor.execute_validation(result)
            self.assertEqual(result["validation_attempts"], 2)

    @patch("workflow_executor.subprocess.run")
    def test_cleanup_test_environment(self, mock_run):
        """Test the cleanup test environment method."""
        # Mock subprocess calls
        mock_run.return_value = MagicMock(returncode=0)
        
        # Call cleanup
        self.executor._cleanup_test_environment()
        
        # Verify cleanup commands were called
        calls = mock_run.call_args_list
        
        # Should have calls to kill test processes
        self.assertTrue(any("pkill" in str(call) for call in calls))
        
    @patch("workflow_executor.subprocess.run")
    def test_cleanup_test_environment_error_handling(self, mock_run):
        """Test cleanup handles errors gracefully."""
        # Mock subprocess error
        mock_run.side_effect = subprocess.CalledProcessError(1, ["pkill"])
        
        # Should not raise exception
        try:
            self.executor._cleanup_test_environment()
        except Exception as e:
            self.fail(f"Cleanup raised unexpected exception: {e}")

    @patch("workflow_executor.subprocess.run")
    @patch("builtins.open")
    def test_execute_validation_coverage_extraction(self, mock_open_func, mock_run):
        """Test coverage percentage extraction from different formats."""
        with patch("pathlib.Path.exists", return_value=True):
            # Test various coverage data formats
            test_cases = [
                ({"percentage": "78.5%", "maintained": True}, "78.5%", True),
                ({"percentage": 78.5, "maintained": True}, "78.5", True),
                ({"coverage": "78.5%"}, "unknown", False),  # Wrong key
                ({}, "unknown", False),  # Empty data
            ]
            
            mock_run.return_value = MagicMock(returncode=0)
            
            for coverage_data, expected_pct, expected_maintained in test_cases:
                mock_open_func.return_value = mock_open(
                    read_data=json.dumps(coverage_data)
                )().__enter__()
                
                result = self.executor.execute_validation(self.context)
                
                self.assertEqual(
                    result["coverage_percentage"], 
                    expected_pct,
                    f"Failed for data: {coverage_data}"
                )
                self.assertEqual(
                    result.get("coverage_maintained", False),
                    expected_maintained,
                    f"Failed for data: {coverage_data}"
                )

    def test_execute_validation_phase_outputs_structure(self):
        """Test that phase outputs have correct structure."""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.executor.execute_validation(self.context)
            
            # Check required keys
            self.assertIn("validation_passed", result)
            self.assertIn("tests_run", result)
            self.assertIn("validation_attempts", result)
            self.assertIn("next_phase", result)
            
            # Check types
            self.assertIsInstance(result["validation_passed"], bool)
            self.assertIsInstance(result["tests_run"], bool)
            self.assertIsInstance(result["validation_attempts"], int)


if __name__ == "__main__":
    unittest.main()