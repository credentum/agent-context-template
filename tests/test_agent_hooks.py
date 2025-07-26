#!/usr/bin/env python3
"""
Tests for AgentHooks
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from agent_hooks import AgentHooks, WorkflowViolationError, get_workflow_decorator  # noqa: E402


class TestAgentHooks:
    """Test suite for AgentHooks."""

    @pytest.fixture
    def temp_state_file(self, tmp_path):
        """Create a temporary state file."""
        state_file = tmp_path / ".workflow-state-456.json"
        return str(state_file)

    @pytest.fixture
    def hooks(self, tmp_path):
        """Create hooks instance with test config."""
        # Change to temp dir so state files are created there
        with patch("os.getcwd", return_value=str(tmp_path)):
            # Use a unique issue number for each test to avoid state conflicts
            import random

            issue_num = random.randint(1000, 9999)
            hooks = AgentHooks(issue_num)
            # Ensure the state is properly initialized
            if "phases" not in hooks.enforcer.state:
                hooks.enforcer.state["phases"] = {}
            return hooks

    @pytest.fixture
    def sample_context(self):
        """Create sample execution context."""
        return {
            "issue_number": 456,
            "phase": "planning",
            "agent_type": "task-planner",
            "scope_is_clear": False,
        }

    def test_pre_phase_hook_valid(self, hooks, sample_context):
        """Test valid pre-phase hook execution."""
        # Setup: mark investigation as completed
        hooks.enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        hooks.enforcer._save_state()

        can_proceed, message, context_updates = hooks.pre_phase_hook(
            "planning", "task-planner", sample_context
        )

        assert can_proceed is True
        assert "Entering phase" in message
        assert "workflow.phase.planning.status" in context_updates

    def test_pre_phase_hook_investigation_skip(self, hooks):
        """Test investigation phase can be skipped when scope is clear."""
        context = {"scope_is_clear": True}

        can_proceed, message, context_updates = hooks.pre_phase_hook(
            "investigation", "issue-investigator", context
        )

        assert can_proceed is True
        assert "Investigation skipped" in message
        # Verify investigation was marked as completed
        assert hooks.enforcer.state["phases"]["investigation"]["status"] == "completed"
        assert hooks.enforcer.state["phases"]["investigation"]["outputs"]["skipped"] is True

    def test_pre_phase_hook_blocked(self, hooks, sample_context):
        """Test pre-phase hook when prerequisites not met."""
        # Try to enter implementation without completing planning
        can_proceed, message, context_updates = hooks.pre_phase_hook(
            "implementation", "main-claude", sample_context
        )

        assert can_proceed is False
        assert "Previous phase" in message

    def test_post_phase_hook_success(self, hooks):
        """Test successful post-phase hook."""
        # Setup: complete investigation first
        hooks.enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        # Then properly start planning phase
        can_proceed, _, _ = hooks.enforcer.enforce_phase_entry("planning", "task-planner")
        assert can_proceed is True

        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }

        success, message = hooks.post_phase_hook("planning", outputs)
        assert success is True
        assert "completed successfully" in message

    def test_post_phase_hook_missing_outputs(self, hooks):
        """Test post-phase hook with missing outputs."""
        hooks.enforcer.state["phases"]["planning"] = {"status": "in_progress"}
        hooks.enforcer._save_state()

        outputs = {"task_template_created": True}  # Missing other outputs

        success, message = hooks.post_phase_hook("planning", outputs)
        assert success is False
        assert "Missing required outputs" in message

    def test_workflow_decorator_success(self, hooks):
        """Test workflow decorator with successful execution."""
        # Setup prerequisites
        hooks.enforcer.state["phases"]["investigation"] = {"status": "completed"}
        hooks.enforcer.state["phases"]["planning"] = {"status": "completed"}
        hooks.enforcer._save_state()

        # Mock git branch check
        with patch.object(hooks.enforcer, "_get_current_branch", return_value="feature/test"):

            @hooks.workflow_decorator("implementation", "main-claude")
            def implement_feature(context):
                return {"implementation_complete": True}

            context = {"test": "data"}
            result = implement_feature(context)

            assert result == {"implementation_complete": True}
            assert hooks.enforcer.state["phases"]["implementation"]["status"] == "completed"

    def test_workflow_decorator_violation(self, hooks):
        """Test workflow decorator raises exception on violation."""

        @hooks.workflow_decorator("planning", "task-planner")
        def plan_task(context):
            # Return incomplete outputs to trigger post-phase failure
            return {"task_template_created": True}  # Missing other required outputs

        context = {"test": "data"}

        # Complete investigation first so pre-phase passes
        hooks.enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        hooks.enforcer._save_state()

        # Should raise WorkflowViolationError due to missing outputs in post-phase
        with pytest.raises(WorkflowViolationError) as exc_info:
            plan_task(context)

        assert "Failed to complete planning" in str(exc_info.value)

    def test_workflow_decorator_exception_handling(self, hooks):
        """Test workflow decorator handles exceptions properly."""
        # Setup prerequisites
        hooks.enforcer.state["phases"]["investigation"] = {"status": "completed"}
        hooks.enforcer._save_state()

        @hooks.workflow_decorator("planning", "task-planner")
        def failing_function(context):
            raise ValueError("Test error")

        context = {"test": "data"}

        with pytest.raises(ValueError):
            failing_function(context)

        # Verify phase was marked as failed
        assert hooks.enforcer.state["phases"]["planning"]["status"] == "failed"
        assert "Test error" in hooks.enforcer.state["phases"]["planning"]["errors"][0]

    def test_extract_outputs_planning(self, hooks, tmp_path):
        """Test output extraction for planning phase."""
        # Create test files with the actual issue number from hooks
        issue_num = hooks.issue_number
        task_template = (
            tmp_path / "context" / "trace" / "task-templates" / f"issue-{issue_num}-test.md"
        )
        task_template.parent.mkdir(parents=True)
        task_template.write_text("test")

        scratchpad = (
            tmp_path / "context" / "trace" / "scratchpad" / f"2025-01-01-issue-{issue_num}-test.md"
        )
        scratchpad.parent.mkdir(parents=True)
        scratchpad.write_text("test")

        with patch(
            "glob.glob",
            side_effect=lambda p: (
                [str(task_template)] if "task-template" in p else [str(scratchpad)]
            ),
        ):
            outputs = hooks._extract_outputs("planning", {}, {})

            assert outputs["task_template_created"] is True
            assert outputs["scratchpad_created"] is True

    def test_extract_outputs_implementation(self, hooks):
        """Test output extraction for implementation phase."""
        with patch.object(hooks.enforcer, "_get_current_branch", return_value="feature/test"):
            with patch.object(hooks, "_check_git_commits_exist", return_value=True):
                outputs = hooks._extract_outputs("implementation", {}, {})

                assert outputs["branch_created"] is True
                assert outputs["implementation_complete"] is True
                assert outputs["commits_made"] is True

    def test_extract_outputs_validation(self, hooks):
        """Test output extraction for validation phase."""
        context = {
            "tests_run": True,
            "ci_passed": True,
            "coverage_maintained": True,
            "coverage_percentage": "85.5%",
        }

        outputs = hooks._extract_outputs("validation", {}, context)

        assert outputs["tests_run"] is True
        assert outputs["ci_passed"] is True
        assert outputs["coverage_maintained"] is True
        assert outputs["coverage_percentage"] == "85.5%"

    def test_check_git_commit_exists(self, hooks):
        """Test git commit checking."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="abc123 docs(trace): add task template for issue #456"
            )

            result = hooks._check_git_commit_exists("issue #456", "docs(trace): add task template")
            assert result is True

            mock_run.return_value = MagicMock(stdout="def456 feat: unrelated commit")
            result = hooks._check_git_commit_exists("issue #456", "docs(trace): add task template")
            assert result is False

    def test_check_git_commits_exist(self, hooks):
        """Test checking for commits on branch."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="5\n")
            assert hooks._check_git_commits_exist() is True

            mock_run.return_value = MagicMock(stdout="0\n")
            assert hooks._check_git_commits_exist() is False

    def test_check_branch_pushed(self, hooks):
        """Test checking if branch is pushed."""
        with patch.object(hooks.enforcer, "_get_current_branch", return_value="feature/test"):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(stdout="refs/heads/feature/test")
                assert hooks._check_branch_pushed() is True

                mock_run.return_value = MagicMock(stdout="")
                assert hooks._check_branch_pushed() is False

    def test_set_nested_dict(self, hooks):
        """Test setting nested dictionary values."""
        d = {}
        hooks._set_nested_dict(d, "a.b.c", "value")
        assert d == {"a": {"b": {"c": "value"}}}

        d = {"a": {"x": "y"}}
        hooks._set_nested_dict(d, "a.b", "value")
        assert d == {"a": {"x": "y", "b": "value"}}

    def test_log_hook_execution(self, hooks, tmp_path):
        """Test hook execution logging."""
        # hooks fixture already patches os.getcwd, so we don't need to patch again
        hooks._log_hook_execution("pre", "planning", "task-planner", True, "Test message")

        log_file = tmp_path / "context" / "trace" / "logs" / "workflow-enforcement.log"
        assert log_file.exists()

        with open(log_file) as f:
            log_entry = json.loads(f.readline())

            assert log_entry["hook_type"] == "pre"
            assert log_entry["phase"] == "planning"
            assert log_entry["agent"] == "task-planner"
            assert log_entry["success"] is True
            assert log_entry["message"] == "Test message"
            assert log_entry["issue"] == 456

    def test_convenience_functions(self, tmp_path):
        """Test convenience functions."""
        from agent_hooks import enforce_post_phase, enforce_pre_phase

        with patch("os.getcwd", return_value=str(tmp_path)):
            # Test pre-phase enforcement
            can_proceed, message, updates = enforce_pre_phase(
                789, "investigation", "issue-investigator", {"scope_is_clear": True}
            )
            assert can_proceed is True

            # Test post-phase enforcement
            # Need to create a proper state with all required fields
            enforcer_file = tmp_path / ".workflow-state-789.json"
            state = {
                "issue_number": 789,
                "created_at": datetime.now().isoformat(),
                "current_phase": "investigation",
                "phases": {
                    "investigation": {
                        "phase_name": "investigation",
                        "status": "in_progress",
                        "started_at": datetime.now().isoformat(),
                        "agent_type": "issue-investigator",
                    }
                },
                "metadata": {"enforcer_version": "1.0.0", "workflow_version": "1.0.0"},
            }
            with open(enforcer_file, "w") as f:
                json.dump(state, f)

            success, message = enforce_post_phase(
                789, "investigation", {"scope_clarity": "clear", "investigation_completed": True}
            )
            assert success is True

    def test_get_workflow_decorator(self, tmp_path):
        """Test getting workflow decorator."""
        with patch("os.getcwd", return_value=str(tmp_path)):
            decorator = get_workflow_decorator(999, "planning", "task-planner")
            assert callable(decorator)

            # Test the decorator works
            @decorator
            def test_func(context):
                return {"result": "success"}

            # Should fail due to missing prerequisites
            with pytest.raises(WorkflowViolationError):
                test_func({})

    def test_workflow_violation_error(self):
        """Test WorkflowViolationError exception."""
        error = WorkflowViolationError("Test violation")
        assert str(error) == "Test violation"
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
