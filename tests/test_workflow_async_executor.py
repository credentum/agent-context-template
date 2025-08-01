#!/usr/bin/env python3
"""Unit tests for AsyncWorkflowExecutor."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_async_executor import AsyncWorkflowExecutor  # noqa: E402


class TestAsyncWorkflowExecutor(unittest.TestCase):
    """Test cases for AsyncWorkflowExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        self.issue_number = 123
        self.executor = AsyncWorkflowExecutor(self.issue_number)
        
    def tearDown(self):
        """Clean up test files."""
        # Clean up any test files created
        for suffix in [".log", ".pid", ".status"]:
            test_file = Path(f".workflow-async-{self.issue_number}{suffix}")
            if test_file.exists():
                test_file.unlink()
                
    def test_init(self):
        """Test executor initialization."""
        self.assertEqual(self.executor.issue_number, 123)
        self.assertEqual(self.executor.log_file, Path(".workflow-async-123.log"))
        self.assertEqual(self.executor.pid_file, Path(".workflow-async-123.pid"))
        self.assertEqual(self.executor.status_file, Path(".workflow-async-123.status"))
        
    @patch("workflow_async_executor.subprocess.Popen")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_start_workflow_success(self, mock_is_running, mock_popen):
        """Test successful workflow start."""
        mock_is_running.return_value = False
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        with patch("builtins.open", mock_open()):
            result = self.executor.start_workflow(hybrid=True, skip_phases=[0, 1])
            
        self.assertTrue(result)
        mock_popen.assert_called_once()
        
        # Check command construction
        call_args = mock_popen.call_args[0][0]
        self.assertIn("--hybrid", call_args)
        self.assertIn("--skip-phases", call_args)
        self.assertIn("0", call_args)
        self.assertIn("1", call_args)
        
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_start_workflow_already_running(self, mock_is_running):
        """Test start when workflow already running."""
        mock_is_running.return_value = True
        
        with patch("builtins.print") as mock_print:
            result = self.executor.start_workflow()
            
        self.assertFalse(result)
        mock_print.assert_any_call(f"❌ Workflow already running for issue #{self.issue_number}")
        
    def test_check_status_no_file(self):
        """Test status check when no status file exists."""
        result = self.executor.check_status()
        self.assertEqual(result["status"], "not_found")
        self.assertEqual(result["message"], "No workflow found")
        
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_check_status_running(self, mock_is_running):
        """Test status check for running workflow."""
        mock_is_running.return_value = True
        
        # Create test status file
        status_data = {
            "status": "running",
            "message": "Test workflow",
            "updated": "2025-01-01T00:00:00",
            "issue_number": self.issue_number
        }
        
        with open(self.executor.status_file, "w") as f:
            json.dump(status_data, f)
            
        result = self.executor.check_status()
        self.assertEqual(result["status"], "running")
        
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_check_status_completed(self, mock_is_running):
        """Test status check for completed workflow."""
        mock_is_running.return_value = False
        
        # Create test status file
        status_data = {"status": "running", "message": "Test workflow"}
        
        with open(self.executor.status_file, "w") as f:
            json.dump(status_data, f)
            
        result = self.executor.check_status()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["message"], "Workflow completed")
        
    def test_get_logs_no_file(self):
        """Test getting logs when no log file exists."""
        result = self.executor.get_logs()
        self.assertEqual(result, "No logs found")
        
    @patch("workflow_async_executor.subprocess.run")
    def test_get_logs_success(self, mock_run):
        """Test successfully getting logs."""
        # Create test log file
        self.executor.log_file.touch()
        
        mock_run.return_value = MagicMock(stdout="Test log content")
        
        result = self.executor.get_logs(tail_lines=10)
        self.assertEqual(result, "Test log content")
        mock_run.assert_called_once_with(
            ["tail", "-10", str(self.executor.log_file)],
            capture_output=True,
            text=True
        )
        
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_stop_workflow_not_running(self, mock_is_running):
        """Test stopping workflow when not running."""
        mock_is_running.return_value = False
        
        with patch("builtins.print") as mock_print:
            result = self.executor.stop_workflow()
            
        self.assertFalse(result)
        mock_print.assert_called_with("No running workflow found")
        
    @patch("workflow_async_executor.os.killpg")
    @patch("workflow_async_executor.os.getpgid")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_stop_workflow_success(self, mock_is_running, mock_getpgid, mock_killpg):
        """Test successfully stopping workflow."""
        mock_is_running.return_value = True
        mock_getpgid.return_value = 12345
        
        # Create test PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("12345")
            
        result = self.executor.stop_workflow()
        
        self.assertTrue(result)
        mock_killpg.assert_called_once()
        
    @patch("workflow_async_executor.os.killpg")
    @patch("workflow_async_executor.os.getpgid")
    @patch.object(AsyncWorkflowExecutor, "_is_running")
    def test_stop_workflow_process_not_found(self, mock_is_running, mock_getpgid, mock_killpg):
        """Test stopping workflow when process not found."""
        mock_is_running.return_value = True
        mock_killpg.side_effect = ProcessLookupError()
        
        # Create test PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("12345")
            
        result = self.executor.stop_workflow()
        self.assertFalse(result)
        
    @patch("workflow_async_executor.os.kill")
    def test_is_running_true(self, mock_kill):
        """Test checking if workflow is running (true case)."""
        # Create test PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("12345")
            
        mock_kill.return_value = None  # Process exists
        
        result = self.executor._is_running()
        self.assertTrue(result)
        mock_kill.assert_called_with(12345, 0)
        
    def test_is_running_no_pid_file(self):
        """Test checking if workflow is running when no PID file."""
        result = self.executor._is_running()
        self.assertFalse(result)
        
    @patch("workflow_async_executor.os.kill")
    def test_is_running_process_not_exists(self, mock_kill):
        """Test checking if workflow is running when process doesn't exist."""
        # Create test PID file
        with open(self.executor.pid_file, "w") as f:
            f.write("12345")
            
        mock_kill.side_effect = OSError()
        
        result = self.executor._is_running()
        self.assertFalse(result)
        
    def test_update_status(self):
        """Test updating status file."""
        self.executor._update_status("running", "Test message")
        
        self.assertTrue(self.executor.status_file.exists())
        
        with open(self.executor.status_file) as f:
            data = json.load(f)
            
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["message"], "Test message")
        self.assertEqual(data["issue_number"], self.issue_number)
        self.assertIn("updated", data)


