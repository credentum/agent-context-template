#!/usr/bin/env python3
"""
Chaos engineering tests for system resilience
Tests system behavior under adverse conditions
"""

import concurrent.futures
import os
import random
import signal
import tempfile
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
import yaml


class ChaosMonkey:
    """Injects various failures into the system"""

    def __init__(self):
        self.active = False
        self.failures_injected = []

    @contextmanager
    def random_failures(self, failure_rate: float = 0.1):
        """Randomly inject failures during context"""
        self.active = True
        original_open = open

        def chaos_open(*args, **kwargs):
            if self.active and random.random() < failure_rate:
                self.failures_injected.append(("open", args[0] if args else None))
                raise IOError("Chaos monkey struck!")
            return original_open(*args, **kwargs)

        with patch("builtins.open", chaos_open):
            try:
                yield self
            finally:
                self.active = False

    @contextmanager
    def memory_pressure(self, size_mb: int = 100):
        """Create memory pressure during context"""
        # Allocate large array to consume memory
        data = []
        try:
            for _ in range(size_mb):
                data.append(bytearray(1024 * 1024))  # 1MB chunks
            yield self
        finally:
            # Release memory
            data.clear()

    @contextmanager
    def cpu_stress(self, threads: int = 4, duration: float = 1.0):
        """Create CPU stress during context"""
        stop_event = threading.Event()

        def cpu_burn():
            start = time.time()
            while not stop_event.is_set() and (time.time() - start) < duration:
                # Burn CPU cycles
                sum(i * i for i in range(10000))

        # Start stress threads
        stress_threads = []
        for _ in range(threads):
            t = threading.Thread(target=cpu_burn)
            t.start()
            stress_threads.append(t)

        try:
            yield self
        finally:
            stop_event.set()
            for t in stress_threads:
                t.join(timeout=1.0)


@pytest.mark.chaos
class TestFileSystemChaos:
    """Test resilience to file system failures"""

    def test_disk_full_simulation(self):
        """Test behavior when disk is full"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Simulate disk full by patching write operations
            write_count = 0
            max_writes = 5

            original_write = Path.write_text

            def limited_write(self, *args, **kwargs):
                nonlocal write_count
                write_count += 1
                if write_count > max_writes:
                    raise OSError(28, "No space left on device")
                return original_write(self, *args, **kwargs)

            with patch.object(Path, "write_text", limited_write):
                # Try to write multiple files
                files_written = 0
                errors_caught = 0

                for i in range(10):
                    try:
                        file_path = temp_path / f"test_{i}.txt"
                        file_path.write_text(f"Content {i}")
                        files_written += 1
                    except OSError as e:
                        if e.errno == 28:  # ENOSPC
                            errors_caught += 1
                        else:
                            raise

                assert files_written == max_writes
                assert errors_caught == 5

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a file and make it read-only
            protected_file = temp_path / "protected.yaml"
            protected_file.write_text("content: protected")
            os.chmod(protected_file, 0o444)  # Read-only

            # Try to write to it
            error_caught = False
            try:
                protected_file.write_text("new content")
            except PermissionError:
                error_caught = True

            assert error_caught, "Should catch permission error"

            # Cleanup
            os.chmod(protected_file, 0o644)

    def test_concurrent_file_access(self):
        """Test handling of concurrent file access"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "concurrent.yaml"

            # Initial content
            test_file.write_text(yaml.dump({"counter": 0}))

            def increment_counter(file_path: Path, iterations: int):
                """Increment counter in file multiple times"""
                successes = 0
                conflicts = 0

                for _ in range(iterations):
                    try:
                        # Read current value
                        with open(file_path) as f:
                            data = yaml.safe_load(f)

                        # Increment
                        data["counter"] += 1

                        # Write back
                        with open(file_path, "w") as f:
                            yaml.dump(data, f)

                        successes += 1
                    except Exception:
                        conflicts += 1

                return successes, conflicts

            # Run concurrent updates
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(increment_counter, test_file, 20) for _ in range(5)]

                results = [f.result() for f in futures]

            # Check results
            total_successes = sum(r[0] for r in results)
            total_conflicts = sum(r[1] for r in results)

            # Some updates should succeed
            assert total_successes > 0

            # Final counter value should be <= total attempts
            with open(test_file) as f:
                final_data = yaml.safe_load(f)

            assert final_data["counter"] <= 100  # 5 threads * 20 iterations


