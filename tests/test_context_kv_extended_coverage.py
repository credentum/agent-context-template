#!/usr/bin/env python3
"""Extended tests for context_kv.py to improve coverage to >75%"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import duckdb
import pytest
import redis
import yaml

from src.storage.context_kv import (
    CacheEntry,
    ContextKV,
    DuckDBAnalytics,
    MetricEvent,
    RedisConnector,
)


class TestRedisConnectorExtended:
    """Extended tests for RedisConnector to improve coverage"""

    def test_load_performance_config_file_not_found(self):
        """Test loading performance config when file doesn't exist"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            connector = RedisConnector()
            assert connector.perf_config == {}

    def test_load_performance_config_with_data(self):
        """Test loading performance config with actual data"""
        perf_data = {
            "kv_store": {"redis": {"connection_pool": {"max_size": 100}, "batch_size": 1000}}
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(perf_data))):
            with patch("yaml.safe_load", return_value=perf_data):
                connector = RedisConnector()
                assert connector.perf_config == perf_data["kv_store"]["redis"]

    def test_load_performance_config_empty_kv_store(self):
        """Test loading performance config with empty kv_store"""
        perf_data = {"kv_store": {}}

        with patch("builtins.open", mock_open(read_data=yaml.dump(perf_data))):
            with patch("yaml.safe_load", return_value=perf_data):
                connector = RedisConnector()
                assert connector.perf_config == {}

    @patch("redis.Redis")
    def test_connect_with_ssl(self, mock_redis_class):
        """Test Redis connection with SSL enabled"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        config = {
            "redis": {"host": "secure.redis.com", "port": 6380, "ssl": True, "password": "secret"}
        }

        connector = RedisConnector()
        connector.config = config
        connector.perf_config = {"connection_pool": {"max_size": 100}}

        result = connector.connect(password="secret")

        assert result is True
        assert connector.redis_client == mock_redis

        # Verify SSL was passed to connection
        call_kwargs = mock_redis_class.call_args[1]
        assert call_kwargs["ssl"] is True
        assert call_kwargs["password"] == "secret"

    @patch("redis.Redis")
    @patch("click.echo")
    def test_connect_failure(self, mock_echo, mock_redis_class):
        """Test Redis connection failure"""
        mock_redis_class.side_effect = redis.ConnectionError("Connection refused")

        connector = RedisConnector()
        result = connector.connect()

        assert result is False
        assert connector.redis_client is None
        mock_echo.assert_called()

    def test_disconnect_with_pipeline(self):
        """Test disconnect when pipeline exists"""
        connector = RedisConnector()

        # Mock Redis client and pipeline
        mock_client = Mock()
        mock_pipeline = Mock()
        connector.redis_client = mock_client
        connector.pipeline = mock_pipeline

        result = connector.disconnect()

        assert result is True
        assert connector.redis_client is None
        assert connector.pipeline is None
        mock_client.close.assert_called_once()

    @patch("click.echo")
    def test_disconnect_error(self, mock_echo):
        """Test disconnect with error"""
        connector = RedisConnector()

        # Mock Redis client that raises on close
        mock_client = Mock()
        mock_client.close.side_effect = Exception("Close failed")
        connector.redis_client = mock_client

        result = connector.disconnect()

        assert result is False
        mock_echo.assert_called()

    def test_start_pipeline(self):
        """Test starting a Redis pipeline"""
        connector = RedisConnector()

        # Mock Redis client
        mock_client = Mock()
        mock_pipeline = Mock()
        mock_client.pipeline.return_value = mock_pipeline
        connector.redis_client = mock_client

        connector.start_pipeline()

        assert connector.pipeline == mock_pipeline
        mock_client.pipeline.assert_called_once()

    def test_execute_pipeline_success(self):
        """Test executing pipeline successfully"""
        connector = RedisConnector()

        # Mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.execute.return_value = [True, True, True]
        connector.pipeline = mock_pipeline

        results = connector.execute_pipeline()

        assert results == [True, True, True]
        assert connector.pipeline is None
        mock_pipeline.execute.assert_called_once()

    @patch("click.echo")
    def test_execute_pipeline_error(self, mock_echo):
        """Test pipeline execution with error"""
        connector = RedisConnector()

        # Mock pipeline that raises
        mock_pipeline = Mock()
        mock_pipeline.execute.side_effect = redis.RedisError("Pipeline failed")
        connector.pipeline = mock_pipeline

        results = connector.execute_pipeline()

        assert results == []
        assert connector.pipeline is None
        mock_echo.assert_called()

    def test_execute_pipeline_no_pipeline(self):
        """Test executing pipeline when none exists"""
        connector = RedisConnector()
        connector.pipeline = None

        results = connector.execute_pipeline()

        assert results == []


class TestDuckDBAnalyticsExtended:
    """Extended tests for DuckDBAnalytics to improve coverage"""

    def test_connect_with_existing_db(self):
        """Test connecting to existing DuckDB database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "metrics.duckdb"

            # Create database first
            conn = duckdb.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.close()

            config = {"duckdb": {"path": str(db_path)}}

            metrics = DuckDBAnalytics()
            metrics.config = config

            result = metrics.connect()

            assert result is True
            assert metrics.conn is not None

            # Verify table creation was attempted
            tables = metrics.conn.execute("SHOW TABLES").fetchall()
            assert len(tables) >= 1

    @patch("duckdb.connect")
    @patch("click.echo")
    def test_connect_failure(self, mock_echo, mock_connect):
        """Test DuckDB connection failure"""
        mock_connect.side_effect = Exception("Connection failed")

        metrics = DuckDBAnalytics()
        result = metrics.connect()

        assert result is False
        assert metrics.conn is None
        mock_echo.assert_called()

    def test_insert_metric_success(self):
        """Test inserting metric successfully"""
        metrics = DuckDBAnalytics()

        # Mock connection
        mock_conn = Mock()
        mock_conn.execute.return_value = Mock()
        metrics.conn = mock_conn

        event = MetricEvent(
            timestamp=datetime.now(),
            metric_name="test_metric",
            value=42.0,
            tags={"env": "test"},
            document_id="doc123",
            agent_id="agent456",
        )

        result = metrics.insert_metric(event)

        assert result is True
        mock_conn.execute.assert_called_once()

        # Verify SQL contains expected values
        sql_call = mock_conn.execute.call_args[0][0]
        assert "INSERT INTO metrics" in sql_call
        assert "test_metric" in str(mock_conn.execute.call_args)

    @patch("click.echo")
    def test_insert_metric_error(self, mock_echo):
        """Test inserting metric with error"""
        metrics = DuckDBAnalytics()

        # Mock connection that raises
        mock_conn = Mock()
        mock_conn.execute.side_effect = Exception("Insert failed")
        metrics.conn = mock_conn

        event = MetricEvent(
            timestamp=datetime.now(), metric_name="test_metric", value=42.0, tags={}
        )

        result = metrics.insert_metric(event)

        assert result is False
        mock_echo.assert_called()

    def test_query_time_range_success(self):
        """Test querying metrics by time range"""
        metrics = DuckDBAnalytics()

        # Mock connection and results
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (datetime.now(), "metric1", 10.0, {}, "doc1", "agent1"),
            (datetime.now(), "metric2", 20.0, {}, "doc2", "agent2"),
        ]
        mock_conn.execute.return_value = mock_result
        metrics.conn = mock_conn

        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()

        results = metrics.query_time_range(start, end, metric_name="metric1")

        assert len(results) == 2
        assert all(isinstance(r, MetricEvent) for r in results)

        # Verify query includes metric_name filter
        sql_call = mock_conn.execute.call_args[0][0]
        assert "WHERE timestamp BETWEEN" in sql_call
        assert "AND metric_name =" in sql_call

    def test_query_time_range_no_metric_filter(self):
        """Test querying metrics without metric name filter"""
        metrics = DuckDBAnalytics()

        # Mock connection
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        metrics.conn = mock_conn

        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()

        results = metrics.query_time_range(start, end)

        assert results == []

        # Verify query doesn't include metric_name filter
        sql_call = mock_conn.execute.call_args[0][0]
        assert "AND metric_name =" not in sql_call

    @patch("click.echo")
    def test_query_time_range_error(self, mock_echo):
        """Test query error handling"""
        metrics = DuckDBAnalytics()

        # Mock connection that raises
        mock_conn = Mock()
        mock_conn.execute.side_effect = Exception("Query failed")
        metrics.conn = mock_conn

        results = metrics.query_time_range(datetime.now(), datetime.now())

        assert results == []
        mock_echo.assert_called()

    def test_get_aggregates_success(self):
        """Test getting metric aggregates"""
        metrics = DuckDBAnalytics()

        # Mock connection and results
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [("metric1", 5, 10.0, 50.0, 100.0, 25.0)]
        mock_conn.execute.return_value = mock_result
        metrics.conn = mock_conn

        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()

        results = metrics.get_aggregates(start, end, group_by="metric_name")

        assert len(results) == 1
        assert results[0]["metric_name"] == "metric1"
        assert results[0]["count"] == 5
        assert results[0]["min_value"] == 10.0

    @patch("click.echo")
    def test_get_aggregates_error(self, mock_echo):
        """Test aggregate query error"""
        metrics = DuckDBAnalytics()

        # Mock connection that raises
        mock_conn = Mock()
        mock_conn.execute.side_effect = Exception("Aggregate failed")
        metrics.conn = mock_conn

        results = metrics.get_aggregates(datetime.now(), datetime.now())

        assert results == []
        mock_echo.assert_called()


