#!/usr/bin/env python3
"""Tests for LLMReviewer class."""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    from src.agents.llm_reviewer import LLMReviewer

    anthropic_available = True
except ImportError:
    anthropic_available = False


@pytest.mark.skipif(not anthropic_available, reason="anthropic package not available")
class TestLLMReviewer:
    """Test cases for LLMReviewer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_api_key = "test-api-key-12345"
        self.mock_repo_root = Path("/tmp/test-repo")

    @patch("src.agents.llm_reviewer.anthropic")
    def test_init_with_api_key(self, mock_anthropic):
        """Test LLMReviewer initialization with API key."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key, verbose=True)

        assert reviewer.api_key == self.test_api_key
        assert reviewer.verbose is True
        assert reviewer.timeout == 120
        mock_anthropic.Anthropic.assert_called_once_with(api_key=self.test_api_key)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-api-key"})
    @patch("src.agents.llm_reviewer.anthropic")
    def test_init_with_env_var(self, mock_anthropic):
        """Test LLMReviewer initialization with environment variable."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer()

        assert reviewer.api_key == "env-api-key"
        mock_anthropic.Anthropic.assert_called_once_with(api_key="env-api-key")

    @patch("src.agents.llm_reviewer.anthropic")
    def test_init_no_api_key(self, mock_anthropic):
        """Test LLMReviewer initialization fails without API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY must be provided"):
            LLMReviewer()

    @patch("src.agents.llm_reviewer.anthropic")
    def test_tool_bash(self, mock_anthropic):
        """Test bash tool execution."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.return_value = (0, "output", "")
            result = reviewer._tool_bash("echo hello")

            assert result == "output"
            mock_run.assert_called_once()

    @patch("src.agents.llm_reviewer.anthropic")
    def test_tool_read(self, mock_anthropic):
        """Test read tool functionality."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch(
            "builtins.open",
            mock_open_multiple_files(
                {str(reviewer.repo_root / "test.py"): "line 1\nline 2\nline 3"}
            ),
        ):
            with patch.object(Path, "exists", return_value=True):
                result = reviewer._tool_read("test.py")

                expected_lines = ["     1→line 1", "     2→line 2", "     3→line 3"]
                assert result == "\n".join(expected_lines)

    @patch("src.agents.llm_reviewer.anthropic")
    def test_tool_read_file_not_found(self, mock_anthropic):
        """Test read tool with non-existent file."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(Path, "exists", return_value=False):
            result = reviewer._tool_read("nonexistent.py")

            assert "File not found: nonexistent.py" in result

    @patch("src.agents.llm_reviewer.anthropic")
    def test_tool_grep(self, mock_anthropic):
        """Test grep tool functionality."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.return_value = (0, "test.py:5:def test_function():", "")
            result = reviewer._tool_grep("test_function", "*.py")

            assert result == "test.py:5:def test_function():"
            mock_run.assert_called_once()

    @patch("src.agents.llm_reviewer.anthropic")
    def test_tool_glob(self, mock_anthropic):
        """Test glob tool functionality."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.return_value = (0, "./src/test.py\n./tests/test_file.py", "")
            result = reviewer._tool_glob("*.py")

            assert "./src/test.py" in result
            assert "./tests/test_file.py" in result

    @patch("src.agents.llm_reviewer.anthropic")
    def test_get_prompt_template(self, mock_anthropic):
        """Test prompt template extraction."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)
        prompt = reviewer._get_prompt_template()

        # Verify key elements of the prompt
        assert "ARC-Reviewer" in prompt
        assert "YAML" in prompt
        assert "schema_version" in prompt
        assert "verdict" in prompt
        assert "blocking" in prompt
        assert "Review criteria" in prompt

    @patch("src.agents.llm_reviewer.anthropic")
    def test_review_pr_success(self, mock_anthropic):
        """Test successful PR review."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Mock Claude API response
        mock_response = Mock()
        mock_response.content = [
            Mock(
                type="text",
                text="""schema_version: "1.0"
pr_number: 123
timestamp: "2025-07-27T10:00:00Z"
reviewer: "ARC-Reviewer"
verdict: "APPROVE"
summary: "All checks passed"
coverage:
  current_pct: 85.5
  status: "PASS"
  meets_baseline: true
issues:
  blocking: []
  warnings: []
  nits: []