@pytest.mark.chaos
class TestNetworkChaos:
    """Test resilience to network failures"""

    @patch("requests.get")
    def test_network_timeout_handling(self, mock_get):
        """Test handling of network timeouts"""
        import requests

        # Simulate timeout
        mock_get.side_effect = requests.Timeout("Connection timed out")

        # Function that handles timeouts gracefully
        def fetch_with_retry(url: str, max_retries: int = 3) -> Optional[str]:
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, timeout=5)
                    return response.text
                except requests.Timeout:
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(2**attempt)  # Exponential backoff
            return None

        result = fetch_with_retry("http://example.com")
        assert result is None
        assert mock_get.call_count == 3

    @patch("requests.post")
    def test_intermittent_network_failures(self, mock_post):
        """Test handling of intermittent network failures"""
        # Fail first 2 attempts, succeed on 3rd
        mock_post.side_effect = [
            ConnectionError("Network unreachable"),
            ConnectionError("Network unreachable"),
            Mock(status_code=200, json=lambda: {"success": True}),
        ]

        import requests

        def resilient_post(url: str, data: dict) -> dict:
            """Post with retry logic"""
            last_error: Optional[Exception] = None

            for attempt in range(3):
                try:
                    response = requests.post(url, json=data)
                    if response.status_code == 200:
                        return response.json()
                except ConnectionError as e:
                    last_error = e
                    time.sleep(0.1 * (attempt + 1))

            if last_error:
                raise last_error
            else:
                raise RuntimeError("Failed after retries")

        result = resilient_post("http://api.example.com", {"test": "data"})
        assert result["success"] is True
        assert mock_post.call_count == 3


@pytest.mark.chaos
class TestResourceExhaustion:
    """Test behavior under resource exhaustion"""

    def test_thread_pool_exhaustion(self):
        """Test handling when thread pool is exhausted"""
        completed_tasks = []
        failed_tasks = []

        def slow_task(task_id: int):
            """Simulate slow task"""
            time.sleep(0.1)
            return task_id

        # Create small thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit many tasks
            futures = []
            for i in range(20):
                future = executor.submit(slow_task, i)
                futures.append((i, future))

            # Wait with timeout
            for task_id, future in futures:
                try:
                    result = future.result(timeout=0.5)
                    completed_tasks.append(result)
                except concurrent.futures.TimeoutError:
                    failed_tasks.append(task_id)

        # Some tasks should complete, some may timeout
        assert len(completed_tasks) > 0
        assert len(completed_tasks) + len(failed_tasks) == 20

    def test_memory_leak_detection(self):
        """Test detection of memory leaks"""
        import gc
        import sys

        # Track object counts
        initial_objects = len(gc.get_objects())

        # Simulate potential memory leak
        leaked_objects = []

        def create_circular_reference():
            class Node:
                def __init__(self):
                    self.data = [0] * 1000
                    self.ref = None

            # Create circular reference
            node1 = Node()
            node2 = Node()
            node1.ref = node2
            node2.ref = node1

            # Intentionally keep reference
            leaked_objects.append(node1)

        # Create many objects
        for _ in range(100):
            create_circular_reference()

        # Force garbage collection
        gc.collect()

        # Check object growth
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Significant growth indicates potential leak
        assert object_growth > 100  # We intentionally leaked objects

        # Cleanup
        leaked_objects.clear()
        gc.collect()


