#!/usr/bin/env python3
"""Unit tests for PhaseRunner."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_phase_runner import PhaseRunner  # noqa: E402


class TestPhaseRunner(unittest.TestCase):
    """Test cases for PhaseRunner."""

    def setUp(self):
        """Set up test fixtures."""
        self.issue_number = 456
        self.runner = PhaseRunner(self.issue_number, hybrid=False)
        
    def tearDown(self):
        """Clean up test files."""
        # Clean up any test state files
        state_file = Path(f".workflow-phase-state-{self.issue_number}.json")
        if state_file.exists():
            state_file.unlink()
            
    def test_init(self):
        """Test runner initialization."""
        self.assertEqual(self.runner.issue_number, 456)
        self.assertFalse(self.runner.hybrid)
        self.assertEqual(self.runner.completed_phases, [])
        self.assertEqual(
            self.runner.state_file, 
            Path(f".workflow-phase-state-{self.issue_number}.json")
        )
        
    def test_init_hybrid(self):
        """Test runner initialization with hybrid mode."""
        runner = PhaseRunner(789, hybrid=True)
        self.assertTrue(runner.hybrid)
        
    def test_phase_timeout_constant(self):
        """Test that PHASE_TIMEOUT_SECONDS is defined."""
        self.assertEqual(self.runner.PHASE_TIMEOUT_SECONDS, 90)
        
    @patch.object(PhaseRunner, "_run_single_phase")
    @patch.object(PhaseRunner, "_cleanup_state")
    @patch.object(PhaseRunner, "_save_state")
    @patch.object(PhaseRunner, "_load_state")
    def test_run_all_phases_success(self, mock_load, mock_save, mock_cleanup, mock_run):
        """Test successful execution of all phases."""
        mock_run.return_value = True
        
        result = self.runner.run_all_phases()
        
        self.assertTrue(result)
        mock_load.assert_called_once()
        self.assertEqual(mock_run.call_count, 6)  # All 6 phases
        self.assertEqual(mock_save.call_count, 6)  # Saved after each phase
        mock_cleanup.assert_called_once()
        
    @patch.object(PhaseRunner, "_run_single_phase")
    @patch.object(PhaseRunner, "_load_state")
    def test_run_all_phases_with_skip(self, mock_load, mock_run):
        """Test running phases with some skipped."""
        mock_run.return_value = True
        
        result = self.runner.run_all_phases(skip_phases=[0, 1])
        
        self.assertTrue(result)
        # Should run 4 phases (6 total - 2 skipped)
        self.assertEqual(mock_run.call_count, 4)
        
    @patch.object(PhaseRunner, "_run_single_phase")
    @patch.object(PhaseRunner, "_load_state")
    def test_run_all_phases_with_completed(self, mock_load, mock_run):
        """Test running phases when some already completed."""
        # Set up already completed phases
        self.runner.completed_phases = [0, 1]
        mock_run.return_value = True
        
        result = self.runner.run_all_phases()
        
        self.assertTrue(result)
        # Should run 4 phases (6 total - 2 completed)
        self.assertEqual(mock_run.call_count, 4)
        
    @patch.object(PhaseRunner, "_run_single_phase")
    @patch.object(PhaseRunner, "_load_state")
    @patch("builtins.print")
    def test_run_all_phases_failure(self, mock_print, mock_load, mock_run):
        """Test phase execution failure."""
        # Fail on phase 2
        mock_run.side_effect = [True, True, False]
        
        result = self.runner.run_all_phases()
        
        self.assertFalse(result)
        self.assertEqual(mock_run.call_count, 3)  # Stopped at phase 2
        
    @patch("workflow_phase_runner.subprocess.run")
    def test_run_single_phase_success(self, mock_run):
        """Test successful single phase execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = self.runner._run_single_phase(2)
        
        self.assertTrue(result)
        
        # Check command construction
        call_args = mock_run.call_args[0][0]
        self.assertIn("workflow-issue", call_args)
        self.assertIn(str(self.issue_number), call_args)
        self.assertIn("--skip-phases", call_args)
        # Should skip all phases except 2
        for i in [0, 1, 3, 4, 5]:
            self.assertIn(str(i), call_args)
        self.assertNotIn("--hybrid", call_args)  # Not in hybrid mode
        
    @patch("workflow_phase_runner.subprocess.run")
    def test_run_single_phase_hybrid(self, mock_run):
        """Test single phase execution in hybrid mode."""
        runner = PhaseRunner(self.issue_number, hybrid=True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = runner._run_single_phase(0)
        
        self.assertTrue(result)
        
        # Check that --hybrid is included
        call_args = mock_run.call_args[0][0]
        self.assertIn("--hybrid", call_args)
        
    @patch("workflow_phase_runner.subprocess.run")
    def test_run_single_phase_failure(self, mock_run):
        """Test single phase execution failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Test error"
        mock_run.return_value = mock_result
        
        with patch("builtins.print") as mock_print:
            result = self.runner._run_single_phase(3)
            
        self.assertFalse(result)
        mock_print.assert_any_call("❌ Phase failed with exit code: 1")
        mock_print.assert_any_call("Error: Test error")
        
    @patch("workflow_phase_runner.subprocess.run")
    def test_run_single_phase_timeout(self, mock_run):
        """Test single phase execution timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=[], timeout=90)
        
        with patch("builtins.print") as mock_print:
            result = self.runner._run_single_phase(4)
            
        self.assertFalse(result)
        mock_print.assert_called_with(
            f"⏱️  Phase timed out after {self.runner.PHASE_TIMEOUT_SECONDS} seconds"
        )
        
    def test_load_state_no_file(self):
        """Test loading state when file doesn't exist."""
        self.runner._load_state()
        self.assertEqual(self.runner.completed_phases, [])
        
    def test_load_state_success(self):
        """Test successfully loading state."""
        # Create test state file
        test_data = {"completed_phases": [0, 1, 2]}
        with open(self.runner.state_file, "w") as f:
            json.dump(test_data, f)
            
        self.runner._load_state()
        self.assertEqual(self.runner.completed_phases, [0, 1, 2])
        
    def test_load_state_invalid_json(self):
        """Test loading state with invalid JSON."""
        # Create test state file with invalid JSON
        with open(self.runner.state_file, "w") as f:
            f.write("invalid json")
            
        with patch("builtins.print") as mock_print:
            self.runner._load_state()
            
        self.assertEqual(self.runner.completed_phases, [])
        # Should print warning
        printed_messages = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Could not load state" in msg for msg in printed_messages))
        
    def test_save_state_success(self):
        """Test successfully saving state."""
        self.runner.completed_phases = [0, 1, 2]
        self.runner._save_state()
        
        self.assertTrue(self.runner.state_file.exists())
        
        with open(self.runner.state_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["completed_phases"], [0, 1, 2])
        
    @patch("builtins.open")
    def test_save_state_failure(self, mock_open):
        """Test save state failure."""
        mock_open.side_effect = IOError("Test error")
        
        with patch("builtins.print") as mock_print:
            self.runner._save_state()
            
        # Should print warning
        printed_messages = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("Could not save state" in msg for msg in printed_messages))
        
    def test_cleanup_state(self):
        """Test state file cleanup."""
        # Create test state file
        self.runner.state_file.touch()
        self.assertTrue(self.runner.state_file.exists())
        
        self.runner._cleanup_state()
        self.assertFalse(self.runner.state_file.exists())
        
    def test_cleanup_state_no_file(self):
        """Test cleanup when no state file exists."""
        # Should not raise error
        self.runner._cleanup_state()
        
    def test_phases_structure(self):
        """Test that PHASES has correct structure."""
        self.assertEqual(len(self.runner.PHASES), 6)
        
        for phase_name, phase_num, description in self.runner.PHASES:
            self.assertIsInstance(phase_name, str)
            self.assertIsInstance(phase_num, int)
            self.assertIsInstance(description, str)
            self.assertIn(phase_num, range(6))
            
        # Check phase order
        phase_names = [p[0] for p in self.runner.PHASES]
        expected_names = [
            "investigation", "planning", "implementation",
            "validation", "pr_creation", "monitoring"
        ]
        self.assertEqual(phase_names, expected_names)


