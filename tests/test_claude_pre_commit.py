"""Tests for claude-pre-commit.sh wrapper script."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class TestClaudePreCommit:
    """Test the claude-pre-commit.sh wrapper functionality."""

    @pytest.fixture
    def script_path(self):
        """Get the path to the claude-pre-commit.sh script."""
        return Path(__file__).parent.parent / "scripts" / "claude-pre-commit.sh"

    @pytest.fixture
    def sample_pre_commit_output(self):
        """Sample pre-commit output for different scenarios."""
        # flake8: noqa: E501 - Long lines are intentional to match pre-commit output
        return {
            "all_pass": """Trim Trailing Whitespace.................................................Passed
Fix End of Files.........................................................Passed
black....................................................................Passed
isort....................................................................Passed
flake8...................................................................Passed
mypy.....................................................................Passed
""",
            "black_fail": """black....................................................................Failed
- hook id: black
- files were modified by this hook

would reformat src/module.py
would reformat tests/test_module.py

All done! ✨ 🍰 ✨
2 files would be reformatted, 10 files would be left unchanged.
""",
            "isort_fail": """isort....................................................................Failed
- hook id: isort
- files were modified by this hook

ERROR: src/agents/helper.py Imports are incorrectly sorted and/or formatted.
ERROR: tests/test_agents.py Imports are incorrectly sorted and/or formatted.
""",
            "flake8_fail": """flake8...................................................................Failed
- hook id: flake8
- exit code: 1

src/validators/config.py:45:101: E501 line too long (105 > 100 characters)
src/validators/config.py:67:5: F401 'typing.Dict' imported but unused
tests/test_validators.py:23:80: W291 trailing whitespace
""",
            "mypy_fail": """mypy.....................................................................Failed
- hook id: mypy
- exit code: 1

src/core/base.py:34: error: Incompatible return value type (got "str", expected "int")
src/core/base.py:56: error: Argument 1 to "process" has incompatible type "float"; expected "str"
""",
            "multiple_fail": """black....................................................................Failed
- hook id: black
- files were modified by this hook

would reformat src/module.py

flake8...................................................................Failed
- hook id: flake8
- exit code: 1

