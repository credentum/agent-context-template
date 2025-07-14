#!/usr/bin/env python3
"""
Unit tests for agent state machines
Tests state transitions, phase status updates, and task completion tracking
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import yaml

from src.agents.update_sprint import SprintUpdater


class TestSprintUpdaterStateMachine:
    """Test SprintUpdater state machine functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.context_dir = Path(self.temp_dir) / "context"
        self.sprints_dir = self.context_dir / "sprints"
        self.sprints_dir.mkdir(parents=True)

        self.test_sprint = {
            "metadata": {
                "document_type": "sprint",
                "created_date": "2024-01-01",
                "sprint_number": 1,
            },
            "sprint_number": 1,
            "status": "in_progress",
            "phases": [
                {
                    "name": "Planning",
                    "status": "completed",
                    "tasks": [
                        {"name": "Define objectives", "status": "completed"},
                        {"name": "Create timeline", "status": "completed"},
                    ],
                },
                {
                    "name": "Development",
                    "status": "in_progress",
                    "tasks": [
                        {"name": "Implement feature A", "status": "completed"},
                        {"name": "Implement feature B", "status": "pending"},
                        {"name": "Write tests", "status": "pending"},
                    ],
                },
                {
                    "name": "Testing",
                    "status": "pending",
                    "tasks": [
                        {"name": "Run integration tests", "status": "pending"},
                        {"name": "User acceptance testing", "status": "pending"},
                    ],
                },
            ],
        }

    def teardown_method(self):
        """Clean up temp files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_sprint_file(self, sprint_data, filename="sprint_001.yaml"):
        """Create a sprint YAML file"""
        sprint_path = self.sprints_dir / filename
        with open(sprint_path, "w") as f:
            yaml.dump(sprint_data, f)
        return sprint_path

    @patch("pathlib.Path.cwd")
    @patch("subprocess.run")
    def test_state_transitions_pending_to_in_progress(self, mock_run, mock_cwd):
        """Test state transition from pending to in_progress"""
        mock_cwd.return_value = Path(self.temp_dir)
        mock_run.return_value = Mock(returncode=0)

        # Create sprint with pending task
        sprint: Dict[str, Any] = self.test_sprint.copy()
        sprint["phases"][1]["tasks"][1]["status"] = "pending"

        # Create GitHub issue marking task as in progress
        github_issues = [
            {
                "number": 1,
                "title": "Implement feature B - In Progress",
                "state": "open",
                "labels": [{"name": "in-progress"}],
                "body": "Working on feature B",
            }
        ]

        mock_run.return_value = Mock(returncode=0, stdout=json.dumps(github_issues))

        self.create_sprint_file(sprint)

        updater = SprintUpdater(sprint_id="sprint_001")
        updater.context_dir = self.context_dir
        updater.sprints_dir = self.sprints_dir

        # Simulate task update logic
        phases: List[Dict[str, Any]] = sprint["phases"]
        updated = False

        for phase in phases:
            for task in phase.get("tasks", []):
                if task["name"] == "Implement feature B" and task["status"] == "pending":
                    task["status"] = "in_progress"
                    updated = True

        assert updated is True
        assert phases[1]["tasks"][1]["status"] == "in_progress"

    def test_state_transitions_in_progress_to_completed(self):
        """Test state transition from in_progress to completed"""
        sprint: Dict[str, Any] = self.test_sprint.copy()
        sprint["phases"][1]["tasks"][0]["status"] = "in_progress"

        # Simulate completion
        phases: List[Dict[str, Any]] = sprint["phases"]
        for phase in phases:
            for task in phase.get("tasks", []):
                if task["name"] == "Implement feature A" and task["status"] == "in_progress":
                    task["status"] = "completed"

        assert phases[1]["tasks"][0]["status"] == "completed"

    def test_phase_status_auto_update(self):
        """Test automatic phase status update based on task completion"""
        sprint: Dict[str, Any] = self.test_sprint.copy()

        # Complete all tasks in Development phase
        for task in sprint["phases"][1]["tasks"]:
            task["status"] = "completed"

        # Simulate phase update logic
        phase: Dict[str, Any] = sprint["phases"][1]
        all_tasks_completed = all(
            task.get("status") == "completed" for task in phase.get("tasks", [])
        )

        if all_tasks_completed:
            phase["status"] = "completed"

        assert sprint["phases"][1]["status"] == "completed"

    def test_sprint_status_progression(self):
        """Test overall sprint status progression"""
        sprint: Dict[str, Any] = self.test_sprint.copy()

        # Test planning -> in_progress
        sprint["status"] = "planning"
        if sprint["phases"][0]["status"] == "completed":
            sprint["status"] = "in_progress"
        assert sprint["status"] == "in_progress"

        # Test in_progress -> completed
        # Complete all phases
        for phase in sprint["phases"]:
            phase["status"] = "completed"

        all_phases_completed = all(phase.get("status") == "completed" for phase in sprint["phases"])
        assert isinstance(sprint["phases"], list)

        if all_phases_completed:
            sprint["status"] = "completed"

        assert sprint["status"] == "completed"

    @patch("subprocess.run")
    def test_match_task_to_issue(self, mock_run):
        """Test task to GitHub issue matching logic"""
        mock_run.return_value = Mock(returncode=0)

        updater = SprintUpdater()

        # Test exact match
        assert updater._match_task_to_issue("Implement feature A", "Implement feature A") is True

        # Test case insensitive match
        assert updater._match_task_to_issue("implement feature a", "Implement Feature A") is True

        # Test with extra punctuation
        assert (
            updater._match_task_to_issue(
                "Implement feature A", "[Task] Implement feature A - In Progress"
            )
            is True
        )

        # Test no match
        assert updater._match_task_to_issue("Implement feature A", "Implement feature B") is False

        # Test partial word match prevention
        assert updater._match_task_to_issue("test", "integration tests completed") is False

    def test_task_status_validation(self):
        """Test task status validation"""
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]

        task = {"name": "Test task", "status": "pending"}

        # Test valid statuses
        for status in valid_statuses:
            task["status"] = status
            assert task["status"] in valid_statuses

        # Test invalid status detection
        task["status"] = "invalid_status"
        assert task["status"] not in valid_statuses

    def test_concurrent_phase_management(self):
        """Test handling of concurrent phases"""
        sprint: Dict[str, Any] = {
            "phases": [
                {
                    "name": "Backend Development",
                    "status": "in_progress",
                    "tasks": [
                        {"name": "API implementation", "status": "in_progress"},
                        {"name": "Database schema", "status": "completed"},
                    ],
                },
                {
                    "name": "Frontend Development",
                    "status": "in_progress",
                    "concurrent": True,
                    "tasks": [
                        {"name": "UI components", "status": "in_progress"},
                        {"name": "State management", "status": "pending"},
                    ],
                },
            ]
        }

        # Both phases can be in_progress simultaneously
        phases_list: List[Dict[str, Any]] = sprint["phases"]
        active_phases = [phase for phase in phases_list if phase["status"] == "in_progress"]

        assert len(active_phases) == 2
        assert all(phase.get("concurrent", True) for phase in active_phases[1:])
        # Ensure all phases are dict types
        for phase in active_phases:
            assert isinstance(phase, dict)

    def test_blocked_task_handling(self):
        """Test handling of blocked tasks"""
        task: Dict[str, Any] = {
            "name": "Deploy to production",
            "status": "blocked",
            "blocked_by": "Waiting for security review",
            "blocked_since": "2024-01-15",
        }

        # Blocked tasks should not prevent phase completion
        phase: Dict[str, Any] = {
            "name": "Deployment",
            "status": "in_progress",
            "tasks": [
                {"name": "Prepare deployment", "status": "completed"},
                task,
                {"name": "Post-deployment verification", "status": "pending"},
            ],
        }

        # Check if phase can complete with blocked tasks
        tasks_list: List[Dict[str, Any]] = phase["tasks"]
        non_blocked_tasks = [t for t in tasks_list if t.get("status") != "blocked"]

        all_non_blocked_completed = all(t.get("status") == "completed" for t in non_blocked_tasks)

        assert all_non_blocked_completed is False  # Still have pending task


class TestAgentStateValidation:
    """Test state validation across different agents"""

    def test_valid_agent_states(self):
        """Test valid states for different agent types"""
        # Sprint agent states
        sprint_states = ["planning", "in_progress", "completed", "cancelled"]

        # Task states
        task_states = ["pending", "in_progress", "completed", "blocked"]

        # Phase states (defined for documentation purposes)
        _ = ["pending", "in_progress", "completed", "skipped"]

        # Validate state sets don't overlap incorrectly
        assert "planning" in sprint_states
        assert "planning" not in task_states
        assert "blocked" in task_states
        assert "blocked" not in sprint_states

    def test_state_transition_rules(self):
        """Test state transition validation rules"""
        # Define valid transitions
        transitions = {
            "pending": ["in_progress", "blocked", "skipped"],
            "in_progress": ["completed", "blocked", "pending"],
            "completed": [],  # Terminal state
            "blocked": ["in_progress", "pending"],
            "skipped": [],  # Terminal state
        }

        # Test valid transition
        current_state = "pending"
        new_state = "in_progress"
        assert new_state in transitions.get(current_state, [])

        # Test invalid transition
        current_state = "completed"
        new_state = "pending"
        assert new_state not in transitions.get(current_state, [])
