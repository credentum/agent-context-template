"""
Integration tests with real database instances
Run these tests with: pytest tests/test_integration_real.py -v --integration
"""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest
import yaml

from src.integrations.graphrag_integration import GraphRAGIntegration
from src.storage.graph_builder import GraphBuilder
from src.storage.hash_diff_embedder import HashDiffEmbedder
from src.storage.neo4j_init import Neo4jInitializer

# Import components
from src.storage.vector_db_init import VectorDBInitializer

# Mark all tests as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def test_config():
    """Create test configuration"""
    config = {
        "qdrant": {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": int(os.getenv("QDRANT_PORT", 6333)),
            "collection_name": "test_integration",
            "embedding_model": "text-embedding-ada-002",
            "ssl": False,
            "timeout": 10,
        },
        "neo4j": {
            "host": os.getenv("NEO4J_HOST", "localhost"),
            "port": int(os.getenv("NEO4J_PORT", 7687)),
            "database": "test_integration",
            "ssl": False,
            "timeout": 10,
        },
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    yield config_path

    # Cleanup
    os.unlink(config_path)


@pytest.fixture(scope="module")
def neo4j_creds():
    """Get Neo4j credentials from environment"""
    return {
        "username": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "testpassword"),
    }


@pytest.fixture(scope="module")
def test_documents(tmp_path_factory):
    """Create test documents"""
    test_dir = tmp_path_factory.mktemp("test_docs")

    # Create test documents
    docs = [
        {
            "id": "design-001",
            "document_type": "design",
            "title": "Test Architecture",
            "description": "Architecture for testing",
            "created_date": "2025-07-11",
            "status": "active",
            "content": "This design references [[decision-001]] for choices.",
        },
        {
            "id": "decision-001",
            "document_type": "decision",
            "title": "Technology Stack Decision",
            "rationale": "Based on requirements",
            "created_date": "2025-07-11",
            "status": "active",
            "alternatives_considered": {"option1": "Description 1", "option2": "Description 2"},
        },
        {
            "id": "sprint-001",
            "document_type": "sprint",
            "title": "Sprint 1",
            "sprint_number": 1,
            "start_date": "2025-07-11",
            "end_date": "2025-07-25",
            "status": "in_progress",
            "goals": ["Complete integration tests"],
        },
    ]

    for doc in docs:
        file_path = test_dir / f"{doc['id']}.yaml"
        with open(file_path, "w") as f:
            yaml.dump(doc, f)

    yield test_dir

    # Cleanup
    shutil.rmtree(test_dir)


class TestVectorDBIntegration:
    """Test vector database with real Qdrant instance"""

    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
    def test_vector_db_lifecycle(self, test_config, test_documents):
        """Test complete vector DB lifecycle"""
        # Initialize Qdrant
        initializer = VectorDBInitializer(test_config)
        assert initializer.connect()

        # Create collection
        assert initializer.create_collection(force=True)

        # Verify collection
        assert initializer.verify_setup()

        # Initialize embedder
        embedder = HashDiffEmbedder(test_config)
        assert embedder.connect()

        # Embed documents
        embedded, total = embedder.embed_directory(test_documents)
        assert embedded == 3
        assert total == 3

        # Verify embeddings exist
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=initializer.config["qdrant"]["host"], port=initializer.config["qdrant"]["port"]
        )

        collection_info = client.get_collection("test_integration")
        assert collection_info.points_count == 3

        # Test re-embedding (should skip)
        embedded2, total2 = embedder.embed_directory(test_documents)
        assert embedded2 == 0  # Nothing new to embed
        assert total2 == 3

        # Cleanup
        client.delete_collection("test_integration")


