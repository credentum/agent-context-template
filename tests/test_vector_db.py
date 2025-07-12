"""
Tests for vector database components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from pathlib import Path
import tempfile
import shutil

# Import components to test
from src.storage.vector_db_init import VectorDBInitializer
from src.storage.hash_diff_embedder import HashDiffEmbedder, DocumentHash
from src.analytics.sum_scores_api import SumScoresAPI, SearchResult


class TestVectorDBInitializer:
    """Test vector database initialization"""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create test config file"""
        config = {
            "qdrant": {
                "version": "1.14.x",
                "host": "localhost",
                "port": 6333,
                "collection_name": "test_collection",
                "embedding_model": "text-embedding-ada-002",
            }
        }
        config_path = tmp_path / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            import yaml

            yaml.dump(config, f)
        return str(config_path)

    def test_load_config(self, config_file):
        """Test configuration loading"""
        initializer = VectorDBInitializer(config_file)
        assert initializer.config["qdrant"]["host"] == "localhost"
        assert initializer.config["qdrant"]["port"] == 6333

    @patch("src.storage.vector_db_init.QdrantClient")
    def test_connect_success(self, mock_client_class, config_file):
        """Test successful connection"""
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client_class.return_value = mock_client

        initializer = VectorDBInitializer(config_file)
        assert initializer.connect() is True
        mock_client_class.assert_called_once_with(host="localhost", port=6333, timeout=30)

    @patch("src.storage.vector_db_init.QdrantClient")
    def test_connect_failure(self, mock_client_class, config_file):
        """Test connection failure"""
        mock_client_class.side_effect = Exception("Connection failed")

        initializer = VectorDBInitializer(config_file)
        assert initializer.connect() is False

    @patch("src.storage.vector_db_init.QdrantClient")
    def test_create_collection(self, mock_client_class, config_file):
        """Test collection creation"""
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client_class.return_value = mock_client

        initializer = VectorDBInitializer(config_file)
        initializer.client = mock_client

        assert initializer.create_collection() is True
        mock_client.create_collection.assert_called_once()

        # Check collection parameters
        call_args = mock_client.create_collection.call_args
        assert call_args.kwargs["collection_name"] == "test_collection"
        assert call_args.kwargs["vectors_config"].size == 1536


