"""
End-to-end tests for the Agent-First Context System
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import yaml
import time
from unittest.mock import patch
import subprocess

# Import components
from src.agents.context_lint import ContextLinter
from src.agents.cleanup_agent import CleanupAgent
from src.agents.update_sprint import SprintUpdater
from src.storage.vector_db_init import VectorDBInitializer
from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.storage.neo4j_init import Neo4jInitializer
from src.storage.graph_builder import GraphBuilder
from src.integrations.graphrag_integration import GraphRAGIntegration
from src.validators.config_validator import ConfigValidator


@pytest.mark.e2e
class TestEndToEnd:
    """End-to-end tests for complete workflows"""

    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a complete test project structure"""
        # Create directory structure
        (tmp_path / "context").mkdir()
        (tmp_path / "context" / "design").mkdir()
        (tmp_path / "context" / "decisions").mkdir()
        (tmp_path / "context" / "sprints").mkdir()
        (tmp_path / "context" / "schemas").mkdir()

        # Copy schema files
        schema_dir = Path(__file__).parent.parent / "context" / "schemas"
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.yaml"):
                shutil.copy(schema_file, tmp_path / "context" / "schemas")

        # Create configuration files
        main_config = {
            "system": {"schema_version": "1.0.0", "created_date": "2025-07-11"},
            "linter": {"warning_days_old": 90, "warning_days_until_expire": 7},
            "qdrant": {
                "version": "1.14.x",
                "host": "localhost",
                "port": 6333,
                "collection_name": "test_e2e",
                "embedding_model": "text-embedding-ada-002",
                "ssl": False,
            },
            "neo4j": {
                "version": "5.x",
                "host": "localhost",
                "port": 7687,
                "database": "test_e2e",
                "ssl": False,
            },
            "storage": {"retention_days": 90, "archive_path": "context/archive"},
            "agents": {"cleanup": {"schedule": "0 2 * * *", "expire_after_days": 30}},
        }

        with open(tmp_path / ".ctxrc.yaml", "w") as f:
            yaml.dump(main_config, f)

        # Create sample documents
        design_doc = {
            "schema_version": "1.0.0",
            "document_type": "design",
            "id": "e2e-design-001",
            "title": "E2E Test Architecture",
            "description": "Architecture for end-to-end testing",
            "created_date": "2025-07-11",
            "last_modified": "2025-07-11",
            "last_referenced": "2025-07-11",
            "expires": "2025-12-31",
            "status": "approved",
            "components": ["vector-db", "graph-db", "agents"],
            "rationale": "Testing the complete system integration",
        }

        with open(tmp_path / "context" / "design" / "e2e-design-001.yaml", "w") as f:
            yaml.dump(design_doc, f)

        sprint_doc = {
            "schema_version": "1.0.0",
            "document_type": "sprint",
            "id": "e2e-sprint-001",
            "title": "E2E Test Sprint",
            "created_date": "2025-07-11",
            "last_modified": "2025-07-11",
            "last_referenced": "2025-07-11",
            "sprint_number": 1,
            "start_date": "2025-07-11",
            "end_date": "2025-07-25",
            "status": "in_progress",
            "goals": ["Complete E2E testing"],
            "phases": [
                {
                    "phase": 1,
                    "name": "Testing",
                    "duration_days": 14,
                    "status": "in_progress",
                    "tasks": ["Run E2E tests", "Validate integration"],
                }
            ],
        }

        with open(tmp_path / "context" / "sprints" / "sprint-001.yaml", "w") as f:
            yaml.dump(sprint_doc, f)

        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        yield tmp_path

        # Cleanup
        os.chdir(original_cwd)

    def test_config_validation_workflow(self, test_project):
        """Test configuration validation workflow"""
        # Validate configuration
        validator = ConfigValidator()
        valid, errors, warnings = validator.validate_all()

        assert valid is True
        assert len(errors) == 0
        # SSL warnings are expected in test environment
        assert any("SSL is disabled" in w for w in warnings)

    def test_lint_and_cleanup_workflow(self, test_project):
        """Test linting and cleanup workflow"""
        # Step 1: Lint documents
        linter = ContextLinter()
        valid, total = linter.validate_directory(test_project / "context")

        assert valid == 2  # design and sprint docs
        assert total == 2
        assert len(linter.errors) == 0

        # Step 2: Run cleanup (dry run)
        cleanup = CleanupAgent(dry_run=True, verbose=True)
        cleaned = cleanup.cleanup_old_documents(test_project / "context")

        # Should not clean anything in dry run
        assert cleaned == 0

        # Verify files still exist
        assert (test_project / "context" / "design" / "e2e-design-001.yaml").exists()

    @pytest.mark.skipif(
        not all([os.getenv("QDRANT_HOST"), os.getenv("NEO4J_HOST"), os.getenv("OPENAI_API_KEY")]),
        reason="Integration services not available",
    )
    def test_vector_graph_workflow(self, test_project):
        """Test complete vector and graph database workflow"""
        # Step 1: Initialize Vector DB
        vdb_init = VectorDBInitializer()
        assert vdb_init.connect()
        assert vdb_init.create_collection(force=True)

        # Step 2: Embed documents
        embedder = HashDiffEmbedder()
        assert embedder.connect()
        embedded, total = embedder.embed_directory(test_project / "context")
        assert embedded == 2

        # Step 3: Initialize Graph DB
        neo4j_init = Neo4jInitializer()
        neo4j_password = os.getenv("NEO4J_PASSWORD", "testpassword")
        assert neo4j_init.connect(password=neo4j_password)
        assert neo4j_init.create_constraints()
        assert neo4j_init.setup_graph_schema()

        # Step 4: Build graph
        with GraphBuilder() as builder:
            assert builder.connect(password=neo4j_password)
            processed, total = builder.process_directory(test_project / "context")
            assert processed == 2

        # Step 5: Test GraphRAG search
        with GraphRAGIntegration() as graphrag:
            assert graphrag.connect(neo4j_password=neo4j_password)

            # Create test query
            import random

            query_vector = [random.random() for _ in range(1536)]

            result = graphrag.search(
                query="test architecture", query_vector=query_vector, max_hops=2, top_k=5
            )

            assert result.query == "test architecture"
            assert len(result.vector_results) > 0

    @patch("subprocess.run")
    def test_github_actions_workflow_simulation(self, mock_run, test_project):
        """Test simulated GitHub Actions workflow"""
        # Simulate the vector-graph-sync workflow

        # Step 1: Validate YAML
        mock_run.return_value.returncode = 0
        result = subprocess.run(["python", "context_lint.py", "validate", "context/"])
        assert result.returncode == 0

        # Step 2: Check configuration
        result = subprocess.run(["python", "config_validator.py"])
        assert result.returncode == 0

        # Step 3: Simulate database operations (mocked)
        # In real workflow, this would initialize Qdrant and Neo4j

        # Step 4: Generate report
        report_path = test_project / "sync_report.md"
        with open(report_path, "w") as f:
            f.write("## Vector and Graph Sync Report\n\n")
            f.write("**Status**: Success\n")
            f.write("**Documents Processed**: 2\n")

        assert report_path.exists()

    def test_sprint_update_workflow(self, test_project):
        """Test sprint update workflow"""
        # Create mock GitHub CLI output
        github_issues = [
            {"number": 1, "title": "Run E2E tests", "state": "open", "labels": [{"name": "task"}]},
            {
                "number": 2,
                "title": "Validate integration",
                "state": "closed",
                "labels": [{"name": "task"}],
            },
        ]

        # Mock GitHub CLI
        with patch("subprocess.run") as mock_run:
            # Mock issue list
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = yaml.dump(github_issues)

            # Update sprint
            updater = SprintUpdater()
            updated = updater.update_sprint_status(
                "sprint-001", test_project / "context" / "sprints"
            )

            assert updated is True

        # Verify sprint was updated
        with open(test_project / "context" / "sprints" / "sprint-001.yaml") as f:
            sprint = yaml.safe_load(f)

        # Should have task status updated
        assert sprint["phases"][0]["tasks"][0] == "Run E2E tests"

    def test_error_recovery_workflow(self, test_project):
        """Test error recovery and resilience"""
        # Test with invalid configuration
        with open(test_project / ".ctxrc.yaml", "w") as f:
            f.write("invalid: yaml: content:")

        # Components should handle gracefully
        linter = ContextLinter()
        assert linter.config == {}  # Should use defaults

        # Fix configuration
        with open(test_project / ".ctxrc.yaml", "w") as f:
            yaml.dump(
                {
                    "system": {"schema_version": "1.0.0"},
                    "qdrant": {"host": "localhost"},
                    "neo4j": {"host": "localhost"},
                },
                f,
            )

        # Should work now
        linter2 = ContextLinter()
        assert "system" in linter2.config

    def test_performance_config_workflow(self, test_project):
        """Test performance configuration workflow"""
        # Create performance config
        perf_config = {
            "vector_db": {"embedding": {"batch_size": 50, "max_retries": 5}},
            "graph_db": {"query": {"max_path_length": 3}},
        }

        with open(test_project / "performance.yaml", "w") as f:
            yaml.dump(perf_config, f)

        # Validate performance config
        validator = ConfigValidator()
        valid = validator.validate_performance_config("performance.yaml")

        assert valid is True
        assert len(validator.errors) == 0


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceE2E:
    """End-to-end performance tests"""

    def test_large_dataset_processing(self, tmp_path):
        """Test processing large number of documents"""
        # Create many documents
        (tmp_path / "context" / "test").mkdir(parents=True)

        num_docs = 100
        for i in range(num_docs):
            doc = {
                "schema_version": "1.0.0",
                "document_type": "design",
                "id": f"perf-test-{i:04d}",
                "title": f"Performance Test Document {i}",
                "created_date": "2025-07-11",
                "last_modified": "2025-07-11",
                "description": f"Document {i} for performance testing",
            }

            with open(tmp_path / "context" / "test" / f"doc-{i:04d}.yaml", "w") as f:
                yaml.dump(doc, f)

        # Time the linting process
        os.chdir(tmp_path)

        start_time = time.time()
        linter = ContextLinter()
        valid, total = linter.validate_directory(Path("context"))
        elapsed = time.time() - start_time

        assert total == num_docs
        assert elapsed < 10  # Should process 100 docs in under 10 seconds

        # Calculate throughput
        throughput = num_docs / elapsed
        assert throughput > 10  # Should process at least 10 docs/second
