#!/usr/bin/env python3
"""
Unit tests for workflow_test_utils module.

Tests all three utility functions with comprehensive coverage including
edge cases and integration scenarios.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from scripts.workflow_test_utils import (
    _extract_acceptance_criteria,
    _is_code_file,
    _parse_criteria_items,
    _verify_single_criterion,
    count_code_commits,
    validate_implementation_phase,
    verify_task_completion,
)


class TestValidateImplementationPhase:
    """Test validate_implementation_phase function."""

    @patch("subprocess.run")
    def test_validate_implementation_phase_success(self, mock_run):
        """Test successful validation with code changes."""
        # Mock git branch check
        mock_run.side_effect = [
            Mock(stdout="  feature/issue-1708", returncode=0),  # branch exists
        ]

        # Mock count_code_commits to return positive number
        with patch("scripts.workflow_test_utils.count_code_commits", return_value=2):
            # Mock task template verification
            with patch(
                "scripts.workflow_test_utils.verify_task_completion",
                return_value={"criterion1": True, "criterion2": True},
            ):
                with patch("pathlib.Path.glob", return_value=[Path("fake_template.md")]):
                    result = validate_implementation_phase(1708)
                    assert result is True

    @patch("subprocess.run")
    def test_validate_implementation_phase_no_branch(self, mock_run):
        """Test when no feature branch exists."""
        # Mock all branch checks returning empty
        mock_run.side_effect = [
            Mock(stdout="", returncode=0),  # feature/issue-1708
            Mock(stdout="", returncode=0),  # fix/issue-1708
            Mock(stdout="", returncode=0),  # issue-1708
            Mock(stdout="", returncode=0),  # feature/1708
        ]

        result = validate_implementation_phase(1708)
        assert result is False

    @patch("subprocess.run")
    def test_validate_implementation_phase_no_code_commits(self, mock_run):
        """Test when branch exists but no code commits."""
        mock_run.side_effect = [
            Mock(stdout="  feature/issue-1708", returncode=0),
        ]

        with patch("scripts.workflow_test_utils.count_code_commits", return_value=0):
            result = validate_implementation_phase(1708)
            assert result is False

    @patch("subprocess.run")
    def test_validate_implementation_phase_low_completion_rate(self, mock_run):
        """Test when completion rate is below 70%."""
        mock_run.side_effect = [
            Mock(stdout="  feature/issue-1708", returncode=0),
        ]

        with patch("scripts.workflow_test_utils.count_code_commits", return_value=1):
            # Only 1 out of 3 criteria met (33% < 70%)
            with patch(
                "scripts.workflow_test_utils.verify_task_completion",
                return_value={"c1": True, "c2": False, "c3": False},
            ):
                with patch("pathlib.Path.glob", return_value=[Path("fake_template.md")]):
                    result = validate_implementation_phase(1708)
                    assert result is False

    @patch("subprocess.run")
    def test_validate_implementation_phase_git_error(self, mock_run):
        """Test handling of git command errors."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = validate_implementation_phase(1708)
        assert result is False

    @patch("subprocess.run")
    def test_validate_implementation_phase_alternative_branch(self, mock_run):
        """Test finding alternative branch naming patterns."""
        mock_run.side_effect = [
            Mock(stdout="", returncode=0),  # feature/issue-1708 not found
            Mock(stdout="  fix/issue-1708", returncode=0),  # fix/issue-1708 found
        ]

        with patch("scripts.workflow_test_utils.count_code_commits", return_value=1):
            with patch("pathlib.Path.glob", return_value=[]):  # No template
                result = validate_implementation_phase(1708)
                assert result is True


