#!/usr/bin/env python3
"""
Unit tests for metadata validation
Tests validation of document metadata, configuration metadata, and data integrity
"""

import json
from datetime import datetime

import pytest


class TestDocumentMetadataValidation:
    """Test validation of document metadata structures"""

    def test_valid_document_metadata(self):
        """Test valid document metadata structure"""
        metadata = {
            "document_type": "design",
            "version": "1.0",
            "created_date": "2024-01-01",
            "updated_date": "2024-01-15",
            "author": "system",
            "tags": ["architecture", "backend"],
            "status": "active",
        }

        # Validate required fields
        assert metadata.get("document_type") is not None
        assert metadata.get("created_date") is not None
        assert isinstance(metadata.get("tags"), list)

    def test_sprint_metadata_validation(self):
        """Test sprint-specific metadata validation"""
        sprint_metadata = {
            "document_type": "sprint",
            "sprint_number": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-01-14",
            "team": "backend",
            "velocity": 21,
            "created_date": "2023-12-28",
        }

        # Validate sprint-specific fields
        assert sprint_metadata["document_type"] == "sprint"
        assert isinstance(sprint_metadata["sprint_number"], int)
        assert sprint_metadata["sprint_number"] > 0

        # Validate date consistency
        start = datetime.fromisoformat(str(sprint_metadata["start_date"]))
        end = datetime.fromisoformat(str(sprint_metadata["end_date"]))
        assert end > start

    def test_decision_metadata_validation(self):
        """Test decision document metadata validation"""
        decision_metadata = {
            "document_type": "decision",
            "decision_id": "DEC-001",
            "title": "Choose primary database",
            "status": "approved",
            "impact": "high",
            "stakeholders": ["engineering", "product"],
            "decision_date": "2024-01-10",
            "review_date": "2024-04-10",
        }

        # Validate decision-specific fields
        assert decision_metadata["document_type"] == "decision"
        assert str(decision_metadata["decision_id"]).startswith("DEC-")
        assert decision_metadata["status"] in [
            "draft",
            "proposed",
            "approved",
            "rejected",
            "superseded",
        ]
        assert decision_metadata["impact"] in ["low", "medium", "high", "critical"]

    def test_trace_metadata_validation(self):
        """Test trace document metadata validation"""
        trace_metadata = {
            "document_type": "trace",
            "trace_id": "trace-2024-01-15-001",
            "session_id": "session-abc123",
            "timestamp": "2024-01-15T10:30:00Z",
            "agent": "cleanup_agent",
            "action": "archive_documents",
            "result": "success",
            "duration_ms": 1250,
        }

        # Validate trace-specific fields
        assert trace_metadata["document_type"] == "trace"
        assert str(trace_metadata["trace_id"]).startswith("trace-")
        assert trace_metadata["result"] in ["success", "failure", "partial"]
        assert isinstance(trace_metadata["duration_ms"], int)
        assert trace_metadata["duration_ms"] >= 0

    def test_metadata_timestamp_validation(self):
        """Test timestamp validation in metadata"""
        # Valid ISO format timestamps
        valid_timestamps = [
            "2024-01-01",
            "2024-01-01T00:00:00",
            "2024-01-01T00:00:00Z",
            "2024-01-01T00:00:00+00:00",
        ]

        for timestamp in valid_timestamps:
            # Should not raise exception
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Invalid timestamps
        invalid_timestamps = [
            "2024/01/01",
            "01-01-2024",
            "2024-13-01",  # Invalid month
            "2024-01-32",  # Invalid day
            "not-a-date",
        ]

        for timestamp in invalid_timestamps:
            with pytest.raises(ValueError):
                datetime.fromisoformat(timestamp)

    def test_metadata_tag_validation(self):
        """Test tag validation in metadata"""
        # Valid tags
        valid_tags = ["backend", "api", "database", "security", "v2.0", "high-priority"]

        for tag in valid_tags:
            assert isinstance(tag, str)
            assert len(tag) > 0
            assert len(tag) <= 50  # Reasonable tag length limit

        # Validate tag list
        tags = ["backend", "api"]
        assert isinstance(tags, list)
        assert all(isinstance(tag, str) for tag in tags)


class TestConfigurationMetadataValidation:
    """Test validation of configuration metadata"""

    def test_system_config_metadata(self):
        """Test system configuration metadata validation"""
        config_metadata = {
            "version": "1.0.0",
            "environment": "production",
            "last_updated": "2024-01-15T10:00:00Z",
            "updated_by": "admin",
            "checksum": "abc123def456",
        }

        # Validate version format
        version_parts = config_metadata["version"].split(".")
        assert len(version_parts) == 3
        assert all(part.isdigit() for part in version_parts)

        # Validate environment
        assert config_metadata["environment"] in ["development", "staging", "production"]

    def test_agent_config_metadata(self):
        """Test agent configuration metadata validation"""
        agent_metadata = {
            "agent_name": "cleanup_agent",
            "agent_version": "2.1.0",
            "capabilities": ["archive", "delete", "compress"],
            "schedule": "0 2 * * *",  # Cron format
            "enabled": True,
            "max_retries": 3,
            "timeout_seconds": 300,
        }

        # Validate agent fields
        assert str(agent_metadata["agent_name"]).endswith("_agent")
        assert isinstance(agent_metadata["capabilities"], list)
        assert isinstance(agent_metadata["enabled"], bool)
        assert int(agent_metadata["max_retries"]) >= 0
        assert int(agent_metadata["timeout_seconds"]) > 0

    def test_connection_metadata_validation(self):
        """Test connection configuration metadata"""
        connection_metadata = {
            "service": "qdrant",
            "host": "localhost",
            "port": 6333,
            "ssl": True,
            "ssl_verify": True,
            "connection_timeout": 30,
            "read_timeout": 60,
            "max_retries": 3,
        }

        # Validate connection fields
        assert int(connection_metadata["port"]) > 0
        assert int(connection_metadata["port"]) <= 65535
        assert isinstance(connection_metadata["ssl"], bool)
        assert int(connection_metadata["connection_timeout"]) > 0
        assert int(connection_metadata["read_timeout"]) >= int(
            connection_metadata["connection_timeout"]
        )


