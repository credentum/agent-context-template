"""Unit tests for Distributed CI Coordinator."""

import json

# Import the module under test
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from distributed_ci_coordinator import (
        CIJob,
    )
    from distributed_ci_coordinator import CIRunner as Runner  # type: ignore[import-not-found]
    from distributed_ci_coordinator import (
        DistributedCICoordinator,
    )
except ImportError as e:
    # If import fails, skip this test module
    pytest.skip(f"distributed_ci_coordinator module not found: {e}", allow_module_level=True)


class TestCIJob(unittest.TestCase):
    """Test CIJob dataclass."""

    def test_job_creation(self):
        """Test creating a CI job."""
        job = CIJob(
            job_id="test-123",
            command="pytest",
            dependencies=["src/", "tests/"],
            env_vars={"PYTHON_VERSION": "3.11"},
            timeout=300,
        )

        self.assertEqual(job.job_id, "test-123")
        self.assertEqual(job.command, "pytest")
        self.assertEqual(job.dependencies, ["src/", "tests/"])
        self.assertEqual(job.status, "pending")
        self.assertIsNone(job.assigned_runner)

    def test_job_to_dict(self):
        """Test converting job to dictionary."""
        job = CIJob(
            job_id="test-123",
            command="pytest",
            dependencies=["src/"],
            env_vars={},
            timeout=60,
        )
        job_dict = job.to_dict()

        self.assertIn("job_id", job_dict)
        self.assertIn("created_at", job_dict)
        self.assertEqual(job_dict["command"], "pytest")


class TestRunner(unittest.TestCase):
    """Test Runner dataclass."""

    def test_runner_creation(self):
        """Test creating a runner."""
        runner = Runner(
            runner_id="runner-1",
            capabilities=["docker", "gpu"],
            max_concurrent_jobs=4,
        )

        self.assertEqual(runner.runner_id, "runner-1")
        self.assertEqual(runner.capabilities, ["docker", "gpu"])
        self.assertEqual(runner.current_jobs, 0)
        self.assertTrue(runner.is_active)

    def test_runner_to_dict(self):
        """Test converting runner to dictionary."""
        runner = Runner(runner_id="runner-1", capabilities=[], max_concurrent_jobs=2)
        runner_dict = runner.to_dict()

        self.assertIn("runner_id", runner_dict)
        self.assertIn("last_heartbeat", runner_dict)
        self.assertEqual(runner_dict["current_jobs"], 0)


