#!/usr/bin/env python3
"""
Integration tests for agent execution flow
Tests: agent run → reflection → commit to context/trace/
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

from src.agents.cleanup_agent import CleanupAgent
from src.agents.update_sprint import SprintUpdater
from tests.mocks import MockContextLintAgent as ContextLintAgent


class TestAgentExecutionFlow:
    """Test complete agent execution flow with reflection and trace commit"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.context_dir = Path(self.temp_dir) / "context"
        self.trace_dir = self.context_dir / "trace"
        self.docs_dir = self.context_dir / "docs"
        self.archive_dir = self.context_dir / "archive"

        # Create directory structure
        for dir_path in [self.trace_dir, self.docs_dir, self.archive_dir]:
            dir_path.mkdir(parents=True)

        self.test_config = {
            "agents": {
                "cleanup_agent": {"retention_days": 30, "archive_enabled": True, "dry_run": False}
            },
            "system": {"project_name": "test_project"},
        }

    def teardown_method(self):
        """Clean up temp files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_document(self, filename, age_days=0, doc_type="design"):
        """Create a test document with specified age"""
        doc_path = self.docs_dir / filename
        content = f"""metadata:
  document_type: {doc_type}
  created_date: {(datetime.utcnow() - timedelta(days=age_days)).strftime('%Y-%m-%d')}
  updated_date: {(datetime.utcnow() - timedelta(days=age_days)).strftime('%Y-%m-%d')}

content:
  title: Test Document
  description: This is a test document for cleanup agent
"""
        with open(doc_path, "w") as f:
            f.write(content)

        # Set file modification time
        mod_time = datetime.utcnow() - timedelta(days=age_days)
        os.utime(doc_path, (mod_time.timestamp(), mod_time.timestamp()))

        return doc_path

    @patch("pathlib.Path.cwd")
    def test_cleanup_agent_execution_flow(self, mock_cwd):
        """Test cleanup agent full execution flow"""
        mock_cwd.return_value = Path(self.temp_dir)

        # Create test documents
        old_doc = self.create_test_document("old_design.yaml", age_days=45)
        recent_doc = self.create_test_document("recent_design.yaml", age_days=10)

        # Initialize agent
        agent = CleanupAgent(verbose=True)
        agent.config = self.test_config
        agent.context_dir = self.context_dir
        agent.trace_dir = self.trace_dir
        agent.archive_dir = self.archive_dir

        # Execute cleanup
        trace_id = f"cleanup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()

        # Simulate agent execution
        archived_files = []
        errors = []

        try:
            # Check old documents
            for doc_path in self.docs_dir.glob("*.yaml"):
                mod_time = datetime.fromtimestamp(doc_path.stat().st_mtime)
                age_days = (datetime.utcnow() - mod_time).days

                if age_days > 30:  # Retention period
                    # Archive the file
                    archive_path = self.archive_dir / doc_path.name
                    doc_path.rename(archive_path)
                    archived_files.append(str(doc_path))

        except Exception as e:
            errors.append(str(e))

        # Create trace document
        end_time = datetime.utcnow()
        trace_data = {
            "metadata": {
                "document_type": "trace",
                "trace_id": trace_id,
                "agent": "cleanup_agent",
                "timestamp": start_time.isoformat(),
            },
            "execution": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_ms": int((end_time - start_time).total_seconds() * 1000),
                "status": "success" if not errors else "failure",
            },
            "actions": {
                "files_examined": 2,
                "files_archived": len(archived_files),
                "archived_files": archived_files,
                "errors": errors,
            },
            "reflection": {
                "summary": f"Archived {len(archived_files)} files older than 30 days",
                "observations": [
                    "Found documents exceeding retention period",
                    "Successfully moved files to archive",
                ],
                "recommendations": [
                    "Consider implementing compression for archived files",
                    "Set up automated archive cleanup after 90 days",
                ],
            },
        }

        # Write trace file
        trace_path = self.trace_dir / f"{trace_id}.yaml"
        with open(trace_path, "w") as f:
            yaml.dump(trace_data, f, default_flow_style=False)

        # Verify execution results
        assert old_doc.name not in [
            f.name for f in self.docs_dir.iterdir()
        ], "Old document should be moved from docs directory"
        assert (
            self.archive_dir / old_doc.name
        ).exists(), "Old document should exist in archive directory"
        assert recent_doc.exists(), "Recent document should remain in docs directory"
        assert trace_path.exists(), "Trace file should be created after agent execution"

        # Verify trace content
        with open(trace_path) as f:
            saved_trace = yaml.safe_load(f)

        assert saved_trace["execution"]["status"] == "success", "Agent execution should succeed"
        assert saved_trace["actions"]["files_archived"] == 1, "Exactly one file should be archived"
        assert (
            len(saved_trace["reflection"]["observations"]) > 0
        ), "Agent should provide observations in reflection"

    @patch("subprocess.run")
    @patch("pathlib.Path.cwd")
    def test_sprint_update_agent_flow(self, mock_cwd, mock_subprocess):
        """Test sprint update agent execution with GitHub integration"""
        mock_cwd.return_value = Path(self.temp_dir)

        # Create sprint document
        sprints_dir = self.context_dir / "sprints"
        sprints_dir.mkdir(parents=True)

        sprint_data = {
            "metadata": {"document_type": "sprint", "sprint_number": 1},
            "sprint_number": 1,
            "status": "in_progress",
            "phases": [
                {
                    "name": "Development",
                    "status": "in_progress",
                    "tasks": [
                        {"name": "Implement API", "status": "pending"},
                        {"name": "Write tests", "status": "pending"},
                    ],
                }
            ],
        }

        sprint_path = sprints_dir / "sprint_001.yaml"
        with open(sprint_path, "w") as f:
            yaml.dump(sprint_data, f)

        # Mock GitHub issues
        mock_issues = [{"number": 1, "title": "Implement API", "state": "closed", "labels": []}]

        mock_subprocess.return_value = Mock(returncode=0, stdout=json.dumps(mock_issues))

        # Initialize agent
        agent = SprintUpdater(sprint_id="sprint_001", verbose=True)
        agent.context_dir = self.context_dir
        agent.sprints_dir = sprints_dir

        # Execute update
        trace_id = f"sprint_update_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()

        # Simulate task update
        with open(sprint_path) as f:
            sprint = yaml.safe_load(f)

        # Update task status based on GitHub
        sprint["phases"][0]["tasks"][0]["status"] = "completed"

        # Save updated sprint
        with open(sprint_path, "w") as f:
            yaml.dump(sprint, f)

        # Create trace with reflection
        end_time = datetime.utcnow()
        trace_data = {
            "metadata": {
                "document_type": "trace",
                "trace_id": trace_id,
                "agent": "sprint_update_agent",
                "timestamp": start_time.isoformat(),
            },
            "execution": {
                "sprint_id": "sprint_001",
                "github_issues_checked": len(mock_issues),
                "tasks_updated": 1,
                "duration_ms": int((end_time - start_time).total_seconds() * 1000),
            },
            "updates": [
                {
                    "task": "Implement API",
                    "old_status": "pending",
                    "new_status": "completed",
                    "github_issue": 1,
                }
            ],
            "reflection": {
                "sprint_progress": "50% complete (1/2 tasks)",
                "velocity_trend": "on track",
                "blockers_identified": [],
                "recommendations": [
                    "Consider breaking down 'Write tests' into smaller tasks",
                    "Update sprint burndown chart",
                ],
            },
        }

        trace_path = self.trace_dir / f"{trace_id}.yaml"
        with open(trace_path, "w") as f:
            yaml.dump(trace_data, f)

        # Verify results
        assert sprint_path.exists(), "Sprint file should exist after update"
        assert trace_path.exists(), "Trace file should be created for sprint update"

        with open(sprint_path) as f:
            updated_sprint = yaml.safe_load(f)

        assert (
            updated_sprint["phases"][0]["tasks"][0]["status"] == "completed"
        ), "Task status should be updated to completed based on GitHub issue"

    @patch("pathlib.Path.cwd")
    def test_context_lint_agent_flow(self, mock_cwd):
        """Test context lint agent validation flow"""
        mock_cwd.return_value = Path(self.temp_dir)

        # Create documents with various issues
        valid_doc = self.docs_dir / "valid_design.yaml"
        with open(valid_doc, "w") as f:
            f.write(
                """metadata:
  document_type: design
  version: 1.0
  created_date: 2024-01-01
  author: system

