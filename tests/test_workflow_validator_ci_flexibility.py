#!/usr/bin/env python3
"""
Tests for flexible CI validation in workflow-validator.py
Testing issue #1662 requirements
"""

import importlib.util
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml

# Load workflow validator using importlib for reliable importing
workflow_dir = Path(__file__).parent.parent / ".claude" / "workflows"
workflow_validator_path = workflow_dir / "workflow-validator.py"

try:
    spec = importlib.util.spec_from_file_location("workflow_validator", workflow_validator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {workflow_validator_path}")
    workflow_validator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(workflow_validator_module)

    WorkflowValidator = workflow_validator_module.WorkflowValidator

    IMPORT_SUCCESS = True
except Exception as e:
    print(f"Import failed: {e}")
    IMPORT_SUCCESS = False
    WorkflowValidator = None


@unittest.skipUnless(IMPORT_SUCCESS, "workflow_validator module not available")
class TestWorkflowValidatorCIFlexibility(unittest.TestCase):
    """Test flexible CI validation functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.workflow_dir = Path(self.temp_dir)

        # Create .claude/config directory structure
        config_dir = self.workflow_dir / ".claude" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = config_dir / "workflow-enforcement.yaml"
        self.issue_number = 1662

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_config(self, ci_config: dict):
        """Create a test configuration file."""
        config = {"phases": {"validation": {"ci_validation": ci_config}}}
        with open(self.config_file, "w") as f:
            yaml.dump(config, f)

    def _create_marker_file(self, filename: str, age_hours: float = 0):
        """Create a CI marker file with specified age."""
        marker_path = self.workflow_dir / filename
        marker_path.touch()

        # Set file modification time
        if age_hours > 0:
            past_time = datetime.now() - timedelta(hours=age_hours)
            timestamp = past_time.timestamp()
            os.utime(marker_path, (timestamp, timestamp))

    def test_default_config_backward_compatibility(self):
        """Test that default configuration maintains backward compatibility."""
        # Don't create config file to test defaults
        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should use 1-hour default for backward compatibility
        self._create_marker_file(".last-ci-run", age_hours=0.5)
        self.assertTrue(validator._check_ci_status())

        # Should fail with old marker (>1 hour)
        self._create_marker_file(".last-ci-run", age_hours=2)
        self.assertFalse(validator._check_ci_status())

    def test_no_time_limit_configuration(self):
        """Test CI validation with no time limit (max_age_hours: 0)."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 0,  # No time limit
                "marker_files": [".last-ci-run"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should pass even with very old marker
        self._create_marker_file(".last-ci-run", age_hours=48)
        self.assertTrue(validator._check_ci_status())

    def test_multiple_marker_files(self):
        """Test CI validation with multiple marker file options."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 2,
                "marker_files": [".last-ci-run", "ci-output.log", "coverage.xml"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should fail with no markers
        self.assertFalse(validator._check_ci_status())

        # Should pass with any of the marker files
        self._create_marker_file("coverage.xml", age_hours=1)
        self.assertTrue(validator._check_ci_status())

    def test_flexible_time_limits(self):
        """Test configurable time limits."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 6,  # 6-hour limit
                "marker_files": [".last-ci-run"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should pass within 6 hours
        self._create_marker_file(".last-ci-run", age_hours=4)
        self.assertTrue(validator._check_ci_status())

        # Should fail after 6 hours
        self._create_marker_file(".last-ci-run", age_hours=8)
        self.assertFalse(validator._check_ci_status())

    def test_ci_not_required_mode(self):
        """Test mode where CI is not required."""
        self._create_config(
            {
                "require_ci": False,
                "max_age_hours": 1,
                "marker_files": [".last-ci-run"],
                "allow_test_only": True,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Mock _check_tests_run to return True
        with patch.object(validator, "_check_tests_run", return_value=True):
            # Should pass even without CI markers if tests passed
            self.assertTrue(validator._check_ci_status())

    def test_pytest_cache_marker(self):
        """Test that pytest cache is recognized as a CI marker."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 2,
                "marker_files": [".pytest_cache/v/cache/lastfailed"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Create pytest cache directory and file
        pytest_dir = self.workflow_dir / ".pytest_cache" / "v" / "cache"
        pytest_dir.mkdir(parents=True)
        self._create_marker_file(".pytest_cache/v/cache/lastfailed", age_hours=1)

        self.assertTrue(validator._check_ci_status())

    def test_environment_awareness_docker_unavailable(self):
        """Test behavior when Docker CI is not available."""
        self._create_config(
            {
                "require_ci": False,  # Be flexible about CI requirements
                "max_age_hours": 0,
                "marker_files": ["ci-output.log", ".pytest_cache/v/cache/lastfailed"],
                "allow_test_only": True,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Create pytest cache as alternative to Docker CI
        pytest_dir = self.workflow_dir / ".pytest_cache" / "v" / "cache"
        pytest_dir.mkdir(parents=True)
        self._create_marker_file(".pytest_cache/v/cache/lastfailed")

        # Mock tests running
        with patch.object(validator, "_check_tests_run", return_value=True):
            self.assertTrue(validator._check_ci_status())

    def test_resume_workflow_scenario(self):
        """Test workflow resume scenario with old CI markers."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 0,  # No time limit for resume scenarios
                "marker_files": [".last-ci-run", "ci-output.log"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Create old CI marker (24 hours old)
        self._create_marker_file(".last-ci-run", age_hours=24)

        # Should pass because time limit is disabled
        self.assertTrue(validator._check_ci_status())

    def test_configuration_loading_error_handling(self):
        """Test graceful handling of configuration loading errors."""
        # Create invalid YAML file
        with open(self.config_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should fall back to default configuration
        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should behave like default (1-hour limit)
        self._create_marker_file(".last-ci-run", age_hours=0.5)
        self.assertTrue(validator._check_ci_status())

        self._create_marker_file(".last-ci-run", age_hours=2)
        self.assertFalse(validator._check_ci_status())

    def test_missing_config_file(self):
        """Test behavior when config file doesn't exist."""
        # Don't create config file
        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Should use default configuration
        config = validator.config
        self.assertEqual(config["phases"]["validation"]["ci_validation"]["max_age_hours"], 1)
        self.assertEqual(config["phases"]["validation"]["ci_validation"]["require_ci"], True)

    def test_phase_prerequisite_with_flexible_ci(self):
        """Test phase 4 prerequisites with flexible CI validation."""
        self._create_config(
            {
                "require_ci": True,
                "max_age_hours": 0,  # No time limit
                "marker_files": ["coverage.xml"],
                "allow_test_only": False,
            }
        )

        validator = WorkflowValidator(self.issue_number, self.workflow_dir)

        # Mock other prerequisites as met
        with patch.object(validator, "_phase_completed", return_value=True):
            # Create coverage.xml marker
            self._create_marker_file("coverage.xml")

            # Phase 4 prerequisites should pass
            can_proceed, errors = validator.validate_phase_prerequisites(4)
            self.assertTrue(can_proceed)
            self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
