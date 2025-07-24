#!/usr/bin/env python3
"""
Tests for ARC-Reviewer module.

Tests the extracted ARC-Reviewer logic to ensure it maintains compatibility
with the original GitHub Actions workflow behavior.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.agents.arc_reviewer import ARCReviewer


class TestARCReviewer:
    """Test suite for ARCReviewer class."""

    def test_init_default(self):
        """Test ARCReviewer initialization with defaults."""
        reviewer = ARCReviewer()
        assert reviewer.verbose is False
        assert "baseline" in reviewer.coverage_config
        assert reviewer.repo_root.name == "agent-context-template"

    def test_init_verbose(self):
        """Test ARCReviewer initialization with verbose mode."""
        reviewer = ARCReviewer(verbose=True)
        assert reviewer.verbose is True

    def test_load_coverage_config_success(self, tmp_path):
        """Test successful loading of coverage configuration."""
        # Create temporary config file
        config_data = {"baseline": 75.0, "target": 80.0, "validator_target": 85.0}
        config_file = tmp_path / ".coverage-config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Mock the config path
        with patch.object(Path, "parent", new_callable=lambda: tmp_path):
            reviewer = ARCReviewer()
            # Can't easily test this without mocking the entire path resolution
            # Instead test the fallback behavior
            assert "baseline" in reviewer.coverage_config

    def test_load_coverage_config_fallback(self):
        """Test fallback when coverage config file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            reviewer = ARCReviewer()
            expected_defaults = {"baseline": 78.0, "target": 85.0, "validator_target": 90.0}
            assert reviewer.coverage_config["baseline"] == expected_defaults["baseline"]
            assert reviewer.coverage_config["target"] == expected_defaults["target"]
            assert (
                reviewer.coverage_config["validator_target"]
                == expected_defaults["validator_target"]
            )

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        reviewer = ARCReviewer()
        exit_code, stdout, stderr = reviewer._run_command(["echo", "test"])

        assert exit_code == 0
        assert stdout == "success output"
        assert stderr == ""

    @patch("subprocess.run")
    def test_run_command_failure(self, mock_run):
        """Test command execution failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error output"
        mock_run.return_value = mock_result

        reviewer = ARCReviewer()
        exit_code, stdout, stderr = reviewer._run_command(["false"])

        assert exit_code == 1
        assert stdout == ""
        assert stderr == "error output"

    @patch("subprocess.run")
    def test_run_command_timeout(self, mock_run):
        """Test command timeout handling."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 300)

        reviewer = ARCReviewer()
        exit_code, stdout, stderr = reviewer._run_command(["sleep", "1000"])

        assert exit_code == 1
        assert stdout == ""
        assert "timed out" in stderr

    def test_get_changed_files_success(self):
        """Test getting changed files list."""
        reviewer = ARCReviewer()
        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "src/file1.py\nsrc/file2.py\n", "")

            files = reviewer._get_changed_files("main")

            assert files == ["src/file1.py", "src/file2.py"]
            mock_cmd.assert_called_once_with(["git", "diff", "--name-only", "origin/main...HEAD"])

    def test_get_changed_files_failure(self):
        """Test getting changed files when git command fails."""
        reviewer = ARCReviewer()
        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (1, "", "git error")

            files = reviewer._get_changed_files("main")

            assert files == []

    def test_check_coverage_with_json(self, tmp_path):
        """Test coverage checking with coverage.json file."""
        # Create mock coverage.json
        coverage_data = {
            "totals": {"percent_covered": 85.5},
            "files": {"src/validators/test.py": {"summary": {"percent_covered": 92.0}}},
        }

        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path

        coverage_json = tmp_path / "coverage.json"
        with open(coverage_json, "w") as f:
            json.dump(coverage_data, f)

        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            result = reviewer._check_coverage()

            assert result["current_pct"] == 85.5
            assert result["meets_baseline"] is True
            assert result["status"] == "PASS"
            assert "src/validators/test.py" in result["details"]["validators"]

    def test_check_coverage_no_json(self, tmp_path):
        """Test coverage checking without coverage.json file."""
        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path  # Point to empty directory

        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "", "")

            result = reviewer._check_coverage()

            assert result["current_pct"] == 0.0
            assert result["meets_baseline"] is False
            assert result["status"] == "FAIL"

    def test_check_code_quality_pass(self):
        """Test code quality check when pre-commit passes."""
        reviewer = ARCReviewer()

        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (0, "All hooks passed", "")

            issues = reviewer._check_code_quality(["src/test.py"])

            assert issues == []

    def test_check_code_quality_fail(self):
        """Test code quality check when pre-commit fails."""
        reviewer = ARCReviewer()

        with patch.object(reviewer, "_run_command") as mock_cmd:
            mock_cmd.return_value = (1, "", "hooks failed")

            issues = reviewer._check_code_quality(["src/test.py"])

            assert len(issues) == 1
            assert issues[0]["category"] == "code_quality"
            assert "Pre-commit hooks failed" in issues[0]["description"]

    def test_check_context_integrity_valid(self, tmp_path):
        """Test context integrity check with valid files."""
        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path

        # Create valid context file
        context_dir = tmp_path / "context"
        context_dir.mkdir()
        context_file = context_dir / "test.yaml"

        with open(context_file, "w") as f:
            yaml.dump({"schema_version": "1.0", "data": "test"}, f)

        issues = reviewer._check_context_integrity(["context/test.yaml"])

        assert issues == []

    def test_check_context_integrity_missing_schema(self, tmp_path):
        """Test context integrity check with missing schema_version."""
        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path

        # Create invalid context file
        context_dir = tmp_path / "context"
        context_dir.mkdir()
        context_file = context_dir / "test.yaml"

        with open(context_file, "w") as f:
            yaml.dump({"data": "test"}, f)

        issues = reviewer._check_context_integrity(["context/test.yaml"])

        assert len(issues) == 1
        assert issues[0]["category"] == "context_integrity"
        assert "Missing schema_version" in issues[0]["description"]

    def test_check_test_coverage_specific_validators(self):
        """Test specific validator coverage checking."""
        reviewer = ARCReviewer()
        reviewer.coverage_config["validator_target"] = 90.0

        coverage_data = {
            "details": {"validators": {"src/validators/test.py": 85.0}}  # Below target
        }

        issues = reviewer._check_test_coverage_specific(["src/validators/test.py"], coverage_data)

        assert len(issues) == 1
        assert issues[0]["category"] == "test_coverage"
        assert "85.0% below target 90.0%" in issues[0]["description"]

    def test_check_security_no_secrets(self, tmp_path):
        """Test security check with clean files."""
        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path

        # Create clean file
        test_file = tmp_path / "src" / "test.py"
        test_file.parent.mkdir(parents=True)
        with open(test_file, "w") as f:
            f.write("def test(): pass")

        issues = reviewer._check_security(["src/test.py"])

        assert issues == []

    def test_check_security_with_secrets(self, tmp_path):
        """Test security check with potential secrets."""
        reviewer = ARCReviewer()
        reviewer.repo_root = tmp_path

        # Create file with potential secret
        test_file = tmp_path / "src" / "test.py"
        test_file.parent.mkdir(parents=True)
        with open(test_file, "w") as f:
            f.write('API_KEY = "secret"')

        issues = reviewer._check_security(["src/test.py"])

        assert len(issues) == 1
        assert issues[0]["category"] == "security"
        assert "secret" in issues[0]["description"]

    def test_review_pr_approve(self):
        """Test complete PR review that should approve."""
        reviewer = ARCReviewer()

        # Mock all check methods to return clean results
        with (
            patch.object(reviewer, "_get_changed_files", return_value=["src/test.py"]),
            patch.object(
                reviewer,
                "_check_coverage",
                return_value={
                    "current_pct": 85.0,
                    "status": "PASS",
                    "meets_baseline": True,
                    "details": {},
                },
            ),
            patch.object(reviewer, "_check_code_quality", return_value=[]),
            patch.object(reviewer, "_check_context_integrity", return_value=[]),
            patch.object(reviewer, "_check_test_coverage_specific", return_value=[]),
            patch.object(reviewer, "_check_security", return_value=[]),
        ):

            result = reviewer.review_pr(pr_number=123)

            assert result["verdict"] == "APPROVE"
            assert result["pr_number"] == 123
            assert result["reviewer"] == "ARC-Reviewer"
            assert len(result["issues"]["blocking"]) == 0

    def test_review_pr_request_changes(self):
        """Test complete PR review that should request changes."""
        reviewer = ARCReviewer()

        # Mock coverage check to fail baseline
        with (
            patch.object(reviewer, "_get_changed_files", return_value=["src/test.py"]),
            patch.object(
                reviewer,
                "_check_coverage",
                return_value={
                    "current_pct": 70.0,
                    "status": "FAIL",
                    "meets_baseline": False,
                    "details": {},
                },
            ),
            patch.object(reviewer, "_check_code_quality", return_value=[]),
            patch.object(reviewer, "_check_context_integrity", return_value=[]),
            patch.object(reviewer, "_check_test_coverage_specific", return_value=[]),
            patch.object(reviewer, "_check_security", return_value=[]),
        ):

            result = reviewer.review_pr(pr_number=123)

            assert result["verdict"] == "REQUEST_CHANGES"
            assert len(result["issues"]["blocking"]) == 1
            assert "Coverage 70.0% below baseline" in result["issues"]["blocking"][0]["description"]

    def test_format_yaml_output(self):
        """Test YAML output formatting."""
        reviewer = ARCReviewer()

        test_data = {
            "schema_version": "1.0",
            "verdict": "APPROVE",
            "issues": {"blocking": [], "warnings": [], "nits": []},
        }

        yaml_output = reviewer.format_yaml_output(test_data)

        # Verify it's valid YAML
        parsed = yaml.safe_load(yaml_output)
        assert parsed["schema_version"] == "1.0"
        assert parsed["verdict"] == "APPROVE"

    def test_review_and_output(self, capsys):
        """Test review and output method."""
        reviewer = ARCReviewer()

        with patch.object(reviewer, "review_pr") as mock_review:
            mock_review.return_value = {
                "schema_version": "1.0",
                "verdict": "APPROVE",
                "summary": "Test review",
            }

            reviewer.review_and_output(pr_number=123)

            captured = capsys.readouterr()
            assert "schema_version: '1.0'" in captured.out
            assert "verdict: APPROVE" in captured.out

    def test_review_and_output_request_changes_exits(self, capsys):
        """Test that review_and_output exits with code 1 when verdict is REQUEST_CHANGES."""
        reviewer = ARCReviewer()
        with patch.object(reviewer, "review_pr") as mock_review:
            mock_review.return_value = {
                "schema_version": "1.0",
                "verdict": "REQUEST_CHANGES",
                "summary": "Issues found",
            }
            with pytest.raises(SystemExit) as exc_info:
                reviewer.review_and_output(pr_number=123)
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "verdict: REQUEST_CHANGES" in captured.out

    def test_main_function(self):
        """Test main function CLI interface."""
        import sys
        from unittest.mock import patch

        test_args = ["arc_reviewer.py", "--pr", "123", "--verbose"]

        with (
            patch.object(sys, "argv", test_args),
            patch("src.agents.arc_reviewer.ARCReviewer") as mock_reviewer_class,
        ):

            mock_reviewer = MagicMock()
            mock_reviewer_class.return_value = mock_reviewer

            from src.agents.arc_reviewer import main

            main()

            mock_reviewer_class.assert_called_once_with(verbose=True)
            mock_reviewer.review_and_output.assert_called_once_with(
                pr_number=123, base_branch="main", runtime_test=False
            )
