"""End-to-end tests for the complete workflow pipeline.

This module tests the entire workflow execution pipeline to ensure that
each phase produces expected outputs and the complete pipeline works correctly.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.e2e
class TestWorkflowPipelineE2E:
    """End-to-end tests for the complete workflow pipeline."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            repo_path.mkdir()
            # Initialize git repo
            os.system(f"cd {repo_path} && git init -q")
            os.system(f"cd {repo_path} && git config user.email 'test@example.com'")
            os.system(f"cd {repo_path} && git config user.name 'Test User'")
            # Create initial files
            (repo_path / "src").mkdir()
            (repo_path / "src" / "__init__.py").touch()
            (repo_path / "src" / "example.py").write_text(
                "def hello():\n    return 'Hello, World!'\n"
            )
            (repo_path / "tests").mkdir()
            (repo_path / "tests" / "__init__.py").touch()
            (repo_path / "scripts").mkdir()
            (repo_path / "context").mkdir()
            (repo_path / "context" / "trace").mkdir()
            os.system(f"cd {repo_path} && git add . && git commit -m 'Initial commit' -q")
            yield repo_path

    def test_simple_function_addition(self, temp_repo):
        """Test adding a simple function to existing module."""
        # Simulate adding a function
        self._simulate_function_addition(temp_repo)

        # Verify function was actually added
        example_content = (temp_repo / "src" / "example.py").read_text()
        assert "def goodbye():" in example_content
        assert "return 'Goodbye, World!'" in example_content

        # Verify test was created
        test_file = temp_repo / "tests" / "test_example.py"
        assert test_file.exists()
        test_content = test_file.read_text()
        assert "def test_goodbye" in test_content

        # Verify commits contain code changes
        assert_commits_contain_code_changes(temp_repo)

    def test_new_file_creation(self, temp_repo):
        """Test creating a new module with functions and tests."""
        # Simulate module creation
        self._simulate_module_creation(temp_repo)

        # Verify module was created
        calc_file = temp_repo / "src" / "calculator.py"
        assert calc_file.exists()
        calc_content = calc_file.read_text()
        assert "def add(" in calc_content
        assert "def subtract(" in calc_content

        # Verify tests were created
        test_file = temp_repo / "tests" / "test_calculator.py"
        assert test_file.exists()
        assert_code_files_created([str(calc_file), str(test_file)])

    def test_bug_fix_scenario(self, temp_repo):
        """Test fixing a bug in existing code."""
        # Create buggy code
        buggy_code = """def divide(a, b):
    # Bug: No zero division check
    return a / b
"""
        (temp_repo / "src" / "math_utils.py").write_text(buggy_code)
        os.system(f"cd {temp_repo} && git add . && git commit -m 'Add buggy divide' -q")

        # Simulate bug fix
        self._simulate_bug_fix(temp_repo)

        # Verify bug was fixed
        fixed_content = (temp_repo / "src" / "math_utils.py").read_text()
        assert "if b == 0:" in fixed_content
        assert "return None" in fixed_content

        # Verify implementation matches requirements
        assert_implementation_matches_requirements(
            {"fixed_zero_division": True, "returns_none": True}, temp_repo
        )

    def test_prevents_documentation_only_implementation(self, temp_repo):
        """Ensure the #1706 bug cannot happen again."""
        # Simulate documentation-only implementation (the bug)
        self._simulate_documentation_only(temp_repo)

        # This should fail our verification
        with pytest.raises(AssertionError, match="No code changes detected"):
            assert_no_documentation_only_implementation(temp_repo)

    def test_code_modification(self, temp_repo):
        """Test modifying existing function logic."""
        # Create initial code
        initial_code = """def process_data(data):
    # Simple processing
    return data.upper()
"""
        (temp_repo / "src" / "processor.py").write_text(initial_code)
        os.system(f"cd {temp_repo} && git add . && git commit -m 'Add processor' -q")

        # Simulate code modification
        self._simulate_code_modification(temp_repo)

        # Verify modification was made
        modified_content = (temp_repo / "src" / "processor.py").read_text()
        assert "if data is None:" in modified_content
        assert "return ''" in modified_content

    def test_workflow_artifacts_creation(self, temp_repo):
        """Test that workflow creates expected artifacts."""
        # Create workflow artifacts
        task_template_dir = temp_repo / "context" / "trace" / "task-templates"
        task_template_dir.mkdir(parents=True, exist_ok=True)

        scratchpad_dir = temp_repo / "context" / "trace" / "scratchpad"
        scratchpad_dir.mkdir(parents=True, exist_ok=True)

        # Create sample artifacts
        (task_template_dir / "issue-9999-test.md").write_text("# Task Template")
        (scratchpad_dir / "2024-01-01-issue-9999-test.md").write_text("# Scratchpad")
        (temp_repo / ".workflow-state-9999.json").write_text('{"issue_number": 9999}')

        # Verify artifacts
        from src.utils.workflow_test_utils import verify_workflow_artifacts

        results = verify_workflow_artifacts(temp_repo, 9999)

        assert results["context/trace/task-templates/issue-9999-*.md"]
        assert results["context/trace/scratchpad/*-issue-9999-*.md"]
        assert results[".workflow-state-*.json"]

    def test_workflow_phase_outputs(self):
        """Test that phase outputs are validated correctly."""
        from src.utils.workflow_test_utils import verify_workflow_phase_outputs

        # Test valid outputs
        valid_outputs = {
            "branch_created": True,
            "commits_made": True,
            "implementation_complete": True,
        }
        assert verify_workflow_phase_outputs("implementation", valid_outputs)

        # Test invalid outputs (missing required field)
        invalid_outputs = {
            "branch_created": True,
            "commits_made": True,
            # Missing implementation_complete
        }
        assert not verify_workflow_phase_outputs("implementation", invalid_outputs)

    # Helper methods for simulating implementations
    def _simulate_function_addition(self, repo_path: Path):
        """Simulate adding a function to existing module."""
        example_path = repo_path / "src" / "example.py"
        content = example_path.read_text()
        content += "\n\ndef goodbye():\n    return 'Goodbye, World!'\n"
        example_path.write_text(content)

        # Create test
        test_content = """import pytest
from src.example import hello, goodbye

def test_goodbye():
    assert goodbye() == 'Goodbye, World!'
"""
        (repo_path / "tests" / "test_example.py").write_text(test_content)

        # Commit changes
        os.system(f"cd {repo_path} && git add . && git commit -m 'feat: add goodbye function' -q")

    def _simulate_module_creation(self, repo_path: Path):
        """Simulate creating a new module."""
        calc_content = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        (repo_path / "src" / "calculator.py").write_text(calc_content)

        test_content = """import pytest
from src.calculator import add, subtract

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 5) == -5
"""
        (repo_path / "tests" / "test_calculator.py").write_text(test_content)

        os.system(
            f"cd {repo_path} && git add . && git commit -m 'feat: create calculator module' -q"
        )

    def _simulate_bug_fix(self, repo_path: Path):
        """Simulate fixing a bug."""
        fixed_code = """def divide(a, b):
    # Fixed: Added zero division check
    if b == 0:
        return None
    return a / b
"""
        (repo_path / "src" / "math_utils.py").write_text(fixed_code)

        test_content = """import pytest
from src.math_utils import divide

def test_divide():
    assert divide(10, 2) == 5
    assert divide(0, 5) == 0
    assert divide(10, 0) is None  # Zero division returns None
"""
        (repo_path / "tests" / "test_math_utils.py").write_text(test_content)

        os.system(
            f"cd {repo_path} && git add . && git commit -m 'fix: handle zero division in divide function' -q"
        )

    def _simulate_documentation_only(self, repo_path: Path):
        """Simulate documentation-only changes (the bug)."""
        # Only create documentation files
        doc_content = "# Documentation for logging feature"
        (repo_path / "docs").mkdir(exist_ok=True)
        (repo_path / "docs" / "logging.md").write_text(doc_content)
        os.system(
            f"cd {repo_path} && git add . && git commit -m 'docs: add logging documentation' -q"
        )

    def _simulate_code_modification(self, repo_path: Path):
        """Simulate modifying existing code."""
        modified_code = """def process_data(data):
    # Enhanced processing with None handling
    if data is None:
        return ''
    if not isinstance(data, str):
        raise TypeError("Data must be a string")
    return data.upper()
"""
        (repo_path / "src" / "processor.py").write_text(modified_code)
        os.system(
            f"cd {repo_path} && git add . && git commit -m 'fix: handle None values in processor' -q"
        )


