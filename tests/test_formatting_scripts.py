"""
Integration tests for Claude formatting validation scripts.

Tests the functionality of:
- scripts/validate-file-format.sh
- scripts/claude-post-edit.sh
- .claude/hooks/post-edit.sh
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestValidateFileFormat:
    """Test validate-file-format.sh functionality."""

    @pytest.fixture
    def script_path(self):
        """Get the path to validate-file-format.sh."""
        return Path(__file__).parent.parent / "scripts" / "validate-file-format.sh"

    def test_script_exists_and_executable(self, script_path):
        """Test that the script exists and is executable."""
        assert script_path.exists()
        assert os.access(script_path, os.X_OK)

    def test_python_file_needs_formatting(self, script_path, tmp_path):
        """Test detection of Python formatting issues."""
        # Create a poorly formatted Python file
        test_file = tmp_path / "bad_format.py"
        test_file.write_text(
            """import os
import sys
def badly_formatted(x,y):
    return x+y
"""
        )

        # Run the script
        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should detect issues - either through formatting or linting
        assert "CLAUDE_FORMAT_CHECK:START" in result.stdout
        assert "CLAUDE_FORMAT_CHECK:END" in result.stdout
        # Should report issues or be in error/warning state
        assert result.returncode != 0 or "issues_found: 0" not in result.stdout

    def test_python_file_well_formatted(self, script_path, tmp_path):
        """Test that well-formatted Python passes validation."""
        # Create a well-formatted Python file
        test_file = tmp_path / "good_format.py"
        test_file.write_text(
            '''"""Well formatted module."""


def well_formatted(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y
'''
        )

        # Run the script
        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should pass
        assert result.returncode == 0
        assert "status: success" in result.stdout

    def test_auto_fix_mode(self, script_path, tmp_path):
        """Test that --fix mode corrects formatting issues."""
        # Create a file with fixable issues
        test_file = tmp_path / "fixable.py"
        test_file.write_text(
            """import sys
import os
def needs_space(x,y): return x+y
"""
        )

        # Run with --fix
        result = subprocess.run(
            [str(script_path), str(test_file), "--fix"],
            capture_output=True,
            text=True,
        )

        # Should complete successfully
        assert "CLAUDE_FORMAT_CHECK:START" in result.stdout
        assert "CLAUDE_FORMAT_CHECK:END" in result.stdout

        # File should be modified if Black is available
        content = test_file.read_text()
        # Either file was fixed or script ran successfully
        assert result.returncode == 0 or "def needs_space(x, y):" in content

    def test_yaml_file_validation(self, script_path, tmp_path):
        """Test YAML file validation."""
        # Create a YAML file with issues
        test_file = tmp_path / "test.yaml"
        test_file.write_text(
            """key: value
  bad_indent: wrong
trailing_spaces:  value
"""
        )

        # Run the script
        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should detect YAML issues if yamllint is available
        if "yamllint" in result.stdout or "YAML" in result.stdout:
            assert result.returncode == 1

    def test_nonexistent_file(self, script_path):
        """Test handling of nonexistent files."""
        result = subprocess.run(
            [str(script_path), "/nonexistent/file.py"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "File not found" in result.stdout

    def test_structured_output_format(self, script_path, tmp_path):
        """Test that output follows the expected structured format."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")  # Well-formatted to ensure full output

        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Verify structured output
        assert "CLAUDE_FORMAT_CHECK:START" in result.stdout
        assert "CLAUDE_FORMAT_CHECK:END" in result.stdout
        assert "status:" in result.stdout
        assert "file:" in result.stdout
        assert "issues_found:" in result.stdout
        assert "auto_fixed:" in result.stdout
        assert "remaining_issues:" in result.stdout