class TestContextKVExtended:
    """Extended tests for ContextKV to improve coverage"""

    @patch("src.storage.context_kv.RedisConnector")
    @patch("src.storage.context_kv.DuckDBAnalytics")
    def test_init_with_components(self, mock_duckdb_class, mock_redis_class):
        """Test ContextKV initialization"""
        mock_redis = Mock()
        mock_duckdb = Mock()
        mock_redis_class.return_value = mock_redis
        mock_duckdb_class.return_value = mock_duckdb

        kv = ContextKV(verbose=True)

        assert kv.redis == mock_redis
        assert kv.duckdb == mock_duckdb
        assert kv.verbose is True

    def test_connect_all_success(self):
        """Test connecting all components successfully"""
        kv = ContextKV()

        # Mock components
        kv.redis = Mock()
        kv.redis.connect.return_value = True
        kv.duckdb = Mock()
        kv.duckdb.connect.return_value = True

        result = kv.connect(**{"password": "test"})

        assert result is True
        kv.redis.connect.assert_called_once_with(password="test")
        kv.duckdb.connect.assert_called_once()

    def test_connect_redis_failure(self):
        """Test connection when Redis fails"""
        kv = ContextKV()

        # Mock components
        kv.redis = Mock()
        kv.redis.connect.return_value = False
        kv.duckdb = Mock()

        result = kv.connect()

        assert result is False
        kv.duckdb.connect.assert_not_called()

    def test_cache_get_success(self):
        """Test getting value from cache"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.get.return_value = json.dumps(
            {
                "key": "test_key",
                "value": {"data": "test"},
                "created_at": datetime.now().isoformat(),
                "ttl_seconds": 3600,
                "hit_count": 5,
                "last_accessed": datetime.now().isoformat(),
            }
        ).encode()
        mock_client.hincrby.return_value = 6

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        value = kv.cache_get("test_key")

        assert value == {"data": "test"}
        mock_client.get.assert_called_once_with("cache:test_key")
        mock_client.hincrby.assert_called_once()

    def test_cache_get_not_found(self):
        """Test getting non-existent value from cache"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.get.return_value = None

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        value = kv.cache_get("missing_key")

        assert value is None

    @patch("click.echo")
    def test_cache_get_error(self, mock_echo):
        """Test cache get with error"""
        kv = ContextKV(verbose=True)

        # Mock Redis client that raises
        mock_client = Mock()
        mock_client.get.side_effect = redis.RedisError("Get failed")

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        value = kv.cache_get("test_key")

        assert value is None
        mock_echo.assert_called()

    def test_cache_set_success(self):
        """Test setting value in cache"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.setex.return_value = True

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        result = kv.cache_set("test_key", {"data": "test"}, ttl_seconds=3600)

        assert result is True
        mock_client.setex.assert_called_once()

        # Verify the cache entry structure
        call_args = mock_client.setex.call_args
        assert call_args[0][0] == "cache:test_key"
        assert call_args[0][1] == 3600

    @patch("click.echo")
    def test_cache_set_error(self, mock_echo):
        """Test cache set with error"""
        kv = ContextKV(verbose=True)

        # Mock Redis client that raises
        mock_client = Mock()
        mock_client.setex.side_effect = redis.RedisError("Set failed")

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        result = kv.cache_set("test_key", {"data": "test"})

        assert result is False
        mock_echo.assert_called()

    def test_session_create_success(self):
        """Test creating a session"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.hset.return_value = 1
        mock_client.expire.return_value = True

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        session_id = kv.session_create({"user": "test"}, ttl_seconds=7200)

        assert session_id is not None
        assert len(session_id) == 64  # SHA-256 hex length
        assert mock_client.hset.call_count == 3  # data, created_at, last_accessed
        mock_client.expire.assert_called_once()

    def test_session_get_success(self):
        """Test getting session data"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.hgetall.return_value = {
            b"data": json.dumps({"user": "test"}).encode(),
            b"created_at": datetime.now().isoformat().encode(),
            b"last_accessed": datetime.now().isoformat().encode(),
        }
        mock_client.hset.return_value = 1

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        data = kv.session_get("session123")

        assert data == {"user": "test"}
        mock_client.hgetall.assert_called_once_with("session:session123")
        mock_client.hset.assert_called_once()  # Update last_accessed

    def test_session_get_not_found(self):
        """Test getting non-existent session"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.hgetall.return_value = {}

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        data = kv.session_get("missing_session")

        assert data is None

    def test_session_delete_success(self):
        """Test deleting a session"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_client.delete.return_value = 1

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        result = kv.session_delete("session123")

        assert result is True
        mock_client.delete.assert_called_once_with("session:session123")

    def test_record_metric_success(self):
        """Test recording a metric"""
        kv = ContextKV()

        # Mock DuckDB
        kv.duckdb = Mock()
        kv.duckdb.insert_metric.return_value = True

        result = kv.record_metric(metric_name="test_metric", value=42.0, tags={"env": "test"})

        assert result is True
        kv.duckdb.insert_metric.assert_called_once()

        # Verify MetricEvent was created correctly
        call_args = kv.duckdb.insert_metric.call_args[0][0]
        assert isinstance(call_args, MetricEvent)
        assert call_args.metric_name == "test_metric"
        assert call_args.value == 42.0

    def test_query_metrics_success(self):
        """Test querying metrics"""
        kv = ContextKV()

        # Mock DuckDB
        mock_events = [
            MetricEvent(timestamp=datetime.now(), metric_name="test_metric", value=42.0, tags={})
        ]
        kv.duckdb = Mock()
        kv.duckdb.query_time_range.return_value = mock_events

        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()

        results = kv.query_metrics(start, end, metric_name="test_metric")

        assert results == mock_events
        kv.duckdb.query_time_range.assert_called_once_with(start, end, "test_metric")

    def test_batch_record_metrics_success(self):
        """Test batch recording metrics"""
        kv = ContextKV()

        # Mock Redis with pipeline
        mock_pipeline = Mock()
        kv.redis = Mock()
        kv.redis.redis_client = Mock()
        kv.redis.pipeline = None

        # Mock DuckDB
        kv.duckdb = Mock()
        kv.duckdb.conn = Mock()

        events = [
            MetricEvent(
                timestamp=datetime.now(),
                metric_name=f"metric_{i}",
                value=float(i),
                tags={"batch": "test"},
            )
            for i in range(5)
        ]

        kv.batch_record_metrics(events)

        # Verify batch insert was attempted
        assert kv.duckdb.conn.executemany.called

    @patch("click.echo")
    def test_batch_record_metrics_error(self, mock_echo):
        """Test batch recording with error"""
        kv = ContextKV(verbose=True)

        # Mock DuckDB that raises
        kv.duckdb = Mock()
        kv.duckdb.conn = Mock()
        kv.duckdb.conn.executemany.side_effect = Exception("Batch failed")

        events = [MetricEvent(timestamp=datetime.now(), metric_name="test", value=1.0, tags={})]

        kv.batch_record_metrics(events)

        mock_echo.assert_called()

    def test_cache_stats_success(self):
        """Test getting cache statistics"""
        kv = ContextKV()

        # Mock Redis client with info
        mock_client = Mock()
        mock_client.info.return_value = {
            "used_memory_human": "10M",
            "connected_clients": 5,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200,
        }
        mock_client.dbsize.return_value = 50

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        stats = kv.cache_stats()

        assert stats["memory_usage"] == "10M"
        assert stats["total_keys"] == 50
        assert stats["hit_rate"] == 0.8

    def test_cleanup_expired_sessions_success(self):
        """Test cleaning up expired sessions"""
        kv = ContextKV()

        # Mock Redis client
        mock_client = Mock()
        mock_cursor = Mock()

        # Simulate SCAN returning session keys
        mock_client.scan.side_effect = [
            (100, [b"session:old1", b"session:old2"]),
            (0, [b"session:old3"]),
        ]

        # Mock TTL checks - negative means expired
        mock_client.ttl.side_effect = [-1, -1, -1]
        mock_client.delete.return_value = 1

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        count = kv.cleanup_expired_sessions()

        assert count == 3
        assert mock_client.delete.call_count == 3

    @patch("click.echo")
    def test_cleanup_expired_sessions_error(self, mock_echo):
        """Test cleanup with error"""
        kv = ContextKV(verbose=True)

        # Mock Redis client that raises
        mock_client = Mock()
        mock_client.scan.side_effect = redis.RedisError("Scan failed")

        kv.redis = Mock()
        kv.redis.redis_client = mock_client

        count = kv.cleanup_expired_sessions()

        assert count == 0
        mock_echo.assert_called()


class TestCLICommands:
    """Test CLI commands"""

    @patch("src.storage.context_kv.ContextKV")
    def test_cli_test_connection(self, mock_kv_class):
        """Test CLI connection test command"""
        from click.testing import CliRunner

        from src.storage.context_kv import main

        mock_kv = Mock()
        mock_kv.connect.return_value = True
        mock_kv_class.return_value = mock_kv

        runner = CliRunner()
        result = runner.invoke(main, ["test-connection"])

        assert result.exit_code == 0
        assert "✓ Redis connection successful" in result.output
        assert "✓ DuckDB connection successful" in result.output

    @patch("src.storage.context_kv.ContextKV")
    def test_cli_cache_operations(self, mock_kv_class):
        """Test CLI cache operations"""
        from click.testing import CliRunner

        from src.storage.context_kv import main

        mock_kv = Mock()
        mock_kv.connect.return_value = True
        mock_kv.cache_set.return_value = True
        mock_kv.cache_get.return_value = {"test": "data"}
        mock_kv_class.return_value = mock_kv

        runner = CliRunner()

        # Test cache set
        result = runner.invoke(main, ["cache-demo"])
        assert result.exit_code == 0
        assert "Cache Operations" in result.output

    @patch("src.storage.context_kv.ContextKV")
    def test_cli_metrics_demo(self, mock_kv_class):
        """Test CLI metrics demo"""
        from click.testing import CliRunner

        from src.storage.context_kv import main

        mock_kv = Mock()
        mock_kv.connect.return_value = True
        mock_kv.record_metric.return_value = True
        mock_kv.query_metrics.return_value = []
        mock_kv.duckdb = Mock()
        mock_kv.duckdb.get_aggregates.return_value = []
        mock_kv_class.return_value = mock_kv

        runner = CliRunner()
        result = runner.invoke(main, ["metrics-demo"])

        assert result.exit_code == 0
        assert "Metrics Operations" in result.output
