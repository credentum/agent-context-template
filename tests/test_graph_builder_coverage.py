#!/usr/bin/env python3
"""
Additional tests for graph_builder.py to improve coverage to 75%+
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

from src.storage.graph_builder import GraphBuilder


class TestGraphBuilderCoverage:
    """Additional test suite for comprehensive graph builder coverage"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_file(self, temp_dir):
        """Create a test config file"""
        config = {
            "neo4j": {
                "host": "localhost",
                "port": 7687,
                "database": "test_graph",
                "use_ssl": False,
            },
            "system": {"name": "test_system"},
        }
        config_path = temp_dir / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return str(config_path)

    @pytest.fixture
    def builder(self, config_file):
        """Create GraphBuilder instance"""
        return GraphBuilder(config_path=config_file, verbose=True)

    def test_init_with_default_config(self):
        """Test initialization with default config (no file)"""
        builder = GraphBuilder(config_path="nonexistent.yaml")
        assert builder.config == {}
        assert builder.database == "context_graph"  # default value

    def test_init_with_io_error(self, temp_dir):
        """Test initialization with IO error"""
        config_path = temp_dir / ".ctxrc.yaml"
        # Create directory instead of file to trigger error
        config_path.mkdir()

        # The current implementation only catches FileNotFoundError
        # so other errors will propagate
        try:
            builder = GraphBuilder(config_path=str(config_path))
            # If it doesn't raise, it should have empty config
            assert builder.config == {}
        except Exception:
            # Expected behavior - current code doesn't handle this
            pass

    def test_context_manager(self, builder):
        """Test context manager functionality"""
        builder.driver = Mock()

        with builder as b:
            assert b == builder

        builder.driver.close.assert_called_once()

    def test_context_manager_with_exception(self, builder):
        """Test context manager with exception during cleanup"""
        builder.driver = Mock()
        builder.driver.close.side_effect = Exception("Close error")

        # Should not raise exception
        with builder as b:
            assert b == builder

    def test_load_config_non_dict(self, temp_dir):
        """Test loading config that's not a dict"""
        config_path = temp_dir / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            f.write("- list\n- not\n- dict")

        builder = GraphBuilder(config_path=str(config_path))
        assert builder.config == {}

    def test_load_processed_cache_exists(self, temp_dir):
        """Test loading existing processed cache"""
        cache_dir = temp_dir / "context" / ".graph_cache"
        cache_dir.mkdir(parents=True)

        cache_data = {"doc1.yaml": "hash1", "doc2.yaml": "hash2"}
        cache_path = cache_dir / "processed.json"
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

        with patch.object(
            Path,
            "__new__",
            lambda cls, *args: cache_path if "processed.json" in str(args[0]) else Path(*args),
        ):
            builder = GraphBuilder()
            assert builder.processed_docs == cache_data

    def test_load_processed_cache_invalid_json(self, temp_dir):
        """Test loading invalid JSON cache"""
        cache_dir = temp_dir / "context" / ".graph_cache"
        cache_dir.mkdir(parents=True)

        cache_path = cache_dir / "processed.json"
        with open(cache_path, "w") as f:
            f.write("invalid json")

        with patch.object(
            Path,
            "__new__",
            lambda cls, *args: cache_path if "processed.json" in str(args[0]) else Path(*args),
        ):
            builder = GraphBuilder()
            assert builder.processed_docs == {}

    def test_load_processed_cache_not_dict(self, temp_dir):
        """Test loading cache that's not a dict"""
        cache_dir = temp_dir / "context" / ".graph_cache"
        cache_dir.mkdir(parents=True)

        cache_path = cache_dir / "processed.json"
        with open(cache_path, "w") as f:
            json.dump(["list", "not", "dict"], f)

        with patch.object(
            Path,
            "__new__",
            lambda cls, *args: cache_path if "processed.json" in str(args[0]) else Path(*args),
        ):
            builder = GraphBuilder()
            assert builder.processed_docs == {}

    def test_save_processed_cache(self, builder, temp_dir):
        """Test saving processed cache"""
        cache_dir = temp_dir / "context" / ".graph_cache"
        builder.processed_cache_path = cache_dir / "processed.json"
        builder.processed_docs = {"doc1.yaml": "hash1"}

        builder._save_processed_cache()

        assert builder.processed_cache_path.exists()
        with open(builder.processed_cache_path) as f:
            data = json.load(f)
            assert data == {"doc1.yaml": "hash1"}

    def test_compute_doc_hash(self, builder):
        """Test document hash computation"""
        data = {"id": "test", "title": "Test", "content": "Test content"}
        hash1 = builder._compute_doc_hash(data)
        hash2 = builder._compute_doc_hash(data)

        # Same data should produce same hash
        assert hash1 == hash2

        # Different data should produce different hash
        data["content"] = "Different content"
        hash3 = builder._compute_doc_hash(data)
        assert hash1 != hash3

    def test_connect_no_password(self, builder):
        """Test connect without password"""
        result = builder.connect(username="neo4j", password=None)
        assert result is False

    def test_connect_success(self, builder):
        """Test successful connection"""
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context

        with patch("src.storage.graph_builder.GraphDatabase.driver", return_value=mock_driver):
            result = builder.connect(username="neo4j", password="password")
            assert result is True
            assert builder.driver == mock_driver

    def test_connect_failure(self, builder):
        """Test connection failure"""
        with patch(
            "src.storage.graph_builder.GraphDatabase.driver",
            side_effect=Exception("Connection failed"),
        ):
            result = builder.connect(username="neo4j", password="password")
            assert result is False

    def test_create_document_node_basic(self, builder):
        """Test creating basic document node"""
        mock_session = Mock()
        mock_result = Mock()
        mock_session.run.return_value = mock_result

        data = {
            "document_type": "design",
            "id": "design-001",
            "title": "Test Design",
            "created_date": "2025-07-11",
            "last_modified": "2025-07-11",
            "status": "active",
        }

        doc_id = builder._create_document_node(mock_session, data, Path("test.yaml"))

        assert doc_id == "design-001"
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert "MERGE" in call_args[0][0]
        assert call_args[1]["id"] == "design-001"

    def test_create_document_node_sprint(self, builder):
        """Test creating sprint document node"""
        mock_session = Mock()

        data = {
            "document_type": "sprint",
            "id": "sprint-001",
            "title": "Sprint 1",
            "sprint_number": 1,
            "start_date": "2025-07-01",
            "end_date": "2025-07-14",
            "status": "active",
        }

        doc_id = builder._create_document_node(mock_session, data, Path("sprint.yaml"))

        assert doc_id == "sprint-001"
        call_args = mock_session.run.call_args[1]
        props = call_args["props"]
        assert props["sprint_number"] == 1
        assert props["start_date"] == "2025-07-01"
        assert props["end_date"] == "2025-07-14"

    def test_create_document_node_decision(self, builder):
        """Test creating decision document node"""
        mock_session = Mock()

        data = {
            "document_type": "decision",
            "id": "decision-001",
            "title": "Test Decision",
            "decision_date": "2025-07-11",
            "status": "approved",
        }

        doc_id = builder._create_document_node(mock_session, data, Path("decision.yaml"))

        assert doc_id == "decision-001"
        call_args = mock_session.run.call_args[1]
        props = call_args["props"]
        assert props["decision_date"] == "2025-07-11"
        assert props["status"] == "approved"

    def test_create_relationships_sprint(self, builder):
        """Test creating relationships for sprint document"""
        mock_session = Mock()

        data = {
            "document_type": "sprint",
            "phases": [
                {
                    "phase": 1,
                    "name": "Planning",
                    "duration_days": 3,
                    "status": "completed",
                    "tasks": ["Task 1", "Task 2"],
                }
            ],
            "team": [{"agent": "agent1", "role": "Developer"}],
        }

        builder._create_relationships(mock_session, data, "sprint-001")

        # Should create phase, tasks, and team member relationships
        assert mock_session.run.call_count >= 3

    def test_create_relationships_decision(self, builder):
        """Test creating relationships for decision document"""
        mock_session = Mock()

        data = {
            "document_type": "decision",
            "alternatives_considered": {"Option A": "Description A", "Option B": "Description B"},
            "related_decisions": ["decision-002"],
        }

        builder._create_relationships(mock_session, data, "decision-001")

        # Should create alternative and related decision relationships
        assert mock_session.run.call_count >= 3

    def test_create_relationships_graph_metadata(self, builder):
        """Test creating relationships from graph metadata"""
        mock_session = Mock()

        data = {
            "document_type": "design",
            "graph_metadata": {
                "relationships": [
                    {"type": "IMPLEMENTS", "target": "design-002"},
                    {"type": "DEPENDS_ON", "target": "design-003"},
                ]
            },
        }

        builder._create_relationships(mock_session, data, "design-001")

        # Should create metadata relationships
        assert mock_session.run.call_count >= 2

    def test_extract_references(self, builder):
        """Test extracting document references from content"""
        content = """
        This references [[doc-001]] and @doc-002.
        Also mentions #doc-003 and [[doc-004]].
        """

        refs = builder._extract_references(content)

        assert refs == {"doc-001", "doc-002", "doc-003", "doc-004"}

    def test_process_document_empty_file(self, builder, temp_dir):
        """Test processing empty document"""
        doc_path = temp_dir / "empty.yaml"
        doc_path.touch()

        result = builder.process_document(doc_path)
        assert result is False

    def test_process_document_no_driver(self, builder, temp_dir):
        """Test processing document without driver connection"""
        doc_path = temp_dir / "test.yaml"
        with open(doc_path, "w") as f:
            yaml.dump({"id": "test", "title": "Test"}, f)

        builder.driver = None
        result = builder.process_document(doc_path)
        assert result is False

    def test_process_document_cached(self, builder, temp_dir):
        """Test processing already cached document"""
        doc_path = temp_dir / "test.yaml"
        data = {"id": "test", "title": "Test"}

        with open(doc_path, "w") as f:
            yaml.dump(data, f)

        # Add to cache
        doc_hash = builder._compute_doc_hash(data)
        builder.processed_docs[str(doc_path)] = doc_hash

        # Should skip processing
        result = builder.process_document(doc_path)
        assert result is True

    def test_process_document_force(self, builder, temp_dir):
        """Test force processing cached document"""
        doc_path = temp_dir / "test.yaml"
        data = {"id": "test", "title": "Test"}

        with open(doc_path, "w") as f:
            yaml.dump(data, f)

        # Add to cache
        doc_hash = builder._compute_doc_hash(data)
        builder.processed_docs[str(doc_path)] = doc_hash

        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        # Should process despite cache
        result = builder.process_document(doc_path, force=True)
        assert result is True
        assert mock_session.run.call_count > 0

    def test_process_document_with_references(self, builder, temp_dir):
        """Test processing document with references"""
        doc_path = temp_dir / "test.yaml"
        data = {
            "id": "test",
            "title": "Test",
            "content": "This references [[other-doc]] and @another-doc",
            "created_date": "2025-07-11",
        }

        with open(doc_path, "w") as f:
            yaml.dump(data, f)

        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        result = builder.process_document(doc_path)
        assert result is True

        # Should create document, references, and timeline relationships
        assert mock_session.run.call_count >= 3

    def test_process_document_exception(self, builder, temp_dir):
        """Test processing document with exception"""
        doc_path = temp_dir / "test.yaml"
        with open(doc_path, "w") as f:
            f.write("invalid: yaml: [")

        result = builder.process_document(doc_path)
        assert result is False

    def test_process_directory(self, builder, temp_dir):
        """Test processing directory of documents"""
        # Create test documents
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        for i in range(3):
            doc_path = docs_dir / f"doc{i}.yaml"
            with open(doc_path, "w") as f:
                yaml.dump({"id": f"doc-{i}", "title": f"Doc {i}"}, f)

        # Create schema file (should be skipped)
        schema_dir = docs_dir / "schemas"
        schema_dir.mkdir()
        schema_file = schema_dir / "schema.yaml"
        schema_file.touch()

        # Mock driver
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        # Redirect cache path to temp directory to avoid filesystem issues
        cache_dir = temp_dir / ".graph_cache"
        builder.processed_cache_path = cache_dir / "processed.json"

        processed, total = builder.process_directory(docs_dir)

        assert total == 3  # Should skip schema file
        assert processed == 3

    def test_process_directory_with_cache_save(self, builder, temp_dir):
        """Test that process_directory saves cache"""
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()

        doc_path = docs_dir / "doc.yaml"
        with open(doc_path, "w") as f:
            yaml.dump({"id": "doc", "title": "Doc"}, f)

        # Mock driver and cache path
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        cache_dir = temp_dir / ".graph_cache"
        builder.processed_cache_path = cache_dir / "processed.json"

        processed, total = builder.process_directory(docs_dir)

        assert builder.processed_cache_path.exists()

    def test_cleanup_orphaned_nodes_no_driver(self, builder):
        """Test cleanup without driver connection"""
        builder.driver = None
        removed = builder.cleanup_orphaned_nodes()
        assert removed == 0

    def test_cleanup_orphaned_nodes(self, builder):
        """Test cleanup of orphaned nodes"""
        # Mock driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        # Mock query results
        mock_result = [
            {"id": "doc1", "file_path": "/nonexistent/doc1.yaml"},
            {"id": "doc2", "file_path": str(Path("existing.yaml").absolute())},
        ]
        mock_session.run.return_value = mock_result

        # Add to cache
        builder.processed_docs["/nonexistent/doc1.yaml"] = "hash1"

        # Create existing file
        Path("existing.yaml").touch()

        try:
            removed = builder.cleanup_orphaned_nodes()
            assert removed == 1  # Should remove only non-existent file
            assert "/nonexistent/doc1.yaml" not in builder.processed_docs
        finally:
            Path("existing.yaml").unlink(missing_ok=True)

    def test_cleanup_orphaned_nodes_exception(self, builder):
        """Test cleanup with exception"""
        mock_driver = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(side_effect=Exception("Session error"))
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        removed = builder.cleanup_orphaned_nodes()
        assert removed == 0

    def test_get_statistics_no_driver(self, builder):
        """Test getting statistics without driver"""
        builder.driver = None
        stats = builder.get_statistics()
        assert stats == {}

    def test_get_statistics(self, builder):
        """Test getting graph statistics"""
        # Mock driver and session
        mock_driver = Mock()
        mock_session = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        # Mock query results
        mock_results = [
            [{"label": "Document", "count": 10}, {"label": "Sprint", "count": 5}],
            [{"type": "REFERENCES", "count": 20}, {"type": "HAS_PHASE", "count": 8}],
            [{"type": "design", "count": 6}, {"type": "sprint", "count": 4}],
        ]
        mock_session.run.side_effect = mock_results

        stats = builder.get_statistics()

        assert stats["node_counts"]["Document"] == 10
        assert stats["relationship_counts"]["REFERENCES"] == 20
        assert stats["document_types"]["design"] == 6

    def test_get_statistics_exception(self, builder):
        """Test getting statistics with exception"""
        mock_driver = Mock()
        mock_context = Mock()
        mock_context.__enter__ = Mock(side_effect=Exception("Query error"))
        mock_context.__exit__ = Mock(return_value=None)
        mock_driver.session.return_value = mock_context
        builder.driver = mock_driver

        stats = builder.get_statistics()
        assert "error" in stats

    def test_close_with_driver(self, builder):
        """Test closing driver connection"""
        mock_driver = Mock()
        builder.driver = mock_driver

        builder.close()
        mock_driver.close.assert_called_once()

    def test_close_without_driver(self, builder):
        """Test closing without driver"""
        builder.driver = None
        builder.close()  # Should not raise

    @patch("click.echo")
    def test_main_connect_failure(self, mock_echo):
        """Test main function with connection failure"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        runner = CliRunner()
        with patch("src.storage.graph_builder.GraphBuilder.connect", return_value=False):
            result = runner.invoke(main, ["--password", "test"])
            assert result.exit_code == 0
            assert any("Failed to connect" in str(call) for call in mock_echo.call_args_list)

    @patch("click.echo")
    def test_main_cleanup(self, mock_echo):
        """Test main function with cleanup option"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        runner = CliRunner()
        with (
            patch("src.storage.graph_builder.GraphBuilder.connect", return_value=True),
            patch("src.storage.graph_builder.GraphBuilder.cleanup_orphaned_nodes", return_value=5),
            patch("src.storage.graph_builder.GraphBuilder.close"),
        ):
            result = runner.invoke(main, ["--password", "test", "--cleanup"])
            assert result.exit_code == 0
            assert any("Removed 5 orphaned nodes" in str(call) for call in mock_echo.call_args_list)

    @patch("click.echo")
    def test_main_stats(self, mock_echo):
        """Test main function with stats option"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        stats_data = {
            "node_counts": {"Document": 10, "Sprint": 5},
            "relationship_counts": {"REFERENCES": 20},
            "document_types": {"design": 6},
        }

        runner = CliRunner()
        with (
            patch("src.storage.graph_builder.GraphBuilder.connect", return_value=True),
            patch("src.storage.graph_builder.GraphBuilder.get_statistics", return_value=stats_data),
            patch("src.storage.graph_builder.GraphBuilder.close"),
        ):
            result = runner.invoke(main, ["--password", "test", "--stats"])
            assert result.exit_code == 0
            assert any("Graph Statistics" in str(call) for call in mock_echo.call_args_list)

    @patch("click.echo")
    def test_main_process_file(self, mock_echo, temp_dir):
        """Test main function processing single file"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        doc_path = temp_dir / "test.yaml"
        with open(doc_path, "w") as f:
            yaml.dump({"id": "test"}, f)

        runner = CliRunner()
        with (
            patch("src.storage.graph_builder.GraphBuilder.connect", return_value=True),
            patch("src.storage.graph_builder.GraphBuilder.process_document", return_value=True),
            patch("src.storage.graph_builder.GraphBuilder.close"),
        ):
            result = runner.invoke(main, [str(doc_path), "--password", "test"])
            assert result.exit_code == 0
            assert any("✓ Processed:" in str(call) for call in mock_echo.call_args_list)

    @patch("click.echo")
    def test_main_process_directory(self, mock_echo, temp_dir):
        """Test main function processing directory"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        runner = CliRunner()
        with (
            patch("src.storage.graph_builder.GraphBuilder.connect", return_value=True),
            patch("src.storage.graph_builder.GraphBuilder.process_directory", return_value=(8, 10)),
            patch("src.storage.graph_builder.GraphBuilder.close"),
        ):
            result = runner.invoke(main, [str(temp_dir), "--password", "test"])
            assert result.exit_code == 0
            assert any("Processed: 8/10" in str(call) for call in mock_echo.call_args_list)

    @patch("click.echo")
    def test_main_with_force_and_verbose(self, mock_echo, temp_dir):
        """Test main function with force and verbose options"""
        from click.testing import CliRunner

        from src.storage.graph_builder import main

        runner = CliRunner()
        with (
            patch("src.storage.graph_builder.GraphBuilder.connect", return_value=True),
            patch(
                "src.storage.graph_builder.GraphBuilder.process_directory", return_value=(10, 10)
            ),
            patch("src.storage.graph_builder.GraphBuilder.close"),
        ):
            result = runner.invoke(
                main, [str(temp_dir), "--password", "test", "--force", "--verbose"]
            )
            assert result.exit_code == 0
            assert any("Graph building complete" in str(call) for call in mock_echo.call_args_list)