class TestGraphDBIntegration:
    """Test graph database with real Neo4j instance"""

    @pytest.mark.skipif(
        not (os.getenv("NEO4J_HOST") or os.getenv("NEO4J_PASSWORD")),
        reason="Neo4j not available - set NEO4J_HOST and NEO4J_PASSWORD env vars",
    )
    def test_graph_db_lifecycle(self, test_config, neo4j_creds, test_documents):
        """Test complete graph DB lifecycle"""
        # Initialize Neo4j
        initializer = Neo4jInitializer(test_config)
        assert initializer.connect(**neo4j_creds)

        # Create constraints and indexes
        assert initializer.create_constraints()
        assert initializer.create_indexes()
        assert initializer.setup_graph_schema()

        # Initialize graph builder
        builder = GraphBuilder(test_config)
        assert builder.connect(**neo4j_creds)

        # Process documents
        processed, total = builder.process_directory(test_documents)
        assert processed == 3
        assert total == 3

        # Verify graph structure
        with builder.driver.session(database=builder.database) as session:
            # Check nodes
            result = session.run("MATCH (n:Document) RETURN count(n) as count")
            assert result.single()["count"] == 3

            # Check relationships
            result = session.run("MATCH ()-[r:REFERENCES]->() RETURN count(r) as count")
            assert result.single()["count"] >= 1  # At least one reference

        # Test statistics
        stats = builder.get_statistics()
        assert stats["node_counts"]["Document"] == 3
        assert "REFERENCES" in stats["relationship_counts"]

        # Cleanup
        builder.close()


class TestGraphRAGIntegration:
    """Test GraphRAG with real databases"""

    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
    def test_graphrag_search(self, test_config, neo4j_creds, test_documents):
        """Test GraphRAG search functionality"""
        # Ensure both databases are populated
        # (Assuming previous tests have run)

        # Initialize GraphRAG
        graphrag = GraphRAGIntegration(test_config)
        assert graphrag.connect(
            neo4j_username=neo4j_creds["username"], neo4j_password=neo4j_creds["password"]
        )

        # Create a test query vector (normally from embedding)
        import random

        query_vector = [random.random() for _ in range(1536)]

        # Perform search
        result = graphrag.search(
            query="architecture decisions", query_vector=query_vector, max_hops=2, top_k=5
        )

        # Verify results
        assert result.query == "architecture decisions"
        assert len(result.vector_results) > 0
        assert result.combined_score >= 0
        assert len(result.reasoning_path) > 0

        # Test document impact analysis
        impact = graphrag.analyze_document_impact("design-001")
        assert impact["document_id"] == "design-001"
        assert impact["direct_connections"] >= 0

        # Cleanup
        graphrag.close()


class TestPerformanceIntegration:
    """Test performance with larger datasets"""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not (os.getenv("NEO4J_HOST") or os.getenv("NEO4J_PASSWORD")),
        reason="Neo4j not available - set NEO4J_HOST and NEO4J_PASSWORD env vars",
    )
    def test_bulk_processing(self, test_config, neo4j_creds):
        """Test processing many documents"""
        # Create many test documents
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create 100 documents
            for i in range(100):
                doc = {
                    "id": f"perf-test-{i:03d}",
                    "document_type": "test",
                    "title": f"Performance Test {i}",
                    "created_date": "2025-07-11",
                    "content": f"Content for document {i}",
                }

                with open(test_dir / f"doc-{i:03d}.yaml", "w") as f:
                    yaml.dump(doc, f)

            # Time the processing
            builder = GraphBuilder(test_config)
            assert builder.connect(**neo4j_creds)

            start_time = time.time()
            processed, total = builder.process_directory(test_dir)
            elapsed = time.time() - start_time

            assert processed == 100
            assert elapsed < 60  # Should process 100 docs in under 1 minute

            # Cleanup
            with builder.driver.session(database=builder.database) as session:
                session.run(
                    "MATCH (n:Document) WHERE n.id STARTS WITH 'perf-test-' DETACH DELETE n"
                )

            builder.close()


@pytest.fixture(autouse=True)
def cleanup_test_data(request, test_config, neo4j_creds):
    """Cleanup test data after each test"""
    yield

    # Only cleanup if Neo4j is available
    try:
        from neo4j import GraphDatabase

        neo4j_config = yaml.safe_load(open(test_config))["neo4j"]
        driver = GraphDatabase.driver(
            f"bolt://{neo4j_config['host']}:{neo4j_config['port']}",
            auth=(neo4j_creds["username"], neo4j_creds["password"]),
        )

        with driver.session(database=neo4j_config.get("database", "neo4j")) as session:
            # Clean test data
            session.run(
                "MATCH (n) WHERE n.id STARTS WITH 'test-' OR n.id STARTS WITH 'design-' OR n.id STARTS WITH 'decision-' OR n.id STARTS WITH 'sprint-' DETACH DELETE n"
            )

        driver.close()
    except Exception:
        pass  # Ignore cleanup errors
