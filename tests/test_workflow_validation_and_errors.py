#!/usr/bin/env python3
"""Tests for input validation and error handling in workflow modules."""

import os
import platform
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_async_executor import AsyncWorkflowExecutor  # noqa: E402
from workflow_phase_runner import PhaseRunner  # noqa: E402


class TestInputValidation(unittest.TestCase):
    """Test input validation for security."""

    def test_phase_runner_invalid_issue_number_string(self):
        """Test PhaseRunner rejects string issue numbers."""
        with self.assertRaises(ValueError) as cm:
            PhaseRunner("123")
        self.assertIn("positive integer", str(cm.exception))

    def test_phase_runner_invalid_issue_number_negative(self):
        """Test PhaseRunner rejects negative issue numbers."""
        with self.assertRaises(ValueError) as cm:
            PhaseRunner(-1)
        self.assertIn("positive integer", str(cm.exception))

    def test_phase_runner_invalid_issue_number_zero(self):
        """Test PhaseRunner rejects zero as issue number."""
        with self.assertRaises(ValueError) as cm:
            PhaseRunner(0)
        self.assertIn("positive integer", str(cm.exception))

    def test_phase_runner_valid_issue_number(self):
        """Test PhaseRunner accepts valid issue numbers."""
        # Should not raise
        runner = PhaseRunner(123)
        self.assertEqual(runner.issue_number, 123)

    def test_async_executor_invalid_issue_number_string(self):
        """Test AsyncWorkflowExecutor rejects string issue numbers."""
        with self.assertRaises(ValueError) as cm:
            AsyncWorkflowExecutor("456")
        self.assertIn("positive integer", str(cm.exception))

    def test_async_executor_invalid_issue_number_negative(self):
        """Test AsyncWorkflowExecutor rejects negative issue numbers."""
        with self.assertRaises(ValueError) as cm:
            AsyncWorkflowExecutor(-99)
        self.assertIn("positive integer", str(cm.exception))

    def test_async_executor_invalid_issue_number_zero(self):
        """Test AsyncWorkflowExecutor rejects zero as issue number."""
        with self.assertRaises(ValueError) as cm:
            AsyncWorkflowExecutor(0)
        self.assertIn("positive integer", str(cm.exception))

    def test_async_executor_valid_issue_number(self):
        """Test AsyncWorkflowExecutor accepts valid issue numbers."""
        # Should not raise
        executor = AsyncWorkflowExecutor(456)
        self.assertEqual(executor.issue_number, 456)

    def test_phase_runner_issue_number_float(self):
        """Test PhaseRunner handles float that could be int."""
        # Python allows this but we should validate
        with self.assertRaises(ValueError):
            PhaseRunner(123.5)

    def test_async_executor_issue_number_float(self):
        """Test AsyncWorkflowExecutor handles float that could be int."""
        with self.assertRaises(ValueError):
            AsyncWorkflowExecutor(456.7)


class TestWindowsCompatibility(unittest.TestCase):
    """Test Windows-specific code paths."""

    @patch("platform.system")
    @patch("os.kill")
    def test_async_executor_stop_workflow_windows(self, mock_kill, mock_platform):
        """Test stop_workflow on Windows uses taskkill."""
        mock_platform.return_value = "Windows"

        # Create executor
        executor = AsyncWorkflowExecutor(789)

        # Create PID file
        with open(executor.pid_file, "w") as f:
            f.write("12345")

        # Mock subprocess for taskkill
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = executor.stop_workflow()

            # Should use taskkill on Windows
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            self.assertEqual(cmd[0], "taskkill")
            self.assertIn("/F", cmd)
            self.assertIn("/PID", cmd)
            self.assertIn("12345", cmd)

        self.assertTrue(result)

    @patch("platform.system")
    def test_async_executor_stop_workflow_windows_taskkill_failure(self, mock_platform):
        """Test stop_workflow on Windows handles taskkill failure."""
        mock_platform.return_value = "Windows"

        executor = AsyncWorkflowExecutor(890)

        # Create PID file
        with open(executor.pid_file, "w") as f:
            f.write("54321")

        # Mock subprocess to fail
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, ["taskkill"])

            with patch("builtins.print") as mock_print:
                result = executor.stop_workflow()

            self.assertFalse(result)
            # Should print error
            printed_messages = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("Error" in msg for msg in printed_messages))

    @patch("platform.system")
    @patch("os.killpg")
    def test_async_executor_stop_workflow_linux(self, mock_killpg, mock_platform):
        """Test stop_workflow on Linux uses killpg."""
        mock_platform.return_value = "Linux"

        executor = AsyncWorkflowExecutor(901)

        # Create PID file
        with open(executor.pid_file, "w") as f:
            f.write("67890")

        # Mock successful killpg
        mock_killpg.return_value = None

        result = executor.stop_workflow()

        # Should use killpg on Linux
        mock_killpg.assert_called_once_with(67890, 15)  # SIGTERM = 15
        self.assertTrue(result)

    @patch("platform.system")
    @patch("os.killpg")
    def test_async_executor_stop_workflow_linux_no_process_group(self, mock_killpg, mock_platform):
        """Test stop_workflow on Linux falls back to kill when no process group."""
        mock_platform.return_value = "Linux"

        executor = AsyncWorkflowExecutor(902)

        # Create PID file
        with open(executor.pid_file, "w") as f:
            f.write("11111")

        # Mock killpg to fail with "No such process"
        mock_killpg.side_effect = ProcessLookupError("No such process")

        with patch("os.kill") as mock_kill:
            result = executor.stop_workflow()

            # Should fall back to regular kill
            mock_kill.assert_called_once_with(11111, 15)

        self.assertTrue(result)


