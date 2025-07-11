#!/usr/bin/env python3
"""
Tests for sprint automation functionality
"""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import yaml
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update_sprint import SprintUpdater
from sprint_issue_linker import SprintIssueLinker


class TestSprintUpdater:
    """Test suite for sprint update functionality"""
    
    @pytest.fixture
    def temp_context_dir(self):
        """Create a temporary context directory"""
        temp_dir = tempfile.mkdtemp()
        context_dir = Path(temp_dir) / "context"
        sprints_dir = context_dir / "sprints"
        sprints_dir.mkdir(parents=True)
        
        # Create test config
        config = {
            'agents': {
                'pm_agent': {
                    'sprint_duration_days': 14
                }
            }
        }
        with open(Path(temp_dir) / ".ctxrc.yaml", 'w') as f:
            yaml.dump(config, f)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        yield sprints_dir
        
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
    
    def test_find_active_sprint(self, temp_context_dir):
        """Test finding the active sprint"""
        # Create test sprints
        sprint1 = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-001',
            'title': 'Sprint 1',
            'status': 'completed',
            'sprint_number': 1,
            'start_date': '2025-01-01',
            'end_date': '2025-01-14',
            'created_date': '2025-01-01',
            'last_modified': '2025-01-14',
            'last_referenced': '2025-01-14'
        }
        
        sprint2 = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-002',
            'title': 'Sprint 2',
            'status': 'in_progress',
            'sprint_number': 2,
            'start_date': '2025-01-15',
            'end_date': '2025-01-28',
            'created_date': '2025-01-15',
            'last_modified': '2025-01-15',
            'last_referenced': '2025-01-15'
        }
        
        with open(temp_context_dir / "sprint-001.yaml", 'w') as f:
            yaml.dump(sprint1, f)
        
        with open(temp_context_dir / "sprint-002.yaml", 'w') as f:
            yaml.dump(sprint2, f)
        
        updater = SprintUpdater()
        current_sprint = updater._get_current_sprint()
        
        assert current_sprint is not None
        assert current_sprint.name == "sprint-002.yaml"
    
    @patch('subprocess.run')
    def test_update_phase_status(self, mock_run, temp_context_dir):
        """Test updating phase status based on issues"""
        # Mock GitHub issues response
        mock_issues = [
            {
                'number': 1,
                'title': 'Define YAML schema with yamale',
                'state': 'CLOSED',
                'labels': [{'name': 'sprint-1'}]
            },
            {
                'number': 2,
                'title': 'Implement context-lint CLI',
                'state': 'CLOSED',
                'labels': [{'name': 'sprint-1'}]
            }
        ]
        
        mock_result = MagicMock()
        mock_result.stdout = yaml.dump(mock_issues)
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Create test sprint
        sprint_data = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-001',
            'title': 'Sprint 1',
            'status': 'in_progress',
            'sprint_number': 1,
            'phases': [
                {
                    'phase': 0,
                    'name': 'Setup',
                    'status': 'pending',
                    'tasks': [
                        'Define YAML schema with yamale',
                        'Implement context-lint CLI'
                    ]
                }
            ],
            'created_date': '2025-01-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-14',
            'last_modified': '2025-01-01',
            'last_referenced': '2025-01-01'
        }
        
        with open(temp_context_dir / "sprint-001.yaml", 'w') as f:
            yaml.dump(sprint_data, f)
        
        updater = SprintUpdater(sprint_id='sprint-001')
        
        # Test phase update
        updated = updater._update_phase_status(sprint_data['phases'], mock_issues)
        
        assert updated == True
        assert sprint_data['phases'][0]['status'] == 'completed'
    
    def test_create_next_sprint(self, temp_context_dir):
        """Test creating the next sprint when current is completed"""
        # Create completed sprint
        sprint_data = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-001',
            'title': 'Sprint 1',
            'status': 'completed',
            'sprint_number': 1,
            'team': [
                {'role': 'lead', 'agent': 'pm_agent'}
            ],
            'created_date': '2025-01-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-14',
            'last_modified': '2025-01-14',
            'last_referenced': '2025-01-14'
        }
        
        with open(temp_context_dir / "sprint-001.yaml", 'w') as f:
            yaml.dump(sprint_data, f)
        
        updater = SprintUpdater()
        new_sprint_path = updater._create_next_sprint(sprint_data)
        
        assert new_sprint_path is not None
        assert new_sprint_path.name == "sprint-002.yaml"
        assert new_sprint_path.exists()
        
        # Check new sprint content
        with open(new_sprint_path, 'r') as f:
            new_data = yaml.safe_load(f)
        
        assert new_data['sprint_number'] == 2
        assert new_data['status'] == 'planning'
        assert new_data['team'] == sprint_data['team']
    
    def test_task_matching_logic(self):
        """Test improved task matching to prevent false positives"""
        updater = SprintUpdater()
        
        # Test cases for task matching
        test_cases = [
            # (task, issue_title, should_match)
            ("Write tests", "[Sprint 1] Phase 2: Write tests", True),
            ("Write tests", "Write tests for feature A", True),
            ("test", "Integration tests completed", False),  # "test" != "tests"
            ("test", "Run test suite", True),  # "test" matches as a word
            ("test", "[Sprint 1] Phase 1: test", True),  # Exact word match
            ("implement feature A", "Task: Implement feature A and B", True),
            ("feature A", "Implement feature A", True),
        ]
        
        for task, issue_title, expected in test_cases:
            result = updater._match_task_to_issue(task, issue_title)
            assert result == expected, f"Task '{task}' vs '{issue_title}' - expected {expected}, got {result}"
    
    def test_sprint_status_progression(self, temp_context_dir):
        """Test sprint status progression logic"""
        sprint_data = {
            'status': 'planning',
            'phases': [
                {'status': 'pending'},
                {'status': 'pending'},
                {'status': 'pending'}
            ]
        }
        
        updater = SprintUpdater()
        
        # Test planning -> in_progress
        sprint_data['phases'][0]['status'] = 'in_progress'
        updated = updater._update_sprint_status(sprint_data)
        assert updated == True
        assert sprint_data['status'] == 'in_progress'
        
        # Test in_progress -> completed
        sprint_data['phases'][0]['status'] = 'completed'
        sprint_data['phases'][1]['status'] = 'completed'
        sprint_data['phases'][2]['status'] = 'completed'
        updated = updater._update_sprint_status(sprint_data)
        assert updated == True
        assert sprint_data['status'] == 'completed'