class TestDistributedCICoordinator(unittest.TestCase):
    """Test Distributed CI Coordinator."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch("distributed_ci_coordinator.aioredis")
        self.mock_aioredis = self.patcher.start()

        # Create mock Redis client
        self.mock_redis = AsyncMock()
        self.mock_aioredis.from_url = AsyncMock(return_value=self.mock_redis)

        self.coordinator = DistributedCICoordinator("redis://localhost:6379")

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test coordinator initialization."""
        # Redis should be created
        self.mock_aioredis.from_url.assert_called_once_with("redis://localhost:6379")

    @pytest.mark.asyncio
    async def test_submit_job(self):
        """Test submitting a job."""
        job_id = await self.coordinator.submit_job(
            command="pytest tests/",
            dependencies=["requirements.txt"],
            env_vars={"CI": "true"},
            timeout=600,
        )

        # Should return a job ID
        self.assertTrue(job_id.startswith("job-"))

        # Should save to Redis
        self.mock_redis.hset.assert_called()
        self.mock_redis.lpush.assert_called_with("job_queue", job_id)

    @pytest.mark.asyncio
    async def test_register_runner(self):
        """Test registering a runner."""
        await self.coordinator.register_runner(
            runner_id="runner-1",
            capabilities=["docker", "python"],
            max_concurrent_jobs=2,
        )

        # Should save runner to Redis
        self.mock_redis.hset.assert_called()
        call_args = self.mock_redis.hset.call_args[0]
        self.assertEqual(call_args[0], "runners")
        self.assertEqual(call_args[1], "runner-1")

    @pytest.mark.asyncio
    async def test_assign_job_to_runner(self):
        """Test job assignment logic."""
        # Set up mock data
        self.mock_redis.hgetall = AsyncMock(
            return_value={
                b"runner-1": json.dumps(
                    {
                        "runner_id": "runner-1",
                        "capabilities": ["python"],
                        "current_jobs": 0,
                        "max_concurrent_jobs": 2,
                        "is_active": True,
                        "last_heartbeat": datetime.utcnow().isoformat(),
                    }
                ).encode()
            }
        )

        self.mock_redis.brpop = AsyncMock(return_value=(b"job_queue", b"job-123"))
        self.mock_redis.hget = AsyncMock(
            return_value=json.dumps(
                {
                    "job_id": "job-123",
                    "command": "pytest",
                    "status": "pending",
                }
            ).encode()
        )

        # Register runner
        await self.coordinator.register_runner("runner-1", ["python"], 2)

        # Assign job
        job_id = await self.coordinator.assign_job_to_runner("runner-1")
        self.assertEqual(job_id, "job-123")

    @pytest.mark.asyncio
    async def test_complete_job(self):
        """Test completing a job."""
        # Set up mock job
        job_data = {
            "job_id": "job-123",
            "status": "running",
            "assigned_runner": "runner-1",
        }
        self.mock_redis.hget = AsyncMock(return_value=json.dumps(job_data).encode())

        await self.coordinator.complete_job("job-123", exit_code=0, output="Success")

        # Should update job status
        self.mock_redis.hset.assert_called()
        updated_data = json.loads(self.mock_redis.hset.call_args[0][2])
        self.assertEqual(updated_data["status"], "completed")
        self.assertEqual(updated_data["exit_code"], 0)

    @pytest.mark.asyncio
    async def test_get_job_status(self):
        """Test getting job status."""
        job_data = {
            "job_id": "job-123",
            "status": "running",
            "command": "pytest",
        }
        self.mock_redis.hget = AsyncMock(return_value=json.dumps(job_data).encode())

        status = await self.coordinator.get_job_status("job-123")
        self.assertEqual(status, job_data)

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self):
        """Test getting status of non-existent job."""
        self.mock_redis.hget = AsyncMock(return_value=None)

        status = await self.coordinator.get_job_status("nonexistent")
        self.assertIsNone(status)

    @pytest.mark.asyncio
    async def test_heartbeat(self):
        """Test runner heartbeat."""
        await self.coordinator.heartbeat("runner-1")

        # Should update runner's last heartbeat
        self.mock_redis.hget.assert_called_with("runners", "runner-1")

    @pytest.mark.asyncio
    async def test_check_runner_health(self):
        """Test checking runner health."""
        # Set up mock runners with different heartbeat times
        now = datetime.utcnow()
        runners = {
            b"runner-1": json.dumps(
                {
                    "runner_id": "runner-1",
                    "last_heartbeat": now.isoformat(),
                    "is_active": True,
                }
            ).encode(),
            b"runner-2": json.dumps(
                {
                    "runner_id": "runner-2",
                    "last_heartbeat": "2020-01-01T00:00:00",  # Old heartbeat
                    "is_active": True,
                }
            ).encode(),
        }
        self.mock_redis.hgetall = AsyncMock(return_value=runners)

        await self.coordinator._check_runner_health()

        # Should mark runner-2 as inactive
        calls = self.mock_redis.hset.call_args_list
        self.assertTrue(any("runner-2" in str(call) for call in calls))

    @pytest.mark.asyncio
    async def test_retry_failed_job(self):
        """Test retrying a failed job."""
        job_data = {
            "job_id": "job-123",
            "status": "failed",
            "command": "pytest",
            "retry_count": 1,
        }
        self.mock_redis.hget = AsyncMock(return_value=json.dumps(job_data).encode())

        await self.coordinator._retry_failed_jobs()

        # Should increment retry count and requeue
        self.mock_redis.lpush.assert_called_with("job_queue", "job-123")

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test handling Redis connection errors."""
        self.mock_redis.hget = AsyncMock(side_effect=Exception("Connection lost"))

        with self.assertRaises(Exception):
            await self.coordinator.get_job_status("job-123")


if __name__ == "__main__":
    # Run async tests
    pytest.main([__file__, "-v"])
