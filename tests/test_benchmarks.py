#!/usr/bin/env python3
"""
Benchmark tests to detect performance regressions
Uses pytest-benchmark to track performance over time
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.validators.kv_validators import sanitize_metric_name, validate_redis_key


class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    def test_hash_computation_benchmark(self, benchmark) -> None:
        """Benchmark hash computation performance"""
        embedder = HashDiffEmbedder()

        # Test data of various sizes
        test_content = "x" * 10000  # 10KB of data

        # Benchmark the hash computation
        result = benchmark(embedder._compute_content_hash, test_content)

        # Ensure result is valid
        assert len(result) == 64  # SHA-256 hash
        assert all(c in "0123456789abcdef" for c in result)

    def test_embedding_hash_benchmark(self, benchmark) -> None:
        """Benchmark embedding hash computation"""
        embedder = HashDiffEmbedder()

        # Typical embedding vector (1536 dimensions for ada-002)
        test_embedding = [0.1] * 1536

        # Benchmark the embedding hash computation
        result = benchmark(embedder._compute_embedding_hash, test_embedding)

        # Ensure result is valid
        assert len(result) == 64

    def test_yaml_parsing_benchmark(self, benchmark) -> None:
        """Benchmark YAML parsing performance"""
        # Create a moderately complex YAML document
        test_doc = {
            "metadata": {
                "version": "1.0",
                "created_date": "2024-01-01",
                "tags": ["tag1", "tag2", "tag3"],
            },
            "content": {
                "sections": [
                    {"title": f"Section {i}", "text": "Lorem ipsum" * 10} for i in range(10)
                ]
            },
        }

        yaml_content = yaml.dump(test_doc)

        # Benchmark YAML parsing
        result = benchmark(yaml.safe_load, yaml_content)

        # Ensure parsing worked
        assert isinstance(result, dict)
        assert "metadata" in result

    def test_redis_key_validation_benchmark(self, benchmark) -> None:
        """Benchmark Redis key validation performance"""
        # Various test keys
        test_keys = [
            "simple_key",
            "key:with:colons:and:segments",
            "unicode_key_测试_🔑",
            "a" * 500,  # Long key
        ]

        # Benchmark validation of multiple keys
        def validate_batch():
            return [validate_redis_key(key) for key in test_keys]

        results = benchmark(validate_batch)

        # Ensure validations worked
        assert len(results) == len(test_keys)

    def test_metric_sanitization_benchmark(self, benchmark) -> None:
        """Benchmark metric name sanitization performance"""
        # Various metric names to sanitize
        test_names = [
            "simple.metric",
            "metric with spaces",
            "unicode_метрика_测试",
            "metric" * 100,  # Long name
        ]

        # Benchmark sanitization of multiple names
        def sanitize_batch():
            return [sanitize_metric_name(name) for name in test_names]

        results = benchmark(sanitize_batch)

        # Ensure sanitization worked
        assert len(results) == len(test_names)

    @pytest.mark.slow
    def test_document_embedding_benchmark(self, benchmark) -> None:
        """Benchmark full document embedding process"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test document
            doc_path = Path(temp_dir) / "test_doc.yaml"
            doc_content = {
                "title": "Test Document",
                "content": "This is a test document for benchmarking",
                "metadata": {"type": "benchmark", "version": "1.0"},
            }
            doc_path.write_text(yaml.dump(doc_content))

            # Create embedder
            embedder = HashDiffEmbedder()
            embedder.config = {"qdrant": {"collection_name": "test"}}

            # Mock the embedding part to focus on processing
            def mock_embed_document():
                # Just compute hashes, don't actually call OpenAI
                with open(doc_path) as f:
                    content = f.read()
                content_hash = embedder._compute_content_hash(content)
                return content_hash

            # Benchmark document processing
            result = benchmark(mock_embed_document)

            # Ensure it worked
            assert len(result) == 64


class TestConcurrencyBenchmarks:
    """Benchmarks for concurrent operations"""

    def test_concurrent_hash_cache_benchmark(self, benchmark) -> None:
        """Benchmark concurrent hash cache operations"""
        from concurrent.futures import ThreadPoolExecutor

        embedder = HashDiffEmbedder()
        embedder.hash_cache = {}

        def concurrent_cache_operations():
            """Simulate concurrent cache reads and writes"""
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []

                # Mix of read and write operations
                for i in range(100):
                    if i % 2 == 0:
                        # Write operation
                        future = executor.submit(
                            embedder.hash_cache.__setitem__, f"key_{i}", f"value_{i}"
                        )
                    else:
                        # Read operation
                        future = executor.submit(embedder.hash_cache.get, f"key_{i-1}", None)
                    futures.append(future)

                # Wait for all to complete
                for future in futures:
                    future.result()

            return len(embedder.hash_cache)

        # Benchmark concurrent operations
        result = benchmark(concurrent_cache_operations)

        # Should have written 50 entries (even indices)
        assert result == 50


# Configuration for benchmark comparison
# This allows comparing against previous runs
pytest_benchmark_compare_fail_threshold = {
    "mean": "200%",  # Fail if mean time doubles
    "median": "200%",  # Fail if median time doubles
    "min": "150%",  # Fail if minimum time increases by 50%
    "max": "300%",  # Fail if maximum time triples
}
