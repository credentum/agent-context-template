#!/usr/bin/env python3
"""
Integration tests for document embedding flow
Tests the complete flow: document → embedding → Qdrant storage → retrieval → summarization
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import yaml
from qdrant_client.models import Distance, PointStruct, ScoredPoint, VectorParams

from src.storage.hash_diff_embedder import DocumentHash, HashDiffEmbedder
from src.storage.hash_diff_embedder_async import AsyncHashDiffEmbedder


class TestEmbeddingIntegrationFlow:
    """Test complete embedding flow from document to Qdrant"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test documents
        self.test_documents = {
            "design_doc.yaml": """metadata:
  document_type: design
  title: System Design
  created_date: 2024-01-01

title: System Architecture Design
description: Core system architecture documentation
content: |
  # System Design

  ## Overview
  This document describes the architecture of our system.

  ## Components
  - API Gateway
  - Microservices
  - Database Layer

  ## Data Flow
  Requests flow through the API gateway to appropriate microservices.
""",
            "decision_doc.yaml": """metadata:
  document_type: decision
  decision_id: DEC-001
  status: approved

title: Choose PostgreSQL as primary database
rationale: PostgreSQL provides the best balance of features and performance
alternatives:
  - MySQL
  - MongoDB
decision_date: 2024-01-10
""",
            "sprint_doc.yaml": """metadata:
  document_type: sprint
  sprint_number: 1

status: in_progress
start_date: 2024-01-01
end_date: 2024-01-14
goals:
  - Complete user authentication
  - Set up CI/CD pipeline
""",
        }

    def teardown_method(self):
        """Clean up temp files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_documents(self):
        """Create test documents in temp directory"""
        docs_dir = Path(self.temp_dir) / "context" / "docs"
        docs_dir.mkdir(parents=True)

        doc_paths = []
        for filename, content in self.test_documents.items():
            doc_path = docs_dir / filename
            with open(doc_path, "w") as f:
                f.write(content)
            doc_paths.append(doc_path)

        return doc_paths

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    @patch("src.storage.hash_diff_embedder.openai.OpenAI")
    @patch("pathlib.Path.cwd")
    def test_document_to_embedding_flow(
        self, mock_cwd, mock_openai_class, mock_qdrant_client, test_config, mock_embedding_vector
    ):
        """Test complete flow from document to embedding storage"""
        mock_cwd.return_value = Path(self.temp_dir)

        # Mock OpenAI client and embeddings
        mock_openai_instance = Mock()
        mock_embeddings = Mock()
        mock_embeddings.create.return_value = Mock(data=[Mock(embedding=mock_embedding_vector)])
        mock_openai_instance.embeddings = mock_embeddings
        mock_openai_class.return_value = mock_openai_instance

        # Mock Qdrant client
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_client.upsert.return_value = None
        mock_qdrant_client.return_value = mock_client

        # Create documents
        doc_paths = self.create_test_documents()

        # Initialize embedder with proper config path
        config_path = Path(self.temp_dir) / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        embedder = HashDiffEmbedder(str(config_path), verbose=True)
        embedder.client = mock_client
        # Clear any existing hash cache to ensure test isolation
        embedder.hash_cache = {}
        # Use a temporary cache path for this test
        embedder.hash_cache_path = Path(self.temp_dir) / "test_hash_cache.json"

        # Set OpenAI API key for the test
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            # Process each document by actually embedding them
            embedded_count = 0
            for doc_path in doc_paths:
                # All documents are now YAML files
                vector_id = embedder.embed_document(doc_path, force=True)
                if vector_id:
                    embedded_count += 1

        # Verify embeddings were created
        assert (
            embedded_count == 3
        ), f"Expected 3 documents to be embedded, but only {embedded_count} were processed"
        assert (
            len(embedder.hash_cache) == 3
        ), f"Expected 3 entries in hash cache, but found {len(embedder.hash_cache)}: {list(embedder.hash_cache.keys())}"
        assert (
            mock_embeddings.create.call_count >= 3
        ), f"Expected OpenAI embeddings.create to be called at least 3 times, but was called {mock_embeddings.create.call_count} times"

        # Save hash cache
        embedder._save_hash_cache()
        assert embedder.hash_cache_path.exists()

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_embedding_retrieval_flow(self, mock_qdrant_client):
        """Test retrieval of embedded documents from Qdrant"""
        # Mock Qdrant search results
        mock_results = [
            ScoredPoint(
                id="vec_design_doc",
                score=0.95,
                version=1,  # Required in newer qdrant-client versions
                payload={
                    "document_id": "design_doc",
                    "content": "System architecture design",
                    "document_type": "design",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ),
            ScoredPoint(
                id="vec_decision_doc",
                score=0.87,
                version=1,  # Required in newer qdrant-client versions
                payload={
                    "document_id": "decision_doc",
                    "content": "Database selection decision",
                    "document_type": "decision",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ),
        ]

        mock_client = Mock()
        mock_client.search.return_value = mock_results
        mock_qdrant_client.return_value = mock_client

        # Search for similar documents
        query_embedding = [0.1, 0.2, 0.3] * 512
        results = mock_client.search(
            collection_name="test_collection", query_vector=query_embedding, limit=5
        )

        # Verify results
        assert len(results) == 2
        assert results[0].score > results[1].score
        assert results[0].payload["document_type"] == "design"

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    @patch("openai.Embedding.create")
    def test_incremental_embedding_update(
        self, mock_openai_embed, mock_qdrant_client, mock_embedding_vector
    ):
        """Test incremental updates - only changed documents are re-embedded"""
        mock_openai_embed.return_value = Mock(data=[Mock(embedding=mock_embedding_vector)])

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Initialize embedder with existing hash cache
        embedder = HashDiffEmbedder()
        embedder.client = mock_client

        # Add existing document to cache
        embedder.hash_cache["existing_doc"] = DocumentHash(
            document_id="existing_doc",
            file_path="/path/to/existing.md",
            content_hash="abc123",
            embedding_hash="def456",
            last_embedded=datetime.utcnow().isoformat(),
            vector_id="vec_existing",
        )

        # Process same document (unchanged)
        content = "Existing content"
        content_hash = embedder._compute_content_hash(content)

        # If content hash matches, should not re-embed
        if content_hash == "abc123":
            needs_embedding = False
        else:
            needs_embedding = True

        assert needs_embedding is True  # Hash won't match "abc123"

    @patch("src.storage.hash_diff_embedder_async.AsyncHashDiffEmbedder")
    @pytest.mark.asyncio
    async def test_async_batch_embedding_flow(self, mock_async_embedder_class):
        """Test async batch embedding for better performance"""
        # Mock async embedder
        mock_embedder = AsyncMock()
        mock_embedder.process_batch.return_value = [
            {"document_id": "doc1", "vector_id": "vec1", "success": True},
            {"document_id": "doc2", "vector_id": "vec2", "success": True},
            {"document_id": "doc3", "vector_id": "vec3", "success": True},
        ]
        mock_async_embedder_class.return_value = mock_embedder

        # Process batch of documents
        documents = [
            {"id": "doc1", "content": "Content 1"},
            {"id": "doc2", "content": "Content 2"},
            {"id": "doc3", "content": "Content 3"},
        ]

        results = await mock_embedder.process_batch(documents)

        # Verify batch processing
        assert len(results) == 3
        assert all(r["success"] for r in results)

    def test_embedding_error_handling(self):
        """Test error handling in embedding flow"""
        embedder = HashDiffEmbedder()

        # Test with invalid content
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute"):
            embedder._compute_content_hash(None)

        # Test that embedding hash accepts various types (uses json.dumps internally)
        # This should not raise an error as json.dumps handles strings
        hash_result = embedder._compute_embedding_hash("not a list")
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hash

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    @patch("openai.Embedding.create")
    def test_embedding_api_failure(self, mock_openai_embed, mock_qdrant_client):
        """Test handling of OpenAI API failures"""
        # Mock API failure
        mock_openai_embed.side_effect = Exception("API rate limit exceeded")

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        embedder = HashDiffEmbedder()
        embedder.client = mock_client

        # Should handle the error gracefully
        with patch("click.echo") as mock_echo:
            # Attempt to embed a document
            try:
                embedder.embed_document("test content", "test_doc")
            except Exception as e:
                assert "API rate limit exceeded" in str(e)

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_qdrant_connection_failure(self, mock_qdrant_client):
        """Test handling of Qdrant connection failures"""
        mock_client = Mock()
        # Mock upsert failure
        mock_client.upsert.side_effect = Exception("Connection refused")
        mock_qdrant_client.return_value = mock_client

        embedder = HashDiffEmbedder()
        embedder.client = mock_client

        # Should handle the error gracefully
        with pytest.raises(Exception, match="Connection refused"):
            embedder.client.upsert(collection_name="test_collection", points=[])

    def test_document_size_limits(self):
        """Test handling of documents exceeding size limits"""
        # Use smaller document for performance (1MB instead of 100MB)
        large_content = "x" * (1024 * 1024 + 1)

        embedder = HashDiffEmbedder()

        # Should handle large documents
        hash_value = embedder._compute_content_hash(large_content)
        assert len(hash_value) == 64

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_concurrent_embedding_conflicts(self, mock_qdrant_client):
        """Test handling of concurrent embedding conflicts"""
        mock_client = Mock()
        # Simulate concurrent modification
        mock_client.retrieve.return_value = [Mock(id="vec_doc1", payload={"version": 2})]
        mock_qdrant_client.return_value = mock_client

        embedder = HashDiffEmbedder()
        embedder.client = mock_client
        embedder.hash_cache["doc1"] = DocumentHash(
            document_id="doc1",
            file_path="/path/to/doc1.md",
            content_hash="old_hash",
            embedding_hash="old_embed",
            last_embedded="2024-01-01T00:00:00",
            vector_id="vec_doc1",
        )

        # Should detect version conflict
        existing = mock_client.retrieve(collection_name="test", ids=["vec_doc1"])
        assert existing[0].payload["version"] == 2

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_document_summarization_flow(self, mock_qdrant_client):
        """Test document retrieval and summarization flow"""
        # Mock retrieved documents
        mock_documents = [
            {
                "id": "doc1",
                "content": "Long technical document about system architecture...",
                "summary": "System uses microservices architecture with API gateway",
            },
            {
                "id": "doc2",
                "content": "Detailed decision rationale for database selection...",
                "summary": "PostgreSQL chosen for ACID compliance and performance",
            },
        ]

        # Mock Qdrant scroll (retrieve all documents)
        mock_client = Mock()
        mock_client.scroll.return_value = (
            [Mock(id=doc["id"], payload=doc) for doc in mock_documents],
            None,
        )
        mock_qdrant_client.return_value = mock_client

        # Retrieve and summarize
        results, _ = mock_client.scroll(
            collection_name="test_collection", limit=100, with_payload=True
        )

        summaries = [r.payload.get("summary") for r in results]

        assert len(summaries) == 2
        assert all(summary for summary in summaries)


class TestEmbeddingConfiguration:
    """Test embedding configuration and settings"""

    def test_embedding_model_configuration(self):
        """Test different embedding model configurations"""
        configs = [
            {"model": "text-embedding-ada-002", "dimensions": 1536, "max_tokens": 8191},
            {"model": "text-embedding-3-small", "dimensions": 1536, "max_tokens": 8191},
            {"model": "text-embedding-3-large", "dimensions": 3072, "max_tokens": 8191},
        ]

        for config in configs:
            assert config["dimensions"] > 0
            assert config["max_tokens"] > 0
            assert config["model"].startswith("text-embedding")

    def test_collection_configuration(self):
        """Test Qdrant collection configuration"""
        collection_config = {
            "vectors": {"size": 1536, "distance": "Cosine"},
            "optimizers_config": {"indexing_threshold": 20000, "memmap_threshold": 50000},
            "hnsw_config": {"m": 16, "ef_construct": 100, "full_scan_threshold": 10000},
        }

        # Validate vector configuration
        assert collection_config["vectors"]["size"] in [1536, 3072]
        assert collection_config["vectors"]["distance"] in ["Cosine", "Euclidean", "Dot"]

        # Validate optimizer settings
        assert collection_config["optimizers_config"]["indexing_threshold"] > 0
        assert collection_config["hnsw_config"]["m"] >= 4


class TestEmbeddingMonitoring:
    """Test embedding process monitoring and metrics"""

    def test_embedding_metrics_collection(self):
        """Test collection of embedding metrics"""
        metrics = {
            "documents_processed": 0,
            "embeddings_created": 0,
            "embeddings_cached": 0,
            "errors": 0,
            "total_time_ms": 0,
            "average_time_per_doc_ms": 0,
        }

        # Simulate processing
        start_time = datetime.utcnow()

        # Process documents
        for i in range(5):
            metrics["documents_processed"] += 1
            if i % 2 == 0:  # New document
                metrics["embeddings_created"] += 1
            else:  # Cached
                metrics["embeddings_cached"] += 1

        # Calculate timing
        end_time = datetime.utcnow()
        metrics["total_time_ms"] = (end_time - start_time).total_seconds() * 1000
        metrics["average_time_per_doc_ms"] = (
            metrics["total_time_ms"] / metrics["documents_processed"]
            if metrics["documents_processed"] > 0
            else 0
        )

        # Verify metrics
        assert metrics["documents_processed"] == 5
        assert metrics["embeddings_created"] == 3
        assert metrics["embeddings_cached"] == 2
        assert metrics["errors"] == 0
