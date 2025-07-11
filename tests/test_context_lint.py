#!/usr/bin/env python3
"""
Tests for context-lint validation system
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml
from context_lint import ContextLinter


class TestContextLint:
    """Test suite for context lint functionality"""
    
    @pytest.fixture
    def temp_context_dir(self):
        """Create a temporary context directory for testing"""
        temp_dir = tempfile.mkdtemp()
        context_dir = Path(temp_dir) / "context"
        
        # Copy schemas
        schema_src = Path(__file__).parent.parent / "context" / "schemas"
        schema_dst = context_dir / "schemas"
        shutil.copytree(schema_src, schema_dst)
        
        # Copy full schema files to project root schemas dir for tests
        root_schema_dir = Path(temp_dir) / "context" / "schemas"
        for schema_name in ['design_full.yaml', 'decision_full.yaml', 'sprint_full.yaml']:
            src = Path(__file__).parent.parent / "context" / "schemas" / schema_name
            if src.exists():
                dst = root_schema_dir / schema_name
                shutil.copy(src, dst)
        
        yield context_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_valid_design_document(self, temp_context_dir):
        """Test validation of a valid design document"""
        linter = ContextLinter()
        
        # Create valid design document
        design_doc = {
            'schema_version': '1.0.0',
            'document_type': 'design',
            'id': 'test-design',
            'title': 'Test Design Document',
            'status': 'active',
            'created_date': '2025-07-11',
            'last_modified': '2025-07-11',
            'last_referenced': '2025-07-11',
            'content': 'This is a test design document.'
        }
        
        doc_path = temp_context_dir / "design" / "test.yaml"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(doc_path, 'w') as f:
            yaml.dump(design_doc, f)
        
        assert linter.validate_file(doc_path) == True
        assert len(linter.errors) == 0
    
    def test_invalid_schema_version(self, temp_context_dir):
        """Test validation fails with invalid schema version"""
        linter = ContextLinter()
        
        # Create document with invalid schema version
        doc = {
            'schema_version': '1.0',  # Invalid format
            'document_type': 'design',
            'id': 'test-design',
            'title': 'Test',
            'status': 'active',
            'created_date': '2025-07-11',
            'last_modified': '2025-07-11',
            'last_referenced': '2025-07-11',
            'content': 'Test content'
        }
        
        doc_path = temp_context_dir / "test.yaml"
        with open(doc_path, 'w') as f:
            yaml.dump(doc, f)
        
        assert linter.validate_file(doc_path) == False
        assert len(linter.errors) > 0
    
    def test_missing_required_field(self, temp_context_dir):
        """Test validation fails when required field is missing"""
        linter = ContextLinter()
        
        # Create document missing 'title' field
        doc = {
            'schema_version': '1.0.0',
            'document_type': 'design',
            'id': 'test-design',
            # 'title' is missing
            'status': 'active',
            'created_date': '2025-07-11',
            'last_modified': '2025-07-11',
            'last_referenced': '2025-07-11',
            'content': 'Test content'
        }
        
        doc_path = temp_context_dir / "test.yaml"
        with open(doc_path, 'w') as f:
            yaml.dump(doc, f)
        
        assert linter.validate_file(doc_path) == False
        assert any('title' in error for error in linter.errors)
    
    def test_auto_fix_timestamps(self, temp_context_dir):
        """Test auto-fix functionality for timestamps"""
        linter = ContextLinter()
        
        # Create document with old timestamps
        doc = {
            'schema_version': '1.0.0',
            'document_type': 'design',
            'id': 'test-design',
            'title': 'Test Design',
            'status': 'active',
            'created_date': '2025-01-01',
            'last_modified': '2025-01-01',
            'last_referenced': '2025-01-01',
            'content': 'Test content'
        }
        
        doc_path = temp_context_dir / "test.yaml"
        with open(doc_path, 'w') as f:
            yaml.dump(doc, f)
        
        # Validate with fix enabled
        assert linter.validate_file(doc_path, fix=True) == True
        assert linter.fixed_count == 1
        
        # Load fixed document
        with open(doc_path, 'r') as f:
            fixed_doc = yaml.safe_load(f)
        
        # Check timestamps were updated
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        assert fixed_doc['last_modified'] == today
        assert fixed_doc['last_referenced'] == today
    
    def test_expiration_warning(self, temp_context_dir):
        """Test warning for documents about to expire"""
        linter = ContextLinter()
        
        from datetime import datetime, timedelta
        expire_soon = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        doc = {
            'schema_version': '1.0.0',
            'document_type': 'design',
            'id': 'test-design',
            'title': 'Test Design',
            'status': 'active',
            'created_date': '2025-07-11',
            'last_modified': '2025-07-11',
            'last_referenced': '2025-07-11',
            'expires': expire_soon,
            'content': 'Test content'
        }
        
        doc_path = temp_context_dir / "test.yaml"
        with open(doc_path, 'w') as f:
            yaml.dump(doc, f)
        
        assert linter.validate_file(doc_path) == True
        assert len(linter.warnings) > 0
        assert any('expires' in warning for warning in linter.warnings)
    
    def test_validate_sprint_document(self, temp_context_dir):
        """Test validation of sprint document with complex schema"""
        linter = ContextLinter()
        
        sprint_doc = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-002',
            'title': 'Test Sprint',
            'status': 'planning',
            'created_date': '2025-07-11',
            'last_modified': '2025-07-11',
            'last_referenced': '2025-07-11',
            'sprint_number': 2,
            'start_date': '2025-07-15',
            'end_date': '2025-07-29',
            'goals': ['Goal 1', 'Goal 2'],
            'phases': [{
                'phase': 0,
                'name': 'Setup',
                'duration_days': 2,
                'status': 'pending',
                'tasks': ['Task 1', 'Task 2']
            }],
            'success_metrics': [{
                'metric': 'test_coverage',
                'target': 90.0,
                'unit': 'percent'
            }]
        }
        
        doc_path = temp_context_dir / "sprints" / "sprint-002.yaml"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(doc_path, 'w') as f:
            yaml.dump(sprint_doc, f)
        
        assert linter.validate_file(doc_path) == True
        assert len(linter.errors) == 0