#!/usr/bin/env python3
"""
Unit tests for workflow executor functionality.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_executor import WorkflowExecutor


class TestWorkflowExecutor(unittest.TestCase):
    """Test WorkflowExecutor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = WorkflowExecutor(1234)

    def test_generate_title_slug_basic(self):
        """Test basic title slug generation."""
        test_cases = [
            ("Simple Title", "simple-title"),
            ("Title with Numbers 123", "title-with-numbers-123"),
            ("Title-with-hyphens", "title-with-hyphens"),
            ("UPPERCASE TITLE", "uppercase-title"),
            ("Title   with   spaces", "title-with-spaces"),
            ("Special!@#$%^&*()Characters", "specialcharacters"),
            ("", ""),
        ]

        for title, expected in test_cases:
            with self.subTest(title=title):
                result = self.executor._generate_title_slug(title)
                self.assertEqual(result, expected)

    def test_generate_title_slug_length_limit(self):
        """Test title slug length limiting."""
        long_title = "This is a very long title that exceeds fifty characters limit"
        result = self.executor._generate_title_slug(long_title)
        self.assertEqual(len(result), 50)
        self.assertEqual(result, "this-is-a-very-long-title-that-exceeds-fifty-chara")
        # Ensure no trailing hyphen
        self.assertFalse(result.endswith("-"))

    def test_generate_title_slug_edge_cases(self):
        """Test edge cases for title slug generation."""
        test_cases = [
            ("---Leading-hyphens", "---leading-hyphens"),
            ("Trailing-hyphens---", "trailing-hyphens"),
            ("Multiple-----hyphens", "multiple-----hyphens"),
            ("[SPRINT-4.3] Fix issue", "sprint-43-fix-issue"),
            ("Issue #123: Bug fix", "issue-123-bug-fix"),
        ]

        for title, expected in test_cases:
            with self.subTest(title=title):
                result = self.executor._generate_title_slug(title)
                self.assertEqual(result, expected)

    def test_determine_branch_type(self):
        """Test branch type determination from labels."""
        test_cases = [
            ([{"name": "bug"}], "fix"),
            ([{"name": "Bug"}], "fix"),  # Case insensitive
            ([{"name": "enhancement"}], "feature"),
            ([{"name": "feature"}], "feature"),
            ([{"name": "documentation"}], "docs"),
            ([{"name": "chore"}], "chore"),
            ([{"name": "maintenance"}], "chore"),
            ([], "fix"),  # Default
            ([{"name": "bug"}, {"name": "feature"}], "fix"),  # Bug takes precedence
            ([{"name": "random-label"}], "fix"),  # Unknown label
        ]

        for labels, expected in test_cases:
            with self.subTest(labels=labels):
                result = self.executor._determine_branch_type(labels)
                self.assertEqual(result, expected)

    @patch("subprocess.run")
    def test_fetch_issue_data_success(self, mock_run):
        """Test successful issue data fetching."""
        mock_issue_data = {
            "title": "Test Issue",
            "body": "Test body",
            "labels": [{"name": "bug"}, {"name": "priority-high"}],
        }

        mock_run.return_value = Mock(stdout=json.dumps(mock_issue_data), returncode=0)

        result = self.executor._fetch_issue_data()

        self.assertEqual(result, mock_issue_data)
        mock_run.assert_called_once_with(
            ["gh", "issue", "view", "1234", "--json", "title,body,labels"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Test caching - should not call subprocess again
        result2 = self.executor._fetch_issue_data()
        self.assertEqual(result2, mock_issue_data)
        self.assertEqual(mock_run.call_count, 1)  # Still only called once

    @patch("subprocess.run")
    def test_fetch_issue_data_failure(self, mock_run):
        """Test issue data fetching with GitHub CLI failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        result = self.executor._fetch_issue_data()

        expected = {"title": "Issue 1234", "body": "No description provided", "labels": []}
        self.assertEqual(result, expected)

    @patch("subprocess.run")
    def test_fetch_issue_data_cache_reset(self, mock_run):
        """Test that cache can be reset."""
        mock_issue_data = {"title": "Test", "body": "Body", "labels": []}
        mock_run.return_value = Mock(stdout=json.dumps(mock_issue_data))

        # First call
        self.executor._fetch_issue_data()
        self.assertEqual(mock_run.call_count, 1)

        # Reset cache
        self.executor._issue_data_cache = None

        # Second call should fetch again
        self.executor._fetch_issue_data()
        self.assertEqual(mock_run.call_count, 2)

    @patch("re.sub")
    def test_generate_title_slug_error_handling(self, mock_sub):
        """Test error handling in title slug generation."""
        # Mock regex error
        mock_sub.side_effect = Exception("Regex error")

        title = "Test Title with Error"
        result = self.executor._generate_title_slug(title)

        # Should fall back to simple replacement
        self.assertEqual(result, "test-title-with-error")

    def test_integration_branch_name_generation(self):
        """Test integration of all methods for branch name generation."""
        # Mock the issue data
        self.executor._issue_data_cache = {
            "title": "[SPRINT-4.3] Fix workflow branch name generation",
            "labels": [{"name": "bug"}, {"name": "sprint-current"}],
            "body": "Test body",
        }

        # Test the full flow
        issue_data = self.executor._fetch_issue_data()
        title_slug = self.executor._generate_title_slug(issue_data["title"])
        branch_type = self.executor._determine_branch_type(issue_data["labels"])
        branch_name = f"{branch_type}/{self.executor.issue_number}-{title_slug}"

        expected = "fix/1234-sprint-43-fix-workflow-branch-name-generation"
        self.assertEqual(branch_name, expected)


if __name__ == "__main__":
    unittest.main()
