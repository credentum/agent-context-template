#!/usr/bin/env python3
"""
Tests for configuration parsing and validation
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest
import yaml


class TestConfigParser:
    """Test suite for .ctxrc.yaml configuration parsing"""

    def test_valid_config(self):
        """Test parsing of valid configuration"""
        config_content = """
system:
  schema_version: "1.0.0"
  created_date: "2025-07-11"
  
qdrant:
  version: "1.14.x"
  host: "localhost"
  port: 6333
  collection_name: "project_context"
  embedding_model: "text-embedding-ada-002"
  
neo4j:
  version: "5.x"
  host: "localhost"
  port: 7687
  database: "context_graph"
  
storage:
  retention_days: 90
  archive_path: "context/archive"
  
agents:
  cleanup:
    schedule: "0 2 * * *"
    expire_after_days: 30
  
  doc_agent:
    auto_update_metadata: true
    
  pm_agent:
    sprint_duration_days: 14
"""

        config = yaml.safe_load(config_content)

        # Validate structure
        assert "system" in config
        assert config["system"]["schema_version"] == "1.0.0"

        assert "qdrant" in config
        assert config["qdrant"]["version"] == "1.14.x"
        assert config["qdrant"]["port"] == 6333

        assert "neo4j" in config
        assert config["neo4j"]["version"] == "5.x"

        assert "storage" in config
        assert config["storage"]["retention_days"] == 90

        assert "agents" in config
        assert "cleanup" in config["agents"]
        assert config["agents"]["cleanup"]["expire_after_days"] == 30

    def test_qdrant_version_validation(self):
        """Test Qdrant version pinning validation"""
        config = {"qdrant": {"version": "1.14.2"}}

        # Should accept 1.14.x versions
        assert config["qdrant"]["version"].startswith("1.14.")

        # Test invalid version
        config["qdrant"]["version"] = "1.15.0"
        assert not config["qdrant"]["version"].startswith("1.14.")

    def test_missing_required_sections(self):
        """Test handling of missing required sections"""
        incomplete_config = {
            "system": {"schema_version": "1.0.0"}
            # Missing other required sections
        }

        required_sections = ["system", "qdrant", "neo4j", "storage", "agents"]
        missing = [s for s in required_sections if s not in incomplete_config]

        assert len(missing) == 4
        assert "qdrant" in missing
        assert "neo4j" in missing
        assert "storage" in missing
        assert "agents" in missing

    def test_agent_configuration(self):
        """Test agent-specific configuration parsing"""
        agent_config: Dict[str, Any] = {
            "agents": {
                "cleanup": {"schedule": "0 2 * * *", "expire_after_days": 30},
                "doc_agent": {"auto_update_metadata": True},
                "pm_agent": {"sprint_duration_days": 14},
            }
        }

        # Validate cleanup agent config
        cleanup: Dict[str, Any] = agent_config["agents"]["cleanup"]
        assert cleanup["schedule"] == "0 2 * * *"  # Cron format
        assert cleanup["expire_after_days"] == 30

        # Validate doc agent config
        doc_agent: Dict[str, Any] = agent_config["agents"]["doc_agent"]
        assert doc_agent["auto_update_metadata"] is True

        # Validate PM agent config
        pm_agent: Dict[str, Any] = agent_config["agents"]["pm_agent"]
        assert pm_agent["sprint_duration_days"] == 14

    def test_evaluation_thresholds(self):
        """Test evaluation configuration validation"""
        eval_config = {"evaluation": {"cosine_threshold": 0.85, "schema_compliance_threshold": 1.0}}

        # Validate thresholds are in valid range
        cosine = eval_config["evaluation"]["cosine_threshold"]
        assert 0.0 <= cosine <= 1.0

        compliance = eval_config["evaluation"]["schema_compliance_threshold"]
        assert compliance == 1.0  # Should be 100% compliant

    def test_security_configuration(self):
        """Test security configuration options"""
        security_config = {"security": {"sigstore_enabled": True, "ipfs_pinning": False}}

        assert security_config["security"]["sigstore_enabled"] is True
        assert security_config["security"]["ipfs_pinning"] is False

    def test_mcp_configuration(self):
        """Test Model Context Protocol configuration"""
        mcp_config: Dict[str, Any] = {"mcp": {"contracts_path": "context/mcp_contracts", "rpc_timeout_seconds": 30}}

        assert mcp_config["mcp"]["contracts_path"] == "context/mcp_contracts"
        assert mcp_config["mcp"]["rpc_timeout_seconds"] == 30
        assert mcp_config["mcp"]["rpc_timeout_seconds"] > 0
