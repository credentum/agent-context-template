#!/usr/bin/env python3
"""
CI Cache Manager - Content-addressable caching system for CI optimization.

This module provides efficient caching for CI dependencies, build artifacts,
and test results using content-addressable storage with support for local
and distributed (Redis) backends.
"""

import hashlib
import json
import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class CacheConfig:
    """Configuration for CI cache manager."""

    backend: str = "local"  # local, redis, s3
    local_cache_dir: str = ".ci-cache"
    redis_url: str = "redis://localhost:6379"
    max_cache_size_mb: int = 5000  # 5GB default
    ttl_hours: int = 168  # 1 week default
    compression: bool = True
    verbose: bool = False


class CacheEntry:
    """Represents a single cache entry with metadata."""

    def __init__(self, key: str, path: str, metadata: Dict[str, Any]):
        self.key = key
        self.path = path
        self.metadata = metadata
        self.created_at = time.time()
        self.accessed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary."""
        return {
            "key": self.key,
            "path": self.path,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create cache entry from dictionary."""
        entry = cls(data["key"], data["path"], data["metadata"])
        entry.created_at = data.get("created_at", time.time())
        entry.accessed_at = data.get("accessed_at", time.time())
        return entry


class CICacheManager:
    """
    CI Cache Manager for optimizing build times through intelligent caching.

    Features:
    - Content-addressable storage
    - Dependency and artifact caching
    - Local and distributed backends
    - Smart invalidation
    - Compression support
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._setup_backend()
        self._cache_index: Dict[str, CacheEntry] = {}
        self._load_cache_index()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_backend(self) -> None:
        """Initialize the appropriate cache backend."""
        if self.config.backend == "local":
            self.cache_dir = Path(self.config.local_cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            self.logger.info(f"Using local cache at {self.cache_dir}")

        elif self.config.backend == "redis":
            if not REDIS_AVAILABLE:
                raise ImportError("Redis not available. Install with pip install redis")
            self.redis_client = redis.from_url(self.config.redis_url)
            try:
                self.redis_client.ping()
                self.logger.info(f"Connected to Redis at {self.config.redis_url}")
            except redis.ConnectionError as e:
                self.logger.error(f"Failed to connect to Redis: {e}")
                raise

        else:
            raise ValueError(f"Unsupported backend: {self.config.backend}")

    def _load_cache_index(self) -> None:
        """Load cache index from storage."""
        if self.config.backend == "local":
            index_file = self.cache_dir / "cache_index.json"
            if index_file.exists():
                try:
                    with open(index_file, "r") as f:
                        data = json.load(f)
                    self._cache_index = {k: CacheEntry.from_dict(v) for k, v in data.items()}
                    self.logger.debug(f"Loaded {len(self._cache_index)} cache entries")
                except Exception as e:
                    self.logger.warning(f"Failed to load cache index: {e}")

    def _save_cache_index(self) -> None:
        """Save cache index to storage."""
        if self.config.backend == "local":
            index_file = self.cache_dir / "cache_index.json"
            try:
                data = {k: v.to_dict() for k, v in self._cache_index.items()}
                with open(index_file, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to save cache index: {e}")

    def _calculate_hash(self, content: Union[str, bytes, Path]) -> str:
        """Calculate SHA-256 hash of content."""
        hasher = hashlib.sha256()

        if isinstance(content, str):
            hasher.update(content.encode())
        elif isinstance(content, bytes):
            hasher.update(content)
        elif isinstance(content, Path):
            if content.is_file():
                with open(content, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
            else:
                # Hash directory contents
                for file_path in sorted(content.rglob("*")):
                    if file_path.is_file():
                        hasher.update(str(file_path.relative_to(content)).encode())
                        with open(file_path, "rb") as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                hasher.update(chunk)

        return hasher.hexdigest()

    def _get_file_dependencies_hash(self, files: List[Path]) -> str:
        """Calculate hash based on file dependencies."""
        content_hashes = []
        for file_path in sorted(files):
            if file_path.exists():
                content_hashes.append(f"{file_path}:{self._calculate_hash(file_path)}")

        combined = "|".join(content_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_cache_key(
        self, command: str, dependencies: List[Path], env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate cache key based on command, dependencies, and environment.

        Args:
            command: The command being cached
            dependencies: List of dependency files/directories
            env_vars: Relevant environment variables

        Returns:
            Cache key string
        """
        # Hash command
        command_hash = hashlib.sha256(command.encode()).hexdigest()

        # Hash dependencies
        deps_hash = self._get_file_dependencies_hash(dependencies)

        # Hash environment variables
        env_hash = ""
        if env_vars:
            env_str = "|".join(f"{k}={v}" for k, v in sorted(env_vars.items()))
            env_hash = hashlib.sha256(env_str.encode()).hexdigest()

        # Combine all hashes
        combined = f"{command_hash}:{deps_hash}:{env_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def has_cache(self, cache_key: str) -> bool:
        """Check if cache entry exists."""
        if self.config.backend == "local":
            return cache_key in self._cache_index
        elif self.config.backend == "redis":
            return bool(self.redis_client.exists(f"cache:{cache_key}"))
        return False

    def get_cache(self, cache_key: str) -> Optional[Path]:
        """
        Retrieve cached content.

        Args:
            cache_key: The cache key to retrieve

        Returns:
            Path to cached content or None if not found
        """
        if not self.has_cache(cache_key):
            return None

        if self.config.backend == "local":
            entry = self._cache_index.get(cache_key)
            if entry:
                entry.accessed_at = time.time()
                cached_path = Path(entry.path)
                if cached_path.exists():
                    self.logger.info(f"Cache hit for key {cache_key}")
                    return cached_path
                else:
                    # Clean up stale entry
                    del self._cache_index[cache_key]
                    self._save_cache_index()

        self.logger.debug(f"Cache miss for key {cache_key}")
        return None

    def set_cache(
        self, cache_key: str, content_path: Path, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store content in cache.

        Args:
            cache_key: The cache key
            content_path: Path to content to cache
            metadata: Optional metadata to store with cache entry

        Returns:
            True if successful, False otherwise
        """
        if not content_path.exists():
            self.logger.error(f"Content path does not exist: {content_path}")
            return False

        try:
            if self.config.backend == "local":
                # Create cache storage path
                cache_storage_path = self.cache_dir / f"{cache_key}.cache"

                # Copy content to cache
                if content_path.is_file():
                    shutil.copy2(content_path, cache_storage_path)
                else:
                    shutil.copytree(content_path, cache_storage_path, dirs_exist_ok=True)

                # Store cache entry
                entry = CacheEntry(
                    key=cache_key, path=str(cache_storage_path), metadata=metadata or {}
                )
                self._cache_index[cache_key] = entry
                self._save_cache_index()

                self.logger.info(f"Cached content for key {cache_key}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to cache content: {e}")
            return False

        return False

    def cache_command_output(
        self,
        command: str,
        dependencies: List[Path],
        output_path: Path,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Cache the output of a command execution.

        Args:
            command: Command that was executed
            dependencies: Files the command depends on
            output_path: Path to command output to cache
            env_vars: Environment variables used

        Returns:
            True if cached successfully
        """
        cache_key = self.get_cache_key(command, dependencies, env_vars)

        metadata = {
            "command": command,
            "dependencies": [str(p) for p in dependencies],
            "env_vars": env_vars or {},
            "cached_at": time.time(),
        }

        return self.set_cache(cache_key, output_path, metadata)

    def get_cached_command_output(
        self, command: str, dependencies: List[Path], env_vars: Optional[Dict[str, str]] = None
    ) -> Optional[Path]:
        """
        Get cached output for a command.

        Args:
            command: Command to check cache for
            dependencies: Files the command depends on
            env_vars: Environment variables

        Returns:
            Path to cached output or None
        """
        cache_key = self.get_cache_key(command, dependencies, env_vars)
        return self.get_cache(cache_key)

    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up
        """
        if self.config.backend != "local":
            return 0

        current_time = time.time()
        ttl_seconds = self.config.ttl_hours * 3600
        expired_keys = []

        for key, entry in self._cache_index.items():
            if current_time - entry.created_at > ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            entry = self._cache_index[key]
            cache_path = Path(entry.path)
            if cache_path.exists():
                if cache_path.is_file():
                    cache_path.unlink()
                else:
                    shutil.rmtree(cache_path)
            del self._cache_index[key]

        if expired_keys:
            self._save_cache_index()
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "backend": self.config.backend,
            "total_entries": len(self._cache_index),
            "cache_size_mb": 0,
            "hit_rate": 0.0,
            "oldest_entry": None,
            "newest_entry": None,
        }

        if self.config.backend == "local" and self.cache_dir.exists():
            # Calculate cache size
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
            stats["cache_size_mb"] = total_size / (1024 * 1024)

            # Find oldest and newest entries
            if self._cache_index:
                entries_by_time = sorted(self._cache_index.values(), key=lambda e: e.created_at)
                stats["oldest_entry"] = entries_by_time[0].created_at
                stats["newest_entry"] = entries_by_time[-1].created_at

        return stats

    def clear_cache(self) -> bool:
        """Clear all cache entries."""
        try:
            if self.config.backend == "local":
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(exist_ok=True)
                self._cache_index.clear()
                self.logger.info("Cache cleared successfully")
                return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False

        return False


def main():
    """CLI interface for cache manager."""
    import argparse

    parser = argparse.ArgumentParser(description="CI Cache Manager")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Stats command
    subparsers.add_parser("stats", help="Show cache statistics")

    # Clear command
    subparsers.add_parser("clear", help="Clear cache")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up expired entries")

    args = parser.parse_args()

    config = CacheConfig(verbose=args.verbose)
    cache_manager = CICacheManager(config)

    if args.command == "stats":
        stats = cache_manager.get_cache_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "clear":
        if cache_manager.clear_cache():
            print("Cache cleared successfully")
        else:
            print("Failed to clear cache")

    elif args.command == "cleanup":
        cleaned = cache_manager.cleanup_expired()
        print(f"Cleaned up {cleaned} expired entries")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