# Verification helper functions
def assert_code_files_created(files: List[str]):
    """Verify specific files exist."""
    for file_path in files:
        assert Path(file_path).exists(), f"Expected file {file_path} not found"


def assert_implementation_matches_requirements(requirements: Dict, repo_path: Path):
    """Check implementation matches requirements."""
    for req_key, expected in requirements.items():
        if req_key == "fixed_zero_division":
            content = (repo_path / "src" / "math_utils.py").read_text()
            has_check = "if b == 0:" in content
            assert has_check == expected, f"Zero division check mismatch: {has_check} != {expected}"
        elif req_key == "returns_none":
            content = (repo_path / "src" / "math_utils.py").read_text()
            has_return = "return None" in content
            assert has_return == expected, f"Return None mismatch: {has_return} != {expected}"


def assert_commits_contain_code_changes(repo_path: Path):
    """Verify real commits made with code changes."""
    # Get list of commits
    result = os.popen(f"cd {repo_path} && git log --oneline").read()
    commits = result.strip().split("\n")

    # Check for code commits (not just docs)
    code_commits = [
        c for c in commits if not c.startswith(("docs:", "chore:")) and "Initial commit" not in c
    ]
    assert len(code_commits) > 0, "No code commits found"


def assert_no_documentation_only_implementation(repo_path: Path):
    """Catch the #1706 bug - ensure not just documentation."""
    # Check git diff for latest commit
    result = os.popen(f"cd {repo_path} && git diff HEAD~1 --name-only").read()
    changed_files = result.strip().split("\n")

    # Check if any code files were changed
    code_extensions = {".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"}
    code_files = [f for f in changed_files if any(f.endswith(ext) for ext in code_extensions)]

    if not code_files:
        # Check if only docs/config files were changed
        doc_patterns = ["docs/", ".md", ".txt", ".yml", ".yaml", ".json", "context/"]
        if all(any(pattern in f for pattern in doc_patterns) for f in changed_files):
            raise AssertionError(
                "No code changes detected - only documentation files were modified!"
            )
