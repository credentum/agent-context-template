"""Comprehensive tests for CleanupAgent to improve coverage"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta
import yaml
import json
from typing import Dict, Any

from src.agents.cleanup_agent import CleanupAgent


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "storage": {
            "retention_days": 90
        },
        "agents": {
            "cleanup": {
                "expire_after_days": 30
            },
            "cleanup_agent": {
                "archive_path": "context/archive",
                "log_retention_days": 30,
                "enable_auto_archive": True,
                "enable_orphan_cleanup": True,
                "enable_log_rotation": True
            }
        },
        "evaluation": {
            "thresholds": {
                "sprint_expiration_days": 21,
                "document_expiration_days": 180,
                "min_progress_threshold": 20
            }
        }
    }


@pytest.fixture
def cleanup_agent(tmp_path, mock_config):
    """Create CleanupAgent instance with mocked config"""
    # Create config file in temp directory
    config_file = tmp_path / ".ctxrc.yaml"
    config_file.write_text(yaml.dump(mock_config))
    
    # Create necessary directories
    (tmp_path / "context").mkdir()
    (tmp_path / "context/archive").mkdir()
    (tmp_path / "context/logs").mkdir()
    (tmp_path / "context/sprints").mkdir()
    (tmp_path / "context/decisions").mkdir()
    
    # Change to the temp directory
    original_cwd = Path.cwd()
    import os
    os.chdir(tmp_path)
    
    try:
        # Create agent (it will load .ctxrc.yaml from current directory)
        agent = CleanupAgent(dry_run=False, verbose=True)
        # Override paths to use temp directory
        agent.context_dir = tmp_path / "context"
        agent.archive_dir = tmp_path / "context" / "archive"
        agent.cleanup_log_path = tmp_path / "context" / "logs" / "cleanup.yaml"
        yield agent
    finally:
        os.chdir(original_cwd)


class TestCleanupAgentCoverage:
    """Comprehensive tests for CleanupAgent"""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default configuration"""
        original_cwd = Path.cwd()
        import os
        os.chdir(tmp_path)
        
        try:
            # Create empty config file
            (tmp_path / ".ctxrc.yaml").write_text("{}")
            agent = CleanupAgent()
            assert agent.config == {}
            assert agent.archive_dir == Path("context/archive")
        finally:
            os.chdir(original_cwd)
    
    def test_load_config_file_not_found(self, tmp_path):
        """Test config loading when file doesn't exist"""
        original_cwd = Path.cwd()
        import os
        os.chdir(tmp_path)
        
        try:
            # Don't create .ctxrc.yaml - it should use defaults
            agent = CleanupAgent(verbose=True)
            # Check it loaded default config
            assert "storage" in agent.config or "agents" in agent.config
        finally:
            os.chdir(original_cwd)
    
    def test_should_archive_expired(self, cleanup_agent, tmp_path):
        """Test document expiration logic"""
        # Test expired document
        expired_doc = {
            "expires": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": "active"
        }
        doc_path = tmp_path / "test.yaml"
        should_archive, reason = cleanup_agent._should_archive(doc_path, expired_doc)
        assert should_archive is True
        assert "expired" in reason
        
        # Test non-expired document
        future_doc = {
            "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "status": "active"
        }
        should_archive, reason = cleanup_agent._should_archive(doc_path, future_doc)
        assert should_archive is False
        
        # Test deprecated old document
        deprecated_doc = {
            "status": "deprecated",
            "last_modified": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        }
        should_archive, reason = cleanup_agent._should_archive(doc_path, deprecated_doc)
        assert should_archive is True
        assert "Deprecated" in reason
    
    def test_should_archive_retention_policy(self, cleanup_agent, tmp_path):
        """Test retention policy logic"""
        # Test document not referenced for long time
        old_ref_doc = {
            "last_referenced": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d"),
            "status": "active"
        }
        doc_path = tmp_path / "test.yaml"
        should_archive, reason = cleanup_agent._should_archive(doc_path, old_ref_doc)
        assert should_archive is True
        assert "retention" in reason
        
        # Test recently referenced document
        recent_ref_doc = {
            "last_referenced": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            "status": "active"
        }
        should_archive, reason = cleanup_agent._should_archive(doc_path, recent_ref_doc)
        assert should_archive is False
    
    def test_archive_document(self, cleanup_agent, tmp_path):
        """Test archiving a document"""
        # Create test document
        doc_path = tmp_path / "context" / "test.yaml"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_content = {"id": "test-001", "content": "test data"}
        doc_path.write_text(yaml.dump(doc_content))
        
        # Archive the document
        result = cleanup_agent.archive_document(doc_path)
        assert result is True
        
        # Check original file is gone
        assert not doc_path.exists()
        
        # Check archived file exists in date-based subdirectory
        archive_subdir = cleanup_agent.archive_dir / datetime.now().strftime("%Y-%m")
        archived_file = archive_subdir / "test.yaml"
        assert archived_file.exists()
        
        # Verify content preserved
        with open(archived_file) as f:
            archived_content = yaml.safe_load(f)
        assert archived_content == doc_content
    
    def test_archive_document_dry_run(self, cleanup_agent, tmp_path):
        """Test dry run mode doesn't actually archive"""
        cleanup_agent.dry_run = True
        
        # Create test document
        doc_path = tmp_path / "context" / "test.yaml"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(yaml.dump({"id": "test-001"}))
        
        # Try to archive in dry run mode
        result = cleanup_agent.archive_document(doc_path)
        assert result is True
        
        # File should still exist
        assert doc_path.exists()
        
        # No archived file should be created
        archive_files = list(cleanup_agent.archive_dir.rglob("*.yaml"))
        assert len(archive_files) == 0
    
    def test_clean_logs(self, cleanup_agent, tmp_path):
        """Test log cleaning functionality"""
        # Create prompts log directory structure
        prompts_dir = tmp_path / "context" / "logs" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Create old and recent date directories
        old_date = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
        recent_date = datetime.now().strftime("%Y-%m-%d")
        
        old_dir = prompts_dir / old_date
        recent_dir = prompts_dir / recent_date
        
        old_dir.mkdir()
        recent_dir.mkdir()
        
        # Add log files to directories
        (old_dir / "prompt.log").write_text("old log")
        (recent_dir / "prompt.log").write_text("new log")
        
        # Clean logs
        cleanup_agent.clean_logs()
        
        # Old directory should be removed
        assert not old_dir.exists()
        assert recent_dir.exists()
    
    def test_log_action(self, cleanup_agent, tmp_path):
        """Test action logging"""
        test_file = tmp_path / "test.yaml"
        
        # Log an action
        cleanup_agent._log_action("archive", test_file, "File expired")
        
        # Check action was recorded
        assert len(cleanup_agent.actions) == 1
        action = cleanup_agent.actions[0]
        assert action["action"] == "archive"
        assert str(test_file) in action["file"]
        assert action["reason"] == "File expired"
        assert "timestamp" in action
    
    def test_process_context_files(self, cleanup_agent, tmp_path):
        """Test processing context files for cleanup"""
        # Create test files with expiration dates
        expired_doc = tmp_path / "context" / "decisions" / "old_decision.yaml"
        expired_doc.parent.mkdir(parents=True, exist_ok=True)
        expired_doc.write_text(yaml.dump({
            "document_type": "decision",
            "expires": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": "active"
        }))
        
        # Create a document that should not be archived
        active_doc = tmp_path / "context" / "decisions" / "active_decision.yaml"
        active_doc.write_text(yaml.dump({
            "document_type": "decision",
            "expires": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "status": "active"
        }))
        
        with patch('click.echo'):
            cleanup_agent.process_context_files()
        
        # Expired document should be archived
        assert not expired_doc.exists()
        # Active document should still exist
        assert active_doc.exists()
        
        # Check archived file exists in date subdirectory
        archive_subdir = cleanup_agent.archive_dir / datetime.now().strftime("%Y-%m")
        assert (archive_subdir / "old_decision.yaml").exists()
    
    def test_handle_yaml_error(self, cleanup_agent, tmp_path):
        """Test handling of invalid YAML files"""
        invalid_yaml = tmp_path / "context" / "invalid.yaml"
        invalid_yaml.parent.mkdir(parents=True, exist_ok=True)
        invalid_yaml.write_text("{ invalid yaml content :")
        
        # Should not crash when processing invalid YAML
        with patch('click.echo'):
            cleanup_agent.process_context_files()
    
    def test_write_cleanup_log(self, cleanup_agent, tmp_path):
        """Test writing cleanup log"""
        # Add some actions
        cleanup_agent._log_action("archive", tmp_path / "file1.yaml", "Expired")
        cleanup_agent._log_action("clean", tmp_path / "file2.log", "Old log")
        
        # Write log
        cleanup_agent.write_cleanup_log()
        
        # Check log file exists
        assert cleanup_agent.cleanup_log_path.exists()
        
        # Verify log content
        with open(cleanup_agent.cleanup_log_path) as f:
            log_data = yaml.safe_load(f)
        
        assert "cleanup_runs" in log_data
        assert len(log_data["cleanup_runs"]) > 0
        
        latest_run = log_data["cleanup_runs"][-1]
        assert len(latest_run["actions"]) == 2
    
    def test_archive_with_metadata(self, cleanup_agent, tmp_path):
        """Test archiving with metadata preservation"""
        test_file = tmp_path / "context" / "test_with_meta.yaml"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        original_data = {
            "id": "test-001",
            "created_date": "2024-01-01",
            "content": "test content"
        }
        test_file.write_text(yaml.dump(original_data))
        
        cleanup_agent.archive_document(test_file)
        
        # Check archived file preserves content
        archive_subdir = cleanup_agent.archive_dir / datetime.now().strftime("%Y-%m")
        archive_file = archive_subdir / "test_with_meta.yaml"
        
        with open(archive_file) as f:
            archived_data = yaml.safe_load(f)
        
        assert archived_data == original_data
    
    def test_run_method(self, cleanup_agent):
        """Test the main run method"""
        with patch('click.echo'):
            with patch.object(cleanup_agent, 'process_context_files') as mock_process:
                with patch.object(cleanup_agent, 'clean_logs') as mock_logs:
                    with patch.object(cleanup_agent, 'write_cleanup_log') as mock_write_log:
                        cleanup_agent.run()
                        
                        mock_process.assert_called_once()
                        mock_logs.assert_called_once()
                        mock_write_log.assert_called_once()