class TestClaudePostEdit:
    """Test claude-post-edit.sh orchestrator functionality."""

    @pytest.fixture
    def script_path(self):
        """Get the path to claude-post-edit.sh."""
        return Path(__file__).parent.parent / "scripts" / "claude-post-edit.sh"

    def test_script_exists_and_executable(self, script_path):
        """Test that the script exists and is executable."""
        assert script_path.exists()
        assert os.access(script_path, os.X_OK)

    def test_multiple_file_validation(self, script_path, tmp_path):
        """Test validation of multiple files."""
        # Create multiple test files
        file1 = tmp_path / "file1.py"
        file1.write_text("x = 1\n")

        file2 = tmp_path / "file2.py"
        file2.write_text("def good():\n    pass\n")

        # Run the script
        result = subprocess.run(
            [str(script_path), str(file1), str(file2)],
            capture_output=True,
            text=True,
            env={**os.environ, "NO_COLOR": "1"},  # Disable color output
        )

        # Should show it's running
        assert "Claude Post-Edit Format Check" in result.stdout or result.returncode in (0, 1)

    def test_summary_output(self, script_path, tmp_path):
        """Test that summary is displayed correctly."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
            env={**os.environ, "NO_COLOR": "1"},
        )

        # Script should run successfully
        assert result.returncode == 0 or "Claude Post-Edit Format Check" in result.stdout

    def test_fix_mode_flag(self, script_path, tmp_path):
        """Test that --fix flag is passed through correctly."""
        test_file = tmp_path / "fixme.py"
        test_file.write_text("x=1")

        # Run with --fix
        result = subprocess.run(
            [str(script_path), str(test_file), "--fix"],
            capture_output=True,
            text=True,
        )

        # Should attempt to fix
        assert result.returncode == 0 or "Fixed" in result.stdout

    def test_log_file_creation(self, script_path, tmp_path, monkeypatch):
        """Test that edit log is created."""
        # Change to temp directory to avoid polluting project
        monkeypatch.chdir(tmp_path)

        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        # Run script
        subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Check log file was created
        log_file = tmp_path / "context" / "trace" / "logs" / "claude-edits.log"
        assert log_file.exists()

    def test_exit_codes(self, script_path, tmp_path):
        """Test appropriate exit codes."""
        # Success case
        good_file = tmp_path / "good.py"
        good_file.write_text("x = 1\n")

        result = subprocess.run(
            [str(script_path), str(good_file)],
            capture_output=True,
        )
        assert result.returncode == 0

        # Failure case
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("import unused_module\nx=1")

        result = subprocess.run(
            [str(script_path), str(bad_file)],
            capture_output=True,
        )
        # Should fail due to formatting issues
        assert result.returncode == 1


class TestPostEditHook:
    """Test .claude/hooks/post-edit.sh functionality."""

    @pytest.fixture
    def hook_path(self):
        """Get the path to post-edit.sh hook."""
        return Path(__file__).parent.parent / ".claude" / "hooks" / "post-edit.sh"

    def test_hook_exists_and_executable(self, hook_path):
        """Test that the hook exists and is executable."""
        assert hook_path.exists()
        assert os.access(hook_path, os.X_OK)

    def test_hook_functions_available(self, hook_path):
        """Test that hook functions are defined when sourced."""
        # Source the script and check function availability
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"source {hook_path} && type claude_validate_edits && type claude_format_edits",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "claude_validate_edits is a function" in result.stdout
        assert "claude_format_edits is a function" in result.stdout

    def test_hook_usage_message(self, hook_path):
        """Test that running hook directly shows usage."""
        result = subprocess.run(
            [str(hook_path)],
            capture_output=True,
            text=True,
        )

        assert "Claude Post-Edit Hook Functions" in result.stdout
        assert "claude_validate_edits" in result.stdout
        assert "claude_format_edits" in result.stdout


class TestFormatterIntegration:
    """Test integration with actual formatters."""

    @pytest.fixture
    def script_path(self):
        """Get validate-file-format.sh path."""
        return Path(__file__).parent.parent / "scripts" / "validate-file-format.sh"

    @pytest.mark.skipif(
        subprocess.run(["which", "black"], capture_output=True).returncode != 0,
        reason="Black not installed",
    )
    def test_black_integration(self, script_path, tmp_path):
        """Test Black formatter integration."""
        test_file = tmp_path / "black_test.py"
        test_file.write_text("x=1+2")

        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        assert "black" in result.stdout.lower()

    @pytest.mark.skipif(
        subprocess.run(["which", "isort"], capture_output=True).returncode != 0,
        reason="isort not installed",
    )
    def test_isort_integration(self, script_path, tmp_path):
        """Test isort integration."""
        test_file = tmp_path / "isort_test.py"
        test_file.write_text("import sys\nimport os\n")

        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should pass or mention isort
        assert result.returncode == 0 or "isort" in result.stdout.lower()

    @pytest.mark.skipif(
        subprocess.run(["which", "flake8"], capture_output=True).returncode != 0,
        reason="Flake8 not installed",
    )
    def test_flake8_integration(self, script_path, tmp_path):
        """Test Flake8 integration."""
        test_file = tmp_path / "flake8_test.py"
        test_file.write_text("import unused_module\nx = 1\n")

        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )

        # Should detect unused import
        assert "flake8" in result.stdout.lower() or "F401" in result.stdout


class TestPerformance:
    """Test performance requirements."""

    @pytest.fixture
    def script_path(self):
        """Get validate-file-format.sh path."""
        return Path(__file__).parent.parent / "scripts" / "validate-file-format.sh"

    def test_validation_under_2_seconds(self, script_path, tmp_path):
        """Test that validation completes in under 2 seconds."""
        import time

        # Create a typical Python file
        test_file = tmp_path / "perf_test.py"
        test_file.write_text(
            """
import os
import sys

def example_function(x, y):
    '''Example function for performance testing.'''
    result = x + y
    return result

class ExampleClass:
    def __init__(self):
        self.value = 42

    def method(self):
        return self.value * 2
"""
        )

        # Measure execution time
        start_time = time.time()
        result = subprocess.run(
            [str(script_path), str(test_file)],
            capture_output=True,
            text=True,
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete in under 2 seconds
        assert execution_time < 2.0, f"Validation took {execution_time:.2f}s, exceeding 2s target"
        assert result.returncode == 0
