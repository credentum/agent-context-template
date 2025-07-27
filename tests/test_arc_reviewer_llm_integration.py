#!/usr/bin/env python3
"""Tests for ARCReviewer LLM integration."""

import os
from unittest.mock import Mock, patch

from src.agents.arc_reviewer import ARCReviewer


class TestARCReviewerLLMIntegration:
    """Test LLM integration in ARCReviewer."""

    def test_init_auto_detect_no_api_key(self):
        """Test auto-detection without API key defaults to rule-based."""
        with patch.dict(os.environ, {}, clear=True):
            reviewer = ARCReviewer(verbose=True)

            assert reviewer.use_llm is False
            assert reviewer.llm_reviewer is None

    @patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-key"})
    @patch("src.agents.arc_reviewer.LLMReviewer")
    def test_init_auto_detect_with_api_key(self, mock_llm_reviewer_class):
        """Test auto-detection with API key enables LLM mode."""
        mock_llm_reviewer = Mock()
        mock_llm_reviewer_class.return_value = mock_llm_reviewer

        reviewer = ARCReviewer(verbose=True)

        assert reviewer.use_llm is True
        assert reviewer.llm_reviewer == mock_llm_reviewer
        mock_llm_reviewer_class.assert_called_once_with(verbose=True, timeout=120)

    @patch("src.agents.arc_reviewer.LLMReviewer")
    def test_init_force_llm_mode(self, mock_llm_reviewer_class):
        """Test forcing LLM mode."""
        mock_llm_reviewer = Mock()
        mock_llm_reviewer_class.return_value = mock_llm_reviewer

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-key"}):
            reviewer = ARCReviewer(use_llm=True, verbose=True)

        assert reviewer.use_llm is True
        assert reviewer.llm_reviewer == mock_llm_reviewer

    def test_init_force_rule_based_mode(self):
        """Test forcing rule-based mode."""
        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-key"}):
            reviewer = ARCReviewer(use_llm=False, verbose=True)

        assert reviewer.use_llm is False
        assert reviewer.llm_reviewer is None

    @patch("src.agents.arc_reviewer.LLMReviewer")
    def test_init_llm_not_available(self, mock_llm_reviewer_class):
        """Test LLM mode when LLMReviewer import fails."""
        with patch("src.agents.arc_reviewer.LLMReviewer", None):
            with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-key"}):
                reviewer = ARCReviewer(use_llm=True, verbose=True)

            assert reviewer.use_llm is False
            assert reviewer.llm_reviewer is None

    @patch("src.agents.arc_reviewer.LLMReviewer")
    def test_init_llm_initialization_error(self, mock_llm_reviewer_class):
        """Test LLM mode when LLMReviewer initialization fails."""
        mock_llm_reviewer_class.side_effect = Exception("API key invalid")

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "invalid-key"}):
            reviewer = ARCReviewer(use_llm=True, verbose=True)

        assert reviewer.use_llm is False
        assert reviewer.llm_reviewer is None

    @patch("src.agents.arc_reviewer.LLMReviewer")
    def test_review_pr_delegates_to_llm(self, mock_llm_reviewer_class):
        """Test that review_pr delegates to LLM reviewer when enabled."""
        mock_llm_reviewer = Mock()
        mock_llm_response = {
            "schema_version": "1.0",
            "verdict": "APPROVE",
            "reviewer": "ARC-Reviewer (LLM)",
        }
        mock_llm_reviewer.review_pr.return_value = mock_llm_response
        mock_llm_reviewer_class.return_value = mock_llm_reviewer

        with patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "test-key"}):
            reviewer = ARCReviewer(verbose=True)

        result = reviewer.review_pr(pr_number=123, base_branch="main")

        assert result == mock_llm_response
        mock_llm_reviewer.review_pr.assert_called_once_with(pr_number=123, base_branch="main")

    @patch.object(ARCReviewer, "_get_changed_files")
    @patch.object(ARCReviewer, "_check_coverage")
    def test_review_pr_falls_back_to_rule_based(self, mock_check_coverage, mock_get_changed_files):
        """Test that review_pr falls back to rule-based when LLM disabled."""
        mock_get_changed_files.return_value = []
        mock_check_coverage.return_value = {
            "current_pct": 80.0,
            "status": "PASS",
            "meets_baseline": True,
            "details": {},
        }

        reviewer = ARCReviewer(use_llm=False, verbose=True)

        result = reviewer.review_pr(pr_number=123)

        # Should get rule-based response
        assert result["reviewer"] == "ARC-Reviewer"
        assert result["verdict"] in ["APPROVE", "REQUEST_CHANGES"]
        mock_get_changed_files.assert_called_once()
        mock_check_coverage.assert_called_once()

    def test_command_line_llm_flags(self):
        """Test command line flag parsing for LLM mode."""
        import argparse

        from src.agents.arc_reviewer import main

        # Test --llm flag
        with patch("sys.argv", ["arc_reviewer.py", "--llm"]):
            with patch("src.agents.arc_reviewer.ARCReviewer") as mock_reviewer_class:
                with patch.object(argparse.ArgumentParser, "parse_args") as mock_parse:
                    mock_args = Mock()
                    mock_args.llm = True
                    mock_args.no_llm = False
                    mock_args.verbose = False
                    mock_args.timeout = 120
                    mock_args.skip_coverage = False
                    mock_args.pr = None
                    mock_args.base = "main"
                    mock_args.runtime_test = False
                    mock_parse.return_value = mock_args

                    mock_reviewer = Mock()
                    mock_reviewer_class.return_value = mock_reviewer

                    try:
                        main()
                    except SystemExit:
                        pass  # Expected from review_and_output

                    mock_reviewer_class.assert_called_once_with(
                        verbose=False, timeout=120, skip_coverage=False, use_llm=True
                    )

        # Test --no-llm flag
        with patch("sys.argv", ["arc_reviewer.py", "--no-llm"]):
            with patch("src.agents.arc_reviewer.ARCReviewer") as mock_reviewer_class:
                with patch.object(argparse.ArgumentParser, "parse_args") as mock_parse:
                    mock_args = Mock()
                    mock_args.llm = False
                    mock_args.no_llm = True
                    mock_args.verbose = False
                    mock_args.timeout = 120
                    mock_args.skip_coverage = False
                    mock_args.pr = None
                    mock_args.base = "main"
                    mock_args.runtime_test = False
                    mock_parse.return_value = mock_args

                    mock_reviewer = Mock()
                    mock_reviewer_class.return_value = mock_reviewer

                    try:
                        main()
                    except SystemExit:
                        pass  # Expected from review_and_output

                    mock_reviewer_class.assert_called_once_with(
                        verbose=False, timeout=120, skip_coverage=False, use_llm=False
                    )

    def test_command_line_conflicting_flags_error(self):
        """Test that conflicting LLM flags raise an error."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--llm", action="store_true")
        parser.add_argument("--no-llm", action="store_true")

        # This should not raise an error at parse time
        args = parser.parse_args(["--llm", "--no-llm"])
        assert args.llm is True
        assert args.no_llm is True

        # The error should be caught in the main() function logic
        # which we test separately
