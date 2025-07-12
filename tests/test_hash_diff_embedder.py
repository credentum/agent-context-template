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
    def test_load_config_success(self, mock_yaml_load, mock_file, test_config):
        """Test successful config loading"""
        mock_yaml_load.return_value = test_config

        embedder = HashDiffEmbedder()

        assert embedder.config == test_config
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
        assert hash1 == embedder._compute_content_hash(
            content1
        ), "Same content should produce identical hash"
        # Different content should produce different hash
        assert hash1 != hash2, "Different content should produce different hashes"
        # Hash should be SHA-256 (64 hex chars)
        assert len(hash1) == 64, f"Hash should be 64 characters long, got {len(hash1)}"
        assert all(
            c in "0123456789abcdef" for c in hash1
        ), "Hash should only contain hex characters"

    def test_compute_embedding_hash(self):
        """Test embedding hash computation"""
        embedder = HashDiffEmbedder()

        embedding1 = [0.1, 0.2, 0.3, 0.4]
        embedding2 = [0.1, 0.2, 0.3, 0.5]

        hash1 = embedder._compute_embedding_hash(embedding1)
        hash2 = embedder._compute_embedding_hash(embedding2)

        # Same embedding should produce same hash
        assert hash1 == embedder._compute_embedding_hash(
            embedding1
        ), "Same embedding should produce identical hash"
        # Different embedding should produce different hash
        assert hash1 != hash2, "Different embeddings should produce different hashes"
        # Hash should be SHA-256 (64 hex chars)
        assert len(hash1) == 64, f"Embedding hash should be 64 characters long, got {len(hash1)}"

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

        assert (
            len(embedder.hash_cache) == 1
        ), f"Expected 1 item in cache, found {len(embedder.hash_cache)}"
        assert "doc1" in embedder.hash_cache, "Document 'doc1' should be in hash cache"
        assert isinstance(
            embedder.hash_cache["doc1"], DocumentHash
        ), "Cache entry should be DocumentHash instance"
        assert embedder.hash_cache["doc1"].document_id == "doc1", "Document ID should match"

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
    def test_connect_success(self, mock_qdrant_client, test_config, monkeypatch):
        """Test successful connection"""
        # Set OpenAI API key from test config
        monkeypatch.setenv("OPENAI_API_KEY", test_config["openai"]["api_key"])

        mock_client = Mock()
        mock_client.get_collections.return_value = Mock(collections=[])
        mock_qdrant_client.return_value = mock_client

        embedder = HashDiffEmbedder()
        embedder.config = test_config

        result = embedder.connect()

        assert result is True, "Connection should succeed and return True"
        assert embedder.client == mock_client, "Client should be set after successful connection"
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


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_compute_content_hash_with_none(self):
        """Test content hash computation with None input"""
        embedder = HashDiffEmbedder()

        with pytest.raises(AttributeError, match="'NoneType' object has no attribute"):
            embedder._compute_content_hash(None)

    def test_compute_content_hash_with_empty_string(self):
        """Test content hash computation with empty string"""
        embedder = HashDiffEmbedder()

        # Empty string should still produce a valid hash
        hash_value = embedder._compute_content_hash("")
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_content_hash_with_unicode(self):
        """Test content hash computation with Unicode content"""
        embedder = HashDiffEmbedder()

        unicode_content = "Hello 世界 🌍 Здравствуй"
        hash_value = embedder._compute_content_hash(unicode_content)
        assert len(hash_value) == 64

        # Same Unicode content should produce same hash
        hash_value2 = embedder._compute_content_hash(unicode_content)
        assert hash_value == hash_value2

    def test_compute_embedding_hash_with_invalid_types(self):
        """Test embedding hash computation with invalid input types"""
        embedder = HashDiffEmbedder()

        # Test with string instead of list
        with pytest.raises(TypeError, match="embedding must be a list"):
            embedder._compute_embedding_hash("not a list")

        # Test with None
        with pytest.raises(TypeError, match="embedding must be a list"):
            embedder._compute_embedding_hash(None)

        # Test with dict
        with pytest.raises(TypeError, match="embedding must be a list"):
            embedder._compute_embedding_hash({"key": "value"})

    def test_compute_embedding_hash_with_empty_list(self):
        """Test embedding hash computation with empty list"""
        embedder = HashDiffEmbedder()

        # Empty embedding should still produce a valid hash
        hash_value = embedder._compute_embedding_hash([])
        assert len(hash_value) == 64

    def test_load_config_with_malformed_yaml(self):
        """Test config loading with malformed YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: value\n  bad: indentation:")
            config_path = f.name

        try:
            with patch("click.echo") as mock_echo:
                embedder = HashDiffEmbedder(config_path)
                assert embedder.config == {}
                mock_echo.assert_called_with(f"Error loading {config_path}: ", err=True)
        finally:
            os.unlink(config_path)

    def test_load_hash_cache_with_corrupted_file(self):
        """Test hash cache loading with corrupted JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json content")
            cache_path = f.name

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(HashDiffEmbedder, "hash_cache_path", Path(cache_path)):
                with patch("click.echo") as mock_echo:
                    embedder = HashDiffEmbedder()
                    assert embedder.hash_cache == {}
                    # Check that error was logged
                    assert any(
                        "Failed to load hash cache" in str(call)
                        for call in mock_echo.call_args_list
                    )

        os.unlink(cache_path)

    def test_save_hash_cache_with_permission_error(self):
        """Test saving hash cache when permission is denied"""
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

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("click.echo") as mock_echo:
                embedder._save_hash_cache()
                # Should handle the error gracefully
                mock_echo.assert_called()

    @patch("src.storage.hash_diff_embedder.QdrantClient")
    def test_connect_with_timeout(self, mock_qdrant_client):
        """Test connection with timeout error"""
        from qdrant_client.http.exceptions import ResponseHandlingException

        mock_qdrant_client.side_effect = ResponseHandlingException("Connection timeout")

        embedder = HashDiffEmbedder()
        embedder.config = {"qdrant": {"host": "localhost", "port": 6333}}

        with patch("click.echo") as mock_echo:
            result = embedder.connect()
            assert result is False
            mock_echo.assert_called_with(
                "Failed to connect to Qdrant: Connection timeout", err=True
            )

    def test_document_hash_with_invalid_data(self):
        """Test DocumentHash dataclass with invalid data types"""
        # This should work - dataclass doesn't validate types at runtime
        doc_hash = DocumentHash(
            document_id=123,  # Should be string
            file_path=None,  # Should be string
            content_hash=[],  # Should be string
            embedding_hash={},  # Should be string
            last_embedded=datetime.now(),  # Should be string
            vector_id=True,  # Should be string
        )

        # Dataclass creation succeeds but values are wrong types
        assert doc_hash.document_id == 123
        assert doc_hash.file_path is None