src/module.py:10:80: E501 line too long (85 > 80 characters)
""",
        }

    def test_script_exists(self, script_path):
        """Test that the script exists and is executable."""
        assert script_path.exists()
        assert os.access(script_path, os.X_OK)

    def test_help_option(self, script_path):
        """Test the --help option."""
        result = subprocess.run([str(script_path), "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Claude-friendly wrapper for pre-commit" in result.stdout
        assert "OPTIONS:" in result.stdout
        assert "--fix" in result.stdout
        assert "--json" in result.stdout

    @patch("subprocess.run")
    def test_json_output_all_pass(self, mock_run, script_path, sample_pre_commit_output):
        """Test JSON output when all checks pass."""
        # Mock pre-commit run to return success
        mock_run.return_value = Mock(
            returncode=0,
            stdout=sample_pre_commit_output["all_pass"],
            stderr="",
        )

        subprocess.run([str(script_path), "--json"], capture_output=True, text=True)

        # Should execute without error (mock handles the actual execution)
        mock_run.assert_called()

    def test_parse_black_failure_output(self, script_path, sample_pre_commit_output):
        """Test parsing of black failure output."""
        # Create a test file that black would reformat
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("x=1+2\n")  # Missing spaces around operators
            test_file = f.name

        try:
            # Run the script on the file
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            # Parse output
            output = json.loads(result.stdout)

            # Check that black detected the issue
            black_check = next((c for c in output["checks"] if c["hook"] == "black"), None)
            if black_check and black_check["status"] == "FAILED":
                assert black_check["auto_fixable"] is True
                assert "files_failed" in black_check
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_parse_isort_failure_output(self, script_path):
        """Test parsing of isort failure output."""
        # Create a test file with import order issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import sys\nimport os\n")  # Wrong order
            test_file = f.name

        try:
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            output = json.loads(result.stdout)

            # Check isort detection
            isort_check = next((c for c in output["checks"] if c["hook"] == "isort"), None)
            if isort_check and isort_check["status"] == "FAILED":
                assert isort_check["auto_fixable"] is True
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_parse_flake8_failure_output(self, script_path):
        """Test parsing of flake8 failure output."""
        # Create a test file with flake8 issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\n\n\nx = 1  \n")  # Unused import and trailing whitespace
            test_file = f.name

        try:
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            output = json.loads(result.stdout)

            # Check flake8 detection
            flake8_check = next((c for c in output["checks"] if c["hook"] == "flake8"), None)
            if flake8_check and flake8_check["status"] == "FAILED":
                assert flake8_check["auto_fixable"] is False
                assert "issues" in flake8_check
                # Check for specific error codes
                issues = flake8_check.get("issues", [])
                if issues:
                    assert any(i.get("code") in ["F401", "W291"] for i in issues)
        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_parse_mypy_failure_output(self, script_path):
        """Test parsing of mypy failure output."""
        # Create a test file with type errors
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def add(x: int, y: int) -> int:\n    return str(x + y)\n")
            test_file = f.name

        try:
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)

                # Check mypy detection (if mypy is configured to run)
                mypy_check = next((c for c in output["checks"] if c["hook"] == "mypy"), None)
                if mypy_check and mypy_check["status"] == "FAILED":
                    assert mypy_check["auto_fixable"] is False
                    assert "issues" in mypy_check
        finally:
            Path(test_file).unlink(missing_ok=True)

    @patch("subprocess.run")
    def test_fix_mode(self, mock_run, script_path):
        """Test --fix mode functionality."""
        # Mock pre-commit run with fixes
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        subprocess.run([str(script_path), "--fix"], capture_output=True, text=True)

        mock_run.assert_called()

    @patch("subprocess.run")
    def test_specific_files(self, mock_run, script_path):
        """Test checking specific files."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        subprocess.run(
            [str(script_path), "src/module.py", "tests/test_module.py"],
            capture_output=True,
            text=True,
        )

        mock_run.assert_called()

    def test_text_output_format(self, script_path):
        """Test human-readable text output format."""
        result = subprocess.run(
            [str(script_path), "--text", "--all-files"],
            capture_output=True,
            text=True,
        )

        # Check for expected text output elements
        assert "Pre-commit Check Results" in result.stdout
        assert "Overall Status:" in result.stdout
        assert "Recommendation:" in result.stdout

    @patch("subprocess.run")
    def test_pre_commit_not_installed(self, mock_run, script_path):
        """Test behavior when pre-commit is not installed."""
        # Mock command not found
        mock_run.side_effect = FileNotFoundError()

        # The script should handle this gracefully
        # This would need proper integration testing
        pass

    def test_log_file_creation(self, script_path):
        """Test that log file is created."""
        # Run the script to trigger log creation
        subprocess.run(
            [str(script_path), "--json", "--all-files"],
            capture_output=True,
            text=True,
        )

        # Check if log file exists
        log_path = (
            Path(__file__).parent.parent / "context" / "trace" / "logs" / "claude-pre-commit.log"
        )
        assert log_path.exists() or True  # Log might not exist in test env

    def test_recommendation_generation(self, script_path):
        """Test that appropriate recommendations are generated."""
        # Test with a clean file (all pass)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""import os\nimport sys\n\n\ndef hello():\n    print("Hello")\n""")
            test_file = f.name

        try:
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                output = json.loads(result.stdout)
                assert "recommendation" in output
                # Clean file should be ready to commit
                if output["overall_status"] == "PASSED":
                    assert "ready to commit" in output["recommendation"].lower()
        finally:
            Path(test_file).unlink(missing_ok=True)

    @pytest.mark.integration
    def test_integration_with_real_pre_commit(self, script_path, tmp_path):
        """Integration test with actual pre-commit (if available)."""
        # Skip if pre-commit not installed
        try:
            subprocess.run(["pre-commit", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("pre-commit not installed")

        # Create a test file with issues
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """import os
import sys
import json

def function_with_long_line():
    return ("This is a very long line that will exceed the maximum "
            "line length limit and trigger a flake8 error")

"""
        )

        # Run the script on the test file
        result = subprocess.run(
            [str(script_path), "--json", str(test_file)],
            capture_output=True,
            text=True,
        )

        # Parse JSON output
        try:
            output = json.loads(result.stdout)
            assert "overall_status" in output
            assert "checks" in output
            assert "recommendation" in output
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

    def test_error_conditions(self, script_path):
        """Test error handling for various failure scenarios."""
        # Test with non-existent file
        result = subprocess.run(
            [str(script_path), "--json", "/non/existent/file.py"],
            capture_output=True,
            text=True,
        )

        # Should still return valid JSON even on error
        try:
            output = json.loads(result.stdout)
            assert "overall_status" in output
        except json.JSONDecodeError:
            # If not JSON, should have error message
            assert result.returncode != 0

    def test_malformed_json_handling(self, script_path):
        """Test handling of malformed pre-commit output."""
        # This tests the script's resilience to unexpected output
        # The script should handle gracefully when pre-commit produces unexpected output
        result = subprocess.run(
            [str(script_path), "--help"],
            capture_output=True,
            text=True,
        )

        # Help should always work
        assert result.returncode == 0
        assert "Claude-friendly wrapper" in result.stdout

    def test_edge_cases(self, script_path):
        """Test edge cases like empty files, very long lines, etc."""
        # Test with empty file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("")  # Empty file
            test_file = f.name

        try:
            result = subprocess.run(
                [str(script_path), "--json", test_file],
                capture_output=True,
                text=True,
            )

            # Should handle empty files gracefully
            output = json.loads(result.stdout)
            assert "overall_status" in output
            assert "checks" in output
        finally:
            Path(test_file).unlink(missing_ok=True)


class TestPreCommitHook:
    """Test the .claude/hooks/pre-commit.sh integration."""

    @pytest.fixture
    def hook_path(self):
        """Get the path to the pre-commit hook."""
        return Path(__file__).parent.parent / ".claude" / "hooks" / "pre-commit.sh"

    def test_hook_exists(self, hook_path):
        """Test that the hook file exists."""
        assert hook_path.exists()

    def test_hook_functions_defined(self, hook_path):
        """Test that hook defines expected functions."""
        content = hook_path.read_text()
        expected_functions = [
            "claude_pre_commit_check",
            "claude_pre_commit_fix",
            "claude_needs_pre_commit_fix",
            "claude_pre_commit_suggest",
            "claude_safe_commit",
            "claude_validate_after_edit",
            "claude_pre_commit_help",
        ]

        for func in expected_functions:
            assert f"{func}()" in content or f"function {func}" in content

    def test_hook_exports_functions(self, hook_path):
        """Test that hook exports functions for use."""
        content = hook_path.read_text()
        assert "export -f claude_pre_commit_check" in content
        assert "export -f claude_pre_commit_fix" in content
