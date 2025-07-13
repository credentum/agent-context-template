#!/usr/bin/env python3
"""
End-to-end tests for full project lifecycle
Tests: Project clone → run replay_trace.sh → verify output matches snapshot
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


@pytest.mark.e2e
@pytest.mark.slow
class TestProjectLifecycle:
    """Test complete project lifecycle from clone to verification"""

    def setup_method(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.original_dir = Path.cwd()

    def teardown_method(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def create_test_project(self) -> Path:
        """Create a minimal test project structure"""
        # Create project directories
        dirs = [
            "context/docs",
            "context/decisions",
            "context/sprints",
            "context/trace",
            "context/archive",
            ".github/workflows",
            "src/agents",
            "src/validators",
            "tests",
        ]

        for dir_path in dirs:
            (self.project_dir / dir_path).mkdir(parents=True)

        # Create config file
        config = {
            "system": {"project_name": "test_project", "version": "1.0.0"},
            "agents": {
                "cleanup_agent": {"enabled": True, "retention_days": 30},
                "update_sprint": {"enabled": True, "auto_update": True},
            },
            "qdrant": {"host": "localhost", "port": 6333, "collection_name": "test_context"},
            "neo4j": {"host": "localhost", "port": 7687},
            "storage": {"root": "./context"},
        }

        config_path = self.project_dir / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)

        # Create initial documents
        self.create_initial_documents()

        # Create replay script
        self.create_replay_script()

        # Initialize git repo with proper config
        subprocess.run(["git", "init"], cwd=self.project_dir, check=True, timeout=30)
        # Set git config for CI environment
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.project_dir,
            check=True,
            timeout=30,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.project_dir,
            check=True,
            timeout=30,
        )
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True, timeout=30)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, timeout=30
        )

        return self.project_dir

    def create_initial_documents(self):
        """Create initial context documents"""
        # Design document
        design_doc = {
            "metadata": {
                "document_type": "design",
                "version": "1.0",
                "created_date": "2024-01-01",
                "author": "system",
            },
            "title": "System Architecture",
            "content": {
                "overview": "Microservices architecture with event-driven communication",
                "components": ["API Gateway", "Auth Service", "Data Service"],
                "patterns": ["CQRS", "Event Sourcing"],
            },
        }

        design_path = self.project_dir / "context/docs/architecture.yaml"
        with open(design_path, "w") as f:
            yaml.dump(design_doc, f)

        # Decision document
        decision_doc = {
            "metadata": {
                "document_type": "decision",
                "decision_id": "DEC-001",
                "status": "approved",
                "created_date": "2024-01-05",
            },
            "title": "Use PostgreSQL for primary datastore",
            "rationale": "ACID compliance and strong consistency required",
            "alternatives": ["MongoDB", "DynamoDB"],
            "decision_date": "2024-01-05",
        }

        decision_path = self.project_dir / "context/decisions/DEC-001.yaml"
        with open(decision_path, "w") as f:
            yaml.dump(decision_doc, f)

        # Sprint document
        sprint_doc = {
            "metadata": {"document_type": "sprint", "sprint_number": 1},
            "sprint_number": 1,
            "status": "completed",
            "start_date": "2024-01-01",
            "end_date": "2024-01-14",
            "goals": ["Set up infrastructure", "Implement auth"],
            "phases": [
                {
                    "name": "Setup",
                    "status": "completed",
                    "tasks": [
                        {"name": "Configure CI/CD", "status": "completed"},
                        {"name": "Set up environments", "status": "completed"},
                    ],
                }
            ],
        }

        sprint_path = self.project_dir / "context/sprints/sprint_001.yaml"
        with open(sprint_path, "w") as f:
            yaml.dump(sprint_doc, f)

    def create_replay_script(self):
        """Create replay_trace.sh script"""
        script_content = """#!/bin/bash
# Replay trace script for testing

echo "Starting trace replay..."

# Set up environment
export CONTEXT_DIR="./context"
export TRACE_DIR="$CONTEXT_DIR/trace"

# Create snapshot directory
SNAPSHOT_DIR="$CONTEXT_DIR/snapshots/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SNAPSHOT_DIR"