class TestAsyncExecutorErrorHandling(unittest.TestCase):
    """Test error handling scenarios for AsyncWorkflowExecutor."""

    def test_start_workflow_timeout_handling(self):
        """Test handling of subprocess timeout during start."""
        executor = AsyncWorkflowExecutor(1001)

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=5)

            with patch("builtins.print") as mock_print:
                result = executor.start_workflow()

            self.assertFalse(result)
            # Should print timeout error
            printed_messages = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("timeout" in msg.lower() for msg in printed_messages))

    def test_get_logs_file_not_found(self):
        """Test get_logs when log file doesn't exist."""
        executor = AsyncWorkflowExecutor(1002)

        logs = executor.get_logs()

        self.assertEqual(logs, "Log file not found")

    def test_get_logs_permission_denied(self):
        """Test get_logs with permission error."""
        executor = AsyncWorkflowExecutor(1003)

        # Create log file
        executor.log_file.touch()

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Access denied")

            with patch("builtins.print") as mock_print:
                logs = executor.get_logs()

            # Should return error message
            self.assertIn("Error reading", logs)

    def test_stop_workflow_no_pid_file(self):
        """Test stop_workflow when PID file doesn't exist."""
        executor = AsyncWorkflowExecutor(1004)

        with patch("builtins.print") as mock_print:
            result = executor.stop_workflow()

        self.assertFalse(result)
        # Should print "not running" message
        printed_messages = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("not running" in msg.lower() for msg in printed_messages))

    def test_stop_workflow_invalid_pid_file(self):
        """Test stop_workflow with corrupted PID file."""
        executor = AsyncWorkflowExecutor(1005)

        # Create PID file with invalid content
        with open(executor.pid_file, "w") as f:
            f.write("not_a_pid")

        with patch("builtins.print") as mock_print:
            result = executor.stop_workflow()

        self.assertFalse(result)
        # Should print error
        printed_messages = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Error" in msg for msg in printed_messages))

    def test_check_status_io_error(self):
        """Test check_status with IO error reading status file."""
        executor = AsyncWorkflowExecutor(1006)

        # Create status file
        executor.status_file.touch()

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = IOError("Disk error")

            result = executor.check_status()

        self.assertEqual(result["status"], "error")
        self.assertIn("read", result["message"].lower())

    def test_update_status_disk_full(self):
        """Test update_status with disk full error."""
        executor = AsyncWorkflowExecutor(1007)

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("No space left on device")

            with patch("builtins.print") as mock_print:
                executor._update_status("test", "Testing")

            # Should print error but not crash
            printed_messages = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("space" in msg.lower() for msg in printed_messages))

    @patch("os.kill")
    def test_is_running_zombie_process(self, mock_kill):
        """Test is_running with zombie process."""
        executor = AsyncWorkflowExecutor(1008)

        # Create PID file
        with open(executor.pid_file, "w") as f:
            f.write("99999")

        # Mock kill to succeed (process exists but might be zombie)
        mock_kill.return_value = None

        result = executor._is_running()

        # Should return True (process exists)
        self.assertTrue(result)
        mock_kill.assert_called_once_with(99999, 0)


class TestPhaseRunnerErrorScenarios(unittest.TestCase):
    """Test error scenarios for PhaseRunner."""

    @patch("subprocess.run")
    def test_run_single_phase_command_not_found(self, mock_run):
        """Test handling when workflow_cli.py is not found."""
        runner = PhaseRunner(2001)

        mock_run.side_effect = FileNotFoundError("python not found")

        with patch("builtins.print") as mock_print:
            result = runner._run_single_phase(0)

        self.assertFalse(result)
        # Should print error
        printed_messages = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("not found" in msg.lower() for msg in printed_messages))

    @patch("subprocess.run")
    def test_run_single_phase_keyboard_interrupt(self, mock_run):
        """Test handling of keyboard interrupt during phase execution."""
        runner = PhaseRunner(2002)

        mock_run.side_effect = KeyboardInterrupt()

        # Should propagate KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            runner._run_single_phase(1)

    def test_cleanup_state_os_error(self):
        """Test cleanup_state with OS error."""
        runner = PhaseRunner(2003)

        # Create state file
        runner.state_file.touch()

        with patch("pathlib.Path.unlink") as mock_unlink:
            mock_unlink.side_effect = OSError("Device busy")

            with patch("builtins.print") as mock_print:
                runner._cleanup_state()

            # Should print warning
            printed_messages = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any("Could not remove" in msg for msg in printed_messages))


if __name__ == "__main__":
    unittest.main()
