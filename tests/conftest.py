#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures
"""

import os
from pathlib import Path

import pytest


@pytest.fixture
def test_config():
    """Test configuration fixture"""
    return {
        "qdrant": {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": int(os.getenv("QDRANT_PORT", "6333")),
            "api_key": os.getenv("QDRANT_API_KEY", "test_key"),
            "collection_name": os.getenv("QDRANT_COLLECTION", "test_collection"),
            "embedding_model": os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"),
        },
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY", "test_openai_key"),
        },
        "neo4j": {
            "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            "username": os.getenv("NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD", "test_password"),
        },
    }


@pytest.fixture
def mock_embedding_vector():
    """Mock embedding vector fixture"""
    return [0.1, 0.2, 0.3] * 512  # 1536 dimensions for ada-002


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Create required directories for tests"""
    # Get project root
    project_root = Path(__file__).parent.parent

    # Create required context directories
    directories = [
        "context/design",
        "context/decisions",
        "context/trace",
        "context/sprints",
        "context/logs",
        "context/logs/cleanup",
        "context/logs/eval",
        "context/logs/kv",
        "context/logs/prompts",
        "context/logs/signatures",
        "context/archive",
        "context/mcp_contracts",
        "context/schemas",
        "context/.duckdb",
        "context/.graph_cache",
        "context/.vector_cache",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup is optional - we'll leave directories for other tests
