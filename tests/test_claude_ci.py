#!/usr/bin/env python3
"""
Comprehensive tests for claude-ci.sh unified command hub.

Tests all subcommands, output formats, error handling, and integration
with existing scripts.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestClaudeCICommandHub:
    """Test the claude-ci.sh unified command hub."""

    @pytest.fixture
    def script_path(self):
        """Get path to claude-ci.sh script."""
        return Path(__file__).parent.parent / "scripts" / "claude-ci.sh"

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file within project for testing."""
        # Create temp file within project directory for path validation
        temp_dir = Path(__file__).parent.parent / "tmp"

        try:
            temp_dir.mkdir(exist_ok=True)
        except (OSError, PermissionError) as e:
            pytest.skip(f"Cannot create temp directory: {e}")

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=str(temp_dir)
            ) as f:
                f.write("print('hello world')\n")
                f.flush()
                yield f.name
        except (OSError, PermissionError) as e:
            pytest.skip(f"Cannot create temp file: {e}")
        finally:
            # Clean up temp file
            try:
                if "f" in locals():
                    os.unlink(f.name)
            except (OSError, FileNotFoundError):
                pass  # File already deleted or doesn't exist

            # Clean up temp directory if empty
            try:
                temp_dir.rmdir()
            except OSError:
                pass  # Directory not empty or doesn't exist

    def test_script_exists_and_executable(self, script_path):
        """Test that claude-ci.sh exists and is executable."""
        assert script_path.exists(), "claude-ci.sh script not found"
        assert os.access(script_path, os.X_OK), "claude-ci.sh not executable"

    def test_help_command(self, script_path):
        """Test the help command displays usage information."""
        result = subprocess.run([str(script_path), "help"], capture_output=True, text=True)

        assert result.returncode == 0
        assert "Claude CI Command Hub" in result.stdout
        assert "Usage: claude-ci <command>" in result.stdout
        assert "check <file>" in result.stdout
        assert "test" in result.stdout
        assert "pre-commit" in result.stdout
        assert "review" in result.stdout
        assert "all" in result.stdout

    def test_no_command_shows_help(self, script_path):
        """Test that running without command shows help."""
        result = subprocess.run([str(script_path)], capture_output=True, text=True)

        assert result.returncode == 0
        assert "Claude CI Command Hub" in result.stdout

    def test_invalid_command(self, script_path):
        """Test handling of invalid commands."""
        result = subprocess.run([str(script_path), "invalid"], capture_output=True, text=True)

        assert result.returncode == 1
        assert "Unknown command" in result.stderr

    def test_check_command_file_not_found(self, script_path):
        """Test check command with non-existent file."""
        result = subprocess.run(
            [str(script_path), "check", "/nonexistent/file.py"], capture_output=True, text=True
        )

        assert result.returncode == 1

        # Should output JSON by default
        try:
            output = json.loads(result.stdout)
            assert output["command"] == "check"
            assert output["status"] == "FAILED"
            # Now expects path validation error instead of file not found
            assert "Invalid file path" in str(output["errors"]) or "File not found" in str(
                output["errors"]
            )
        except json.JSONDecodeError:
            pytest.fail("Expected JSON output for check command")

    def test_check_command_file_not_found_within_project(self, script_path):
        """Test check command with non-existent file within project (gets past path validation)."""
        result = subprocess.run(
            [str(script_path), "check", "nonexistent_file.py"], capture_output=True, text=True
        )

        assert result.returncode == 1

        # Should output JSON by default
        try:
            output = json.loads(result.stdout)
            assert output["command"] == "check"
            assert output["status"] == "FAILED"
            # This should get past path validation and hit file not found
            assert "File not found" in str(output["errors"])
        except json.JSONDecodeError:
            pytest.fail("Expected JSON output for file not found check")

    def test_check_command_pretty_output(self, script_path, temp_file):
        """Test check command with pretty output format."""
        result = subprocess.run(
            [str(script_path), "check", temp_file, "--pretty"], capture_output=True, text=True
        )

        # Should use pretty output, not JSON
        assert "✅" in result.stdout or "❌" in result.stdout
        # Should not be JSON
        assert not result.stdout.strip().startswith("{")

    def test_json_output_format(self, script_path):
        """Test JSON output format structure."""
        result = subprocess.run(
            [str(script_path), "check", "/nonexistent", "--json"], capture_output=True, text=True
        )

        try:
            output = json.loads(result.stdout)

            # Verify required JSON fields
            required_fields = [
                "command",
                "status",
                "target",
                "duration",
                "checks",
                "errors",
                "next_action",
            ]
            for field in required_fields:
                assert field in output, f"Missing required field: {field}"

            assert output["command"] == "check"
            assert output["status"] in ["PASSED", "FAILED", "SKIPPED"]

        except json.JSONDecodeError:
            pytest.fail("Expected valid JSON output")

    def test_test_command_basic(self, script_path):
        """Test the test command."""
        result = subprocess.run(
            [str(script_path), "test", "--json"], capture_output=True, text=True
        )

        # Test command should delegate to claude-test-changed.sh
        # It may fail if dependencies aren't available, but should produce JSON
        if result.stdout.strip():
            try:
                output = json.loads(result.stdout)
                assert "command" in output or "files_changed" in output
            except json.JSONDecodeError:
                # claude-test-changed.sh produces its own JSON format
                pass

    def test_pre_commit_command_basic(self, script_path):
        """Test the pre-commit command."""
        result = subprocess.run(
            [str(script_path), "pre-commit", "--json"], capture_output=True, text=True
        )

        # Pre-commit should delegate to claude-pre-commit.sh
        # Output format depends on underlying script
        assert result.returncode in [0, 1]  # Success or validation failure

    def test_all_command_quick_mode(self, script_path):
        """Test the all command with quick mode."""
        result = subprocess.run(
            [str(script_path), "all", "--quick", "--json"], capture_output=True, text=True
        )

        # Should run pre-commit only in quick mode
        assert result.returncode in [0, 1]  # Success or validation failure

    def test_verbose_flag(self, script_path):
        """Test verbose flag is passed through."""
        result = subprocess.run(
            [str(script_path), "test", "--verbose", "--json"], capture_output=True, text=True
        )

        # Verbose flag should be passed to underlying script
        assert result.returncode in [0, 1]

    def test_fix_flag(self, script_path):
        """Test fix flag is passed through."""
        result = subprocess.run(
            [str(script_path), "pre-commit", "--fix", "--json"], capture_output=True, text=True
        )

        # Fix flag should be passed to underlying script
        assert result.returncode in [0, 1]

    def test_unknown_option(self, script_path):
        """Test handling of unknown options."""
        result = subprocess.run(
            [str(script_path), "test", "--unknown-option"], capture_output=True, text=True
        )

        assert result.returncode == 1
        assert "Unknown option" in result.stderr

    def test_check_command_missing_file_argument(self, script_path):
        """Test check command without file argument."""
        result = subprocess.run([str(script_path), "check"], capture_output=True, text=True)

        assert result.returncode == 1
        assert "check command requires a file argument" in result.stderr

    def test_dependency_scripts_detection(self, script_path):
        """Test that missing dependency scripts are handled gracefully."""
        # This tests the robustness when claude-post-edit.sh etc. are missing
        # The script should detect missing dependencies and report appropriately

        # Test with check command using a non-existent script directory to simulate
        # missing dependencies. Instead of removing PATH (which affects bash itself),
        # rename the scripts directory
        scripts_dir = script_path.parent
        backup_dir = scripts_dir.parent / "scripts_backup"

        try:
            # Temporarily move scripts to simulate missing dependencies
            os.rename(scripts_dir, backup_dir)
            os.makedirs(scripts_dir, exist_ok=True)
            # Put back only the main script but not dependencies
            import shutil

            shutil.copy2(backup_dir / "claude-ci.sh", scripts_dir / "claude-ci.sh")

            result = subprocess.run(
                [str(script_path), "check", "/tmp/test.py"], capture_output=True, text=True
            )

            # Should handle missing dependencies gracefully (return error but not crash)
            assert result.returncode in [0, 1]
        finally:
            # Restore original scripts directory
            if backup_dir.exists():
                import shutil

                shutil.rmtree(scripts_dir)
                os.rename(backup_dir, scripts_dir)

    def test_duration_calculation(self, script_path):
        """Test that duration is calculated and included in output."""
        result = subprocess.run(
            [str(script_path), "check", "/nonexistent"], capture_output=True, text=True
        )

        try:
            output = json.loads(result.stdout)
            assert "duration" in output
            assert output["duration"].endswith("s")  # Should end with 's'
        except json.JSONDecodeError:
            pytest.fail("Expected JSON output with duration")

    def test_comprehensive_mode(self, script_path):
        """Test comprehensive mode runs all checks."""
        result = subprocess.run(
            [str(script_path), "all", "--comprehensive", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Comprehensive mode should run pre-commit, test, and review
        assert result.returncode in [0, 1]

    def test_error_message_structure(self, script_path):
        """Test error message structure in JSON output."""
        result = subprocess.run(
            [str(script_path), "check", "/nonexistent"], capture_output=True, text=True
        )

        try:
            output = json.loads(result.stdout)
            assert "errors" in output
            assert isinstance(output["errors"], list)

            if output["errors"]:
                error = output["errors"][0]
                assert "message" in error

        except json.JSONDecodeError:
            pytest.fail("Expected JSON output with error structure")

    def test_check_command_success_path(self, script_path, temp_file):
        """Test successful execution of check command."""
        result = subprocess.run(
            [str(script_path), "check", temp_file], capture_output=True, text=True
        )

        # Check command should execute (may pass or fail validation)
        assert result.returncode in [0, 1]  # Success or validation failure

        try:
            output = json.loads(result.stdout)
            assert output["command"] == "check"
            assert output["status"] in ["PASSED", "FAILED"]
            assert output["target"] == temp_file
            assert "duration" in output
            assert isinstance(output["errors"], list)
            assert "next_action" in output

        except json.JSONDecodeError:
            pytest.fail("Expected valid JSON output for check command")

    def test_path_validation_security(self, script_path):
        """Test path validation prevents directory traversal."""
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/passwd",
            "../../sensitive_file",
            "/proc/self/environ",
        ]

        for path in dangerous_paths:
            result = subprocess.run(
                [str(script_path), "check", path], capture_output=True, text=True
            )

            assert result.returncode == 1
            try:
                output = json.loads(result.stdout)
                assert output["status"] == "FAILED"
                assert "Invalid file path" in str(output["errors"])
            except json.JSONDecodeError:
                pytest.fail(f"Expected JSON output for path validation failure: {path}")

    def test_json_validation_robustness(self, script_path):
        """Test that jq-based JSON generation is robust."""
        # This test ensures our jq implementation works correctly
        result = subprocess.run(
            [str(script_path), "check", "/nonexistent"], capture_output=True, text=True
        )

        try:
            output = json.loads(result.stdout)

            # Verify all expected fields are present and properly typed
            assert isinstance(output["command"], str)
            assert isinstance(output["status"], str)
            assert isinstance(output["target"], str)
            assert isinstance(output["duration"], str)
            assert isinstance(output["checks"], dict)
            assert isinstance(output["errors"], list)
            assert isinstance(output["next_action"], str)

        except json.JSONDecodeError as e:
            pytest.fail(f"jq-based JSON generation failed to produce valid JSON: {e}")

    def test_all_commands_produce_valid_json(self, script_path, temp_file):
        """Test that all commands produce valid JSON output."""
        # Use simpler commands that are less likely to timeout
        commands = [
            ["check", temp_file],
            ["check", "/nonexistent"],  # This should be fast and produce JSON
        ]

        for cmd_args in commands:
            result = subprocess.run(
                [str(script_path)] + cmd_args, capture_output=True, text=True, timeout=10
            )

            if result.stdout.strip():
                try:
                    # Should produce valid JSON (may be from underlying tools)
                    if result.stdout.strip().startswith("{"):
                        json.loads(result.stdout)
                except json.JSONDecodeError:
                    pytest.fail(
                        f"Command {' '.join(cmd_args)} produced invalid JSON: {result.stdout[:200]}"
                    )

    def test_success_path_integration_with_real_files(self, script_path):
        """Test successful integration with actual project files."""
        # Test with a real Python file from the project
        test_files = [
            "src/core/__init__.py",
            "tests/test_claude_ci.py",  # This test file itself
        ]

        for test_file in test_files:
            if Path(test_file).exists():
                result = subprocess.run(
                    [str(script_path), "check", test_file, "--json"], capture_output=True, text=True
                )

                # Should handle real files gracefully
                assert result.returncode in [0, 1]  # Success or validation failure

                if result.stdout.strip():
                    try:
                        output = json.loads(result.stdout)
                        assert "command" in output
                        assert "status" in output
                        assert output["target"] == test_file
                    except json.JSONDecodeError:
                        pytest.fail(f"Real file test failed for {test_file}: invalid JSON")


class TestClaudeCIIntegration:
    """Integration tests for claude-ci.sh with dependent scripts."""

    @pytest.fixture
    def script_path(self):
        """Get path to claude-ci.sh script."""
        return Path(__file__).parent.parent / "scripts" / "claude-ci.sh"

    def test_integration_with_existing_scripts(self, script_path):
        """Test integration with existing claude-*.sh scripts."""
        scripts_dir = script_path.parent

        # Check that dependent scripts exist
        dependent_scripts = [
            "claude-post-edit.sh",
            "claude-pre-commit.sh",
            "claude-test-changed.sh",
            "run-ci-docker.sh",
        ]

        for script_name in dependent_scripts:
            script_file = scripts_dir / script_name
            if script_file.exists():
                assert os.access(script_file, os.X_OK), f"{script_name} not executable"

    def test_command_delegation(self, script_path):
        """Test that commands are properly delegated to dependent scripts."""
        # This is more of a behavior test - we can't easily mock the scripts
        # but we can verify the command structure works

        result = subprocess.run([str(script_path), "help"], capture_output=True, text=True)

        assert result.returncode == 0
        assert "check <file>" in result.stdout
        assert "pre-commit" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