class TestAsyncWorkflowExecutorCLI(unittest.TestCase):
    """Test cases for AsyncWorkflowExecutor CLI."""
    
    @patch("workflow_async_executor.AsyncWorkflowExecutor")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_start_command(self, mock_args, mock_executor_class):
        """Test main function with start command."""
        from workflow_async_executor import main
        
        # Mock arguments
        mock_args.return_value = MagicMock(
            command="start",
            issue_number=123,
            hybrid=True,
            skip_phases=[0, 1]
        )
        
        # Mock executor instance
        mock_executor = MagicMock()
        mock_executor.start_workflow.return_value = True
        mock_executor_class.return_value = mock_executor
        
        with patch("sys.exit") as mock_exit:
            main()
            
        mock_executor.start_workflow.assert_called_once_with(True, [0, 1])
        mock_exit.assert_called_once_with(0)
        
    @patch("workflow_async_executor.AsyncWorkflowExecutor")
    @patch("argparse.ArgumentParser.parse_args")
    @patch("builtins.print")
    def test_main_status_command(self, mock_print, mock_args, mock_executor_class):
        """Test main function with status command."""
        from workflow_async_executor import main
        
        # Mock arguments
        mock_args.return_value = MagicMock(
            command="status",
            issue_number=456
        )
        
        # Mock executor instance
        mock_executor = MagicMock()
        mock_executor.check_status.return_value = {"status": "running", "message": "Test"}
        mock_executor_class.return_value = mock_executor
        
        main()
        
        mock_executor.check_status.assert_called_once()
        # Check that JSON was printed
        calls = mock_print.call_args_list
        self.assertTrue(any('"status": "running"' in str(call) for call in calls))
        
    @patch("workflow_async_executor.AsyncWorkflowExecutor")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_no_command(self, mock_args, mock_executor_class):
        """Test main function with no command."""
        from workflow_async_executor import main
        
        # Mock arguments
        mock_args.return_value = MagicMock(command=None)
        
        with patch("sys.exit") as mock_exit:
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                main()
                
        mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()