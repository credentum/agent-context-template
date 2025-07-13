#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures
"""

import os
from pathlib import Path

import pytest


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