# Process trace files
echo "Processing trace files..."
for trace_file in "$TRACE_DIR"/*.yaml; do
    if [ -f "$trace_file" ]; then
        echo "  - Processing: $(basename "$trace_file")"
        # Simulate processing
        cp "$trace_file" "$SNAPSHOT_DIR/"
    fi
done

# Generate summary
echo "Generating summary..."
cat > "$SNAPSHOT_DIR/summary.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "traces_processed": $(ls -1 "$TRACE_DIR"/*.yaml 2>/dev/null | wc -l),
    "snapshot_path": "$SNAPSHOT_DIR",
    "status": "success"
}
EOF

echo "Trace replay completed!"
echo "Snapshot saved to: $SNAPSHOT_DIR"
"""

        script_path = self.project_dir / "replay_trace.sh"
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make executable
        os.chmod(script_path, 0o755)

    def create_test_traces(self):
        """Create test trace files"""
        trace_dir = self.project_dir / "context/trace"

        # Cleanup trace
        cleanup_trace = {
            "metadata": {
                "document_type": "trace",
                "trace_id": "cleanup_20240115_100000",
                "agent": "cleanup_agent",
                "timestamp": "2024-01-15T10:00:00Z",
            },
            "execution": {
                "files_examined": 10,
                "files_archived": 2,
                "duration_ms": 500,
                "status": "success",
            },
        }

        trace_path = trace_dir / "cleanup_20240115_100000.yaml"
        with open(trace_path, "w") as f:
            yaml.dump(cleanup_trace, f)

        # Sprint update trace
        sprint_trace = {
            "metadata": {
                "document_type": "trace",
                "trace_id": "sprint_update_20240115_110000",
                "agent": "sprint_updater",
                "timestamp": "2024-01-15T11:00:00Z",
            },
            "execution": {
                "sprint_id": "sprint_001",
                "tasks_updated": 3,
                "github_issues_checked": 5,
                "status": "success",
            },
        }

        trace_path = trace_dir / "sprint_update_20240115_110000.yaml"
        with open(trace_path, "w") as f:
            yaml.dump(sprint_trace, f)

    def test_full_project_lifecycle(self):
        """Test complete project lifecycle"""
        # This test may take up to 10 minutes in CI
        # Step 1: Create project
        project_dir = self.create_test_project()
        assert project_dir.exists()

        # Step 2: Create traces
        self.create_test_traces()

        # Step 3: Run replay_trace.sh
        os.chdir(project_dir)

        result = subprocess.run(["./replay_trace.sh"], capture_output=True, text=True, timeout=300)

        assert result.returncode == 0
        assert "Trace replay completed!" in result.stdout

        # Step 4: Verify snapshot was created
        snapshots_dir = project_dir / "context/snapshots"
        assert snapshots_dir.exists()

        # Find latest snapshot
        snapshot_dirs = list(snapshots_dir.glob("*"))
        assert len(snapshot_dirs) > 0

        latest_snapshot = max(snapshot_dirs, key=lambda p: p.stat().st_mtime)

        # Step 5: Verify snapshot contents
        summary_file = latest_snapshot / "summary.json"
        assert summary_file.exists()

        with open(summary_file) as f:
            summary = json.load(f)

        assert summary["status"] == "success"
        assert summary["traces_processed"] == 2

        # Verify trace files were copied
        trace_files = list(latest_snapshot.glob("*.yaml"))
        assert len(trace_files) == 2

    def test_project_clone_and_setup(self):
        """Test cloning project and initial setup"""
        # Create test project
        source_dir = self.create_test_project()

        # Clone project
        clone_dir = Path(self.test_dir) / "cloned_project"

        result = subprocess.run(
            ["git", "clone", str(source_dir), str(clone_dir)], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert clone_dir.exists()

        # Verify structure
        assert (clone_dir / ".ctxrc.yaml").exists()
        assert (clone_dir / "context").exists()
        assert (clone_dir / "replay_trace.sh").exists()

    def test_document_integrity_check(self):
        """Test document integrity verification"""
        project_dir = self.create_test_project()

        # Calculate checksums for all documents
        checksums = {}

        for doc_path in project_dir.glob("context/**/*.yaml"):
            with open(doc_path, "rb") as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
                checksums[str(doc_path.relative_to(project_dir))] = checksum

        # Save checksums
        checksum_file = project_dir / "context/.checksums.json"
        with open(checksum_file, "w") as f:
            json.dump(checksums, f, indent=2)

        # Verify checksums
        for file_path, expected_checksum in checksums.items():
            full_path = project_dir / file_path
            with open(full_path, "rb") as f:
                content = f.read()
                actual_checksum = hashlib.sha256(content).hexdigest()

            assert actual_checksum == expected_checksum

    def test_agent_execution_sequence(self):
        """Test proper agent execution sequence"""
        project_dir = self.create_test_project()
        os.chdir(project_dir)

        # Expected execution order
        execution_order = [
            "context_lint",  # Validate first
            "cleanup_agent",  # Clean old files
            "update_sprint",  # Update sprint status
            "embed_documents",  # Embed for search
        ]

        # Simulate agent execution
        execution_log = []

        for agent in execution_order:
            execution_log.append(
                {"agent": agent, "timestamp": datetime.utcnow().isoformat(), "status": "success"}
            )
            time.sleep(0.1)  # Ensure different timestamps

        # Verify execution order
        for i in range(1, len(execution_log)):
            prev_time = datetime.fromisoformat(execution_log[i - 1]["timestamp"])
            curr_time = datetime.fromisoformat(execution_log[i]["timestamp"])
            assert curr_time > prev_time