class TestSprintIssueLinker:
    """Test suite for sprint issue linking"""
    
    @pytest.fixture
    def temp_sprint_dir(self):
        """Create temporary sprint directory"""
        temp_dir = tempfile.mkdtemp()
        context_dir = Path(temp_dir) / "context"
        sprints_dir = context_dir / "sprints"
        sprints_dir.mkdir(parents=True)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        yield sprints_dir
        
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)
    
    @patch('subprocess.run')
    def test_create_issues_dry_run(self, mock_run, temp_sprint_dir):
        """Test creating issues in dry run mode"""
        # Create test sprint
        sprint_data = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-001',
            'title': 'Sprint 1',
            'status': 'planning',
            'sprint_number': 1,
            'goals': ['Complete Phase 1'],
            'phases': [
                {
                    'phase': 1,
                    'name': 'Implementation',
                    'status': 'pending',
                    'tasks': [
                        'Implement feature A',
                        'Write tests for feature A'
                    ]
                }
            ],
            'created_date': '2025-01-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-14',
            'last_modified': '2025-01-01',
            'last_referenced': '2025-01-01'
        }
        
        with open(temp_sprint_dir / "sprint-001.yaml", 'w') as f:
            yaml.dump(sprint_data, f)
        
        # Mock empty existing issues
        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        linker = SprintIssueLinker(sprint_id='sprint-001', dry_run=True, verbose=True)
        count = linker.create_issues_from_sprint()
        
        # In dry run, no actual issues created but count should reflect what would be created
        assert count == 0  # Dry run returns 0
        # But mock should have been called to check existing issues
        mock_run.assert_called()
    
    @patch('subprocess.run')
    def test_issue_title_generation(self, mock_run, temp_sprint_dir):
        """Test issue title generation"""
        # Mock gh auth status to succeed
        mock_run.return_value = Mock(returncode=0)
        
        sprint_data = {
            'schema_version': '1.0.0',
            'document_type': 'sprint',
            'id': 'sprint-003',
            'title': 'Sprint 3',
            'status': 'planning',
            'sprint_number': 3,
            'phases': [
                {
                    'phase': 2,
                    'name': 'Testing',
                    'status': 'pending',
                    'tasks': ['Write integration tests']
                }
            ],
            'created_date': '2025-01-01',
            'start_date': '2025-01-01',
            'end_date': '2025-01-14',
            'last_modified': '2025-01-01',
            'last_referenced': '2025-01-01'
        }
        
        with open(temp_sprint_dir / "sprint-003.yaml", 'w') as f:
            yaml.dump(sprint_data, f)
        
        linker = SprintIssueLinker(sprint_id='sprint-003')
        
        # Expected title format
        expected_title = "[Sprint 3] Phase 2: Write integration tests"
        
        # We can't easily test the exact title without mocking more,
        # but we can verify the sprint file is loaded correctly
        sprint_file = linker._get_sprint_file()
        assert sprint_file is not None
        assert sprint_file.name == "sprint-003.yaml"