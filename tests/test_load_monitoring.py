"""Test load monitoring functionality for CI pipeline."""

import os
import subprocess
from pathlib import Path

import pytest


class TestLoadMonitoring:
    """Test load monitoring scripts and integration."""

    @pytest.fixture
    def script_dir(self):
        """Get the scripts directory."""
        return Path(__file__).parent.parent / "scripts"

    @pytest.fixture
    def load_monitor_script(self, script_dir):
        """Get the load monitor script path."""
        return script_dir / "load-monitor.sh"

    @pytest.fixture
    def safe_runner_script(self, script_dir):
        """Get the safe test runner script path."""
        return script_dir / "safe-test-runner.sh"

    def test_load_monitor_script_exists(self, load_monitor_script):
        """Test that load monitor script exists and is executable."""
        assert load_monitor_script.exists()
        assert os.access(load_monitor_script, os.X_OK)

    def test_safe_runner_script_exists(self, safe_runner_script):
        """Test that safe test runner script exists and is executable."""
        assert safe_runner_script.exists()
        assert os.access(safe_runner_script, os.X_OK)

    def test_load_monitor_check_mode(self, load_monitor_script):
        """Test load monitor check mode."""
        # Run with low max load to test both pass and fail cases
        env = os.environ.copy()

        # Test passing case
        env["MAX_LOAD"] = "100"
        result = subprocess.run([str(load_monitor_script), "check"], env=env, capture_output=True)
        assert result.returncode == 0

        # Test failing case
        env["MAX_LOAD"] = "0"
        result = subprocess.run([str(load_monitor_script), "check"], env=env, capture_output=True)
        assert result.returncode == 1

    def test_load_monitor_get_load_mode(self, load_monitor_script):
        """Test load monitor get_load mode."""
        result = subprocess.run(
            [str(load_monitor_script), "get_load"], capture_output=True, text=True
        )
        assert result.returncode == 0
        # Should return a numeric value
        try:
            load_value = float(result.stdout.strip())
            assert load_value >= 0
        except ValueError:
            pytest.fail(f"get_load returned non-numeric value: {result.stdout}")

    def test_load_monitor_suggest_workers(self, load_monitor_script):
        """Test load monitor suggest-workers mode."""
        result = subprocess.run(
            [str(load_monitor_script), "suggest-workers"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        workers = result.stdout.strip()
        assert workers in ["1", "2", "3", "auto"]

    def test_safe_runner_with_throttling_disabled(self, safe_runner_script):
        """Test safe runner with throttling disabled."""
        env = os.environ.copy()
        env["TEST_THROTTLE_ENABLED"] = "false"

        # Run pytest --version (simple command)
        result = subprocess.run(
            [str(safe_runner_script), "--version"],
            env=env,
            capture_output=True,
            text=True,
        )
        # Should run without throttling - pytest --version has various exit codes
        assert result.returncode in [0, 1, 2]

    def test_safe_runner_preflight_check(self, safe_runner_script):
        """Test safe runner preflight check with high load."""
        env = os.environ.copy()
        env["TEST_THROTTLE_ENABLED"] = "true"
        env["MAX_LOAD"] = "0"  # Force failure

        # Try to run pytest (will fail due to load)
        result = subprocess.run(
            [str(safe_runner_script), "--version"],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        # Check for load-related error message in stderr or stdout
        output = result.stderr + result.stdout
        assert "System load too high" in output or "load" in output.lower()

    def test_safe_runner_timeout_handling(self, safe_runner_script):
        """Test safe runner timeout handling."""
        env = os.environ.copy()
        env["PYTEST_TIMEOUT"] = "2"  # 2 second timeout
        env["TEST_THROTTLE_ENABLED"] = "false"  # Skip load check

        # Run pytest --help (should complete quickly)
        result = subprocess.run(
            [str(safe_runner_script), "--help"],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,  # Give it time to complete
        )
        # pytest --help should work or fail gracefully
        assert result.returncode in [0, 1, 2]  # Various pytest exit codes

    def test_load_monitor_verbose_mode(self, load_monitor_script):
        """Test load monitor verbose output."""
        env = os.environ.copy()
        env["VERBOSE"] = "true"
        env["MAX_LOAD"] = "100"

        result = subprocess.run(
            [str(load_monitor_script), "check"],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "System Load Check" in result.stdout
        assert "Current load" in result.stdout
        assert "Load acceptable" in result.stdout

    def test_integration_with_environment_variables(self, load_monitor_script):
        """Test that environment variables are properly respected."""
        test_cases = [
            {"MAX_LOAD": "5", "expected_behavior": "respects custom threshold"},
            {"MAX_LOAD": "999", "expected_behavior": "allows high threshold"},
        ]

        for test_case in test_cases:
            env = os.environ.copy()
            env.update(test_case)

            result = subprocess.run(
                [str(load_monitor_script), "check"], env=env, capture_output=True
            )
            # With MAX_LOAD=999, check should always pass
            if test_case["MAX_LOAD"] == "999":
                assert result.returncode == 0

    def test_load_monitor_error_handling(self, load_monitor_script):
        """Test load monitor handles invalid modes gracefully."""
        result = subprocess.run(
            [str(load_monitor_script), "invalid-mode"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Usage:" in result.stdout
        assert "check" in result.stdout
        assert "suggest-workers" in result.stdout