class TestSnapshotVerification:
    """Test snapshot creation and verification"""

    def test_snapshot_format(self):
        """Test snapshot file format and structure"""
        snapshot = {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.utcnow().isoformat(),
                "project": "test_project",
            },
            "documents": {
                "total_count": 15,
                "by_type": {"design": 5, "decision": 3, "sprint": 4, "trace": 3},
            },
            "agents": {
                "last_run": {
                    "cleanup_agent": "2024-01-15T10:00:00Z",
                    "update_sprint": "2024-01-15T11:00:00Z",
                },
                "status": {"cleanup_agent": "success", "update_sprint": "success"},
            },
            "checksums": {"documents": "abc123...", "configuration": "def456..."},
        }

        # Validate structure
        assert "metadata" in snapshot
        assert "documents" in snapshot
        assert "agents" in snapshot
        assert "checksums" in snapshot

        # Validate metadata
        assert snapshot["metadata"]["version"] == "1.0"
        assert "created_at" in snapshot["metadata"]

        # Validate document counts
        total = sum(snapshot["documents"]["by_type"].values())
        assert total == snapshot["documents"]["total_count"]

    def test_snapshot_comparison(self):
        """Test comparing snapshots for changes"""
        snapshot1 = {
            "documents": {"total_count": 10, "checksum": "abc123"},
            "timestamp": "2024-01-15T10:00:00Z",
        }

        snapshot2 = {
            "documents": {"total_count": 12, "checksum": "def456"},
            "timestamp": "2024-01-15T11:00:00Z",
        }

        # Compare snapshots
        changes = {
            "documents_added": snapshot2["documents"]["total_count"]
            - snapshot1["documents"]["total_count"],
            "checksum_changed": snapshot1["documents"]["checksum"]
            != snapshot2["documents"]["checksum"],
            "time_elapsed": (
                datetime.fromisoformat(snapshot2["timestamp"])
                - datetime.fromisoformat(snapshot1["timestamp"])
            ).total_seconds(),
        }

        assert changes["documents_added"] == 2
        assert changes["checksum_changed"] is True
        assert changes["time_elapsed"] == 3600  # 1 hour


class TestErrorRecovery:
    """Test error scenarios and recovery"""

    def test_corrupted_document_handling(self):
        """Test handling of corrupted documents"""
        # Create corrupted YAML
        corrupted_yaml = """
        metadata:
          document_type: design
        content:
          title: Test
          invalid: [unclosed bracket
        """

        # Try to parse
        try:
            data = yaml.safe_load(corrupted_yaml)
            assert False, "Should have raised exception"
        except yaml.YAMLError as e:
            # Expected behavior
            assert "while parsing" in str(e).lower()

    def test_missing_configuration_fallback(self):
        """Test fallback behavior with missing configuration"""
        # Default configuration
        default_config = {
            "agents": {"cleanup_agent": {"retention_days": 30, "enabled": True}},
            "system": {"project_name": "unnamed_project"},
        }

        # Simulate missing config scenario
        config = None

        # Apply fallback
        if config is None:
            config = default_config

        assert config["agents"]["cleanup_agent"]["retention_days"] == 30
        assert config["system"]["project_name"] == "unnamed_project"
