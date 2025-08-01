#!/usr/bin/env python3
"""Unit tests for WorkflowConfig."""

import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import workflow_config
from workflow_config import WorkflowConfig  # noqa: E402


class TestWorkflowConfig(unittest.TestCase):
    """Test cases for WorkflowConfig."""

    def test_default_phase_timeout(self):
        """Test default phase timeout value."""
        self.assertEqual(WorkflowConfig.PHASE_TIMEOUT_SECONDS, 90)

    def test_default_background_timeout(self):
        """Test default background process timeout."""
        self.assertEqual(WorkflowConfig.BACKGROUND_PROCESS_TIMEOUT, 300)

    def test_default_max_retries(self):
        """Test default max retry attempts."""
        self.assertEqual(WorkflowConfig.MAX_RETRY_ATTEMPTS, 3)

    def test_default_retry_delay(self):
        """Test default retry delay."""
        self.assertEqual(WorkflowConfig.RETRY_DELAY_SECONDS, 5)

    def test_default_coverage_baseline(self):
        """Test default coverage baseline."""
        self.assertEqual(WorkflowConfig.COVERAGE_BASELINE, 78.0)

    def test_default_validators_coverage_threshold(self):
        """Test default validators coverage threshold."""
        self.assertEqual(WorkflowConfig.VALIDATORS_COVERAGE_THRESHOLD, 90.0)

    @patch.dict(os.environ, {"WORKFLOW_PHASE_TIMEOUT": "120"})
    def test_environment_override_phase_timeout(self):
        """Test phase timeout can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.PHASE_TIMEOUT_SECONDS, 120)

    @patch.dict(os.environ, {"WORKFLOW_BACKGROUND_TIMEOUT": "600"})
    def test_environment_override_background_timeout(self):
        """Test background timeout can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.BACKGROUND_PROCESS_TIMEOUT, 600)

    @patch.dict(os.environ, {"WORKFLOW_MAX_RETRIES": "5"})
    def test_environment_override_max_retries(self):
        """Test max retries can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.MAX_RETRY_ATTEMPTS, 5)

    @patch.dict(os.environ, {"WORKFLOW_RETRY_DELAY": "10"})
    def test_environment_override_retry_delay(self):
        """Test retry delay can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.RETRY_DELAY_SECONDS, 10)

    @patch.dict(os.environ, {"COVERAGE_BASELINE": "85.5"})
    def test_environment_override_coverage_baseline(self):
        """Test coverage baseline can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.COVERAGE_BASELINE, 85.5)

    @patch.dict(os.environ, {"VALIDATORS_COVERAGE_THRESHOLD": "95.0"})
    def test_environment_override_validators_coverage(self):
        """Test validators coverage threshold can be overridden by environment variable."""
        # Need to reload the module to pick up env changes
        import importlib

        import workflow_config

        importlib.reload(workflow_config)

        self.assertEqual(workflow_config.WorkflowConfig.VALIDATORS_COVERAGE_THRESHOLD, 95.0)

    def test_all_exports(self):
        """Test __all__ exports correct items."""
        self.assertEqual(workflow_config.__all__, ["WorkflowConfig"])

    def test_config_is_class(self):
        """Test WorkflowConfig is a class."""
        self.assertTrue(isinstance(WorkflowConfig, type))

    def test_all_attributes_exist(self):
        """Test all expected attributes exist on WorkflowConfig."""
        expected_attrs = [
            "PHASE_TIMEOUT_SECONDS",
            "BACKGROUND_PROCESS_TIMEOUT",
            "MAX_RETRY_ATTEMPTS",
            "RETRY_DELAY_SECONDS",
            "COVERAGE_BASELINE",
            "VALIDATORS_COVERAGE_THRESHOLD",
        ]

        for attr in expected_attrs:
            self.assertTrue(
                hasattr(WorkflowConfig, attr), f"WorkflowConfig missing attribute: {attr}"
            )

    def test_all_values_are_numeric(self):
        """Test all config values are numeric types."""
        numeric_attrs = {
            "PHASE_TIMEOUT_SECONDS": int,
            "BACKGROUND_PROCESS_TIMEOUT": int,
            "MAX_RETRY_ATTEMPTS": int,
            "RETRY_DELAY_SECONDS": int,
            "COVERAGE_BASELINE": float,
            "VALIDATORS_COVERAGE_THRESHOLD": float,
        }

        for attr, expected_type in numeric_attrs.items():
            value = getattr(WorkflowConfig, attr)
            self.assertIsInstance(
                value,
                expected_type,
                f"{attr} should be {expected_type.__name__}, got {type(value).__name__}",
            )

    def test_positive_values(self):
        """Test all config values are positive."""
        attrs = [
            "PHASE_TIMEOUT_SECONDS",
            "BACKGROUND_PROCESS_TIMEOUT",
            "MAX_RETRY_ATTEMPTS",
            "RETRY_DELAY_SECONDS",
            "COVERAGE_BASELINE",
            "VALIDATORS_COVERAGE_THRESHOLD",
        ]

        for attr in attrs:
            value = getattr(WorkflowConfig, attr)
            self.assertGreater(value, 0, f"{attr} should be positive, got {value}")

    @patch.dict(os.environ, {"WORKFLOW_PHASE_TIMEOUT": "not_a_number"})
    def test_invalid_env_var_raises_error(self):
        """Test that invalid environment variable values raise errors."""
        # This should raise ValueError when module is imported
        with self.assertRaises(ValueError):
            importlib.reload(workflow_config)

    @patch.dict(os.environ, {"COVERAGE_BASELINE": "not_a_float"})
    def test_invalid_float_env_var_raises_error(self):
        """Test that invalid float environment variable values raise errors."""
        # This should raise ValueError when module is imported
        with self.assertRaises(ValueError):
            importlib.reload(workflow_config)


if __name__ == "__main__":
    unittest.main()
