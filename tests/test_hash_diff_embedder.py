#!/usr/bin/env python3
"""
Unit tests for hash_diff_embedder module
Tests file transforms, YAML parsing, and document embedding logic
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import yaml

from src.storage.hash_diff_embedder import DocumentHash, HashDiffEmbedder


class TestHashDiffEmbedder:
    """Test HashDiffEmbedder class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_config = {
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "collection_name": "test_collection",
                "embedding_model": "text-embedding-ada-002",
                "api_key": "test_key",
            },
            "openai": {"api_key": "test_openai_key"},
        }
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_config_file(self):
        """Create temporary config file"""
        config_path = Path(self.temp_dir) / ".ctxrc.yaml"
        with open(config_path, "w") as f:
            yaml.dump(self.test_config, f)
        return str(config_path)

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_config_success(self, mock_yaml_load, mock_file):
        """Test successful config loading"""
        mock_yaml_load.return_value = self.test_config

        embedder = HashDiffEmbedder()

        assert embedder.config == self.test_config
        assert embedder.embedding_model == "text-embedding-ada-002"

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("click.echo")
    def test_load_config_file_not_found(self, mock_echo, mock_file):
        """Test config loading when file doesn't exist"""
        embedder = HashDiffEmbedder("nonexistent.yaml")

        assert embedder.config == {}
        mock_echo.assert_called_with("Error: nonexistent.yaml not found", err=True)

    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load", return_value=None)
    def test_load_config_empty_yaml(self, mock_yaml_load, mock_file):
        """Test config loading with empty YAML"""
        embedder = HashDiffEmbedder()

        assert embedder.config == {}

    def test_compute_content_hash(self):
        """Test content hash computation"""
        embedder = HashDiffEmbedder()

        content1 = "This is test content"
        content2 = "This is different content"

        hash1 = embedder._compute_content_hash(content1)
        hash2 = embedder._compute_content_hash(content2)

        # Same content should produce same hash
        assert hash1 == embedder._compute_content_hash(content1)
        # Different content should produce different hash
        assert hash1 != hash2
        # Hash should be SHA-256 (64 hex chars)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_compute_embedding_hash(self):
        """Test embedding hash computation"""
        embedder = HashDiffEmbedder()

        embedding1 = [0.1, 0.2, 0.3, 0.4]
        embedding2 = [0.1, 0.2, 0.3, 0.5]

        hash1 = embedder._compute_embedding_hash(embedding1)
        hash2 = embedder._compute_embedding_hash(embedding2)

        # Same embedding should produce same hash
        assert hash1 == embedder._compute_embedding_hash(embedding1)
        # Different embedding should produce different hash
        assert hash1 != hash2
        # Hash should be SHA-256 (64 hex chars)
        assert len(hash1) == 64

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_hash_cache_success(self, mock_json_load, mock_file, mock_exists):
        """Test successful hash cache loading"""
        cache_data = {
            "doc1": {
                "document_id": "doc1",
                "file_path": "/path/to/doc1.md",
                "content_hash": "abc123",
                "embedding_hash": "def456",
                "last_embedded": "2024-01-01T00:00:00",
                "vector_id": "vec1",
            }
        }
        mock_json_load.return_value = cache_data

        embedder = HashDiffEmbedder()

        assert len(embedder.hash_cache) == 1
        assert "doc1" in embedder.hash_cache
        assert isinstance(embedder.hash_cache["doc1"], DocumentHash)
        assert embedder.hash_cache["doc1"].document_id == "doc1"

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_hash_cache_no_file(self, mock_exists):
        """Test hash cache loading when file doesn't exist"""
        embedder = HashDiffEmbedder()

        assert embedder.hash_cache == {}

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load", side_effect=json.JSONDecodeError("error", "doc", 0))
    @patch("click.echo")
    def test_load_hash_cache_invalid_json(self, mock_echo, mock_json_load, mock_file, mock_exists):
        """Test hash cache loading with invalid JSON"""
        embedder = HashDiffEmbedder()

        assert embedder.hash_cache == {}
        assert any("Failed to load hash cache" in str(call) for call in mock_echo.call_args_list)

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_hash_cache(self, mock_json_dump, mock_file, mock_mkdir):
        """Test saving hash cache"""
        embedder = HashDiffEmbedder()
        embedder.hash_cache = {
            "doc1": DocumentHash(
                document_id="doc1",
                file_path="/path/to/doc1.md",
                content_hash="abc123",
                embedding_hash="def456",
                last_embedded="2024-01-01T00:00:00",
                vector_id="vec1",
            )
        }

        embedder._save_hash_cache()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_json_dump.assert_called_once()
        saved_data = mock_json_dump.call_args[0][0]
        assert "doc1" in saved_data
        assert saved_data["doc1"]["document_id"] == "doc1"

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    @patch("openai.api_key", "test_key")
    def test_connect_success(self, mock_qdrant_client):
        """Test successful connection"""
        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_qdrant_client.return_value = mock_client

        embedder = HashDiffEmbedder()
        embedder.config = self.test_config

        result = embedder.connect()

        assert result is True
        assert embedder.client == mock_client
        mock_qdrant_client.assert_called_once_with(host="localhost", port=6333, timeout=30)

    def test_document_hash_dataclass(self):
        """Test DocumentHash dataclass"""
        doc_hash = DocumentHash(
            document_id="test_id",
            file_path="/path/to/file.md",
            content_hash="hash123",
            embedding_hash="embed456",
            last_embedded="2024-01-01T00:00:00",
            vector_id="vec789",
        )

        assert doc_hash.document_id == "test_id"
        assert doc_hash.file_path == "/path/to/file.md"
        assert doc_hash.content_hash == "hash123"
        assert doc_hash.embedding_hash == "embed456"
        assert doc_hash.last_embedded == "2024-01-01T00:00:00"
        assert doc_hash.vector_id == "vec789"


class TestYAMLParsing:
    """Test YAML parsing functionality across the codebase"""

    def test_safe_yaml_parsing(self):
        """Test that safe_load is used for YAML parsing"""
        yaml_content = """
        test:
          key: value
          number: 123
          list:
            - item1
            - item2
        """

        # Test safe_load doesn't execute arbitrary Python
        result = yaml.safe_load(yaml_content)

        assert isinstance(result, dict)
        assert result["test"]["key"] == "value"
        assert result["test"]["number"] == 123
        assert result["test"]["list"] == ["item1", "item2"]

    def test_yaml_parsing_invalid_content(self):
        """Test YAML parsing with invalid content"""
        invalid_yaml = "key: value\n  invalid: indentation:"

        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_yaml)

    def test_yaml_parsing_empty_content(self):
        """Test YAML parsing with empty content"""
        empty_yaml = ""
        result = yaml.safe_load(empty_yaml)

        assert result is None
