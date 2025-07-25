"""Unit tests for CI Analytics Metrics."""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

# Import the module under test
try:
    from metrics import CIMetric, CIMetricsCollector  # type: ignore[import-not-found]
except ImportError:
    # Define mock classes for testing when metrics.py doesn't have these exports
    from dataclasses import dataclass
    from typing import Any, Dict, Optional

    @dataclass
    class CIMetric:  # type: ignore[no-redef]
        timestamp: datetime
        workflow_name: str
        job_name: str
        status: str
        duration_seconds: float
        runner_type: Optional[str] = None
        cache_hit: Optional[bool] = None
        artifacts_size_mb: Optional[float] = None
        metadata: Optional[Dict[str, Any]] = None

        def to_dict(self):
            return {
                "timestamp": self.timestamp.isoformat(),
                "workflow_name": self.workflow_name,
                "job_name": self.job_name,
                "status": self.status,
                "duration_seconds": self.duration_seconds,
                "runner_type": self.runner_type,
                "cache_hit": self.cache_hit,
                "artifacts_size_mb": self.artifacts_size_mb,
                "metadata": self.metadata or {},
            }

    class CIMetricsCollector:  # type: ignore[no-redef]
        def __init__(self, db_path="metrics.db"):
            self.db_path = db_path
            self._init_database()

        def _init_database(self):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ci_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    runner_type TEXT,
                    cache_hit BOOLEAN,
                    artifacts_size_mb REAL,
                    metadata TEXT
                )
            """
            )
            conn.commit()
            conn.close()

        def collect_metric(self, metric: CIMetric):
            pass

        def get_metrics_by_timerange(self, start_time, end_time):
            return []

        def get_metrics_by_workflow(self, workflow_name):
            return []

        def calculate_success_rate(self, workflow_name):
            return 0.0

        def calculate_average_duration(self, workflow_name):
            return 0.0

        def get_cache_hit_rate(self, workflow_name):
            return 0.0

        def get_failure_trends(self, workflow_name, days=7):
            return []

        def aggregate_by_runner_type(self):
            return {}

        def export_to_json(self, filepath):
            pass

        def cleanup_old_metrics(self, days=30):
            pass

        def get_percentile_duration(self, workflow_name, percentile):
            return 0.0


class TestCIMetric(unittest.TestCase):
    """Test CIMetric dataclass."""

    def test_metric_creation(self):
        """Test creating a CI metric."""
        metric = CIMetric(
            timestamp=datetime.utcnow(),
            workflow_name="Unit Tests",
            job_name="test-python-3.11",
            status="success",
            duration_seconds=120.5,
            runner_type="ubuntu-latest",
            cache_hit=True,
            artifacts_size_mb=5.2,
        )

        self.assertEqual(metric.workflow_name, "Unit Tests")
        self.assertEqual(metric.status, "success")
        self.assertTrue(metric.cache_hit)
        self.assertEqual(metric.duration_seconds, 120.5)

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        now = datetime.utcnow()
        metric = CIMetric(
            timestamp=now,
            workflow_name="Build",
            job_name="build-app",
            status="failure",
            duration_seconds=60,
        )
        metric_dict = metric.to_dict()

        self.assertEqual(metric_dict["timestamp"], now.isoformat())
        self.assertEqual(metric_dict["workflow_name"], "Build")
        self.assertEqual(metric_dict["status"], "failure")
        self.assertIn("metadata", metric_dict)


class TestCIMetricsCollector(unittest.TestCase):
    """Test CI Metrics Collector."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_metrics.db")
        self.collector = CIMetricsCollector(db_path=self.db_path)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_database_initialization(self):
        """Test database is initialized correctly."""
        # Check table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ci_metrics'")
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result)

    def test_collect_metric(self):
        """Test collecting a metric."""
        metric = CIMetric(
            timestamp=datetime.utcnow(),
            workflow_name="Test Workflow",
            job_name="test-job",
            status="success",
            duration_seconds=100,
        )

        self.collector.collect_metric(metric)

        # Verify metric was saved
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ci_metrics")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 1)

    def test_get_metrics_by_timerange(self):
        """Test retrieving metrics by time range."""
        now = datetime.utcnow()

        # Add metrics at different times
        for i in range(5):
            metric = CIMetric(
                timestamp=now - timedelta(hours=i),
                workflow_name=f"Workflow {i}",
                job_name="job",
                status="success",
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        # Get metrics from last 2 hours
        start_time = now - timedelta(hours=2)
        metrics = self.collector.get_metrics_by_timerange(start_time, now)

        self.assertEqual(len(metrics), 3)  # Should get metrics from 0, 1, 2 hours ago

    def test_get_metrics_by_workflow(self):
        """Test retrieving metrics by workflow."""
        # Add metrics for different workflows
        workflows = ["Build", "Test", "Deploy", "Test"]
        for workflow in workflows:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name=workflow,
                job_name="job",
                status="success",
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        # Get metrics for Test workflow
        metrics = self.collector.get_metrics_by_workflow("Test")

        self.assertEqual(len(metrics), 2)
        self.assertTrue(all(m.workflow_name == "Test" for m in metrics))

    def test_calculate_success_rate(self):
        """Test calculating success rate."""
        # Add mix of success and failure metrics
        statuses = ["success", "success", "failure", "success", "failure"]
        for status in statuses:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name="Build",
                job_name="job",
                status=status,
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        success_rate = self.collector.calculate_success_rate("Build")

        self.assertAlmostEqual(success_rate, 0.6, places=2)  # 3/5 = 0.6

    def test_calculate_average_duration(self):
        """Test calculating average duration."""
        # Add metrics with different durations
        durations = [60, 120, 90, 150, 80]
        for duration in durations:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name="Test",
                job_name="job",
                status="success",
                duration_seconds=duration,
            )
            self.collector.collect_metric(metric)

        avg_duration = self.collector.calculate_average_duration("Test")

        self.assertEqual(avg_duration, 100)  # (60+120+90+150+80)/5 = 100

    def test_get_cache_hit_rate(self):
        """Test calculating cache hit rate."""
        # Add metrics with mix of cache hits
        cache_hits = [True, True, False, True, False, True]
        for hit in cache_hits:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name="Build",
                job_name="job",
                status="success",
                duration_seconds=60,
                cache_hit=hit,
            )
            self.collector.collect_metric(metric)

        hit_rate = self.collector.get_cache_hit_rate("Build")

        self.assertAlmostEqual(hit_rate, 0.667, places=2)  # 4/6 ≈ 0.667

    def test_get_failure_trends(self):
        """Test getting failure trends."""
        now = datetime.utcnow()

        # Add failures at different times
        for i in range(10):
            metric = CIMetric(
                timestamp=now - timedelta(days=i),
                workflow_name="Deploy",
                job_name="job",
                status="failure" if i % 3 == 0 else "success",
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        trends = self.collector.get_failure_trends("Deploy", days=7)

        self.assertIsInstance(trends, list)
        self.assertTrue(len(trends) <= 7)

    def test_aggregate_by_runner_type(self):
        """Test aggregating metrics by runner type."""
        runner_types = ["ubuntu-latest", "windows-latest", "ubuntu-latest", "macos-latest"]
        for runner in runner_types:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name="Cross-platform",
                job_name="job",
                status="success",
                duration_seconds=60,
                runner_type=runner,
            )
            self.collector.collect_metric(metric)

        aggregated = self.collector.aggregate_by_runner_type()

        self.assertEqual(aggregated["ubuntu-latest"], 2)
        self.assertEqual(aggregated["windows-latest"], 1)
        self.assertEqual(aggregated["macos-latest"], 1)

    def test_export_to_json(self):
        """Test exporting metrics to JSON."""
        # Add some metrics
        for i in range(3):
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name=f"Workflow{i}",
                job_name="job",
                status="success",
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        # Export to JSON
        json_file = os.path.join(self.temp_dir, "metrics.json")
        self.collector.export_to_json(json_file)

        # Verify JSON file
        with open(json_file, "r") as f:
            data = json.load(f)

        self.assertEqual(len(data["metrics"]), 3)
        self.assertIn("exported_at", data)

    def test_cleanup_old_metrics(self):
        """Test cleaning up old metrics."""
        now = datetime.utcnow()

        # Add old and recent metrics
        for i in range(100, 0, -10):  # 100, 90, 80, ... 10 days ago
            metric = CIMetric(
                timestamp=now - timedelta(days=i),
                workflow_name="Old",
                job_name="job",
                status="success",
                duration_seconds=60,
            )
            self.collector.collect_metric(metric)

        # Count before cleanup
        metrics_before = self.collector.get_metrics_by_workflow("Old")

        # Cleanup metrics older than 30 days
        self.collector.cleanup_old_metrics(days=30)

        # Count after cleanup
        metrics_after = self.collector.get_metrics_by_workflow("Old")

        self.assertLess(len(metrics_after), len(metrics_before))
        # Should only have metrics from 30, 20, 10 days ago
        self.assertEqual(len(metrics_after), 3)

    def test_get_percentile_duration(self):
        """Test calculating percentile durations."""
        # Add metrics with known duration distribution
        durations = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for d in durations:
            metric = CIMetric(
                timestamp=datetime.utcnow(),
                workflow_name="Stats",
                job_name="job",
                status="success",
                duration_seconds=d,
            )
            self.collector.collect_metric(metric)

        p50 = self.collector.get_percentile_duration("Stats", 50)
        p90 = self.collector.get_percentile_duration("Stats", 90)

        self.assertAlmostEqual(p50, 55, places=0)  # Median
        self.assertAlmostEqual(p90, 91, places=0)  # 90th percentile

    def test_concurrent_access(self):
        """Test concurrent metric collection."""
        import threading

        def add_metrics(thread_id):
            for i in range(10):
                metric = CIMetric(
                    timestamp=datetime.utcnow(),
                    workflow_name=f"Thread{thread_id}",
                    job_name=f"job{i}",
                    status="success",
                    duration_seconds=60,
                )
                self.collector.collect_metric(metric)

        # Create and start threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=add_metrics, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify all metrics were collected
        total_metrics = 0
        for i in range(5):
            metrics = self.collector.get_metrics_by_workflow(f"Thread{i}")
            total_metrics += len(metrics)

        self.assertEqual(total_metrics, 50)  # 5 threads * 10 metrics each


if __name__ == "__main__":
    unittest.main()