class TestCountCodeCommits:
    """Test count_code_commits function."""

    @patch("subprocess.run")
    def test_count_code_commits_success(self, mock_run):
        """Test successful counting of code commits."""
        # Mock git log returning commit hashes
        mock_run.side_effect = [
            Mock(stdout="abc123 First commit\ndef456 Second commit", returncode=0),
            Mock(
                stdout="scripts/test.py\ntests/test_something.py", returncode=0
            ),  # First commit files
            Mock(stdout="README.md\ncontext/trace/doc.md", returncode=0),  # Second commit files
        ]

        result = count_code_commits("feature/test-branch")
        assert result == 1  # Only first commit has code files

    @patch("subprocess.run")
    def test_count_code_commits_no_commits(self, mock_run):
        """Test when branch has no commits."""
        mock_run.side_effect = [
            Mock(stdout="", returncode=0),  # No commits
        ]

        result = count_code_commits("feature/empty-branch")
        assert result == 0

    @patch("subprocess.run")
    def test_count_code_commits_all_doc_commits(self, mock_run):
        """Test when all commits only touch documentation."""
        mock_run.side_effect = [
            Mock(stdout="abc123 Doc update", returncode=0),
            Mock(stdout="README.md\ndocs/guide.md\ncontext/trace/task.md", returncode=0),
        ]

        result = count_code_commits("feature/docs-only")
        assert result == 0

    @patch("subprocess.run")
    def test_count_code_commits_git_error(self, mock_run):
        """Test handling of git command errors."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = count_code_commits("nonexistent-branch")
        assert result == 0

    @patch("subprocess.run")
    def test_count_code_commits_mixed_files(self, mock_run):
        """Test commits with mixed code and non-code files."""
        mock_run.side_effect = [
            Mock(stdout="abc123 Mixed commit\ndef456 Code commit", returncode=0),
            Mock(stdout="scripts/util.py\nREADME.md\ncontext/doc.md", returncode=0),  # Mixed
            Mock(stdout="src/main.py\ntests/test_main.py", returncode=0),  # Code only
        ]

        result = count_code_commits("feature/mixed-branch")
        assert result == 2  # Both commits have at least one code file


class TestVerifyTaskCompletion:
    """Test verify_task_completion function."""

    def test_verify_task_completion_success(self):
        """Test successful task completion verification."""
        task_content = """
# Task Template

## ✅ Acceptance Criteria
- [x] Create workflow_test_utils.py module
- [ ] Add comprehensive unit tests
- [x] Add docstrings with examples

## Other Section
Some other content.
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=task_content):
                with patch("pathlib.Path.glob", return_value=[]):  # Mock current file check
                    result = verify_task_completion(Path("fake_template.md"))

                    expected = {
                        "Create workflow_test_utils.py module": True,
                        "Add comprehensive unit tests": True,  # File exists check
                        "Add docstrings with examples": True,
                    }
                    assert result == expected

    def test_verify_task_completion_file_not_exists(self):
        """Test when task template file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = verify_task_completion(Path("nonexistent.md"))
            assert result == {}

    def test_verify_task_completion_no_criteria_section(self):
        """Test when template has no acceptance criteria section."""
        task_content = """
# Task Template

## Background
Some background info.

## Implementation
Some implementation notes.
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=task_content):
                result = verify_task_completion(Path("no_criteria.md"))
                assert result == {}

    def test_verify_task_completion_read_error(self):
        """Test handling of file read errors."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", side_effect=Exception("Read error")):
                result = verify_task_completion(Path("error_file.md"))
                assert result == {}

    def test_verify_task_completion_alternative_header(self):
        """Test with alternative acceptance criteria header format."""
        task_content = """
# Task Template

## Acceptance Criteria
- Create new utility functions
- Add error handling
- Write documentation

## Summary
End of template.
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=task_content):
                result = verify_task_completion(Path("alt_header.md"))

                expected = {
                    "Create new utility functions": True,
                    "Add error handling": True,
                    "Write documentation": True,
                }
                assert result == expected


