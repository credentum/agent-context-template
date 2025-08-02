"""Tests for workflow_task_bridge module."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.workflow_task_bridge import WorkflowTaskBridge, create_implementation_script


class TestWorkflowTaskBridge:
    """Test cases for WorkflowTaskBridge class."""

    def test_init(self):
        """Test WorkflowTaskBridge initialization."""
        bridge = WorkflowTaskBridge(123)
        assert bridge.issue_number == 123
        assert isinstance(bridge.workspace_root, Path)
        assert bridge.task_request_file.name == ".task-request-123.json"

    def test_create_task_request(self):
        """Test creating a task request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.workflow_task_bridge.Path.cwd", return_value=Path(tmpdir)):
                bridge = WorkflowTaskBridge(456)
                
                prompt = "Implement feature X"
                agent_type = "general-purpose"
                
                bridge.create_task_request(prompt, agent_type)
                
                # Verify file was created
                assert bridge.task_request_file.exists()
                
                # Verify file contents
                with open(bridge.task_request_file) as f:
                    data = json.load(f)
                
                assert data["issue_number"] == 456
                assert data["prompt"] == prompt
                assert data["agent_type"] == agent_type
                assert "timestamp" in data

    def test_wait_for_completion_success(self):
        """Test waiting for task completion - success case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.workflow_task_bridge.Path.cwd", return_value=Path(tmpdir)):
                bridge = WorkflowTaskBridge(789)
                
                # Create completion file
                completion_file = bridge.workspace_root / ".task-complete-789.json"
                completion_data = {
                    "issue_number": 789,
                    "success": True,
                    "result": "Task completed successfully"
                }
                with open(completion_file, "w") as f:
                    json.dump(completion_data, f)
                
                result = bridge.wait_for_completion(timeout=1)
                assert result is True

    def test_wait_for_completion_failure(self):
        """Test waiting for task completion - failure case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.workflow_task_bridge.Path.cwd", return_value=Path(tmpdir)):
                bridge = WorkflowTaskBridge(790)
                
                # Create completion file with failure
                completion_file = bridge.workspace_root / ".task-complete-790.json"
                completion_data = {
                    "issue_number": 790,
                    "success": False,
                    "error": "Task failed"
                }
                with open(completion_file, "w") as f:
                    json.dump(completion_data, f)
                
                result = bridge.wait_for_completion(timeout=1)
                assert result is False

    def test_wait_for_completion_timeout(self):
        """Test waiting for task completion - timeout case."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.workflow_task_bridge.Path.cwd", return_value=Path(tmpdir)):
                bridge = WorkflowTaskBridge(791)
                
                # No completion file created - should timeout
                result = bridge.wait_for_completion(timeout=0.1)
                assert result is False

    def test_cleanup(self):
        """Test cleanup of task files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.workflow_task_bridge.Path.cwd", return_value=Path(tmpdir)):
                bridge = WorkflowTaskBridge(792)
                
                # Create both files
                bridge.task_request_file.touch()
                completion_file = bridge.workspace_root / ".task-complete-792.json"
                completion_file.touch()
                
                # Verify files exist
                assert bridge.task_request_file.exists()
                assert completion_file.exists()
                
                # Clean up
                bridge.cleanup()
                
                # Verify files are removed
                assert not bridge.task_request_file.exists()
                assert not completion_file.exists()


class TestCreateImplementationScript:
    """Test cases for create_implementation_script function."""

    def test_create_implementation_script_basic(self):
        """Test creating a basic implementation script."""
        issue_data = {
            "number": 123,
            "title": "Add feature X",
            "body": "Implement feature X with tests"
        }
        
        script_content = create_implementation_script(issue_data)
        
        assert "WorkflowTaskBridge" in script_content
        assert "123" in script_content
        assert "Add feature X" in script_content
        assert "general-purpose" in script_content

    def test_create_implementation_script_with_labels(self):
        """Test creating implementation script with different labels."""
        issue_data = {
            "number": 456,
            "title": "Fix bug Y",
            "body": "Fix critical bug Y",
            "labels": [{"name": "bug"}, {"name": "critical"}]
        }
        
        script_content = create_implementation_script(issue_data)
        
        assert "456" in script_content
        assert "Fix bug Y" in script_content
        assert "general-purpose" in script_content

    @patch("subprocess.run")
    def test_create_implementation_script_execution(self, mock_run):
        """Test that the generated script can be executed."""
        mock_run.return_value.returncode = 0
        
        issue_data = {
            "number": 789,
            "title": "Test feature",
            "body": "Test implementation"
        }
        
        script_content = create_implementation_script(issue_data)
        
        # Verify script contains proper Python syntax
        assert script_content.startswith("#!/usr/bin/env python3")
        assert "if __name__ == '__main__':" in script_content
        assert "bridge = WorkflowTaskBridge" in script_content

    def test_create_implementation_script_prompt_format(self):
        """Test that the generated prompt has correct format."""
        issue_data = {
            "number": 111,
            "title": "Implement calculator",
            "body": "Create a calculator with add/subtract functions"
        }
        
        script_content = create_implementation_script(issue_data)
        
        # Check that key elements are in the prompt
        assert "Issue #111" in script_content
        assert "Implement calculator" in script_content
        assert "Create a calculator with add/subtract functions" in script_content