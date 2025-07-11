"""
Tests for graph database components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
from pathlib import Path
import tempfile
import shutil

# Import components to test
from neo4j_init import Neo4jInitializer
from graph_builder import GraphBuilder
from graphrag_integration import GraphRAGIntegration, GraphRAGResult


def create_mock_neo4j_driver():
    """Helper to create properly mocked Neo4j driver with session context manager"""
    mock_driver = Mock()
    mock_session = Mock()
    mock_session_cm = Mock()
    mock_session_cm.__enter__ = Mock(return_value=mock_session)
    mock_session_cm.__exit__ = Mock(return_value=None)
    mock_driver.session.return_value = mock_session_cm
    return mock_driver, mock_session


class TestNeo4jInitializer:
    """Test Neo4j initialization"""
    
    @pytest.fixture
    def config_file(self, tmp_path):
        """Create test config file"""
        config = {
            'neo4j': {
                'version': '5.x',
                'host': 'localhost',
                'port': 7687,
                'database': 'test_graph'
            },
            'system': {
                'schema_version': '1.0.0',
                'created_date': '2025-07-11'
            }
        }
        config_path = tmp_path / ".ctxrc.yaml"
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config, f)
        return str(config_path)
    
    def test_load_config(self, config_file):
        """Test configuration loading"""
        initializer = Neo4jInitializer(config_file)
        assert initializer.config['neo4j']['host'] == 'localhost'
        assert initializer.config['neo4j']['port'] == 7687
        assert initializer.database == 'test_graph'
    
    @patch('neo4j_init.GraphDatabase.driver')
    def test_connect_success(self, mock_driver, config_file):
        """Test successful connection"""
        # Setup mock with proper context manager
        mock_driver_instance, mock_session = create_mock_neo4j_driver()
        mock_driver.return_value = mock_driver_instance
        
        initializer = Neo4jInitializer(config_file)
        assert initializer.connect(username='neo4j', password='test') is True
        
        mock_driver.assert_called_once_with('bolt://localhost:7687', auth=('neo4j', 'test'))
        mock_session.run.assert_called_once_with("RETURN 1 as test")
    
    @patch('neo4j_init.GraphDatabase.driver')
    def test_create_constraints(self, mock_driver, config_file):
        """Test constraint creation"""
        # Setup mock with proper context manager
        mock_driver_instance, mock_session = create_mock_neo4j_driver()
        
        initializer = Neo4jInitializer(config_file)
        initializer.driver = mock_driver_instance
        
        assert initializer.create_constraints() is True
        
        # Check constraints were created
        expected_constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Design) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Decision) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Sprint) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Agent) REQUIRE n.name IS UNIQUE",
        ]
        
        calls = mock_session.run.call_args_list
        for expected in expected_constraints:
            assert any(expected in str(call) for call in calls)
    
    @patch('neo4j_init.GraphDatabase.driver')
    def test_setup_graph_schema(self, mock_driver, config_file):
        """Test graph schema setup"""
        # Setup mock
        mock_driver_instance, mock_session = create_mock_neo4j_driver()
        
        initializer = Neo4jInitializer(config_file)
        initializer.driver = mock_driver_instance
        
        assert initializer.setup_graph_schema() is True
        
        # Check system node was created
        calls = mock_session.run.call_args_list
        system_node_created = any(
            "MERGE (s:System {id: 'agent-context-system'})" in str(call)
            for call in calls
        )
        assert system_node_created


class TestGraphBuilder:
    """Test graph builder component"""
    
    @pytest.fixture
    def test_dir(self):
        """Create test directory structure"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def builder(self, test_dir):
        """Create graph builder"""
        builder = GraphBuilder()
        builder.processed_cache_path = test_dir / ".graph_cache/processed.json"
        return builder
    
    def test_compute_doc_hash(self, builder):
        """Test document hash computation"""
        doc1 = {'id': 'test', 'content': 'test content'}
        doc2 = {'id': 'test', 'content': 'test content'}
        doc3 = {'id': 'test', 'content': 'different content'}
        
        hash1 = builder._compute_doc_hash(doc1)
        hash2 = builder._compute_doc_hash(doc2)
        hash3 = builder._compute_doc_hash(doc3)
        
        assert hash1 == hash2  # Same content
        assert hash1 != hash3  # Different content
    
    @patch('graph_builder.GraphDatabase.driver')
    def test_create_document_node(self, mock_driver, builder, test_dir):
        """Test document node creation"""
        # Setup mock
        mock_driver_instance, mock_session = create_mock_neo4j_driver()
        builder.driver = mock_driver_instance
        
        # Test data
        data = {
            'id': 'test-design',
            'document_type': 'design',
            'title': 'Test Design',
            'created_date': '2025-07-11',
            'status': 'active'
        }
        
        file_path = test_dir / "test.yaml"
        
        # Create node
        doc_id = builder._create_document_node(mock_session, data, file_path)
        
        assert doc_id == 'test-design'
        
        # Check query
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        assert 'Document:Design' in call_args[0][0]
        assert call_args[1]['id'] == 'test-design'
    
    def test_extract_references(self, builder):
        """Test reference extraction from content"""
        content = """
        This references [[design-001]] and @sprint-001.
        Also mentions #decision-002 and [[api-spec]].
        """
        
        references = builder._extract_references(content)
        
        assert 'design-001' in references
        assert 'sprint-001' in references
        assert 'decision-002' in references
        assert 'api-spec' in references
        assert len(references) == 4
    
    @patch('graph_builder.GraphDatabase.driver')
    def test_process_document(self, mock_driver, builder, test_dir):
        """Test document processing"""
        # Setup mock
        mock_driver_instance, mock_session = create_mock_neo4j_driver()
        builder.driver = mock_driver_instance
        
        # Create test document
        test_file = test_dir / "test.yaml"
        test_data = {
            'id': 'test-sprint',
            'document_type': 'sprint',
            'title': 'Test Sprint',
            'sprint_number': 1,
            'phases': [
                {
                    'phase': 0,
                    'name': 'Setup',
                    'status': 'completed',
                    'tasks': ['Task 1', 'Task 2']
                }
            ],
            'team': [
                {'role': 'lead', 'agent': 'pm_agent'}
            ]
        }
        
        with open(test_file, 'w') as f:
            import yaml
            yaml.dump(test_data, f)
        
        # Process document
        success = builder.process_document(test_file)
        
        assert success is True
        
        # Check multiple queries were made
        assert mock_session.run.call_count > 1
        
        # Check cache was updated
        assert str(test_file) in builder.processed_docs


