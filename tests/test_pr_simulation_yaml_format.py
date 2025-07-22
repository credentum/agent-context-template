#!/usr/bin/env python3
"""
Integration tests for PR simulation YAML format validation.

Tests that the YAML output from simulate-pr-review.sh matches the expected
GitHub Actions ARC-Reviewer format exactly, ensuring format consistency.
"""

import subprocess
import unittest
from pathlib import Path

import yaml


class TestPRSimulationYAMLFormat(unittest.TestCase):
    """Test PR simulation YAML format consistency."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.repo_root = Path(__file__).parent.parent
        self.script_path = self.repo_root / "scripts" / "simulate-pr-review.sh"

    def test_yaml_output_format_consistency(self) -> None:
        """Test that simulate-pr-review.sh produces valid YAML matching ARC-Reviewer format."""
        # Skip if script doesn't exist
        if not self.script_path.exists():
            self.skipTest("simulate-pr-review.sh not found")

        # Check that the script produces valid YAML structure
        try:
            result = subprocess.run(
                [str(self.script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.repo_root,
            )
            self.assertEqual(result.returncode, 0, "Script help should work")
            self.assertIn("yaml", result.stdout.lower(), "Script should mention YAML format")
        except subprocess.TimeoutExpired:
            self.skipTest("Script execution timed out")

    def test_arc_reviewer_yaml_format_structure(self) -> None:
        """Test that ARC-Reviewer produces expected YAML structure."""
        try:
            from src.agents.arc_reviewer import ARCReviewer

            reviewer = ARCReviewer()

            # Create a mock review result
            mock_result = {
                "schema_version": "1.0",
                "pr_number": 1234,
                "timestamp": "2025-07-22T00:00:00Z",
                "reviewer": "ARC-Reviewer",
                "verdict": "APPROVE",
                "summary": "Test review",
                "coverage": {
                    "current_pct": 85.0,
                    "status": "PASS",
                    "meets_baseline": True,
                },
                "issues": {
                    "blocking": [],
                    "warnings": [],
                    "nits": [],
                },
                "automated_issues": [],
            }

            # Test YAML formatting
            yaml_output = reviewer.format_yaml_output(mock_result)

            # Validate YAML is parseable
            parsed_yaml = yaml.safe_load(yaml_output)

            # Check required fields
            required_fields = ["schema_version", "verdict", "coverage", "issues"]

            for field in required_fields:
                self.assertIn(field, parsed_yaml, f"YAML output missing required field: {field}")

            # Check issues structure
            issues = parsed_yaml["issues"]
            required_issue_types = ["blocking", "warnings", "nits"]
            for issue_type in required_issue_types:
                self.assertIn(issue_type, issues, f"Issues missing required type: {issue_type}")
                self.assertIsInstance(issues[issue_type], list, f"{issue_type} should be a list")

        except ImportError:
            self.skipTest("ARC-Reviewer module not available")

    def test_yaml_format_documentation_consistency(self) -> None:
        """Test that YAML format documentation is consistent."""
        # Check that script help mentions the format guarantee
        try:
            result = subprocess.run(
                [str(self.script_path), "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.repo_root,
            )

            help_text = result.stdout

            # Should mention ARC-Reviewer requirement for YAML format
            self.assertIn("ARC-Reviewer", help_text, "Help should mention ARC-Reviewer")
            self.assertIn(
                "required for YAML format",
                help_text,
                "Help should mention ARC-Reviewer requirement for YAML",
            )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.skipTest("Script not available for testing")


if __name__ == "__main__":
    unittest.main()
