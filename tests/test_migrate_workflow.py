"""Tests for workflow migration tool"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from migrate_workflow import WorkflowMigrator  # noqa: E402


class TestWorkflowMigrator:
    """Test the workflow migration tool"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.workflows_dir = Path(self.temp_dir) / ".github" / "workflows"
        self.workflows_dir.mkdir(parents=True)
        self.migrator = WorkflowMigrator(str(self.workflows_dir))

    def create_test_workflow(self, name: str, content: dict) -> Path:
        """Create a test workflow file"""
        workflow_path = self.workflows_dir / f"{name}.yml"
        with open(workflow_path, "w") as f:
            yaml.dump(content, f)
        return workflow_path

    def test_init(self):
        """Test migrator initialization"""
        assert self.migrator.workflows_dir == self.workflows_dir
        assert self.migrator.backup_dir == self.workflows_dir / "backup"
        assert "verify-ci-results" in self.migrator.verifier_job_template

    def test_parse_workflow(self):
        """Test workflow parsing"""
        test_workflow = {
            "name": "Test",
            "on": "push",
            "jobs": {"test": {"runs-on": "ubuntu-latest"}},
        }
        workflow_path = self.create_test_workflow("test", test_workflow)

        parsed = self.migrator.parse_workflow(workflow_path)
        assert parsed["name"] == "Test"
        assert "jobs" in parsed

    def test_identify_ci_jobs(self):
        """Test CI job identification"""
        workflow = {
            "jobs": {
                "test": {"name": "Run tests"},
                "lint": {"name": "Check code"},
                "deploy": {"name": "Deploy to prod"},
                "validate": {"steps": [{"name": "Validate configs"}]},
            }
        }

        ci_jobs = self.migrator.identify_ci_jobs(workflow)
        assert "test" in ci_jobs
        assert "lint" in ci_jobs
        assert "validate" in ci_jobs
        assert "deploy" not in ci_jobs

    def test_add_verifier_pattern(self):
        """Test adding verifier pattern to workflow"""
        workflow = {
            "jobs": {"test": {"runs-on": "ubuntu-latest"}, "lint": {"runs-on": "ubuntu-latest"}}
        }
        ci_jobs = ["test", "lint"]

        migrated = self.migrator.add_verifier_pattern(workflow, ci_jobs)

        # Check environment variable added
        assert "env" in migrated
        assert "CI_MIGRATION_MODE" in migrated["env"]

        # Check verifier job added
        assert "verify-ci-results" in migrated["jobs"]
        assert migrated["jobs"]["verify-ci-results"]["needs"] == ci_jobs

        # Check CI jobs have conditions
        assert "if" in migrated["jobs"]["test"]
        assert "verifier-only" in migrated["jobs"]["test"]["if"]

    def test_migrate_workflow_dry_run(self):
        """Test workflow migration in dry run mode"""
        test_workflow = {
            "name": "Test",
            "jobs": {"test": {"runs-on": "ubuntu-latest"}, "check": {"runs-on": "ubuntu-latest"}},
        }
        workflow_path = self.create_test_workflow("test", test_workflow)

        result = self.migrator.migrate_workflow(workflow_path, dry_run=True)
        assert result is None  # Dry run returns None

        # Original file should be unchanged
        with open(workflow_path) as f:
            content = yaml.safe_load(f)
        assert "verify-ci-results" not in content.get("jobs", {})

    def test_migrate_workflow_actual(self):
        """Test actual workflow migration"""
        test_workflow = {
            "name": "Test",
            "jobs": {"test": {"runs-on": "ubuntu-latest"}, "lint": {"runs-on": "ubuntu-latest"}},
        }
        workflow_path = self.create_test_workflow("test", test_workflow)

        result = self.migrator.migrate_workflow(workflow_path, dry_run=False)
        assert result == workflow_path

        # Check backup created
        assert len(list(self.migrator.backup_dir.glob("*.backup.*.yml"))) == 1

        # Check workflow updated
        with open(workflow_path) as f:
            content = yaml.safe_load(f)
        assert "verify-ci-results" in content.get("jobs", {})

        # Check monitoring config created
        monitoring_files = list(self.workflows_dir.glob(".*.monitoring.json"))
        assert len(monitoring_files) == 1

    def test_migrate_workflow_already_migrated(self):
        """Test migrating already migrated workflow"""
        test_workflow = {
            "name": "Test",
            "jobs": {
                "test": {"runs-on": "ubuntu-latest"},
                "verify-ci-results": {"runs-on": "ubuntu-latest"},
            },
        }
        workflow_path = self.create_test_workflow("test", test_workflow)

        result = self.migrator.migrate_workflow(workflow_path, dry_run=False)
        assert result is None  # Should skip already migrated

    def test_create_verifier_action(self):
        """Test creating verifier composite action"""
        action_dir = Path(self.temp_dir) / ".github" / "actions" / "verify-ci-results"

        with patch("pathlib.Path.cwd", return_value=Path(self.temp_dir)):
            self.migrator.create_verifier_action()

        action_file = action_dir / "action.yml"
        assert action_file.exists()

        with open(action_file) as f:
            action_content = yaml.safe_load(f)

        assert action_content["name"] == "Verify CI Results"
        assert "inputs" in action_content
        assert "runs" in action_content
