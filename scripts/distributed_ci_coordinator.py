#!/usr/bin/env python3
"""
Distributed CI Coordinator - Multi-runner job scheduling and coordination.

This module manages distributed CI execution across multiple runners with
load balancing, job scheduling, result aggregation, and fault tolerance.
"""

import asyncio
import json
import logging
import socket
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class JobStatus(Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RunnerInfo:
    """Information about a CI runner."""

    id: str
    hostname: str
    capacity: int = 1
    current_jobs: int = 0
    capabilities: List[str] = None
    last_heartbeat: float = 0.0
    status: str = "idle"  # idle, busy, offline

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

    @property
    def available_slots(self) -> int:
        """Number of available job slots."""
        return max(0, self.capacity - self.current_jobs)

    @property
    def load_percentage(self) -> float:
        """Current load as percentage."""
        return (self.current_jobs / self.capacity) * 100 if self.capacity > 0 else 100


@dataclass
class CIJob:
    """Represents a CI job to be executed."""

    id: str
    command: str
    dependencies: List[str]
    requirements: List[str] = None  # e.g., ["gpu", "docker"]
    priority: int = 0
    timeout_seconds: int = 3600
    retry_count: int = 0
    max_retries: int = 2
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: JobStatus = JobStatus.PENDING
    runner_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def execution_time_seconds(self) -> Optional[float]:
        """Job execution time in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CIJob":
        """Create job from dictionary."""
        data = data.copy()
        data["status"] = JobStatus(data["status"])
        return cls(**data)


class DistributedCICoordinator:
    """
    Distributed CI Coordinator for managing jobs across multiple runners.

    Features:
    - Job queue management
    - Load balancing across runners
    - Runner discovery and health monitoring
    - Result aggregation
    - Fault tolerance and retry logic
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", node_id: Optional[str] = None):
        self.redis_url = redis_url
        self.node_id = node_id or f"coordinator-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
        self.logger = logging.getLogger(__name__)
        self.redis: Optional[aioredis.Redis] = None  # type: ignore[misc]

        # Internal state
        self.runners: Dict[str, RunnerInfo] = {}
        self.jobs: Dict[str, CIJob] = {}
        self.running = False

        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.runner_timeout = 120  # seconds
        self.job_poll_interval = 5  # seconds

        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    async def connect(self) -> bool:
        """Connect to Redis backend."""
        if not REDIS_AVAILABLE:
            self.logger.error("Redis not available. Install with pip install aioredis")
            return False

        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            self.logger.info(f"Connected to Redis at {self.redis_url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def register_runner(self, runner_info: RunnerInfo) -> bool:
        """Register a new runner."""
        try:
            runner_data = asdict(runner_info)
            runner_data["last_heartbeat"] = time.time()

            await self.redis.hset("ci:runners", runner_info.id, json.dumps(runner_data))

            self.runners[runner_info.id] = runner_info
            self.logger.info(
                f"Registered runner {runner_info.id} with capacity {runner_info.capacity}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to register runner: {e}")
            return False

    async def update_runner_heartbeat(self, runner_id: str) -> bool:
        """Update runner heartbeat."""
        try:
            if runner_id in self.runners:
                self.runners[runner_id].last_heartbeat = time.time()

                await self.redis.hset(  # type: ignore[union-attr]
                    "ci:runners", runner_id, json.dumps(asdict(self.runners[runner_id]))
                )
                return True
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat for {runner_id}: {e}")

        return False

    async def get_available_runners(self, requirements: List[str] = None) -> List[RunnerInfo]:
        """Get list of available runners matching requirements."""
        available = []
        current_time = time.time()

        for runner in self.runners.values():
            # Check if runner is online
            if current_time - runner.last_heartbeat > self.runner_timeout:
                continue

            # Check if runner has available capacity
            if runner.available_slots <= 0:
                continue

            # Check if runner meets requirements
            if requirements:
                if not all(req in runner.capabilities for req in requirements):
                    continue

            available.append(runner)

        # Sort by load (least loaded first)
        available.sort(key=lambda r: r.load_percentage)
        return available

    async def submit_job(self, job: CIJob) -> str:
        """Submit a job for execution."""
        try:
            # Store job in Redis
            await self.redis.hset("ci:jobs", job.id, json.dumps(job.to_dict()))

            # Add to job queue
            await self.redis.lpush("ci:job_queue", job.id)

            # Store locally
            self.jobs[job.id] = job

            self.logger.info(f"Submitted job {job.id}: {job.command[:50]}...")
            return job.id

        except Exception as e:
            self.logger.error(f"Failed to submit job: {e}")
            raise

    async def assign_job_to_runner(self, job: CIJob, runner: RunnerInfo) -> bool:
        """Assign a job to a specific runner."""
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.runner_id = runner.id
            job.started_at = time.time()

            # Update runner load
            runner.current_jobs += 1
            if runner.current_jobs >= runner.capacity:
                runner.status = "busy"

            # Store updates
            await self.redis.hset("ci:jobs", job.id, json.dumps(job.to_dict()))

            await self.redis.hset("ci:runners", runner.id, json.dumps(asdict(runner)))

            # Send job to runner
            await self.redis.lpush(f"ci:runner:{runner.id}:jobs", job.id)

            self.logger.info(f"Assigned job {job.id} to runner {runner.id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to assign job {job.id} to runner {runner.id}: {e}")
            return False

    async def process_job_queue(self) -> None:
        """Process pending jobs in the queue."""
        while self.running:
            try:
                # Get next job from queue
                job_id = await self.redis.brpop("ci:job_queue", timeout=self.job_poll_interval)

                if not job_id:
                    continue

                job_id = job_id[1].decode()  # Extract job ID from tuple

                # Get job details
                job_data = await self.redis.hget("ci:jobs", job_id)
                if not job_data:
                    continue

                job = CIJob.from_dict(json.loads(job_data))

                # Find available runner
                available_runners = await self.get_available_runners(job.requirements)

                if not available_runners:
                    # No runners available, put job back in queue
                    await self.redis.lpush("ci:job_queue", job_id)
                    await asyncio.sleep(5)  # Wait before retrying
                    continue

                # Assign to best runner (first in sorted list)
                best_runner = available_runners[0]
                await self.assign_job_to_runner(job, best_runner)

            except Exception as e:
                self.logger.error(f"Error processing job queue: {e}")
                await asyncio.sleep(1)

    async def monitor_job_results(self) -> None:
        """Monitor job results from runners."""
        while self.running:
            try:
                # Check for completed jobs
                result_data = await self.redis.brpop("ci:job_results", timeout=5)

                if not result_data:
                    continue

                result_json = result_data[1].decode()
                result = json.loads(result_json)

                job_id = result["job_id"]
                job = self.jobs.get(job_id)

                if not job:
                    continue

                # Update job with result
                job.status = JobStatus.COMPLETED if result["success"] else JobStatus.FAILED
                job.completed_at = time.time()
                job.result = result.get("output")
                job.error = result.get("error")

                # Update runner load
                if job.runner_id and job.runner_id in self.runners:
                    runner = self.runners[job.runner_id]
                    runner.current_jobs -= 1
                    if runner.current_jobs < runner.capacity:
                        runner.status = "idle"

                # Store updates
                await self.redis.hset("ci:jobs", job_id, json.dumps(job.to_dict()))

                if job.runner_id:
                    await self.redis.hset(
                        "ci:runners", job.runner_id, json.dumps(asdict(self.runners[job.runner_id]))
                    )

                status_msg = "completed" if result["success"] else "failed"
                self.logger.info(f"Job {job_id} {status_msg} on runner {job.runner_id}")

                # Handle retries for failed jobs
                if not result["success"] and job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = JobStatus.PENDING
                    job.started_at = None
                    job.runner_id = None

                    await self.redis.hset("ci:jobs", job_id, json.dumps(job.to_dict()))

                    await self.redis.lpush("ci:job_queue", job_id)
                    self.logger.info(f"Retrying job {job_id} (attempt {job.retry_count + 1})")

            except Exception as e:
                self.logger.error(f"Error monitoring job results: {e}")
                await asyncio.sleep(1)

    async def cleanup_stale_runners(self) -> None:
        """Remove stale/offline runners."""
        while self.running:
            try:
                current_time = time.time()
                stale_runners = []

                for runner_id, runner in self.runners.items():
                    if current_time - runner.last_heartbeat > self.runner_timeout:
                        stale_runners.append(runner_id)

                for runner_id in stale_runners:
                    self.logger.warning(f"Removing stale runner {runner_id}")
                    del self.runners[runner_id]
                    await self.redis.hdel("ci:runners", runner_id)

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                self.logger.error(f"Error cleaning up stale runners: {e}")
                await asyncio.sleep(30)

    async def start_coordinator(self) -> None:
        """Start the distributed CI coordinator."""
        if not await self.connect():
            raise RuntimeError("Failed to connect to Redis")

        self.running = True
        self.logger.info(f"Starting distributed CI coordinator {self.node_id}")

        # Start background tasks
        tasks = [
            asyncio.create_task(self.process_job_queue()),
            asyncio.create_task(self.monitor_job_results()),
            asyncio.create_task(self.cleanup_stale_runners()),
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down coordinator...")
            self.running = False

            # Cancel tasks
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

    async def get_job_status(self, job_id: str) -> Optional[CIJob]:
        """Get status of a specific job."""
        try:
            job_data = await self.redis.hget("ci:jobs", job_id)
            if job_data:
                return CIJob.from_dict(json.loads(job_data))
        except Exception as e:
            self.logger.error(f"Failed to get job status for {job_id}: {e}")

        return None

    async def get_coordinator_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics."""
        stats = {
            "node_id": self.node_id,
            "runners": len(self.runners),
            "active_runners": len(
                [
                    r
                    for r in self.runners.values()
                    if time.time() - r.last_heartbeat < self.runner_timeout
                ]
            ),
            "total_capacity": sum(r.capacity for r in self.runners.values()),
            "jobs_pending": await self.redis.llen("ci:job_queue"),
            "jobs_total": len(self.jobs),
            "jobs_completed": len(
                [j for j in self.jobs.values() if j.status == JobStatus.COMPLETED]
            ),
            "jobs_failed": len([j for j in self.jobs.values() if j.status == JobStatus.FAILED]),
        }

        return stats


# CLI Runner implementation
class CIRunner:
    """CI Runner that executes jobs from the coordinator."""

    def __init__(self, runner_id: str, coordinator_url: str = "redis://localhost:6379"):
        self.runner_id = runner_id
        self.coordinator_url = coordinator_url
        self.logger = logging.getLogger(__name__)
        self.redis: Optional[aioredis.Redis] = None  # type: ignore[misc]
        self.running = False

        # Runner configuration
        self.capacity = 1
        self.capabilities = self._detect_capabilities()

    def _detect_capabilities(self) -> List[str]:
        """Detect runner capabilities."""
        capabilities = ["basic"]

        # Check for Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            capabilities.append("docker")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check for GPU
        if Path("/proc/driver/nvidia/version").exists():
            capabilities.append("gpu")

        return capabilities

    async def connect(self) -> bool:
        """Connect to coordinator."""
        try:
            self.redis = aioredis.from_url(self.coordinator_url)
            await self.redis.ping()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to coordinator: {e}")
            return False

    async def register_with_coordinator(self) -> bool:
        """Register this runner with the coordinator."""
        try:
            runner_info = RunnerInfo(
                id=self.runner_id,
                hostname=socket.gethostname(),
                capacity=self.capacity,
                capabilities=self.capabilities,
                last_heartbeat=time.time(),
            )

            await self.redis.hset("ci:runners", self.runner_id, json.dumps(asdict(runner_info)))

            self.logger.info(f"Registered runner {self.runner_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register runner: {e}")
            return False

    async def execute_job(self, job: CIJob) -> Dict[str, Any]:
        """Execute a CI job."""
        self.logger.info(f"Executing job {job.id}: {job.command}")

        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                job.command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=job.timeout_seconds
            )

            success = process.returncode == 0

            result = {
                "job_id": job.id,
                "success": success,
                "return_code": process.returncode,
                "output": {"stdout": stdout.decode(), "stderr": stderr.decode()},
            }

            if not success:
                result["error"] = f"Command failed with return code {process.returncode}"

            return result

        except asyncio.TimeoutError:
            return {
                "job_id": job.id,
                "success": False,
                "error": f"Job timed out after {job.timeout_seconds} seconds",
            }

        except Exception as e:
            return {"job_id": job.id, "success": False, "error": str(e)}

    async def process_jobs(self) -> None:
        """Process jobs from the coordinator."""
        while self.running:
            try:
                # Get job from queue
                job_data = await self.redis.brpop(f"ci:runner:{self.runner_id}:jobs", timeout=5)

                if not job_data:
                    continue

                job_id = job_data[1].decode()

                # Get job details
                job_json = await self.redis.hget("ci:jobs", job_id)
                if not job_json:
                    continue

                job = CIJob.from_dict(json.loads(job_json))

                # Execute job
                result = await self.execute_job(job)

                # Send result back to coordinator
                await self.redis.lpush("ci:job_results", json.dumps(result))

            except Exception as e:
                self.logger.error(f"Error processing jobs: {e}")
                await asyncio.sleep(1)

    async def send_heartbeat(self) -> None:
        """Send periodic heartbeat to coordinator."""
        while self.running:
            try:
                # Update heartbeat timestamp
                runner_data = await self.redis.hget("ci:runners", self.runner_id)
                if runner_data:
                    runner_info = json.loads(runner_data)
                    runner_info["last_heartbeat"] = time.time()

                    await self.redis.hset("ci:runners", self.runner_id, json.dumps(runner_info))

                await asyncio.sleep(30)  # Heartbeat every 30 seconds

            except Exception as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(30)

    async def start_runner(self) -> None:
        """Start the CI runner."""
        if not await self.connect():
            raise RuntimeError("Failed to connect to coordinator")

        if not await self.register_with_coordinator():
            raise RuntimeError("Failed to register with coordinator")

        self.running = True
        self.logger.info(f"Starting CI runner {self.runner_id}")

        # Start background tasks
        tasks = [
            asyncio.create_task(self.process_jobs()),
            asyncio.create_task(self.send_heartbeat()),
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Shutting down runner...")
            self.running = False

            # Cancel tasks
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)


def main():
    """CLI interface for distributed CI coordinator."""
    import argparse

    parser = argparse.ArgumentParser(description="Distributed CI Coordinator")
    parser.add_argument(
        "--redis-url", default="redis://localhost:6379", help="Redis URL for coordination"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # Coordinator mode
    coord_parser = subparsers.add_parser("coordinator", help="Run as coordinator")
    coord_parser.add_argument("--node-id", help="Coordinator node ID")

    # Runner mode
    runner_parser = subparsers.add_parser("runner", help="Run as runner")
    runner_parser.add_argument("--runner-id", required=True, help="Runner ID")

    # Client mode for job submission
    client_parser = subparsers.add_parser("submit", help="Submit job")
    client_parser.add_argument("--command", required=True, help="Command to execute")
    client_parser.add_argument("--requirements", nargs="*", help="Job requirements")

    args = parser.parse_args()

    if args.mode == "coordinator":
        coordinator = DistributedCICoordinator(redis_url=args.redis_url, node_id=args.node_id)
        asyncio.run(coordinator.start_coordinator())

    elif args.mode == "runner":
        runner = CIRunner(runner_id=args.runner_id, coordinator_url=args.redis_url)
        asyncio.run(runner.start_runner())

    elif args.mode == "submit":

        async def submit_job():
            coordinator = DistributedCICoordinator(redis_url=args.redis_url)
            await coordinator.connect()

            job = CIJob(
                id=str(uuid.uuid4()),
                command=args.command,
                dependencies=[],
                requirements=args.requirements or [],
            )

            job_id = await coordinator.submit_job(job)
            print(f"Submitted job {job_id}")

        asyncio.run(submit_job())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