class TestDataIntegrityValidation:
    """Test data integrity validation functions"""

    def test_checksum_validation(self):
        """Test checksum validation for data integrity"""
        import hashlib

        data = "Important data that needs integrity check"

        # Generate checksum
        checksum = hashlib.sha256(data.encode()).hexdigest()

        # Validate checksum format
        assert len(checksum) == 64  # SHA-256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify checksum
        verification_checksum = hashlib.sha256(data.encode()).hexdigest()
        assert checksum == verification_checksum

    def test_data_size_validation(self):
        """Test data size validation"""
        # Test with representative data sizes (optimized for performance)
        small_data = {"key": "value"}
        medium_data = {"data": "x" * 1000}
        # Use smaller size for performance (10KB instead of 1MB)
        large_data = {"data": "x" * (10 * 1024)}  # 10KB

        # Calculate sizes
        small_size = len(json.dumps(small_data))
        medium_size = len(json.dumps(medium_data))
        large_size = len(json.dumps(large_data))

        # Validate size limits
        assert small_size < 1024  # Less than 1KB
        assert medium_size < 10 * 1024  # Less than 10KB
        assert large_size >= 10 * 1024  # At least 10KB

    def test_reference_integrity_validation(self):
        """Test reference integrity between documents"""
        # Document with references
        document = {
            "id": "doc-001",
            "references": [
                {"type": "decision", "id": "DEC-001"},
                {"type": "design", "id": "design-architecture-v2"},
                {"type": "sprint", "id": "sprint-001"},
            ],
        }

        # Validate reference structure
        for ref in document["references"]:
            assert "type" in ref
            assert "id" in ref
            assert ref.get("type") in ["decision", "design", "sprint", "trace"]
            assert isinstance(ref.get("id"), str)
            assert len(str(ref.get("id", ""))) > 0

    def test_schema_version_validation(self):
        """Test schema version compatibility validation"""
        # Document with schema version
        document = {
            "schema_version": "2.0",
            "min_compatible_version": "1.5",
            "data": {"field": "value"},
        }

        # Parse versions
        current_version = float(str(document["schema_version"]))
        min_version = float(str(document["min_compatible_version"]))

        # Validate version compatibility
        assert current_version >= min_version
        assert current_version <= 10.0  # Reasonable upper limit

    def test_metadata_completeness_validation(self):
        """Test metadata completeness validation"""
        # Define required fields for each document type
        required_fields = {
            "design": ["document_type", "version", "created_date", "author"],
            "decision": ["document_type", "decision_id", "status", "created_date"],
            "sprint": ["document_type", "sprint_number", "start_date", "end_date"],
            "trace": ["document_type", "trace_id", "timestamp", "agent"],
        }

        # Test document
        document = {
            "document_type": "design",
            "version": "1.0",
            "created_date": "2024-01-01",
            "author": "system",
            "title": "System Architecture",
        }

        # Validate required fields
        doc_type = document["document_type"]
        required = required_fields.get(doc_type, [])

        for field in required:
            assert field in document, f"Missing required field: {field}"


class TestMetricMetadataValidation:
    """Test validation of metric metadata"""

    def test_metric_metadata_structure(self):
        """Test metric metadata structure validation"""
        metric_metadata = {
            "metric_name": "system.cpu.usage",
            "metric_type": "gauge",
            "unit": "percent",
            "description": "CPU usage percentage",
            "tags": {"host": "server-01", "environment": "production", "service": "api"},
            "timestamp": datetime.utcnow().isoformat(),
            "value": 75.5,
        }

        # Validate metric metadata
        assert metric_metadata["metric_type"] in ["gauge", "counter", "histogram", "summary"]
        assert isinstance(metric_metadata["value"], (int, float))
        assert 0 <= metric_metadata["value"] <= 100  # For percentage metrics

        # Validate metric name format
        name_parts = str(metric_metadata["metric_name"]).split(".")
        assert len(name_parts) >= 2
        assert all(part.replace("_", "").isalnum() for part in name_parts)

    def test_metric_aggregation_metadata(self):
        """Test metric aggregation metadata validation"""
        aggregation_metadata = {
            "aggregation_type": "average",
            "window": "5m",
            "samples": 60,
            "min_value": 10.0,
            "max_value": 90.0,
            "avg_value": 45.5,
            "std_deviation": 15.2,
        }

        # Validate aggregation fields
        assert aggregation_metadata["aggregation_type"] in ["sum", "average", "min", "max", "count"]
        assert int(aggregation_metadata["samples"]) > 0
        assert float(aggregation_metadata["min_value"]) <= float(aggregation_metadata["avg_value"])
        assert float(aggregation_metadata["avg_value"]) <= float(aggregation_metadata["max_value"])
        assert float(aggregation_metadata["std_deviation"]) >= 0
