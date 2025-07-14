#!/usr/bin/env python3
"""
Smoke tests for directory structure validation
"""

from pathlib import Path

import pytest


class TestDirectoryStructure:
    """Test suite for validating context directory structure"""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory"""
        return Path(__file__).parent.parent

    def test_context_directory_exists(self, project_root):
        """Test that main context directory exists"""
        context_dir = project_root / "context"
        assert context_dir.exists()
        assert context_dir.is_dir()

    def test_required_subdirectories(self, project_root):
        """Test all required subdirectories exist"""
        context_dir = project_root / "context"
        required_dirs = [
            "design",
            "decisions",
            "trace",
            "sprints",
            "logs",
            "archive",
            "mcp_contracts",
            "schemas",
        ]

        for dir_name in required_dirs:
            subdir = context_dir / dir_name
            assert subdir.exists(), f"Missing required directory: context/{dir_name}"
            assert subdir.is_dir(), f"context/{dir_name} is not a directory"

    def test_log_subdirectories(self, project_root):
        """Test log subdirectories exist"""
        logs_dir = project_root / "context" / "logs"
        log_subdirs = ["cleanup", "eval", "prompts", "signatures", "kv"]

        for subdir_name in log_subdirs:
            subdir = logs_dir / subdir_name
            assert subdir.exists(), f"Missing log subdirectory: {subdir_name}"

    def test_schema_files_exist(self, project_root):
        """Test that schema files are present"""
        schemas_dir = project_root / "context" / "schemas"
        required_schemas = ["base.yaml", "design.yaml", "decision.yaml", "sprint.yaml"]

        for schema_file in required_schemas:
            schema_path = schemas_dir / schema_file
            assert schema_path.exists(), f"Missing schema file: {schema_file}"
            assert schema_path.is_file()

            # Verify it's valid YAML
            with open(schema_path, "r") as f:
                content = f.read()
                assert len(content) > 0, f"Schema file {schema_file} is empty"

    def test_config_file_exists(self, project_root):
        """Test that .ctxrc.yaml configuration exists"""
        config_path = project_root / ".ctxrc.yaml"
        assert config_path.exists()
        assert config_path.is_file()

        # Verify it's valid YAML
        import yaml

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            assert config is not None
            assert "system" in config
            assert "qdrant" in config

    def test_documentation_files(self, project_root):
        """Test that documentation files exist"""
        # Main README
        assert (project_root / "README.md").exists()

        # Context README
        context_readme = project_root / "context" / "README.md"
        assert context_readme.exists()

        # CLAUDE.md
        assert (project_root / "CLAUDE.md").exists()

    def test_sample_documents(self, project_root):
        """Test that sample documents were created"""
        context_dir = project_root / "context"

        # Check for sample design document
        design_files = list((context_dir / "design").glob("*.yaml"))
        assert len(design_files) > 0, "No design documents found"

        # Check for sample decision document
        decision_files = list((context_dir / "decisions").glob("*.yaml"))
        assert len(decision_files) > 0, "No decision documents found"

        # Check for sample sprint document
        sprint_files = list((context_dir / "sprints").glob("*.yaml"))
        assert len(sprint_files) > 0, "No sprint documents found"

    def test_executable_scripts(self, project_root):
        """Test that Python scripts exist in src/agents/ directory"""
        scripts = [
            ("src/agents/context_lint.py", "context_lint.py"),
            ("src/agents/cleanup_agent.py", "cleanup_agent.py"),
        ]

        for script_path_str, script_name in scripts:
            script_path = project_root / script_path_str
            assert script_path.exists(), f"Missing script: {script_name} at {script_path_str}"
            assert script_path.is_file()

            # Check shebang
            with open(script_path, "r") as f:
                first_line = f.readline()
                assert first_line.startswith("#!/usr/bin/env python3")

    def test_src_directory_structure(self, project_root):
        """Test that src directory has proper structure"""
        src_dir = project_root / "src"
        assert src_dir.exists(), "Missing src directory"
        assert src_dir.is_dir()

        # Check for required subdirectories
        required_subdirs = ["agents", "core", "storage", "analytics", "integrations", "validators"]
        for subdir_name in required_subdirs:
            subdir = src_dir / subdir_name
            assert subdir.exists(), f"Missing src subdirectory: {subdir_name}"
            assert subdir.is_dir()

            # Check for __init__.py
            init_file = subdir / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in src/{subdir_name}"

    def test_github_workflows(self, project_root):
        """Test that GitHub Actions workflows exist"""
        workflows_dir = project_root / ".github" / "workflows"

        # Check for context-lint workflow
        context_lint_workflow = workflows_dir / "context-lint.yml"
        assert context_lint_workflow.exists()

        # Verify it's valid YAML
        import yaml

        with open(context_lint_workflow, "r") as f:
            workflow = yaml.safe_load(f)
            assert "name" in workflow
            assert workflow["name"] == "Context Lint"

    def test_gitignore_entries(self, project_root):
        """Test that .gitignore has proper entries"""
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists()

        with open(gitignore_path, "r") as f:
            content = f.read()

        # Check for important entries
        important_patterns = [
            "context/logs/**/*.log",
            "context/logs/**/*.yaml",
            "context/archive/**/*.yaml",
            "qdrant_storage/",
            "neo4j_data/",
        ]

        for pattern in important_patterns:
            assert pattern in content, f"Missing .gitignore pattern: {pattern}"
