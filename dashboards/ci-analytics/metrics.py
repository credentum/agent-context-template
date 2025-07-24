#!/usr/bin/env python3
"""
CI Analytics Metrics Collection.

This module collects and aggregates CI performance metrics for the analytics dashboard.
"""

import json
import logging
import sqlite3
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class BuildMetric:
    """Represents a single build execution metric."""

    timestamp: float
    job_id: str
    job_type: str  # test, build, lint, etc.
    duration_seconds: float
    success: bool
    cache_hit: bool
    runner_id: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildMetric":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CacheMetric:
    """Represents cache performance metrics."""

    timestamp: float
    cache_key: str
    hit: bool
    size_bytes: int
    retrieval_time_ms: float
    backend: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ResourceMetric:
    """Represents resource utilization metrics."""

    timestamp: float
    runner_id: str
    cpu_percent: float
    memory_mb: float
    disk_io_mb: float
    network_io_mb: float
    duration_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class CIMetricsCollector:
    """
    Collects and stores CI performance metrics for analysis.

    Features:
    - Build performance tracking
    - Cache hit/miss analysis
    - Resource utilization monitoring
    - Historical trend analysis
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path(".ci-analytics.db")
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._setup_database()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_database(self) -> None:
        """Initialize SQLite database for metrics storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS build_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    job_id TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    cache_hit BOOLEAN NOT NULL,
                    runner_id TEXT,
                    resource_usage TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Cache metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    cache_key TEXT NOT NULL,
                    hit BOOLEAN NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    retrieval_time_ms REAL NOT NULL,
                    backend TEXT NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Resource metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS resource_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    runner_id TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_mb REAL NOT NULL,
                    disk_io_mb REAL NOT NULL,
                    network_io_mb REAL NOT NULL,
                    duration_seconds REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_build_timestamp ON build_metrics(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON cache_metrics(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_resource_timestamp ON resource_metrics(timestamp)"
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Initialized metrics database at {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")
            raise

    def record_build_metric(self, metric: BuildMetric) -> bool:
        """Record a build performance metric."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO build_metrics
                (timestamp, job_id, job_type, duration_seconds, success, cache_hit,
                 runner_id, resource_usage, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.job_id,
                    metric.job_type,
                    metric.duration_seconds,
                    metric.success,
                    metric.cache_hit,
                    metric.runner_id,
                    json.dumps(metric.resource_usage) if metric.resource_usage else None,
                    json.dumps(metric.metadata) if metric.metadata else None,
                ),
            )

            conn.commit()
            conn.close()

            self.logger.debug(f"Recorded build metric for job {metric.job_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to record build metric: {e}")
            return False

    def record_cache_metric(self, metric: CacheMetric) -> bool:
        """Record a cache performance metric."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO cache_metrics
                (timestamp, cache_key, hit, size_bytes, retrieval_time_ms, backend, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.cache_key,
                    metric.hit,
                    metric.size_bytes,
                    metric.retrieval_time_ms,
                    metric.backend,
                    json.dumps(metric.metadata) if metric.metadata else None,
                ),
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Failed to record cache metric: {e}")
            return False

    def record_resource_metric(self, metric: ResourceMetric) -> bool:
        """Record a resource utilization metric."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO resource_metrics
                (timestamp, runner_id, cpu_percent, memory_mb, disk_io_mb,
                 network_io_mb, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metric.timestamp,
                    metric.runner_id,
                    metric.cpu_percent,
                    metric.memory_mb,
                    metric.disk_io_mb,
                    metric.network_io_mb,
                    metric.duration_seconds,
                ),
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Failed to record resource metric: {e}")
            return False

    def get_build_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get build performance summary for the last N hours."""
        try:
            cutoff_time = time.time() - (hours * 3600)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get build statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_builds,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_builds,
                    AVG(duration_seconds) as avg_duration,
                    MIN(duration_seconds) as min_duration,
                    MAX(duration_seconds) as max_duration,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
                FROM build_metrics
                WHERE timestamp > ?
            """,
                (cutoff_time,),
            )

            result = cursor.fetchone()

            if not result or result[0] == 0:
                return {"error": "No build data found"}

            (
                total_builds,
                successful_builds,
                avg_duration,
                min_duration,
                max_duration,
                cache_hits,
            ) = result

            # Get performance by job type
            cursor.execute(
                """
                SELECT
                    job_type,
                    COUNT(*) as count,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM build_metrics
                WHERE timestamp > ?
                GROUP BY job_type
                ORDER BY count DESC
            """,
                (cutoff_time,),
            )

            job_type_stats = {}
            for row in cursor.fetchall():
                job_type, count, avg_dur, success_count = row
                job_type_stats[job_type] = {
                    "count": count,
                    "avg_duration": round(avg_dur, 2),
                    "success_rate": round((success_count / count) * 100, 1),
                }

            conn.close()

            summary = {
                "time_range_hours": hours,
                "total_builds": total_builds,
                "success_rate": round((successful_builds / total_builds) * 100, 1),
                "cache_hit_rate": round((cache_hits / total_builds) * 100, 1),
                "performance": {
                    "avg_duration": round(avg_duration, 2),
                    "min_duration": round(min_duration, 2),
                    "max_duration": round(max_duration, 2),
                },
                "by_job_type": job_type_stats,
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get build performance summary: {e}")
            return {"error": str(e)}

    def get_cache_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get cache performance summary for the last N hours."""
        try:
            cutoff_time = time.time() - (hours * 3600)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get cache statistics
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_requests,
                    SUM(CASE WHEN hit THEN 1 ELSE 0 END) as cache_hits,
                    AVG(retrieval_time_ms) as avg_retrieval_time,
                    SUM(size_bytes) as total_size_bytes,
                    backend
                FROM cache_metrics
                WHERE timestamp > ?
                GROUP BY backend
            """,
                (cutoff_time,),
            )

            backend_stats = {}
            total_requests = 0
            total_hits = 0

            for row in cursor.fetchall():
                requests, hits, avg_time, size_bytes, backend = row
                total_requests += requests
                total_hits += hits

                backend_stats[backend] = {
                    "requests": requests,
                    "hit_rate": round((hits / requests) * 100, 1) if requests > 0 else 0,
                    "avg_retrieval_time_ms": round(avg_time, 2),
                    "total_size_mb": round(size_bytes / (1024 * 1024), 2),
                }

            conn.close()

            overall_hit_rate = (
                round((total_hits / total_requests) * 100, 1) if total_requests > 0 else 0
            )

            summary = {
                "time_range_hours": hours,
                "total_requests": total_requests,
                "overall_hit_rate": overall_hit_rate,
                "by_backend": backend_stats,
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get cache performance summary: {e}")
            return {"error": str(e)}

    def get_resource_utilization_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get resource utilization summary for the last N hours."""
        try:
            cutoff_time = time.time() - (hours * 3600)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get resource statistics by runner
            cursor.execute(
                """
                SELECT
                    runner_id,
                    COUNT(*) as measurements,
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_mb) as avg_memory,
                    MAX(memory_mb) as max_memory,
                    SUM(disk_io_mb) as total_disk_io,
                    SUM(network_io_mb) as total_network_io
                FROM resource_metrics
                WHERE timestamp > ?
                GROUP BY runner_id
                ORDER BY measurements DESC
            """,
                (cutoff_time,),
            )

            runner_stats = {}
            for row in cursor.fetchall():
                runner_id, measurements, avg_cpu, max_cpu, avg_mem, max_mem, disk_io, net_io = row
                runner_stats[runner_id] = {
                    "measurements": measurements,
                    "cpu": {"avg_percent": round(avg_cpu, 1), "max_percent": round(max_cpu, 1)},
                    "memory": {"avg_mb": round(avg_mem, 1), "max_mb": round(max_mem, 1)},
                    "io": {"disk_mb": round(disk_io, 1), "network_mb": round(net_io, 1)},
                }

            conn.close()

            summary = {
                "time_range_hours": hours,
                "runners": len(runner_stats),
                "by_runner": runner_stats,
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get resource utilization summary: {e}")
            return {"error": str(e)}

    def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over the last N days."""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get daily performance trends
            cursor.execute(
                """
                SELECT
                    DATE(datetime(timestamp, 'unixepoch')) as date,
                    COUNT(*) as builds,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as cache_hit_rate
                FROM build_metrics
                WHERE timestamp > ?
                GROUP BY DATE(datetime(timestamp, 'unixepoch'))
                ORDER BY date
            """,
                (cutoff_time,),
            )

            daily_trends = []
            for row in cursor.fetchall():
                date, builds, avg_dur, success_rate, cache_hit_rate = row
                daily_trends.append(
                    {
                        "date": date,
                        "builds": builds,
                        "avg_duration": round(avg_dur, 2),
                        "success_rate": round(success_rate, 1),
                        "cache_hit_rate": round(cache_hit_rate, 1),
                    }
                )

            conn.close()

            # Calculate trend indicators
            if len(daily_trends) >= 2:
                recent_avg_duration = statistics.mean(
                    [d["avg_duration"] for d in daily_trends[-3:]]
                )
                earlier_avg_duration = statistics.mean(
                    [d["avg_duration"] for d in daily_trends[:3]]
                )
                duration_trend = (
                    "improving" if recent_avg_duration < earlier_avg_duration else "declining"
                )
            else:
                duration_trend = "insufficient_data"

            summary = {
                "time_range_days": days,
                "daily_trends": daily_trends,
                "trend_indicators": {"duration_trend": duration_trend},
            }

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get performance trends: {e}")
            return {"error": str(e)}

    def cleanup_old_metrics(self, days: int = 90) -> int:
        """Clean up metrics older than N days."""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count records to be deleted
            cursor.execute("SELECT COUNT(*) FROM build_metrics WHERE timestamp < ?", (cutoff_time,))
            build_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cache_metrics WHERE timestamp < ?", (cutoff_time,))
            cache_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM resource_metrics WHERE timestamp < ?", (cutoff_time,)
            )
            resource_count = cursor.fetchone()[0]

            # Delete old records
            cursor.execute("DELETE FROM build_metrics WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM cache_metrics WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM resource_metrics WHERE timestamp < ?", (cutoff_time,))

            conn.commit()
            conn.close()

            total_deleted = build_count + cache_count + resource_count
            self.logger.info(f"Cleaned up {total_deleted} old metric records")

            return int(total_deleted)

        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")
            return 0

    def export_metrics(self, output_file: Path, format: str = "json", hours: int = 24) -> bool:
        """Export metrics to file."""
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "time_range_hours": hours,
                "build_performance": self.get_build_performance_summary(hours),
                "cache_performance": self.get_cache_performance_summary(hours),
                "resource_utilization": self.get_resource_utilization_summary(hours),
            }

            if format.lower() == "json":
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Exported metrics to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False


def main():
    """CLI interface for metrics collector."""
    import argparse

    parser = argparse.ArgumentParser(description="CI Analytics Metrics Collector")
    parser.add_argument("--db-path", type=Path, help="Database path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Summary command
    summary_parser = subparsers.add_parser("summary", help="Show performance summary")
    summary_parser.add_argument("--hours", type=int, default=24, help="Time range in hours")

    # Trends command
    trends_parser = subparsers.add_parser("trends", help="Show performance trends")
    trends_parser.add_argument("--days", type=int, default=7, help="Time range in days")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export metrics")
    export_parser.add_argument("--output", "-o", type=Path, required=True, help="Output file")
    export_parser.add_argument("--format", default="json", help="Export format")
    export_parser.add_argument("--hours", type=int, default=24, help="Time range in hours")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old metrics")
    cleanup_parser.add_argument(
        "--days", type=int, default=90, help="Keep metrics newer than N days"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    collector = CIMetricsCollector(args.db_path)

    if args.command == "summary":
        build_summary = collector.get_build_performance_summary(args.hours)
        cache_summary = collector.get_cache_performance_summary(args.hours)
        resource_summary = collector.get_resource_utilization_summary(args.hours)

        print("=== Build Performance Summary ===")
        print(json.dumps(build_summary, indent=2))
        print("\n=== Cache Performance Summary ===")
        print(json.dumps(cache_summary, indent=2))
        print("\n=== Resource Utilization Summary ===")
        print(json.dumps(resource_summary, indent=2))

    elif args.command == "trends":
        trends = collector.get_performance_trends(args.days)
        print("=== Performance Trends ===")
        print(json.dumps(trends, indent=2))

    elif args.command == "export":
        success = collector.export_metrics(args.output, args.format, args.hours)
        if success:
            print(f"Metrics exported to {args.output}")
        else:
            print("Failed to export metrics")

    elif args.command == "cleanup":
        deleted = collector.cleanup_old_metrics(args.days)
        print(f"Cleaned up {deleted} old metric records")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
