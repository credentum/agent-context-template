"""Reproducibility tests via trace/hash for audit checkpoints

This module ensures that system state can be reproduced from hashes,
enabling reliable auditing and debugging.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import hashlib
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import shutil

from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.storage.graph_builder import GraphBuilder
from src.storage.context_kv import ContextKV, RedisConnector


class TestReproducibility:
    """Test cases for system reproducibility via hashes"""

    @pytest.fixture
    def test_data_dir(self, tmp_path):
        """Create test data directory with sample documents"""
        data_dir = tmp_path / "test_data"
        data_dir.mkdir()

        # Create sample documents
        docs = {
            "sprint-001.yaml": {
                "schema_version": "1.1.0",
                "document_type": "sprint",
                "id": "sprint-001",
                "title": "Initial Sprint",
                "created_date": "2024-01-01",
                "content": "Sprint planning details",
            },
            "decision-001.yaml": {
                "schema_version": "1.1.0",
                "document_type": "decision",
                "id": "decision-001",
                "title": "Architecture Decision",
                "created_date": "2024-01-02",
                "rationale": "Decision reasoning",
            },
        }

        for filename, content in docs.items():
            (data_dir / filename).write_text(yaml.dump(content))

        return data_dir

    @pytest.fixture
    def hash_embedder(self, tmp_path):
        """Create HashDiffEmbedder instance"""
        config = {
            "embeddings": {
                "provider": "openai",
                "model": "text-embedding-ada-002",
                "dimension": 1536,
            }
        }
        config_path = tmp_path / ".ctxrc.yaml"
        config_path.write_text(yaml.dump(config))

        embedder = HashDiffEmbedder(config_path=str(config_path))
        return embedder

    def test_document_hash_deterministic(self, test_data_dir):
        """Test that document hashes are deterministic"""
        doc_path = test_data_dir / "sprint-001.yaml"

        # Calculate hash multiple times
        hashes = []
        for _ in range(3):
            with open(doc_path) as f:
                content = yaml.safe_load(f)

            # Sort keys for deterministic hashing
            content_str = json.dumps(content, sort_keys=True)
            hash_value = hashlib.sha256(content_str.encode()).hexdigest()
            hashes.append(hash_value)

        # All hashes should be identical
        assert len(set(hashes)) == 1
        assert all(h == hashes[0] for h in hashes)

    def test_state_snapshot_creation(self, test_data_dir, tmp_path):
        """Test creating a reproducible state snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "documents": {},
            "metadata": {"total_documents": 0, "document_types": {}},
        }

        # Process all documents
        for doc_file in test_data_dir.glob("*.yaml"):
            with open(doc_file) as f:
                content = yaml.safe_load(f)

            # Calculate hash
            content_str = json.dumps(content, sort_keys=True)
            doc_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Store in snapshot
            snapshot["documents"][str(doc_file.name)] = {
                "hash": doc_hash,
                "type": content.get("document_type", "unknown"),
                "id": content.get("id", "unknown"),
            }

            # Update metadata
            snapshot["metadata"]["total_documents"] += 1
            doc_type = content.get("document_type", "unknown")
            snapshot["metadata"]["document_types"][doc_type] = (
                snapshot["metadata"]["document_types"].get(doc_type, 0) + 1
            )

        # Save snapshot
        snapshot_path = tmp_path / "snapshot.json"
        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        # Verify snapshot
        assert snapshot["metadata"]["total_documents"] == 2
        assert "sprint" in snapshot["metadata"]["document_types"]
        assert "decision" in snapshot["metadata"]["document_types"]

    def test_state_reproduction_from_snapshot(self, test_data_dir, tmp_path):
        """Test reproducing system state from a snapshot"""
        # Create initial snapshot
        snapshot = self._create_snapshot(test_data_dir)

        # Modify a document
        doc_path = test_data_dir / "sprint-001.yaml"
        with open(doc_path) as f:
            content = yaml.safe_load(f)
        content["title"] = "Modified Sprint"
        with open(doc_path, "w") as f:
            yaml.dump(content, f)

        # Verify document was changed
        new_hash = self._calculate_file_hash(doc_path)
        assert new_hash != snapshot["documents"]["sprint-001.yaml"]["hash"]

        # Restore from snapshot
        self._restore_from_snapshot(snapshot, test_data_dir)

        # Verify restoration
        restored_hash = self._calculate_file_hash(doc_path)
        assert restored_hash == snapshot["documents"]["sprint-001.yaml"]["hash"]

    def test_incremental_hash_tracking(self, hash_embedder, test_data_dir):
        """Test incremental hash tracking for changes"""
        history = []

        # Initial state
        doc_path = test_data_dir / "sprint-001.yaml"
        initial_hash = self._calculate_file_hash(doc_path)
        history.append(
            {"timestamp": datetime.now().isoformat(), "hash": initial_hash, "operation": "initial"}
        )

        # Make changes
        for i in range(3):
            with open(doc_path) as f:
                content = yaml.safe_load(f)

            content[f"iteration_{i}"] = f"change_{i}"

            with open(doc_path, "w") as f:
                yaml.dump(content, f)

            new_hash = self._calculate_file_hash(doc_path)
            history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "hash": new_hash,
                    "operation": f"update_{i}",
                    "parent_hash": history[-1]["hash"],
                }
            )

        # Verify hash chain
        assert len(history) == 4
        assert all(h["hash"] != history[0]["hash"] for h in history[1:])

        # Each hash should have correct parent
        for i in range(1, len(history)):
            assert history[i].get("parent_hash") == history[i - 1]["hash"]

    def test_graph_state_reproducibility(self, tmp_path):
        """Test reproducing graph database state"""
        # Mock graph data
        graph_snapshot = {
            "nodes": [
                {
                    "id": "sprint-001",
                    "labels": ["Sprint", "Document"],
                    "properties": {"title": "Sprint 1"},
                },
                {
                    "id": "decision-001",
                    "labels": ["Decision", "Document"],
                    "properties": {"title": "Decision 1"},
                },
            ],
            "relationships": [{"start": "sprint-001", "end": "decision-001", "type": "REFERENCES"}],
            "metadata": {"node_count": 2, "relationship_count": 1, "snapshot_hash": ""},
        }

        # Calculate snapshot hash
        snapshot_str = json.dumps(graph_snapshot, sort_keys=True)
        graph_snapshot["metadata"]["snapshot_hash"] = hashlib.sha256(
            snapshot_str.encode()
        ).hexdigest()

        # Save snapshot
        snapshot_path = tmp_path / "graph_snapshot.json"
        with open(snapshot_path, "w") as f:
            json.dump(graph_snapshot, f, indent=2)

        # Verify reproducibility
        with open(snapshot_path) as f:
            loaded_snapshot = json.load(f)

        # Recalculate hash
        loaded_snapshot["metadata"]["snapshot_hash"] = ""
        recalc_str = json.dumps(loaded_snapshot, sort_keys=True)
        recalc_hash = hashlib.sha256(recalc_str.encode()).hexdigest()

        assert recalc_hash == graph_snapshot["metadata"]["snapshot_hash"]

    def test_kv_store_state_backup_restore(self):
        """Test KV store state backup and restoration"""
        with patch("redis.Redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client

            # Create KV store
            connector = RedisConnector()
            connector.client = mock_client
            kv_store = ContextKV(connector)

            # Mock data
            test_data = {
                "session:123": {"user": "test", "data": "value1"},
                "config:app": {"setting": "value2"},
                "cache:result": {"result": "value3"},
            }

            # Create backup
            backup = {}
            for key, value in test_data.items():
                mock_client.get.return_value = json.dumps(value)
                mock_client.ttl.return_value = 3600

                backup[key] = {
                    "value": value,
                    "ttl": 3600,
                    "hash": hashlib.sha256(json.dumps(value).encode()).hexdigest(),
                }

            # Simulate data loss
            mock_client.flushdb()

            # Restore from backup
            for key, data in backup.items():
                kv_store.set(key, data["value"], ttl=data["ttl"])

            # Verify restoration
            assert mock_client.setex.call_count == len(test_data)

    def test_audit_checkpoint_creation(self, test_data_dir, tmp_path):
        """Test creating audit checkpoints with hashes"""
        checkpoint = {
            "id": "checkpoint-001",
            "timestamp": datetime.now().isoformat(),
            "system_state": {"documents": {}, "configuration": {}, "metrics": {}},
            "verification": {"hash_algorithm": "sha256", "total_hash": ""},
        }

        # Collect document hashes
        for doc_file in test_data_dir.glob("*.yaml"):
            doc_hash = self._calculate_file_hash(doc_file)
            checkpoint["system_state"]["documents"][doc_file.name] = doc_hash

        # Add configuration hash
        config_data = {"version": "1.0", "settings": {"debug": False}}
        config_hash = hashlib.sha256(json.dumps(config_data).encode()).hexdigest()
        checkpoint["system_state"]["configuration"]["config"] = config_hash

        # Add metrics
        metrics_data = {"processed": 100, "errors": 0}
        metrics_hash = hashlib.sha256(json.dumps(metrics_data).encode()).hexdigest()
        checkpoint["system_state"]["metrics"]["performance"] = metrics_hash

        # Calculate total hash
        state_str = json.dumps(checkpoint["system_state"], sort_keys=True)
        checkpoint["verification"]["total_hash"] = hashlib.sha256(state_str.encode()).hexdigest()

        # Save checkpoint
        checkpoint_path = tmp_path / "audit_checkpoint.json"
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint, f, indent=2)

        # Verify checkpoint can be validated
        assert self._validate_checkpoint(checkpoint)

    def test_diff_based_reproduction(self, test_data_dir):
        """Test reproducing state using diffs"""
        # Initial state
        doc_path = test_data_dir / "sprint-001.yaml"
        with open(doc_path) as f:
            initial_content = yaml.safe_load(f)

        # Create diff history
        diffs = []
        current_content = initial_content.copy()

        # Apply changes
        changes = [
            {"op": "add", "path": "status", "value": "active"},
            {"op": "update", "path": "title", "value": "Updated Sprint"},
            {"op": "add", "path": "progress", "value": 50},
        ]

        for change in changes:
            old_hash = hashlib.sha256(
                json.dumps(current_content, sort_keys=True).encode()
            ).hexdigest()

            # Apply change
            if change["op"] == "add" or change["op"] == "update":
                current_content[change["path"]] = change["value"]

            new_hash = hashlib.sha256(
                json.dumps(current_content, sort_keys=True).encode()
            ).hexdigest()

            diffs.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "old_hash": old_hash,
                    "new_hash": new_hash,
                    "change": change,
                }
            )

        # Reproduce state from initial + diffs
        reproduced_content = initial_content.copy()
        for diff in diffs:
            change = diff["change"]
            if change["op"] in ["add", "update"]:
                reproduced_content[change["path"]] = change["value"]

        # Verify reproduction
        assert reproduced_content == current_content

        # Verify final hash
        final_hash = hashlib.sha256(
            json.dumps(reproduced_content, sort_keys=True).encode()
        ).hexdigest()
        assert final_hash == diffs[-1]["new_hash"]

    # Helper methods
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file's content"""
        with open(file_path) as f:
            content = yaml.safe_load(f)
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _create_snapshot(self, data_dir: Path) -> Dict[str, Any]:
        """Create a snapshot of the data directory"""
        snapshot = {"timestamp": datetime.now().isoformat(), "documents": {}}

        for doc_file in data_dir.glob("*.yaml"):
            with open(doc_file) as f:
                content = yaml.safe_load(f)

            snapshot["documents"][doc_file.name] = {
                "hash": self._calculate_file_hash(doc_file),
                "content": content,
            }

        return snapshot

    def _restore_from_snapshot(self, snapshot: Dict[str, Any], data_dir: Path):
        """Restore data directory from snapshot"""
        for filename, data in snapshot["documents"].items():
            file_path = data_dir / filename
            with open(file_path, "w") as f:
                yaml.dump(data["content"], f)

    def _validate_checkpoint(self, checkpoint: Dict[str, Any]) -> bool:
        """Validate an audit checkpoint"""
        # Recalculate total hash
        state_str = json.dumps(checkpoint["system_state"], sort_keys=True)
        calculated_hash = hashlib.sha256(state_str.encode()).hexdigest()

        return calculated_hash == checkpoint["verification"]["total_hash"]

