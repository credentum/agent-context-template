"""
Shared pytest fixtures and configuration for tests
"""

import os
from pathlib import Path

import pytest


@pytest.fixture
def test_config():
    """Provide test configuration with environment-based credentials"""
    return {
        "qdrant": {
            "host": os.getenv("TEST_QDRANT_HOST", "localhost"),
            "port": int(os.getenv("TEST_QDRANT_PORT", "6333")),
            "collection_name": os.getenv("TEST_QDRANT_COLLECTION", "test_collection"),
            "embedding_model": os.getenv("TEST_EMBEDDING_MODEL", "text-embedding-ada-002"),
            "api_key": os.getenv("TEST_QDRANT_API_KEY", "mock_qdrant_key"),
        },
        "openai": {
            "api_key": os.getenv("TEST_OPENAI_API_KEY", "mock_openai_key"),
        },
    }


@pytest.fixture
def mock_credentials():
    """Provide mock credentials for testing without real API calls"""
    return {
        "qdrant_api_key": "mock_qdrant_key_for_testing",
        "openai_api_key": "mock_openai_key_for_testing",
        "anthropic_api_key": "mock_anthropic_key_for_testing",
    }


@pytest.fixture
def temp_context_dir(tmp_path):
    """Create a temporary context directory structure"""
    context_dir = tmp_path / "context"
    docs_dir = context_dir / "docs"
    sprints_dir = context_dir / "sprints"
    trace_dir = context_dir / "trace"
    archive_dir = context_dir / "archive"

    for directory in [docs_dir, sprints_dir, trace_dir, archive_dir]:
        directory.mkdir(parents=True)

    return context_dir


@pytest.fixture
def sample_yaml_content():
    """Provide sample YAML content for testing"""
    return {
        "valid": """
metadata:
  document_type: design
  version: 1.0
  created_date: 2024-01-01
  author: system

content:
  title: Test Document
  description: This is a test document
""",
        "invalid": """
metadata:
  created_date: 2024-01-01

content:
  title: Missing document_type
""",
        "malformed": """
key: value
  invalid: indentation:
""",
    }


@pytest.fixture
def github_api_responses():
    """Provide mock GitHub API responses"""
    return {
        "issues": [
            {
                "number": 1,
                "title": "Implement feature A",
                "state": "closed",
                "labels": [{"name": "completed"}],
                "body": "Feature A implementation details",
            },
            {
                "number": 2,
                "title": "Fix bug in module B",
                "state": "open",
                "labels": [{"name": "in-progress"}],
                "body": "Bug details and reproduction steps",
            },
        ],
        "pull_request": {
            "number": 100,
            "title": "feat: Add new feature",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "base": {"ref": "main"},
        },
    }


@pytest.fixture
def mock_embedding_vector():
    """Provide a mock embedding vector for testing"""
    # 1536 dimensions for ada-002
    return [0.1, 0.2, 0.3] * 512


@pytest.fixture
def sigstore_mock_data():
    """Provide mock data for Sigstore testing"""
    return {
        "certificate": "-----BEGIN CERTIFICATE-----\nMOCK_CERT_DATA\n-----END CERTIFICATE-----",
        "signature": "mock_signature_base64_encoded",
        "public_key": "mock_public_key",
        "identity": {
            "issuer": "https://github.com/login/oauth",
            "subject": "user@example.com",
        },
    }


# Add pytest markers for different test types
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "mutation: Tests for mutation testing")
