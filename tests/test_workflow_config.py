#!/usr/bin/env python3
"""Unit tests for WorkflowConfig."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_config import WorkflowConfig  # noqa: E402


class TestWorkflowConfig(unittest.TestCase):
    """Test cases for WorkflowConfig."""

    def test_default_phase_timeout(self):
        """Test default phase timeout value."""
        self.assertEqual(WorkflowConfig.PHASE_TIMEOUT_SECONDS, 90)

    def test_default_background_timeout(self):
        """Test default background process timeout value."""
        self.assertEqual(WorkflowConfig.BACKGROUND_PROCESS_TIMEOUT, 300)

    def test_default_max_retries(self):
        """Test default max retry attempts."""
        self.assertEqual(WorkflowConfig.MAX_RETRY_ATTEMPTS, 3)

    def test_default_retry_delay(self):
        """Test default retry delay."""
        self.assertEqual(WorkflowConfig.RETRY_DELAY_SECONDS, 5)

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


if __name__ == "__main__":
    unittest.main()