automated_issues: []""",
            )
        ]

        mock_client.messages.create.return_value = mock_response

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.side_effect = [
                (0, "src/test.py\n", ""),  # changed files
                (0, "diff content", ""),  # full diff
            ]

            result = reviewer.review_pr(pr_number=123, base_branch="main")

            assert result["schema_version"] == "1.0"
            assert result["pr_number"] == 123
            assert result["verdict"] == "APPROVE"
            assert result["reviewer"] == "ARC-Reviewer"
            assert result["coverage"]["current_pct"] == 85.5

    @patch("src.agents.llm_reviewer.anthropic")
    def test_review_pr_with_tool_use(self, mock_anthropic):
        """Test PR review with Claude requesting tool use."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        # First response with tool use request
        mock_tool_request = Mock()
        mock_tool_request.type = "tool_use"
        mock_tool_request.name = "bash"
        mock_tool_request.id = "tool_123"
        mock_tool_request.input = {"command": "pytest --cov=src"}

        mock_response_1 = Mock()
        mock_response_1.content = [mock_tool_request]

        # Second response with final YAML
        mock_response_2 = Mock()
        mock_response_2.content = [
            Mock(
                type="text",
                text="""schema_version: "1.0"
pr_number: 123
verdict: "APPROVE"
summary: "Review completed with tool analysis"
coverage:
  current_pct: 78.5
  status: "PASS"
  meets_baseline: true
issues:
  blocking: []
  warnings: []
  nits: []
automated_issues: []""",
            )
        ]

        mock_client.messages.create.side_effect = [mock_response_1, mock_response_2]

        reviewer = LLMReviewer(api_key=self.test_api_key, verbose=True)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.side_effect = [
                (0, "src/test.py\n", ""),  # changed files
                (0, "diff content", ""),  # full diff
                (0, "test output", ""),  # tool execution
            ]

            result = reviewer.review_pr(pr_number=123)

            assert result["verdict"] == "APPROVE"
            assert mock_client.messages.create.call_count == 2

    @patch("src.agents.llm_reviewer.anthropic")
    def test_review_pr_api_error(self, mock_anthropic):
        """Test PR review with API error."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.side_effect = [(0, "src/test.py\n", ""), (0, "diff content", "")]

            result = reviewer.review_pr(pr_number=123)

            assert result["verdict"] == "REQUEST_CHANGES"
            assert result["reviewer"] == "ARC-Reviewer (LLM)"
            assert len(result["issues"]["blocking"]) == 1
            assert "API error" in result["issues"]["blocking"][0]["description"]

    @patch("src.agents.llm_reviewer.anthropic")
    def test_review_pr_yaml_parse_error(self, mock_anthropic):
        """Test PR review with invalid YAML response."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(type="text", text="Invalid YAML: [unclosed bracket")]
        mock_client.messages.create.return_value = mock_response

        reviewer = LLMReviewer(api_key=self.test_api_key)

        with patch.object(reviewer, "_run_command") as mock_run:
            mock_run.side_effect = [(0, "src/test.py\n", ""), (0, "diff content", "")]

            result = reviewer.review_pr(pr_number=123)

            assert result["verdict"] == "REQUEST_CHANGES"
            assert len(result["issues"]["blocking"]) == 1
            assert "parsing failed" in result["issues"]["blocking"][0]["description"]

    @patch("src.agents.llm_reviewer.anthropic")
    def test_format_yaml_output(self, mock_anthropic):
        """Test YAML formatting."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        reviewer = LLMReviewer(api_key=self.test_api_key)

        test_data = {
            "schema_version": "1.0",
            "verdict": "APPROVE",
            "issues": {"blocking": [], "warnings": [], "nits": []},
        }

        yaml_output = reviewer.format_yaml_output(test_data)

        assert "schema_version: '1.0'" in yaml_output
        assert "verdict: APPROVE" in yaml_output
        assert "blocking: []" in yaml_output


def mock_open_multiple_files(files_dict):
    """Helper to mock multiple file reads."""

    def mock_open_func(*args, **kwargs):
        filename = str(args[0])
        if filename in files_dict:
            mock_file = MagicMock()
            mock_file.read.return_value = files_dict[filename]
            mock_file.__enter__.return_value = mock_file
            return mock_file
        else:
            raise FileNotFoundError(f"No such file: {filename}")

    return mock_open_func


# Integration test (requires real API key)
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key required")
def test_llm_reviewer_integration():
    """Integration test with real API (requires ANTHROPIC_API_KEY)."""
    # This would make a real API call - only run with appropriate setup
    # reviewer = LLMReviewer(verbose=True)
    # result = reviewer.review_pr(pr_number=None, base_branch="main")
    # assert "schema_version" in result
    pass  # Placeholder for actual integration test
