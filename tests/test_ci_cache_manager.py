"""Unit tests for CI Cache Manager."""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the module under test
try:
    from ci_cache_manager import (  # type: ignore[import-not-found]
        CICacheManager,
        LocalCacheBackend,
        RedisCacheBackend,
    )
except ImportError:
    # If import fails, skip this test module
    pytest.skip("ci_cache_manager module not found", allow_module_level=True)


class TestLocalCacheBackend(unittest.TestCase):
    """Test local filesystem cache backend."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backend = LocalCacheBackend(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_set(self):
        """Test basic get/set operations."""
        # Test set
        self.backend.set("test_key", "test_value")

        # Test get
        value = self.backend.get("test_key")
        self.assertEqual(value, "test_value")

    def test_get_nonexistent(self):
        """Test getting non-existent key."""
        value = self.backend.get("nonexistent")
        self.assertIsNone(value)

    def test_delete(self):
        """Test delete operation."""
        # Set a value
        self.backend.set("test_key", "test_value")
        self.assertEqual(self.backend.get("test_key"), "test_value")

        # Delete it
        self.backend.delete("test_key")
        self.assertIsNone(self.backend.get("test_key"))

    def test_exists(self):
        """Test exists operation."""
        # Non-existent key
        self.assertFalse(self.backend.exists("test_key"))

        # Set a value
        self.backend.set("test_key", "test_value")
        self.assertTrue(self.backend.exists("test_key"))

    def test_complex_data(self):
        """Test storing complex data structures."""
        data = {"key": "value", "list": [1, 2, 3], "nested": {"a": "b"}}
        self.backend.set("complex", data)
        retrieved = self.backend.get("complex")
        self.assertEqual(retrieved, data)


class TestRedisCacheBackend(unittest.TestCase):
    """Test Redis cache backend."""

    @patch("ci_cache_manager.redis")
    def test_redis_operations(self, mock_redis):
        """Test Redis backend operations."""
        # Set up mock
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client

        # Create backend
        backend = RedisCacheBackend("redis://localhost:6379")

        # Test set
        backend.set("test_key", {"data": "value"})
        mock_client.set.assert_called_once()
        args = mock_client.set.call_args[0]
        self.assertEqual(args[0], "test_key")
        self.assertEqual(json.loads(args[1]), {"data": "value"})

        # Test get
        mock_client.get.return_value = json.dumps({"data": "value"}).encode()
        value = backend.get("test_key")
        self.assertEqual(value, {"data": "value"})

        # Test get None
        mock_client.get.return_value = None
        value = backend.get("nonexistent")
        self.assertIsNone(value)

        # Test delete
        backend.delete("test_key")
        mock_client.delete.assert_called_once_with("test_key")

        # Test exists
        mock_client.exists.return_value = True
        self.assertTrue(backend.exists("test_key"))

    @patch("ci_cache_manager.redis")
    def test_redis_connection_error(self, mock_redis):
        """Test Redis connection error handling."""
        mock_redis.Redis.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            RedisCacheBackend("redis://localhost:6379")


class TestCICacheManager(unittest.TestCase):
    """Test CI Cache Manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CICacheManager(cache_dir=self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_cache_key(self):
        """Test cache key generation."""
        key = self.cache_manager.get_cache_key(
            command="pytest",
            dependencies=["requirements.txt", "setup.py"],
            env_vars={"PYTHON_VERSION": "3.11"},
        )

        # Key should be a valid SHA256 hash
        self.assertEqual(len(key), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in key))

        # Same inputs should produce same key
        key2 = self.cache_manager.get_cache_key(
            command="pytest",
            dependencies=["requirements.txt", "setup.py"],
            env_vars={"PYTHON_VERSION": "3.11"},
        )
        self.assertEqual(key, key2)

        # Different inputs should produce different keys
        key3 = self.cache_manager.get_cache_key(
            command="pytest",
            dependencies=["requirements.txt"],
            env_vars={"PYTHON_VERSION": "3.11"},
        )
        self.assertNotEqual(key, key3)

    @patch("ci_cache_manager.subprocess.run")
    def test_restore_cache_success(self, mock_run):
        """Test successful cache restoration."""
        # Set up cache
        cache_data = {
            "command": "pytest",
            "exit_code": 0,
            "stdout": "All tests passed",
            "stderr": "",
            "duration": 10.5,
            "artifacts": {"coverage.xml": "base64_encoded_data"},
        }
        key = self.cache_manager.get_cache_key("pytest", [], {})
        self.cache_manager.backend.set(key, cache_data)

        # Test restore
        with patch("builtins.open", unittest.mock.mock_open()):
            result = self.cache_manager.restore_cache("pytest", [], {})

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 0)  # Should not run command

    def test_restore_cache_miss(self):
        """Test cache miss."""
        result = self.cache_manager.restore_cache("pytest", [], {})
        self.assertFalse(result)

    @patch("ci_cache_manager.subprocess.run")
    @patch("ci_cache_manager.time.time")
    def test_run_with_cache_new(self, mock_time, mock_run):
        """Test running command with cache (cache miss)."""
        # Set up mocks
        mock_time.side_effect = [100, 110]  # Start and end time
        mock_run.return_value = Mock(returncode=0, stdout="Test output", stderr="", args=["pytest"])

        # Run command
        with patch("builtins.open", unittest.mock.mock_open(read_data="artifact_data")):
            exit_code = self.cache_manager.run_with_cache(
                "pytest", dependencies=[], env_vars={}, artifacts=["coverage.xml"]
            )

        self.assertEqual(exit_code, 0)
        mock_run.assert_called_once()

        # Check cache was saved
        key = self.cache_manager.get_cache_key("pytest", [], {})
        cached = self.cache_manager.backend.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["exit_code"], 0)
        self.assertEqual(cached["stdout"], "Test output")

    @patch("ci_cache_manager.subprocess.run")
    def test_run_with_cache_hit(self, mock_run):
        """Test running command with cache (cache hit)."""
        # Pre-populate cache
        key = self.cache_manager.get_cache_key("pytest", [], {})
        self.cache_manager.backend.set(
            key,
            {
                "command": "pytest",
                "exit_code": 0,
                "stdout": "Cached output",
                "stderr": "",
                "duration": 5.0,
                "artifacts": {},
            },
        )

        # Run command
        exit_code = self.cache_manager.run_with_cache("pytest", [], {})

        self.assertEqual(exit_code, 0)
        mock_run.assert_not_called()  # Should use cache

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        # Set some cache entries
        key = self.cache_manager.get_cache_key("pytest", [], {})
        self.cache_manager.backend.set(key, {"data": "value"})
        self.assertTrue(self.cache_manager.backend.exists(key))

        # Invalidate
        self.cache_manager.invalidate_cache(key)
        self.assertFalse(self.cache_manager.backend.exists(key))

    def test_hash_file_content(self):
        """Test file content hashing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            hash1 = self.cache_manager._hash_file_content(f.name)
            self.assertEqual(len(hash1), 64)  # SHA256 hash

            # Same content should produce same hash
            hash2 = self.cache_manager._hash_file_content(f.name)
            self.assertEqual(hash1, hash2)

            os.unlink(f.name)

    def test_dependency_change_detection(self):
        """Test that cache key changes when dependencies change."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("version 1")
            f.flush()

            key1 = self.cache_manager.get_cache_key("pytest", [f.name], {})

            # Modify file
            f.seek(0)
            f.write("version 2")
            f.flush()

            key2 = self.cache_manager.get_cache_key("pytest", [f.name], {})
            self.assertNotEqual(key1, key2)

            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