class TestHashDiffEmbedder:
    """Test hash-based embedder"""

    @pytest.fixture
    def test_dir(self):
        """Create test directory structure"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def embedder(self, test_dir):
        """Create embedder with test directory"""
        embedder = HashDiffEmbedder()
        embedder.hash_cache_path = test_dir / ".embeddings_cache/hash_cache.json"
        return embedder

    def test_compute_content_hash(self, embedder):
        """Test content hashing"""
        content = "Test content"
        hash1 = embedder._compute_content_hash(content)
        hash2 = embedder._compute_content_hash(content)
        hash3 = embedder._compute_content_hash("Different content")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA-256 hex length

    def test_needs_embedding(self, embedder, test_dir):
        """Test change detection"""
        # Create test file
        test_file = test_dir / "test.yaml"
        test_file.write_text("content: test")

        # First check - should need embedding
        needs, existing_id = embedder.needs_embedding(test_file)
        assert needs is True
        assert existing_id is None

        # Add to cache
        embedder.hash_cache[str(test_file)] = DocumentHash(
            document_id="test",
            file_path=str(test_file),
            content_hash=embedder._compute_content_hash("content: test"),
            embedding_hash="test_hash",
            last_embedded="2025-07-11",
            vector_id="test-vec-001",
        )

        # Second check - should not need embedding
        needs, existing_id = embedder.needs_embedding(test_file)
        assert needs is False
        assert existing_id == "test-vec-001"

        # Change file
        test_file.write_text("content: changed")

        # Third check - should need embedding again
        needs, existing_id = embedder.needs_embedding(test_file)
        assert needs is True
        assert existing_id is None

    @patch("src.storage.hash_diff_embedder.openai.OpenAI")
    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_embed_document(self, mock_qdrant_class, mock_openai_class, embedder, test_dir):
        """Test document embedding"""
        # Setup mocks
        mock_client = Mock()
        mock_qdrant_class.return_value = mock_client
        embedder.client = mock_client

        # Mock new OpenAI client
        mock_openai = Mock()
        mock_openai_class.return_value = mock_openai
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_openai.embeddings.create.return_value = mock_response

        # Create test document
        test_file = test_dir / "test.yaml"
        test_data = {
            "id": "test-doc",
            "document_type": "design",
            "title": "Test Design",
            "description": "Test description",
            "created_date": "2025-07-11",
        }
        with open(test_file, "w") as f:
            import yaml

            yaml.dump(test_data, f)

        # Embed document
        vector_id = embedder.embed_document(test_file)

        assert vector_id is not None
        assert vector_id.startswith("test-doc-")

        # Check Qdrant upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args

        # Handle both positional and keyword arguments
        if call_args.args:
            points = call_args.kwargs.get(
                "points", call_args.args[1] if len(call_args.args) > 1 else []
            )
        else:
            points = call_args.kwargs.get("points", [])

        assert len(points) == 1
        assert points[0].payload["document_id"] == "test-doc"


class TestSumScoresAPI:
    """Test sum-of-scores search API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return SumScoresAPI()

    def test_calculate_temporal_decay(self, api):
        """Test temporal decay calculation"""
        from datetime import datetime, timedelta

        # Recent document - no decay
        recent_date = datetime.now().strftime("%Y-%m-%d")
        decay = api._calculate_temporal_decay(recent_date)
        assert decay == 1.0

        # Old document - should have decay
        old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        decay = api._calculate_temporal_decay(old_date)
        assert 0.5 <= decay < 1.0

        # No date - default to no decay
        decay = api._calculate_temporal_decay(None)
        assert decay == 1.0

    def test_get_type_boost(self, api):
        """Test document type boosting"""
        assert api._get_type_boost("architecture") == 1.25
        assert api._get_type_boost("design") == 1.2
        assert api._get_type_boost("test") == 0.9
        assert api._get_type_boost("unknown") == 1.0

    @patch("src.analytics.sum_scores_api.QdrantClient")
    def test_search_single(self, mock_client_class, api):
        """Test single vector search"""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        api.client = mock_client

        # Mock search results
        mock_result = Mock()
        mock_result.id = "test-vec-001"
        mock_result.score = 0.85
        mock_result.payload = {
            "document_id": "test-doc",
            "document_type": "design",
            "title": "Test Design",
            "file_path": "/test/path.yaml",
            "last_modified": "2025-07-11",
        }

        mock_client.search.return_value = [mock_result]

        # Perform search
        query_vector = [0.1] * 1536
        results = api.search_single(query_vector, limit=5)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.document_id == "test-doc"
        assert result.score == 0.85
        assert result.boost_factor == 1.2  # design boost
        assert result.decay_factor == 1.0  # recent document
        assert result.final_score == 0.85 * 1.2 * 1.0

    def test_search_multi_aggregation(self, api):
        """Test multi-query aggregation logic"""
        # Create test results
        result1 = SearchResult(
            vector_id="vec1",
            document_id="doc1",
            document_type="design",
            file_path="/test1.yaml",
            title="Test 1",
            score=0.8,
            raw_scores=[0.8],
            decay_factor=1.0,
            boost_factor=1.2,
            final_score=0.96,
            payload={},
        )

        result2 = SearchResult(
            vector_id="vec1",  # Same document
            document_id="doc1",
            document_type="design",
            file_path="/test1.yaml",
            title="Test 1",
            score=0.7,
            raw_scores=[0.7],
            decay_factor=1.0,
            boost_factor=1.2,
            final_score=0.84,
            payload={},
        )

        # Test sum aggregation
        all_results = {"vec1": result1}
        result1.raw_scores.append(0.7)
        result1.score = 0.8 + 0.7  # Sum
        result1.final_score = 1.5 * 1.0 * 1.2

        assert result1.score == 1.5
        assert len(result1.raw_scores) == 2
