#!/usr/bin/env python3
"""
Performance benchmark tests for critical paths
Ensures that performance-critical operations meet timing requirements
"""

import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator

import pytest
import yaml

from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.validators.kv_validators import (
    sanitize_metric_name,
    validate_cache_entry,
    validate_redis_key,
)


@contextmanager
def timing_assert(max_seconds: float, operation: str = "Operation") -> Generator[None, None, None]:
    """Context manager that asserts operation completes within time limit"""
    import os

    # Apply CI environment tolerance - CI environments are often slower
    ci_multiplier = 2.0 if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") else 1.0
    adjusted_limit = max_seconds * ci_multiplier

    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start

        # Always log performance for tracking
        print(f"📊 Performance: {operation} took {elapsed:.3f}s (limit: {adjusted_limit:.1f}s)")

        assert elapsed < adjusted_limit, (
            f"{operation} took {elapsed:.3f}s, "
            f"expected < {adjusted_limit:.1f}s (CI factor: {ci_multiplier}x)"
        )


class TestPerformanceBenchmarks:
    """Test performance of critical operations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.embedder = HashDiffEmbedder()

    @pytest.mark.benchmark
    def test_hash_computation_performance(self):
        """Test that hash computation is fast for typical documents"""
        # Create a typical document (5KB)
        content = "Sample document content\n" * 200

        with timing_assert(0.01, "Hash computation for 5KB document"):
            for _ in range(100):
                self.embedder._compute_content_hash(content)

        # Test larger document (100KB)
        large_content = content * 20

        with timing_assert(0.1, "Hash computation for 100KB document"):
            for _ in range(10):
                self.embedder._compute_content_hash(large_content)

    @pytest.mark.benchmark
    def test_yaml_parsing_performance(self):
        """Test YAML parsing performance for typical documents"""
        # Create a typical YAML document
        doc = {
            "metadata": {
                "document_type": "design",
                "version": "1.0",
                "created_date": "2024-01-01",
                "author": "system",
                "tags": ["architecture", "microservices", "api"],
            },
            "content": {
                "sections": [
                    {
                        "title": f"Section {i}",
                        "content": f"Content for section {i}" * 10,
                        "subsections": [
                            {"title": f"Subsection {j}", "content": f"Details {j}"}
                            for j in range(5)
                        ],
                    }
                    for i in range(10)
                ]
            },
        }

        yaml_content = yaml.dump(doc, default_flow_style=False)

        with timing_assert(
            8.0, "YAML parsing for typical document"
        ):  # Increased from 5.0 for CI stability
            for _ in range(100):
                yaml.safe_load(yaml_content)

    @pytest.mark.benchmark
    def test_validation_performance(self):
        """Test validation functions performance"""
        # Test Redis key validation
        keys = [f"test:key:{i}" for i in range(1000)]

        with timing_assert(0.02, "Redis key validation (1000 keys)"):
            for key in keys:
                validate_redis_key(key)

        # Test metric name sanitization
        names = [f"test.metric.name_{i}" for i in range(1000)]

        with timing_assert(0.02, "Metric name sanitization (1000 names)"):
            for name in names:
                sanitize_metric_name(name)

    @pytest.mark.benchmark
    def test_batch_processing_performance(self):
        """Test batch processing operations"""
        # Create test data
        documents = []
        for i in range(100):
            doc = {
                "id": f"doc_{i}",
                "content": f"Document content {i}" * 50,
                "metadata": {
                    "created": datetime.utcnow().isoformat(),
                    "author": f"user_{i % 10}",
                    "tags": [f"tag_{j}" for j in range(5)],
                },
            }
            documents.append(doc)

        # Test batch hash computation
        with timing_assert(0.5, "Batch hash computation (100 documents)"):
            hashes = []
            for doc in documents:
                content = yaml.dump(doc)
                hash_value = self.embedder._compute_content_hash(content)
                hashes.append(hash_value)

        # Test batch validation
        with timing_assert(0.1, "Batch validation (100 documents)"):
            results = []
            for doc in documents:
                # Simulate validation
                is_valid = (
                    isinstance(doc.get("id"), str)
                    and isinstance(doc.get("content"), str)
                    and isinstance(doc.get("metadata"), dict)
                )
                results.append(is_valid)

    @pytest.mark.benchmark
    def test_file_operations_performance(self):
        """Test file I/O performance"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            files = []
            for i in range(50):
                file_path = temp_path / f"test_{i}.yaml"
                content = {
                    "metadata": {"id": i, "timestamp": datetime.utcnow().isoformat()},
                    "data": {"value": f"test_data_{i}" * 100},
                }
                files.append((file_path, content))

            # Test write performance
            with timing_assert(1.0, "Write 50 YAML files"):
                for file_path, content in files:
                    with open(file_path, "w") as f:
                        yaml.dump(content, f)

            # Test read performance
            with timing_assert(0.5, "Read 50 YAML files"):
                loaded = []
                for file_path, _ in files:
                    with open(file_path) as f:
                        data = yaml.safe_load(f)
                        loaded.append(data)

    @pytest.mark.benchmark
    def test_search_performance(self):
        """Test search and filtering performance"""
        # Create test dataset
        items = []
        for i in range(10000):
            item = {
                "id": i,
                "name": f"item_{i}",
                "category": f"category_{i % 20}",
                "tags": [f"tag_{j}" for j in range(i % 5)],
                "created": datetime.utcnow().isoformat(),
            }
            items.append(item)

        # Test filtering by category
        with timing_assert(0.5, "Filter 10k items by category"):
            filtered = [item for item in items if item["category"] == "category_5"]
            assert len(filtered) == 500

        # Test multi-field search
        with timing_assert(0.1, "Multi-field search in 10k items"):
            # Search for items with tag_2 and specific id pattern
            # Note: items where id % 5 >= 3 will have tag_2
            # Use id % 50 == 3 to ensure we get items with tag_2
            results = [item for item in items if "tag_2" in item["tags"] and item["id"] % 50 == 3]
            # Items like 3, 53, 103, etc. will match (they have id%5=3, so tag_2 is present)
            assert len(results) > 0, f"Expected some results but found {len(results)}"

    @pytest.mark.benchmark
    def test_cache_operations_performance(self):
        """Test cache-like operations performance"""
        cache: Dict[str, Any] = {}

        # Test cache writes
        with timing_assert(0.1, "Cache write 1000 entries"):
            for i in range(1000):
                key = f"cache:key:{i}"
                value = {
                    "data": f"value_{i}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "ttl": 3600,
                }
                cache[key] = value

        # Test cache reads
        with timing_assert(0.5, "Cache read 1000 entries"):
            values = []
            for i in range(1000):
                key = f"cache:key:{i}"
                value = cache.get(key)
                values.append(value)

        # Test cache validation
        with timing_assert(0.1, "Validate 1000 cache entries"):
            valid_count = 0
            for key, value in cache.items():
                entry = {
                    "key": key,
                    "value": value.get("data"),
                    "created_at": value.get("timestamp"),  # validator expects created_at
                    "ttl_seconds": value.get("ttl"),  # validator expects ttl_seconds
                }
                if validate_cache_entry(entry):
                    valid_count += 1
            assert valid_count == 1000