class TestHelperFunctions:
    """Test private helper functions."""

    def test_is_code_file_python_files(self):
        """Test identification of Python code files."""
        assert _is_code_file("scripts/util.py") is True
        assert _is_code_file("src/main.py") is True
        assert _is_code_file("tests/test_something.py") is True

    def test_is_code_file_documentation_files(self):
        """Test exclusion of documentation files."""
        assert _is_code_file("README.md") is False
        assert _is_code_file("docs/guide.rst") is False
        assert _is_code_file("CHANGELOG.txt") is False

    def test_is_code_file_context_files(self):
        """Test exclusion of context/trace files."""
        assert _is_code_file("context/trace/task.md") is False
        assert _is_code_file("context/decisions/adr-001.md") is False

    def test_is_code_file_config_files(self):
        """Test exclusion of configuration files."""
        assert _is_code_file(".gitignore") is False
        assert _is_code_file("setup.py") is False  # Config, not implementation code
        assert _is_code_file("requirements.txt") is False
        assert _is_code_file("Dockerfile") is False

    def test_is_code_file_other_languages(self):
        """Test identification of other language code files."""
        assert _is_code_file("script.sh") is True
        assert _is_code_file("app.js") is True
        assert _is_code_file("main.go") is True
        assert _is_code_file("lib.rs") is True

    def test_is_code_file_code_directories(self):
        """Test files in code directories."""
        assert _is_code_file("lib/helper") is True
        assert _is_code_file("bin/executable") is True

    def test_extract_acceptance_criteria_standard_format(self):
        """Test extraction of standard acceptance criteria format."""
        content = """
# Template

## ✅ Acceptance Criteria
- Criterion 1
- Criterion 2

## Next Section
Other content.
"""
        result = _extract_acceptance_criteria(content)
        assert "- Criterion 1\n- Criterion 2" in result

    def test_extract_acceptance_criteria_not_found(self):
        """Test when no acceptance criteria section exists."""
        content = """
# Template

## Background
Some content.

## Implementation
More content.
"""
        result = _extract_acceptance_criteria(content)
        assert result is None

    def test_parse_criteria_items_checkboxes(self):
        """Test parsing criteria items with checkboxes."""
        criteria_section = """
- [x] Completed item
- [ ] Pending item
- [x] Another completed item
"""
        result = _parse_criteria_items(criteria_section)
        expected = ["Completed item", "Pending item", "Another completed item"]
        assert result == expected

    def test_parse_criteria_items_bullets(self):
        """Test parsing criteria items with bullet points."""
        criteria_section = """
- First criterion
- Second criterion
- Third criterion
"""
        result = _parse_criteria_items(criteria_section)
        expected = ["First criterion", "Second criterion", "Third criterion"]
        assert result == expected

    def test_verify_single_criterion_file_creation(self):
        """Test verification of file creation criteria."""
        with patch("pathlib.Path.exists", return_value=True):
            result = _verify_single_criterion("Create workflow_test_utils.py")
            assert result is True

    def test_verify_single_criterion_test_files(self):
        """Test verification of test-related criteria."""
        with patch("pathlib.Path.glob", return_value=[Path("test_something.py")]):
            result = _verify_single_criterion("Add comprehensive unit tests")
            assert result is True

    def test_verify_single_criterion_documentation(self):
        """Test verification of documentation criteria."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value='"""Docstring"""'):
                result = _verify_single_criterion("Add docstrings with examples")
                assert result is True

    def test_verify_single_criterion_default(self):
        """Test default behavior for unrecognized criteria."""
        result = _verify_single_criterion("Some unknown criterion")
        assert result is True  # Default to True for unknown criteria


class TestIntegration:
    """Integration tests combining multiple functions."""

    @patch("subprocess.run")
    def test_full_workflow_validation(self, mock_run):
        """Test complete workflow validation scenario."""
        # Setup mock git responses
        mock_run.side_effect = [
            Mock(stdout="  feature/issue-123", returncode=0),  # Branch exists
            Mock(stdout="abc123 Add utilities\ndef456 Add tests", returncode=0),  # Commits
            Mock(stdout="scripts/workflow_test_utils.py", returncode=0),  # First commit files
            Mock(stdout="tests/test_workflow_test_utils.py", returncode=0),  # Second commit files
        ]

        # Mock task template
        task_content = """
## ✅ Acceptance Criteria
- [x] Create workflow_test_utils.py
- [x] Add unit tests
- [x] Add docstrings
"""

        with patch("pathlib.Path.glob", return_value=[Path("template.md")]):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.read_text", return_value=task_content):
                    result = validate_implementation_phase(123)
                    assert result is True

    @patch("subprocess.run")
    def test_documentation_only_scenario(self, mock_run):
        """Test scenario where only documentation was created (should fail)."""
        mock_run.side_effect = [
            Mock(stdout="  feature/issue-456", returncode=0),  # Branch exists
            Mock(stdout="abc123 Add docs", returncode=0),  # One commit
            Mock(stdout="README.md\ncontext/trace/task.md", returncode=0),  # Only docs
        ]

        result = validate_implementation_phase(456)
        assert result is False  # Should fail - no code changes


if __name__ == "__main__":
    pytest.main([__file__])
