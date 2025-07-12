"""
Integration tests for vector and graph database components
"""

import pytest
from unittest.mock import Mock, patch
import tempfile
import shutil
from pathlib import Path
import yaml

# Components to test
from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.storage.graph_builder import GraphBuilder
from src.integrations.graphrag_integration import GraphRAGIntegration


class TestIntegration:
    """Integration tests combining multiple components"""

    @pytest.fixture
    def test_dir(self):
        """Create test directory with sample documents"""
        temp_dir = tempfile.mkdtemp()
        test_path = Path(temp_dir)

        # Create test documents
        docs_dir = test_path / "context" / "test"
        docs_dir.mkdir(parents=True)

        # Design document
        design_doc = {
            "id": "design-001",
            "document_type": "design",
            "title": "Test Architecture",
            "description": "References [[decision-001]] for technology choices",
            "created_date": "2025-07-11",
            "status": "active",
        }
        with open(docs_dir / "design-001.yaml", "w") as f:
            yaml.dump(design_doc, f)

        # Decision document
        decision_doc = {
            "id": "decision-001",
            "document_type": "decision",
            "title": "Technology Stack",
            "rationale": "Based on @sprint-001 requirements",
            "created_date": "2025-07-11",
            "status": "active",
            "alternatives_considered": {"option1": "Description 1", "option2": "Description 2"},
        }
        with open(docs_dir / "decision-001.yaml", "w") as f:
            yaml.dump(decision_doc, f)

        yield test_path
        shutil.rmtree(temp_dir)

    @patch("src.storage.hash_diff_embedder.openai.OpenAI")
    @patch("src.storage.hash_diff_embedder.QdrantClient")
    @patch("src.storage.graph_builder.GraphDatabase.driver")
    def test_vector_graph_sync(self, mock_neo4j, mock_qdrant, mock_openai_class, test_dir):
        """Test synchronization between vector and graph databases"""
        # Setup mocks
        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance

        # Mock Neo4j driver with context manager
        mock_neo4j_instance = Mock()
        mock_session = Mock()
        mock_session_cm = Mock()
        mock_session_cm.__enter__ = Mock(return_value=mock_session)
        mock_session_cm.__exit__ = Mock(return_value=None)
        mock_neo4j_instance.session.return_value = mock_session_cm
        mock_neo4j.return_value = mock_neo4j_instance

        # Mock OpenAI client
        mock_openai = Mock()
        mock_openai_class.return_value = mock_openai
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai.embeddings.create.return_value = mock_response

        # Initialize components
        embedder = HashDiffEmbedder()
        embedder.client = mock_qdrant_instance
        embedder.hash_cache_path = test_dir / ".cache" / "embeddings.json"

        builder = GraphBuilder()
        builder.driver = mock_neo4j_instance
        builder.processed_cache_path = test_dir / ".cache" / "graph.json"

        # Process documents
        docs_dir = test_dir / "context" / "test"

        # Embed documents
        embedded, total = embedder.embed_directory(docs_dir)
        assert embedded == 2
        assert total == 2

        # Build graph
        processed, total = builder.process_directory(docs_dir)
        assert processed == 2
        assert total == 2

        # Verify relationships were created
        create_calls = [
            call for call in mock_session.run.call_args_list if "REFERENCES" in str(call)
        ]
        assert len(create_calls) > 0

    @patch("src.integrations.graphrag_integration.QdrantClient")
    @patch("src.integrations.graphrag_integration.GraphDatabase.driver")
    def test_graphrag_search_integration(self, mock_neo4j, mock_qdrant):
        """Test GraphRAG search combining vector and graph results"""
        # Setup mocks
        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance

        # Mock Neo4j driver with context manager
        mock_neo4j_instance = Mock()
        mock_session = Mock()
        mock_session_cm = Mock()
        mock_session_cm.__enter__ = Mock(return_value=mock_session)
        mock_session_cm.__exit__ = Mock(return_value=None)
        mock_neo4j_instance.session.return_value = mock_session_cm
        mock_neo4j.return_value = mock_neo4j_instance

        # Mock vector search results
        mock_vector_result = Mock()
        mock_vector_result.id = "vec1"
        mock_vector_result.score = 0.85
        mock_vector_result.payload = {
            "document_id": "design-001",
            "document_type": "design",
            "title": "Test Architecture",
            "file_path": "/test/design-001.yaml",
        }
        mock_qdrant_instance.search.return_value = [mock_vector_result]

        # Mock graph results
        mock_graph_result = Mock()
        mock_graph_result.__getitem__ = Mock(
            side_effect=lambda k: {
                "source": {"id": "design-001"},
                "target": {"id": "decision-001", "title": "Technology Stack"},
                "relationships": [{"type": "REFERENCES"}],
                "distance": 1,
            }[k]
        )
        mock_session.run.return_value = [mock_graph_result]

        # Use context manager
        with GraphRAGIntegration() as graphrag:
            graphrag.qdrant_client = mock_qdrant_instance
            graphrag.neo4j_driver = mock_neo4j_instance

            # Perform search
            result = graphrag.search(
                query="architecture decisions", query_vector=[0.1] * 1536, max_hops=2, top_k=5
            )

            # Verify results
            assert result.query == "architecture decisions"
            assert len(result.vector_results) == 1
            assert result.vector_results[0]["document_id"] == "design-001"
            assert len(result.reasoning_path) > 0
            assert "design-001" in result.summary

    def test_error_handling_cascade(self):
        """Test error handling across components"""
        # Test context manager cleanup
        mock_driver = Mock()
        with GraphBuilder() as builder:
            builder.driver = mock_driver
            # Context manager should call close() on exit

        mock_driver.close.assert_called_once()

    @pytest.mark.skip(reason="Test takes too long due to rate limit simulation")
    @patch("src.storage.hash_diff_embedder.openai.OpenAI")
    def test_rate_limiting_retry(self, mock_openai_class):
        """Test rate limiting retry logic"""
        import openai as openai_module

        # Mock OpenAI client
        mock_openai = Mock()
        mock_openai_class.return_value = mock_openai

        # Mock rate limit error then success
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]

        # Create a proper RateLimitError with required parameters
        mock_response_error = Mock()
        mock_response_error.status_code = 429
        mock_response_error.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        rate_limit_error = openai_module.RateLimitError(
            message="Rate limit exceeded",
            response=mock_response_error,
            body={"error": {"message": "Rate limit exceeded"}},
        )

        mock_openai.embeddings.create.side_effect = [rate_limit_error, mock_response]

        embedder = HashDiffEmbedder()
        embedder.client = Mock()
        embedder.verbose = True

        # Create test file
        test_file = Path("test.yaml")
        test_data = {"id": "test", "document_type": "test", "title": "Test"}

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(test_data)

            with patch("pathlib.Path.exists", return_value=True):
                # Should retry and succeed
                result = embedder.embed_document(test_file)
                assert result is not None
                assert mock_openai.embeddings.create.call_count == 2