class TestCriticalPathPerformance:
    """Test performance of critical user paths"""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_document_processing_pipeline(self):
        """Test complete document processing pipeline performance"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Simulate document processing pipeline
            documents_processed = 0

            with timing_assert(5.0, "Process 100 documents through pipeline"):
                for i in range(100):
                    # 1. Create document
                    doc = {
                        "metadata": {
                            "document_type": "design",
                            "id": f"doc_{i}",
                            "created": datetime.utcnow().isoformat(),
                        },
                        "content": {"title": f"Document {i}", "body": "x" * 1000},
                    }

                    # 2. Validate document
                    assert doc.get("metadata", {}).get("document_type")

                    # 3. Compute hash
                    content = yaml.dump(doc)
                    HashDiffEmbedder()._compute_content_hash(content)

                    # 4. Save to disk
                    file_path = temp_path / f"doc_{i}.yaml"
                    with open(file_path, "w") as f:
                        yaml.dump(doc, f)

                    # 5. Verify saved
                    assert file_path.exists()

                    documents_processed += 1

            assert documents_processed == 100

    @pytest.mark.benchmark
    def test_agent_execution_performance(self):
        """Test agent execution performance"""
        # Simulate agent execution with timing
        execution_times = []

        with timing_assert(2.0, "Execute 10 agent runs"):
            for run in range(10):
                start = time.perf_counter()

                # Simulate agent tasks
                tasks = []
                for i in range(20):
                    task = {
                        "id": f"task_{i}",
                        "status": "pending",
                        "created": datetime.utcnow().isoformat(),
                    }
                    # Process task
                    task["status"] = "completed"
                    task["completed"] = datetime.utcnow().isoformat()
                    tasks.append(task)

                # Generate report
                report = {
                    "run_id": run,
                    "tasks_completed": len(tasks),
                    "success_rate": 1.0,
                    "duration": time.perf_counter() - start,
                }

                execution_times.append(report["duration"])

        # Verify consistent performance
        avg_time = sum(execution_times) / len(execution_times)
        max_deviation = max(abs(t - avg_time) for t in execution_times)
        assert (
            max_deviation < 0.1
        ), f"Execution times too variable: max deviation {max_deviation:.3f}s"


class TestPerformanceRegression:
    """Test for performance regressions"""

    @pytest.mark.benchmark
    def test_performance_baselines(self):
        """Test against established performance baselines"""
        baselines = {
            "hash_computation_per_kb": 0.02,  # 20ms per KB (realistic for Python)
            "yaml_parse_per_kb": 0.05,  # 50ms per KB
            "validation_per_item": 0.0001,  # 100μs per item
            "file_write_per_mb": 0.5,  # 500ms per MB
        }

        results = {}

        # Test hash computation
        content = "x" * 1024  # 1KB
        start = time.perf_counter()
        for _ in range(100):
            HashDiffEmbedder()._compute_content_hash(content)
        elapsed = time.perf_counter() - start
        results["hash_computation_per_kb"] = elapsed / 100

        # Test YAML parsing
        yaml_content = yaml.dump({"data": "x" * 1000})  # ~1KB
        start = time.perf_counter()
        for _ in range(100):
            yaml.safe_load(yaml_content)
        elapsed = time.perf_counter() - start
        results["yaml_parse_per_kb"] = elapsed / 100

        # Test validation
        start = time.perf_counter()
        for i in range(10000):
            validate_redis_key(f"test:key:{i}")
        elapsed = time.perf_counter() - start
        results["validation_per_item"] = elapsed / 10000

        # Check against baselines
        for metric, baseline in baselines.items():
            if metric in results:
                actual = results[metric]
                assert (
                    actual < baseline * 1.5
                ), f"{metric} regression: {actual:.6f}s vs baseline {baseline:.6f}s"
                print(f"✓ {metric}: {actual:.6f}s (baseline: {baseline:.6f}s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
