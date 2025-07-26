#!/usr/bin/env python3
"""
Tests for WorkflowEnforcer
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from workflow_enforcer import PhaseState, WorkflowEnforcer  # noqa: E402


class TestWorkflowEnforcer:
    """Test suite for WorkflowEnforcer."""

    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """Create a temporary config file."""
        config_path = tmp_path / ".claude" / "config" / "workflow-enforcement.yaml"
        config_path.parent.mkdir(parents=True)
        return str(config_path)

    @pytest.fixture
    def enforcer(self, temp_config_file, tmp_path):
        """Create enforcer instance with test config."""
        # Change to temp dir so state files are created there
        with patch("os.getcwd", return_value=str(tmp_path)):
            # Use a unique issue number for each test to avoid state conflicts
            import random

            issue_num = random.randint(1000, 9999)
            return WorkflowEnforcer(issue_num, temp_config_file)

    @pytest.fixture
    def sample_state(self):
        """Create sample workflow state."""
        return {
            "issue_number": 123,
            "created_at": datetime.now().isoformat(),
            "current_phase": None,
            "phases": {
                "investigation": {
                    "phase_name": "investigation",
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "outputs": {"scope_clarity": "clear", "investigation_completed": True},
                    "errors": [],
                    "agent_type": "issue-investigator",
                }
            },
            "metadata": {"enforcer_version": "1.0.0", "workflow_version": "1.0.0"},
        }

    def test_init_creates_default_config(self, enforcer):
        """Test that initialization creates default config."""
        assert enforcer.config["enforcement"]["enabled"] is True
        assert enforcer.config["enforcement"]["strict_mode"] is True
        assert "phases" in enforcer.config

    def test_enforce_phase_entry_valid(self, enforcer):
        """Test valid phase entry."""
        # Should be able to enter planning after investigation is completed
        enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        enforcer._save_state()

        can_proceed, message, context = enforcer.enforce_phase_entry("planning", "task-planner")
        assert can_proceed is True
        assert "Entering phase" in message
        assert "workflow.phase.planning.status" in context

    def test_enforce_phase_entry_missing_prerequisite(self, enforcer):
        """Test phase entry when prerequisite not met."""
        # Try to enter implementation without completing planning
        can_proceed, message, _ = enforcer.enforce_phase_entry("implementation", "main-claude")
        assert can_proceed is False
        assert "Previous phase 'planning' not" in message

    def test_enforce_phase_entry_on_main_branch(self, enforcer):
        """Test implementation phase blocked on main branch."""
        # Complete prerequisites
        enforcer.state["phases"]["investigation"] = {"status": "completed"}
        enforcer.state["phases"]["planning"] = {"status": "completed"}
        enforcer._save_state()

        # Mock git branch check
        with patch.object(enforcer, "_get_current_branch", return_value="main"):
            can_proceed, message, _ = enforcer.enforce_phase_entry("implementation", "main-claude")
            assert can_proceed is False
            assert "Cannot implement on main branch" in message

    def test_complete_phase_success(self, enforcer):
        """Test successful phase completion."""
        # Complete investigation first
        enforcer.state["phases"]["investigation"] = {
            "status": "completed",
            "outputs": {"scope_clarity": "clear"},
        }
        enforcer._save_state()

        # Now properly start planning phase through enforce_phase_entry
        can_proceed, _, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        assert can_proceed is True

        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }

        # Mock file existence check for required files
        with patch.object(enforcer, "_check_file_exists", return_value=True):
            success, message = enforcer.complete_phase("planning", outputs)
        assert success is True
        assert "completed successfully" in message
        assert enforcer.state["phases"]["planning"]["status"] == "completed"

    def test_complete_phase_missing_outputs(self, enforcer):
        """Test phase completion with missing required outputs."""
        enforcer.state["phases"]["planning"] = {"status": "in_progress"}
        enforcer._save_state()

        outputs = {"task_template_created": True}  # Missing other required outputs

        success, message = enforcer.complete_phase("planning", outputs)
        assert success is False
        assert "Missing required outputs" in message

    def test_validate_workflow_state(self, enforcer):
        """Test workflow state validation."""
        # Create a valid state
        enforcer.state["phases"]["investigation"] = {"status": "completed"}
        enforcer.state["phases"]["planning"] = {"status": "completed"}
        enforcer._save_state()

        is_valid, errors, warnings = enforcer.validate_workflow_state()
        assert is_valid is True
        assert len(errors) == 0

    def test_can_skip_phase(self, enforcer):
        """Test phase skipping logic."""
        context = {"scope_is_clear": True}
        assert enforcer.can_skip_phase("investigation", context) is True

        context = {"scope_is_clear": False}
        assert enforcer.can_skip_phase("investigation", context) is False

    def test_resume_workflow(self, enforcer):
        """Test workflow resume functionality."""
        # Complete investigation and planning
        enforcer.state["phases"]["investigation"] = {"status": "completed"}
        enforcer.state["phases"]["planning"] = {"status": "completed"}
        enforcer._save_state()

        next_phase = enforcer.resume_workflow()
        assert next_phase == "implementation"

        # Mark implementation as in progress
        enforcer.state["phases"]["implementation"] = {"status": "in_progress"}
        enforcer._save_state()

        next_phase = enforcer.resume_workflow()
        assert next_phase == "implementation"  # Should resume current phase

    def test_generate_compliance_report(self, enforcer):
        """Test compliance report generation."""
        enforcer.state["phases"]["investigation"] = {"status": "completed"}
        enforcer.state["phases"]["planning"] = {"status": "in_progress"}
        enforcer._save_state()

        report = enforcer.generate_compliance_report()
        assert f"Issue**: #{enforcer.issue_number}" in report
        assert "✅ Investigation" in report
        assert "🔄 Planning" in report

    def test_check_file_exists(self, enforcer, tmp_path):
        """Test file existence checking."""
        # Create a test file
        test_file = tmp_path / "test-123.md"
        test_file.write_text("test")

        with patch("glob.glob", return_value=[str(test_file)]):
            assert enforcer._check_file_exists("test-*.md") is True

        with patch("glob.glob", return_value=[]):
            assert enforcer._check_file_exists("nonexistent-*.md") is False

    def test_phase_state_dataclass(self):
        """Test PhaseState dataclass."""
        phase = PhaseState(
            phase_name="test",
            status="in_progress",
            started_at=datetime.now().isoformat(),
            agent_type="test-agent",
        )
        assert phase.phase_name == "test"
        assert phase.status == "in_progress"
        assert phase.agent_type == "test-agent"

    def test_state_persistence(self, enforcer, tmp_path):
        """Test state is persisted to file."""
        # Since enforcer was created with patched getcwd, the state file is in tmp_path
        enforcer.state["test_data"] = "test_value"
        enforcer._save_state()

        # The state file is created in the current directory (which is tmp_path due to patch)
        state_file = Path(enforcer.state_file)
        assert state_file.exists()

        with open(state_file) as f:
            loaded_state = json.load(f)
        assert loaded_state["test_data"] == "test_value"

    def test_enforcement_disabled(self, enforcer):
        """Test behavior when enforcement is disabled."""
        enforcer.config["enforcement"]["enabled"] = False

        can_proceed, message, _ = enforcer.enforce_phase_entry("planning", "task-planner")
        assert can_proceed is True
        assert "Enforcement disabled" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
