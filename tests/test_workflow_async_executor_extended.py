#!/usr/bin/env python3
"""Extended unit tests for AsyncWorkflowExecutor to improve coverage."""

import json
import subprocess  # noqa: F401 - Used for subprocess.TimeoutExpired
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_async_executor import AsyncWorkflowExecutor  # noqa: E402


class TestAsyncWorkflowExecutorExtended(unittest.TestCase):
    """Extended test cases for AsyncWorkflowExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        self.issue_number = 999
        self.executor = AsyncWorkflowExecutor(self.issue_number)

    def tearDown(self):
        """Clean up test files."""
        # Clean up any test files created
        for suffix in [".log", ".pid", ".status"]:
            test_file = Path(f".workflow-async-{self.issue_number}{suffix}")
            if test_file.exists():
                test_file.unlink()

    @patch("workflow_async_executor.subprocess.Popen")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    @patch("platform.system")
    def test_start_workflow_windows(self, mock_platform, mock_is_running, mock_popen):
        """Test workflow start on Windows platform."""
        mock_platform.return_value = "Windows"
        mock_is_running.return_value = False
        mock_process = MagicMock()
        mock_process.pid = 54321
        mock_popen.return_value = mock_process

        with patch("builtins.open", mock_open()):
            result = self.executor.start_workflow()

        self.assertTrue(result)
        # Check Windows-specific flags
        kwargs = mock_popen.call_args[1]
        self.assertIn("creationflags", kwargs)

    @patch("workflow_async_executor.subprocess.Popen")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    @patch("platform.system")
    def test_start_workflow_linux(self, mock_platform, mock_is_running, mock_popen):
        """Test workflow start on Linux platform."""
        mock_platform.return_value = "Linux"
        mock_is_running.return_value = False
        mock_process = MagicMock()
        mock_process.pid = 54321
        mock_popen.return_value = mock_process

        with patch("builtins.open", mock_open()):
            result = self.executor.start_workflow()

        self.assertTrue(result)
        # Check Linux-specific behavior
        kwargs = mock_popen.call_args[1]
        self.assertIn("preexec_fn", kwargs)

    @patch("workflow_async_executor.subprocess.Popen")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_start_workflow_exception(self, mock_is_running, mock_popen):
        """Test workflow start with subprocess exception."""
        mock_is_running.return_value = False
        mock_popen.side_effect = Exception("Test error")

        with patch("builtins.print") as mock_print:
            result = self.executor.start_workflow()

        self.assertFalse(result)
        printed_messages = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Test error" in msg for msg in printed_messages))

    def test_check_status_with_invalid_json(self):
        """Test status check with invalid JSON in status file."""
        # Create status file with invalid JSON
        with open(self.executor.status_file, "w") as f:
            f.write("invalid json content")

        result = self.executor.check_status()
        self.assertEqual(result["status"], "error")
        self.assertIn("parse", result["message"].lower())

    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_check_status_completed_workflow(self, mock_is_running):
        """Test status check for completed workflow with cleanup."""
        mock_is_running.return_value = False

        # Create status file
        status_data = {
            "status": "completed",
            "message": "Workflow finished",
            "updated": datetime.now().isoformat(),
            "issue_number": self.issue_number,
        }
        with open(self.executor.status_file, "w") as f:
            json.dump(status_data, f)

        # Create PID file to test cleanup
        self.executor.pid_file.touch()

        result = self.executor.check_status()

        self.assertEqual(result["status"], "completed")
        # PID file should be cleaned up
        self.assertFalse(self.executor.pid_file.exists())

    def test_get_logs_with_content(self):
        """Test getting logs with actual content."""
        # Create log file with content
        log_content = "Line 1\nLine 2\nLine 3\n"
        with open(self.executor.log_file, "w") as f:
            f.write(log_content)

        logs = self.executor.get_logs(lines=2)

        self.assertIn("Line 2", logs)
        self.assertIn("Line 3", logs)
        self.assertNotIn("Line 1", logs)

    def test_get_logs_empty_file(self):
        """Test getting logs from empty file."""
        # Create empty log file
        self.executor.log_file.touch()

        logs = self.executor.get_logs()

        self.assertEqual(logs, "")

    def test_get_logs_with_encoding_error(self):
        """Test getting logs with encoding issues."""
        # Create log file with problematic content
        with open(self.executor.log_file, "wb") as f:
            f.write(b"\xff\xfe Invalid UTF-8")

        with patch("builtins.print"):
            logs = self.executor.get_logs()

        # Should handle error gracefully
        self.assertIsInstance(logs, str)

    @patch("os.kill")
    def test_stop_workflow_permission_error(self, mock_kill):
        """Test stopping workflow with permission error."""
        # Create PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("12345")

        mock_kill.side_effect = PermissionError("Access denied")

        with patch("builtins.print") as mock_print:
            result = self.executor.stop_workflow()

        self.assertFalse(result)
        printed_messages = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Access denied" in msg for msg in printed_messages))

    @patch("os.kill")
    def test_is_running_with_stale_pid(self, mock_kill):
        """Test is_running with stale PID file."""
        # Create PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("99999")

        # Process doesn't exist
        mock_kill.side_effect = ProcessLookupError()

        result = self.executor._is_running()

        self.assertFalse(result)

    def test_is_running_with_invalid_pid(self):
        """Test is_running with invalid PID in file."""
        # Create PID file with invalid content
        with open(self.executor.pid_file, "w") as f:
            f.write("not_a_number")

        result = self.executor._is_running()

        self.assertFalse(result)

    def test_update_status_with_io_error(self):
        """Test update status with IO error."""
        with patch("builtins.open") as mock_open_func:
            mock_open_func.side_effect = IOError("Disk full")

            with patch("builtins.print") as mock_print:
                # Should not raise exception
                self.executor._update_status("error", "Test")

            # Should print error message
            printed_messages = [str(c) for c in mock_print.call_args_list]
            self.assertTrue(any("Disk full" in msg for msg in printed_messages))

    def test_file_paths_consistency(self):
        """Test that all file paths use same pattern."""
        base_name = f".workflow-async-{self.issue_number}"

        self.assertEqual(str(self.executor.log_file), f"{base_name}.log")
        self.assertEqual(str(self.executor.pid_file), f"{base_name}.pid")
        self.assertEqual(str(self.executor.status_file), f"{base_name}.status")

    def test_issue_number_in_status(self):
        """Test that issue number is included in status updates."""
        self.executor._update_status("test", "Testing")

        with open(self.executor.status_file) as f:
            data = json.load(f)

        self.assertEqual(data["issue_number"], self.issue_number)

    @patch("workflow_async_executor.subprocess.Popen")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_start_workflow_command_construction(self, mock_is_running, mock_popen):
        """Test complete command construction for workflow start."""
        mock_is_running.return_value = False
        mock_process = MagicMock()
        mock_process.pid = 11111
        mock_popen.return_value = mock_process

        with patch("builtins.open", mock_open()):
            self.executor.start_workflow(hybrid=True, skip_phases=[2, 3, 4])

        # Verify command construction
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(cmd[0], "python")
        self.assertIn("workflow_phase_runner.py", cmd[1])
        self.assertEqual(cmd[2], str(self.issue_number))
        self.assertIn("--hybrid", cmd)
        self.assertIn("--skip-phases", cmd)
        # All skip phases should be in command
        for phase in ["2", "3", "4"]:
            self.assertIn(phase, cmd)

    def test_all_attribute(self):
        """Test __all__ module attribute."""
        import workflow_async_executor

        self.assertEqual(workflow_async_executor.__all__, ["AsyncWorkflowExecutor"])

    def test_datetime_format_in_status(self):
        """Test datetime format in status updates."""
        self.executor._update_status("test", "Testing")

        with open(self.executor.status_file) as f:
            data = json.load(f)

        # Should be able to parse the datetime
        updated_time = datetime.fromisoformat(data["updated"])
        self.assertIsInstance(updated_time, datetime)


class TestAsyncWorkflowExecutorPlatformSpecific(unittest.TestCase):
    """Platform-specific tests for AsyncWorkflowExecutor."""

    @patch("platform.system")
    @patch("workflow_async_executor.subprocess.CREATE_NEW_PROCESS_GROUP", 0x00000200, create=True)
    def test_windows_creation_flags(self, mock_platform):
        """Test Windows-specific process creation flags."""
        mock_platform.return_value = "Windows"

        executor = AsyncWorkflowExecutor(777)

        with patch("workflow_async_executor.subprocess.Popen") as mock_popen:
            with patch.object(executor, "_is_running", return_value=False):
                mock_process = MagicMock()
                mock_process.pid = 77777
                mock_popen.return_value = mock_process

                with patch("builtins.open", mock_open()):
                    executor.start_workflow()

        # Check that Windows flags were used
        kwargs = mock_popen.call_args[1]
        self.assertEqual(kwargs.get("creationflags"), 0x00000200)


if __name__ == "__main__":
    unittest.main()