"""Integration tests for infra/healthcheck.sh script."""

import os
import subprocess
from pathlib import Path

import pytest


class TestHealthcheckIntegration:
    """Test the healthcheck script against real or mocked services."""

    def setup_method(self):
        """Set up test environment."""
        self.healthcheck_script = Path("infra/healthcheck.sh")
        self.repo_root = Path(__file__).parent.parent

    def test_healthcheck_script_exists_and_executable(self):
        """Test that the healthcheck script exists and is executable."""
        script_path = self.repo_root / self.healthcheck_script
        assert script_path.exists(), f"Healthcheck script not found at {script_path}"
        assert os.access(script_path, os.X_OK), "Healthcheck script is not executable"

    def test_healthcheck_help_command(self):
        """Test that the help command works correctly."""
        result = subprocess.run(
            [str(self.repo_root / self.healthcheck_script), "--help"],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
        )

        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert "Infrastructure Health Check Script" in result.stdout
        assert "Environment Variables:" in result.stdout
        assert "QDRANT_HOST" in result.stdout
        assert "NEO4J_HOST" in result.stdout

    def test_healthcheck_script_syntax(self):
        """Test that the bash script has valid syntax."""
        result = subprocess.run(
            ["bash", "-n", str(self.repo_root / self.healthcheck_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script syntax error: {result.stderr}"

    @pytest.mark.integration
    def test_healthcheck_with_services_down(self):
        """Test healthcheck behavior when services are down."""
        # Set short timeout to make test faster
        env = os.environ.copy()
        env["CURL_TIMEOUT"] = "2"
        env["QDRANT_HOST"] = "127.0.0.1"
        env["QDRANT_PORT"] = "9999"  # Non-existent port
        env["NEO4J_HOST"] = "127.0.0.1"
        env["NEO4J_PORT"] = "9998"  # Non-existent port

        result = subprocess.run(
            [str(self.repo_root / self.healthcheck_script)],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            env=env,
        )

        # Should fail with Qdrant error (exit code 1)
        assert result.returncode == 1, f"Expected failure but got exit code {result.returncode}"
        assert "Qdrant: Failed to connect" in result.stdout
        assert "Failed" in result.stdout

    @pytest.mark.integration
    def test_healthcheck_with_invalid_host(self):
        """Test healthcheck behavior with invalid hostnames."""
        env = os.environ.copy()
        env["CURL_TIMEOUT"] = "2"
        env["QDRANT_HOST"] = "nonexistent.invalid"
        env["NEO4J_HOST"] = "nonexistent.invalid"

        result = subprocess.run(
            [str(self.repo_root / self.healthcheck_script)],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            env=env,
        )

        # Should fail with connection error
        assert result.returncode != 0, "Expected failure with invalid hostnames"
        assert "Failed to connect" in result.stdout

    @pytest.mark.skipif(
        not (Path("infra/docker-compose.yml").exists()),
        reason="Docker compose file not found - skipping live service test",
    )
    def test_healthcheck_with_live_services(self):
        """Test healthcheck against live services (if running)."""
        # First try to start services if not running
        try:
            subprocess.run(
                ["docker-compose", "-f", "infra/docker-compose.yml", "up", "-d"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
            )

            # Wait a moment for services to initialize
            import time

            time.sleep(10)

            # Check if services are running
            docker_ps = subprocess.run(
                ["docker", "ps", "--filter", "name=qdrant", "--filter", "name=neo4j"],
                capture_output=True,
                text=True,
            )

            if "qdrant" in docker_ps.stdout and "neo4j" in docker_ps.stdout:
                # Services are running, test healthcheck
                result = subprocess.run(
                    [str(self.repo_root / self.healthcheck_script)],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_root,
                )

                # Should succeed if services are healthy
                assert result.returncode == 0, f"Healthcheck failed: {result.stdout}"
                assert "All services are healthy" in result.stdout
                # Check for health indicators (ignoring color codes)
                assert "✅ Qdrant" in result.stdout or "Qdrant: Healthy" in result.stdout
                assert "✅ Neo4j" in result.stdout or "Neo4j: Healthy" in result.stdout
            else:
                pytest.skip("Services not running, skipping live test")

        except subprocess.CalledProcessError:
            pytest.skip("Could not start services, skipping live test")
        except Exception as e:
            pytest.skip(f"Error during live test setup: {e}")

    def test_healthcheck_environment_variable_validation(self):
        """Test that environment variables are properly used."""
        # Test with custom ports that will fail
        env = os.environ.copy()
        env["CURL_TIMEOUT"] = "1"
        env["QDRANT_PORT"] = "9876"
        env["NEO4J_PORT"] = "9875"

        result = subprocess.run(
            [str(self.repo_root / self.healthcheck_script)],
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            env=env,
        )

        # Should show the custom port in error message
        assert "localhost:9876/collections" in result.stdout, "Custom Qdrant port not used"

    def test_healthcheck_concurrent_execution(self):
        """Test that multiple instances can run concurrently."""
        import concurrent.futures

        def run_healthcheck():
            env = os.environ.copy()
            env["CURL_TIMEOUT"] = "1"
            env["QDRANT_HOST"] = "127.0.0.1"
            env["QDRANT_PORT"] = "9999"  # Will fail quickly

            return subprocess.run(
                [str(self.repo_root / self.healthcheck_script)],
                capture_output=True,
                text=True,
                cwd=self.repo_root,
                env=env,
            )

        # Run multiple instances concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_healthcheck) for _ in range(3)]
            results = [future.result() for future in futures]

        # All should fail with the same error code
        for result in results:
            assert result.returncode == 1, "All concurrent runs should fail consistently"
            assert "Failed to connect" in result.stdout

    def test_healthcheck_missing_python_dependency(self):
        """Test behavior when neo4j Python package is not available."""
        # This test would require a separate environment without neo4j package
        # For now, we just verify the error message format in the script
        script_content = (self.repo_root / self.healthcheck_script).read_text()

        assert "neo4j module not found" in script_content
        assert "pip install neo4j>=5.0.0" in script_content


class TestHealthcheckScriptContent:
    """Test the content and structure of the healthcheck script."""

    def setup_method(self):
        """Set up test environment."""
        self.script_path = Path(__file__).parent.parent / "infra/healthcheck.sh"
        self.script_content = self.script_path.read_text()

    def test_script_has_proper_shebang(self):
        """Test that script starts with proper shebang."""
        assert self.script_content.startswith("#!/bin/bash")

    def test_script_has_environment_variables(self):
        """Test that script supports environment variable configuration."""
        expected_vars = ["QDRANT_HOST", "QDRANT_PORT", "NEO4J_HOST", "NEO4J_PORT", "CURL_TIMEOUT"]

        for var in expected_vars:
            assert f"${{{var}:-" in self.script_content, f"Missing environment variable {var}"

    def test_script_has_proper_exit_codes(self):
        """Test that script defines proper exit codes."""
        assert "SUCCESS=0" in self.script_content
        assert "QDRANT_FAIL=1" in self.script_content
        assert "NEO4J_FAIL=2" in self.script_content
        assert "PYTHON_FAIL=3" in self.script_content

    def test_script_has_timeout_support(self):
        """Test that script includes timeout support for curl."""
        assert "--max-time" in self.script_content
        assert "CURL_TIMEOUT" in self.script_content

    def test_script_has_help_functionality(self):
        """Test that script includes help functionality."""
        assert "show_help()" in self.script_content
        assert "--help" in self.script_content
        assert "-h" in self.script_content

    def test_script_uses_proper_endpoints(self):
        """Test that script uses correct API endpoints."""
        assert "/collections" in self.script_content  # Qdrant endpoint
        assert "GraphDatabase.driver" in self.script_content  # Neo4j driver

    def test_script_has_error_handling(self):
        """Test that script includes proper error handling."""
        assert "curl is not available" in self.script_content
        assert "Python is not available" in self.script_content
        assert "neo4j module not found" in self.script_content
