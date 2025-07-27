#!/usr/bin/env python3
"""
Tests for Hybrid Workflow Executor.

This module tests the hybrid workflow executor functionality,
including specialist sub-agent integration and fallback behavior.
"""

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from hybrid_workflow_executor import HybridWorkflowExecutor  # noqa: E402
from workflow_executor import WorkflowExecutor  # noqa: E402


class TestHybridWorkflowExecutor(unittest.TestCase):
    """Test cases for HybridWorkflowExecutor."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_issue_number = 9999
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = Path.cwd()
        # Change to temp directory for test isolation
        import os

        os.chdir(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        import os

        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()

    def test_hybrid_executor_initialization(self):
        """Test HybridWorkflowExecutor initializes correctly."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        self.assertEqual(executor.issue_number, self.test_issue_number)
        self.assertTrue(executor.enable_specialists)
        self.assertEqual(executor.specialist_timeout, 300)
        self.assertIsNotNone(executor.specialist_config)

    def test_specialist_config_loading(self):
        """Test loading specialist configuration from YAML."""
        # Create config directory and file
        config_dir = Path(".claude/config")
        config_dir.mkdir(parents=True, exist_ok=True)

        config_content = """
specialist_agents:
  investigation:
    agents:
      - type: test-investigator
    threshold: always
    parallel: false
global_settings:
  max_timeout: 600
"""
        config_file = config_dir / "specialist-agents.yaml"
        config_file.write_text(config_content)

        executor = HybridWorkflowExecutor(self.test_issue_number)

        # Check configuration was loaded
        self.assertIn("investigation", executor.specialist_config)
        self.assertEqual(executor.specialist_config["investigation"]["threshold"], "always")
        self.assertEqual(executor.global_config.get("max_timeout"), 600)

    def test_specialist_disabled_mode(self):
        """Test executor works with specialists disabled."""
        executor = HybridWorkflowExecutor(self.test_issue_number, enable_specialists=False)

        self.assertFalse(executor.enable_specialists)

        # Should not use specialists
        context = {"issue_number": self.test_issue_number}
        self.assertFalse(executor._should_use_specialist("investigation", context))

    def test_should_use_specialist_logic(self):
        """Test decision logic for using specialists."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        # Test "always" threshold
        executor.specialist_config["validation"]["threshold"] = "always"
        self.assertTrue(executor._should_use_specialist("validation", {}))

        # Test "never" threshold
        executor.specialist_config["planning"]["threshold"] = "never"
        self.assertFalse(executor._should_use_specialist("planning", {}))

        # Test "complex" threshold
        executor.specialist_config["investigation"]["threshold"] = "complex"
        self.assertFalse(executor._should_use_specialist("investigation", {}))
        self.assertTrue(executor._should_use_specialist("investigation", {"complexity": "high"}))

        # Test "large_codebase" threshold
        executor.specialist_config["planning"]["threshold"] = "large_codebase"
        self.assertFalse(executor._should_use_specialist("planning", {"files_affected": 5}))
        self.assertTrue(executor._should_use_specialist("planning", {"files_affected": 15}))

    @patch("hybrid_workflow_executor.HybridWorkflowExecutor._consult_specialist")
    def test_investigation_phase_with_specialist(self, mock_consult):
        """Test investigation phase with specialist consultation."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        # Mock specialist response
        mock_consult.return_value = {
            "root_cause_analysis": {
                "complexity": "high",
                "key_components": ["file1.py", "file2.py"],
            }
        }

        context = {
            "issue_number": self.test_issue_number,
            "complexity": "high",
            "scope_is_clear": False,
        }

        with patch.object(WorkflowExecutor, "execute_investigation") as mock_base:
            mock_base.return_value = {"investigation_completed": True}

            result = executor.execute_investigation(context)

            # Verify specialist was consulted
            mock_consult.assert_called_once()
            # Verify base method was called
            mock_base.assert_called_once()
            # Verify result
            self.assertTrue(result["investigation_completed"])

    @patch("hybrid_workflow_executor.HybridWorkflowExecutor._consult_specialist")
    def test_validation_phase_parallel_specialists(self, mock_consult):
        """Test validation phase with parallel specialist execution."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        # Mock different specialist responses
        def mock_specialist_response(agent_type, prompt, context):
            if agent_type == "test-runner":
                return {"test_coverage": "75%", "issues_found": False}
            elif agent_type == "security-analyzer":
                return {"security_issues": [], "issues_found": False}
            return {}

        mock_consult.side_effect = mock_specialist_response

        context = {"issue_number": self.test_issue_number}

        with patch.object(WorkflowExecutor, "execute_validation") as mock_base:
            mock_base.return_value = {
                "tests_run": True,
                "ci_passed": True,
                "quality_checks_passed": True,
            }

            result = executor.execute_validation(context)

            # Verify base validation was called
            mock_base.assert_called_once()
            # Verify specialists were consulted
            self.assertEqual(mock_consult.call_count, 2)
            # Verify result includes specialist validation
            self.assertIn("specialist_validation", result)
            self.assertTrue(result["quality_checks_passed"])

    def test_specialist_timeout_handling(self):
        """Test handling of specialist timeouts."""
        executor = HybridWorkflowExecutor(self.test_issue_number)
        executor.specialist_timeout = 1  # Very short timeout (1 second)

        # Create a slow specialist
        def slow_specialist(agent_type, prompt, context):
            time.sleep(0.5)  # Longer than timeout
            return {"result": "too_late"}

        with patch.object(executor, "_simulate_specialist", side_effect=slow_specialist):
            result = executor._consult_specialist("test-agent", "test prompt", {})

            # Should return empty dict on timeout
            self.assertEqual(result, {})

    def test_graceful_fallback_on_specialist_failure(self):
        """Test graceful fallback when specialists fail."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        # Mock specialist to raise exception
        with patch.object(
            executor, "_consult_specialist", side_effect=Exception("Specialist error")
        ):
            context = {"issue_number": self.test_issue_number, "complexity": "high"}

            with patch.object(WorkflowExecutor, "execute_investigation") as mock_base:
                mock_base.return_value = {"investigation_completed": True}

                # Should not raise exception, should continue with base execution
                result = executor.execute_investigation(context)

                # Verify base method was still called
                mock_base.assert_called_once()
                self.assertTrue(result["investigation_completed"])

    def test_execution_stats(self):
        """Test execution statistics tracking."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        stats = executor.get_execution_stats()

        self.assertTrue(stats["hybrid_mode"])
        self.assertIn("specialists_consulted", stats)
        self.assertIn("specialist_failures", stats)
        self.assertIn("parallel_executions", stats)

    def test_backward_compatibility(self):
        """Test backward compatibility with base WorkflowExecutor."""
        # Base executor
        base_executor = WorkflowExecutor(self.test_issue_number)

        # Hybrid executor with specialists disabled
        hybrid_executor = HybridWorkflowExecutor(self.test_issue_number, enable_specialists=False)

        # Both should have same interface
        self.assertTrue(hasattr(base_executor, "execute_investigation"))
        self.assertTrue(hasattr(hybrid_executor, "execute_investigation"))
        self.assertTrue(hasattr(base_executor, "execute_validation"))
        self.assertTrue(hasattr(hybrid_executor, "execute_validation"))

    def test_prompt_building(self):
        """Test specialist prompt building."""
        executor = HybridWorkflowExecutor(self.test_issue_number)

        context = {"issue_number": self.test_issue_number}

        # Test investigation prompt
        investigation_prompt = executor._build_investigation_prompt(context)
        self.assertIn(str(self.test_issue_number), investigation_prompt)
        self.assertIn("root cause", investigation_prompt.lower())

        # Test research prompt
        research_prompt = executor._build_research_prompt(context)
        self.assertIn(str(self.test_issue_number), research_prompt)
        self.assertIn("codebase", research_prompt.lower())

        # Test validation prompts
        test_prompt = executor._build_validation_prompt("test-runner", context)
        self.assertIn("test", test_prompt.lower())

        security_prompt = executor._build_validation_prompt("security-analyzer", context)
        self.assertIn("security", security_prompt.lower())


if __name__ == "__main__":
    unittest.main()