class TestPhaseRunnerCLI(unittest.TestCase):
    """Test cases for PhaseRunner CLI."""
    
    @patch("workflow_phase_runner.PhaseRunner")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_basic(self, mock_args, mock_runner_class):
        """Test main function basic execution."""
        from workflow_phase_runner import main
        
        # Mock arguments
        mock_args.return_value = MagicMock(
            issue_number=123,
            hybrid=False,
            resume=False,
            skip_phases=None
        )
        
        # Mock runner instance
        mock_runner = MagicMock()
        mock_runner.run_all_phases.return_value = True
        mock_runner_class.return_value = mock_runner
        
        with patch("sys.exit") as mock_exit:
            main()
            
        mock_runner_class.assert_called_once_with(123, False)
        mock_runner.run_all_phases.assert_called_once_with(None)
        mock_exit.assert_called_once_with(0)
        
    @patch("workflow_phase_runner.PhaseRunner")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_resume(self, mock_args, mock_runner_class):
        """Test main function with resume flag."""
        from workflow_phase_runner import main
        
        # Mock arguments
        mock_args.return_value = MagicMock(
            issue_number=456,
            hybrid=True,
            resume=True,
            skip_phases=[0, 1]
        )
        
        # Mock runner instance
        mock_runner = MagicMock()
        mock_runner.run_all_phases.return_value = False
        mock_runner_class.return_value = mock_runner
        
        with patch("sys.exit") as mock_exit:
            main()
            
        mock_runner_class.assert_called_once_with(456, True)
        mock_runner._load_state.assert_called_once()
        mock_runner.run_all_phases.assert_called_once_with([0, 1])
        mock_exit.assert_called_once_with(1)

    def test_save_state_permission_error(self):
        """Test save state with permission error."""
        runner = PhaseRunner(543)
        runner.completed_phases = [0, 1]
        
        # Mock open to raise PermissionError
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")
            
            with patch("builtins.print") as mock_print:
                runner._save_state()
                
            # Should print warning
            printed_messages = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Could not save state" in msg for msg in printed_messages))
            
    def test_save_state_os_error(self):
        """Test save state with OSError."""
        runner = PhaseRunner(432)
        runner.completed_phases = [2, 3]
        
        # Mock open to raise OSError
        with patch("builtins.open") as mock_open_func:
            mock_open_func.side_effect = OSError("Disk full")
            
            with patch("builtins.print") as mock_print:
                runner._save_state()
                
            # Should print warning
            printed_messages = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Could not save state" in msg for msg in printed_messages))
            
    def test_cleanup_state_permission_error(self):
        """Test cleanup state with permission error."""
        runner = PhaseRunner(321)
        
        # Create state file
        runner.state_file.touch()
        
        # Mock Path.unlink to raise PermissionError  
        with patch("pathlib.Path.unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Permission denied")
            
            with patch("builtins.print") as mock_print:
                # Should not raise exception
                runner._cleanup_state()
                
            mock_unlink.assert_called_once()
            # Should print warning
            printed_messages = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Could not remove state file" in msg for msg in printed_messages))
            
    def test_load_state_permission_error(self):
        """Test load state with permission error."""
        runner = PhaseRunner(210)
        
        # Create state file that exists
        runner.state_file.touch()
        
        # Mock open to raise PermissionError
        with patch("builtins.open") as mock_open_func:
            mock_open_func.side_effect = PermissionError("Permission denied")
            
            with patch("builtins.print") as mock_print:
                runner._load_state()
                
            # Should print warning and keep empty completed_phases
            self.assertEqual(runner.completed_phases, [])
            printed_messages = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Could not load state" in msg for msg in printed_messages))
            
    def test_run_single_phase_with_stderr(self):
        """Test single phase with stderr output."""
        runner = PhaseRunner(111)
        
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Test error output"
            mock_run.return_value = mock_result
            
            with patch("builtins.print") as mock_print:
                result = runner._run_single_phase(2)
                
            self.assertFalse(result)
            # Should print both exit code and stderr
            printed_messages = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("exit code: 1" in msg for msg in printed_messages))
            self.assertTrue(any("Test error output" in msg for msg in printed_messages))


if __name__ == "__main__":
    unittest.main()