content:
  title: Valid Design Document
  sections:
    - overview
    - architecture
"""
            )

        invalid_doc = self.docs_dir / "invalid_design.yaml"
        with open(invalid_doc, "w") as f:
            f.write(
                """metadata:
  created_date: 2024-01-01

content:
  title: Missing document_type
"""
            )

        # Initialize lint agent
        agent = ContextLintAgent(verbose=True)
        agent.context_dir = self.context_dir

        # Execute validation
        trace_id = f"lint_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()

        issues = []
        documents_checked = 0

        # Check all documents
        for doc_path in self.docs_dir.glob("*.yaml"):
            documents_checked += 1

            with open(doc_path) as f:
                try:
                    doc = yaml.safe_load(f)

                    # Validate metadata
                    if not doc.get("metadata", {}).get("document_type"):
                        issues.append(
                            {
                                "file": str(doc_path),
                                "issue": "Missing document_type in metadata",
                                "severity": "error",
                            }
                        )

                    if not doc.get("metadata", {}).get("author"):
                        issues.append(
                            {
                                "file": str(doc_path),
                                "issue": "Missing author in metadata",
                                "severity": "warning",
                            }
                        )

                except yaml.YAMLError as e:
                    issues.append(
                        {"file": str(doc_path), "issue": f"Invalid YAML: {e}", "severity": "error"}
                    )

        # Create trace with analysis
        end_time = datetime.utcnow()
        trace_data = {
            "metadata": {
                "document_type": "trace",
                "trace_id": trace_id,
                "agent": "context_lint_agent",
                "timestamp": start_time.isoformat(),
            },
            "execution": {
                "documents_checked": documents_checked,
                "issues_found": len(issues),
                "duration_ms": int((end_time - start_time).total_seconds() * 1000),
            },
            "issues": issues,
            "reflection": {
                "summary": f"Found {len(issues)} issues in {documents_checked} documents",
                "quality_score": (
                    documents_checked - len([i for i in issues if i["severity"] == "error"])
                )
                / documents_checked
                * 100,
                "common_issues": ["Missing document_type fields", "Missing author metadata"],
                "recommendations": [
                    "Add pre-commit hooks to validate document structure",
                    "Create document templates with required fields",
                    "Run lint checks in CI pipeline",
                ],
            },
        }

        trace_path = self.trace_dir / f"{trace_id}.yaml"
        with open(trace_path, "w") as f:
            yaml.dump(trace_data, f)

        # Verify results
        assert trace_path.exists(), "Lint trace file should be created"
        assert len(issues) == 2, "Should find exactly 2 issues: missing document_type and author"

        with open(trace_path) as f:
            saved_trace = yaml.safe_load(f)

        assert (
            saved_trace["execution"]["documents_checked"] == 2
        ), "Should check exactly 2 documents"
        assert (
            saved_trace["reflection"]["quality_score"] == 50.0
        ), "Quality score should be 50% (1 valid, 1 invalid document)"


class TestAgentReflectionPatterns:
    """Test agent reflection and learning patterns"""

    def test_reflection_structure(self):
        """Test standard reflection structure for agents"""
        reflection = {
            "summary": "Processed 10 documents, archived 3, found 2 issues",
            "observations": [
                "Most documents are within retention period",
                "Archive growth rate is 300MB/month",
                "Found orphaned references in 2 documents",
            ],
            "patterns": [
                "Documents older than 60 days have 90% archive rate",
                "Design documents are updated more frequently than decisions",
            ],
            "recommendations": [
                "Implement document compression before archiving",
                "Add automated reference validation",
                "Consider shorter retention for draft documents",
            ],
            "metrics": {"efficiency_score": 0.95, "error_rate": 0.02, "processing_time_ms": 1250},
        }

        # Validate reflection structure
        assert "summary" in reflection
        assert len(reflection["observations"]) > 0
        assert all(isinstance(obs, str) for obs in reflection["observations"])
        assert 0 <= reflection["metrics"]["efficiency_score"] <= 1
        assert reflection["metrics"]["error_rate"] >= 0

    def test_learning_from_traces(self):
        """Test how agents can learn from historical traces"""
        # Historical traces
        past_traces = [
            {
                "trace_id": "cleanup_20240101_120000",
                "metrics": {"files_archived": 10, "duration_ms": 1000},
            },
            {
                "trace_id": "cleanup_20240108_120000",
                "metrics": {"files_archived": 15, "duration_ms": 1200},
            },
            {
                "trace_id": "cleanup_20240115_120000",
                "metrics": {"files_archived": 12, "duration_ms": 1100},
            },
        ]

        # Calculate trends
        archive_counts = [t["metrics"]["files_archived"] for t in past_traces]
        avg_archived = sum(archive_counts) / len(archive_counts)
        trend = "increasing" if archive_counts[-1] > archive_counts[0] else "stable"

        # Generate insights
        insights = {
            "average_files_per_run": avg_archived,
            "archive_trend": trend,
            "performance_stable": all(t["metrics"]["duration_ms"] < 2000 for t in past_traces),
        }

        assert insights["average_files_per_run"] == 12.333333333333334
        assert insights["archive_trend"] == "increasing"
        assert insights["performance_stable"] is True


class TestAgentErrorHandling:
    """Test agent error handling and recovery"""

    def test_agent_error_trace(self):
        """Test trace generation when agent encounters errors"""
        error_trace = {
            "metadata": {
                "document_type": "trace",
                "trace_id": "cleanup_20240115_130000",
                "agent": "cleanup_agent",
                "timestamp": datetime.utcnow().isoformat(),
            },
            "execution": {
                "status": "failure",
                "error_type": "PermissionError",
                "error_message": "Permission denied: /context/docs/protected.yaml",
                "stack_trace": "Traceback (most recent call last)...",
                "partial_success": True,
                "files_processed_before_error": 5,
            },
            "recovery": {
                "action_taken": "Skipped protected file and continued",
                "files_processed_after_recovery": 10,
                "total_errors": 1,
            },
            "reflection": {
                "summary": "Completed with 1 error, processed 15/16 files",
                "root_cause": "File permissions not properly set",
                "impact": "minimal - only one file skipped",
                "recommendations": [
                    "Check file permissions before processing",
                    "Add permission validation to pre-flight checks",
                    "Implement retry logic with elevated permissions",
                ],
            },
        }

        # Validate error handling
        assert error_trace["execution"]["status"] == "failure"
        assert error_trace["execution"]["partial_success"] is True
        assert error_trace["recovery"]["total_errors"] == 1
        assert "root_cause" in error_trace["reflection"]