@pytest.mark.chaos
class TestDataCorruption:
    """Test resilience to data corruption"""

    def test_yaml_corruption_handling(self):
        """Test handling of corrupted YAML files"""
        corrupted_yamls = [
            "{ unclosed bracket",
            "key: value\n  bad indent",
            "- item\n no dash",
            "\x00\x01\x02binary data",
            "recursive: &anchor\n  <<: *anchor",  # Circular reference
        ]

        errors_caught = 0

        for content in corrupted_yamls:
            try:
                yaml.safe_load(content)
            except yaml.YAMLError:
                errors_caught += 1

        # Only 2 out of 5 strings are actually invalid YAML
        assert errors_caught == 2, f"Expected 2 errors, got {errors_caught}"

    def test_partial_write_recovery(self):
        """Test recovery from partial writes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "partial.yaml"

            # Write complete document
            complete_doc = {
                "metadata": {"version": "1.0"},
                "data": {"items": list(range(100))},
            }

            # Simulate partial write - cut in middle of a line to ensure corruption
            yaml_content = yaml.dump(complete_doc)
            # Find a good cut point that will corrupt the YAML
            cut_point = yaml_content.find("- 50")  # Cut in middle of list
            if cut_point > 0:
                partial_content = yaml_content[:cut_point] + "- "  # Incomplete list item
            else:
                partial_content = yaml_content[: len(yaml_content) // 3]  # Fallback

            test_file.write_text(partial_content)

            # Try to read and handle error
            recovery_attempted = False

            try:
                with open(test_file) as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError:
                # Attempt recovery by reading backup
                recovery_attempted = True
                backup_file = temp_path / "partial.yaml.backup"

                if backup_file.exists():
                    with open(backup_file) as f:
                        data = yaml.safe_load(f)
                else:
                    data = None

            assert recovery_attempted
            assert data is None  # No backup exists


@pytest.mark.chaos
class TestSystemResilience:
    """Test overall system resilience"""

    def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures"""

        class Service:
            def __init__(self, name: str, dependencies: Optional[List["Service"]] = None):
                self.name = name
                self.dependencies = dependencies or []
                self.healthy = True
                self.failure_count = 0

            def check_health(self) -> bool:
                """Check service health including dependencies"""
                if not self.healthy:
                    return False

                # Check dependencies with circuit breaker
                for dep in self.dependencies:
                    if dep.failure_count > 3:  # Circuit breaker threshold
                        # Skip unhealthy dependency
                        continue

                    if not dep.check_health():
                        dep.failure_count += 1
                        if dep.failure_count > 3:
                            print(f"Circuit breaker opened for {dep.name}")

                return True

        # Create service dependency chain
        database = Service("database")
        cache = Service("cache", [database])
        api = Service("api", [database, cache])
        web = Service("web", [api])

        # Simulate database failure
        database.healthy = False

        # Check web service (top level)
        # Should not cascade due to circuit breaker
        for _ in range(5):
            web.check_health()

        # Circuit breaker should have opened
        assert database.failure_count > 3

    def test_chaos_monkey_integration(self):
        """Test system behavior with chaos monkey active"""
        monkey = ChaosMonkey()

        def process_documents(docs: List[Dict]) -> Dict[str, Any]:
            """Process documents with potential failures"""
            processed = 0
            failed = 0

            for doc in docs:
                try:
                    # Simulate processing
                    content = yaml.dump(doc)
                    # This might fail due to chaos monkey
                    temp_file = Path(f"/tmp/doc_{doc['id']}.yaml")
                    # Use open() so chaos monkey can intercept
                    with open(temp_file, "w") as f:
                        f.write(content)
                    temp_file.unlink()  # Cleanup
                    processed += 1
                except Exception:
                    failed += 1

            return {
                "processed": processed,
                "failed": failed,
                "success_rate": processed / len(docs) if docs else 0,
            }

        # Create test documents
        docs = [{"id": i, "content": f"Document {i}"} for i in range(20)]

        # Process with chaos monkey
        with monkey.random_failures(failure_rate=0.3):
            results = process_documents(docs)

        # Should handle some failures
        assert results["failed"] > 0
        assert results["processed"] > 0
        assert results["success_rate"] < 1.0

        # Verify chaos monkey tracked failures
        assert len(monkey.failures_injected) > 0


@pytest.mark.chaos
@pytest.mark.slow
class TestLongRunningChaos:
    """Long-running chaos tests"""

    def test_sustained_load_with_failures(self):
        """Test system under sustained load with random failures"""
        duration = 10  # seconds
        start_time = time.time()

        operations = []
        errors = []

        while time.time() - start_time < duration:
            try:
                # Simulate operation that might fail
                if random.random() < 0.9:  # 90% success rate
                    operations.append(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "duration": random.uniform(0.01, 0.1),
                            "success": True,
                        }
                    )
                else:
                    raise Exception("Random failure")

                # Small delay
                time.sleep(0.01)

            except Exception as e:
                errors.append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e),
                    }
                )

        # Analyze results
        total_ops = len(operations) + len(errors)
        success_rate = len(operations) / total_ops if total_ops > 0 else 0

        assert total_ops > 100  # Should process many operations
        assert 0.8 < success_rate < 0.95  # Around expected 90%
        assert len(errors) > 0  # Should have some errors


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "chaos"])