class TestGraphRAGIntegration:
    """Test GraphRAG integration"""
    
    @pytest.fixture
    def graphrag(self):
        """Create GraphRAG instance"""
        return GraphRAGIntegration()
    
    def test_extract_reasoning_path(self, graphrag):
        """Test reasoning path extraction"""
        neighborhood = {
            'nodes': {
                'doc1': {'document_type': 'design'},
                'doc2': {'document_type': 'design'},
                'doc3': {'document_type': 'sprint'}
            },
            'relationships': [
                {'type': 'IMPLEMENTS', 'source': 'doc1', 'target': 'doc2'},
                {'type': 'IMPLEMENTS', 'source': 'doc2', 'target': 'doc3'},
                {'type': 'REFERENCES', 'source': 'doc1', 'target': 'doc3'}
            ],
            'paths': [
                {'nodes': ['doc1', 'doc2'], 'distance': 1},
                {'nodes': ['doc1', 'doc3'], 'distance': 1}
            ]
        }
        
        reasoning = graphrag._extract_reasoning_path(neighborhood)
        
        assert len(reasoning) > 0
        assert any('3 related documents' in r for r in reasoning)
        assert any('2 IMPLEMENTS' in r for r in reasoning)
        assert any('Average connection distance' in r for r in reasoning)
    
    @patch('graphrag_integration.QdrantClient')
    @patch('graphrag_integration.GraphDatabase.driver')
    def test_search(self, mock_neo4j, mock_qdrant, graphrag):
        """Test GraphRAG search"""
        # Setup mocks
        mock_qdrant_instance = Mock()
        mock_qdrant.return_value = mock_qdrant_instance
        
        mock_neo4j_instance, mock_session = create_mock_neo4j_driver()
        mock_neo4j.return_value = mock_neo4j_instance
        
        graphrag.qdrant_client = mock_qdrant_instance
        graphrag.neo4j_driver = mock_neo4j_instance
        
        # Mock vector search results
        mock_vector_result = Mock()
        mock_vector_result.id = 'vec1'
        mock_vector_result.score = 0.85
        mock_vector_result.payload = {
            'document_id': 'doc1',
            'document_type': 'design',
            'title': 'Test Design',
            'file_path': '/test.yaml'
        }
        
        mock_qdrant_instance.search.return_value = [mock_vector_result]
        
        # Mock graph results
        mock_session.run.return_value = []
        
        # Perform search
        query = "test query"
        query_vector = [0.1] * 1536
        
        result = graphrag.search(query, query_vector, max_hops=2, top_k=5)
        
        assert isinstance(result, GraphRAGResult)
        assert result.query == query
        assert len(result.vector_results) == 1
        assert result.vector_results[0]['document_id'] == 'doc1'
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0
    
    def test_analyze_document_impact(self, graphrag):
        """Test document impact analysis"""
        with patch.object(graphrag, 'neo4j_driver') as mock_driver:
            mock_session = Mock()
            mock_driver.session.return_value.__enter__.return_value = mock_session
            
            # Mock direct connections query
            mock_result1 = Mock()
            mock_result1.single.return_value = {
                'direct_count': 5,
                'connections': [
                    {'id': 'doc2', 'type': 'design', 'relationship': 'IMPLEMENTS'},
                    {'id': 'doc3', 'type': 'sprint', 'relationship': 'REFERENCES'}
                ]
            }
            
            # Mock reachability query
            mock_result2 = Mock()
            mock_result2.single.return_value = {'total': 15}
            
            # Mock dependency chain query
            mock_session.run.side_effect = [mock_result1, mock_result2, []]
            
            impact = graphrag.analyze_document_impact('doc1')
            
            assert impact['document_id'] == 'doc1'
            assert impact['direct_connections'] == 5
            assert impact['total_reachable'] == 15
            assert impact['central_score'] == 5 / 15
            assert len(impact['impacted_documents']) == 2