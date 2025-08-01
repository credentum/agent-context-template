#!/usr/bin/env python3
"""Workflow testing utility functions.

This module provides utility functions to support testing of the workflow automation
system, including phase output validation, test state creation, and test issue
number generation. These utilities are designed to work with the WorkflowExecutor
and HybridWorkflowExecutor classes to facilitate comprehensive testing of the
issue-to-PR workflow pipeline.

Functions:
    verify_workflow_phase_outputs: Validate that phase outputs meet requirements
    get_workflow_test_issue_number: Get a standardized test issue number
    create_test_workflow_state: Create test workflow state for different phases
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch


def verify_workflow_phase_outputs(phase_name: str, outputs: Dict[str, Any]) -> bool:
    """
    Verify that workflow phase outputs meet expected criteria.

    Args:
        phase_name: Name of the workflow phase
        outputs: Dictionary of phase outputs

    Returns:
        bool: True if outputs are valid, False otherwise
    """
    # Define required outputs for each phase
    required_outputs = {
        "investigation": ["investigation_completed", "scope_clarity"],
        "planning": ["task_template_created", "scratchpad_created", "documentation_committed"],
        "implementation": ["branch_created", "commits_made", "implementation_complete"],
        "validation": ["tests_run", "ci_passed", "quality_checks_passed"],
        "pr_creation": ["pr_created", "branch_pushed", "labels_applied"],
        "monitoring": ["documentation_verified", "workflow_completed"],
    }

    if phase_name not in required_outputs:
        return False

    # Check all required outputs are present
    for output in required_outputs[phase_name]:
        if output not in outputs:
            return False

    return True


def get_workflow_test_issue_number() -> int:
    """Get a test issue number for workflow testing."""
    return 9999


def create_test_workflow_state(issue_number: int, current_phase: str) -> Dict[str, Any]:
    """
    Create a test workflow state for testing purposes.

    Args:
        issue_number: Issue number for the workflow
        current_phase: Current phase of the workflow

    Returns:
        dict: Test workflow state
    """
    return {
        "schema_version": "1.0",
        "issue_number": issue_number,
        "current_phase": current_phase,
        "phases": {
            "investigation": {
                "phase_name": "investigation",
                "status": "completed",
                "outputs": {"investigation_completed": True, "scope_clarity": "clear"},
            },
            "planning": {
                "phase_name": "planning",
                "status": "completed" if current_phase != "planning" else "in_progress",
                "outputs": {
                    "task_template_created": True,
                    "scratchpad_created": True,
                    "documentation_committed": True,
                },
            },
        },
    }


def create_test_issue_data(
    issue_number: int,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create test issue data matching GitHub API format.
    
    Args:
        issue_number: Issue number
        title: Issue title
        body: Issue body/description
        labels: Optional list of labels
        
    Returns:
        Dictionary matching GitHub issue API response
    """
    return {
        "number": issue_number,
        "title": title,
        "body": body,
        "state": "open",
        "labels": [{"name": label} for label in (labels or [])],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "user": {"login": "test-user"},
    }


def create_test_repository(name: str = "test_repo") -> Path:
    """Create a temporary git repository for testing.
    
    Args:
        name: Repository name
        
    Returns:
        Path to the created repository
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir) / name
    repo_path.mkdir()
    
    # Initialize git repo
    os.system(f"cd {repo_path} && git init")
    os.system(f"cd {repo_path} && git config user.email 'test@example.com'")
    os.system(f"cd {repo_path} && git config user.name 'Test User'")
    
    # Create basic structure
    (repo_path / "src").mkdir()
    (repo_path / "src" / "__init__.py").touch()
    (repo_path / "tests").mkdir()
    (repo_path / "tests" / "__init__.py").touch()
    (repo_path / "scripts").mkdir()
    (repo_path / "context").mkdir()
    (repo_path / "context" / "trace").mkdir()
    
    # Initial commit
    os.system(f"cd {repo_path} && git add . && git commit -m 'Initial commit'")
    
    return repo_path


def verify_code_changes(repo_path: Path, expected_files: List[str]) -> bool:
    """Verify that code changes were made to expected files.
    
    Args:
        repo_path: Path to the repository
        expected_files: List of files that should have been modified
        
    Returns:
        True if all expected files were modified
    """
    # Get changed files in the last commit
    result = os.popen(f"cd {repo_path} && git diff HEAD~1 --name-only").read()
    changed_files = set(result.strip().split('\n'))
    
    # Check if all expected files were changed
    for expected in expected_files:
        if expected not in changed_files:
            return False
    
    return True


def simulate_workflow_execution(
    issue_number: int,
    repo_path: Path,
    phases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Simulate workflow execution for testing.
    
    Args:
        issue_number: Issue number to simulate
        repo_path: Path to test repository
        phases: Optional list of phases to execute (default: all)
        
    Returns:
        Dictionary with execution results
    """
    from scripts.workflow_executor import WorkflowExecutor
    
    results = {
        "issue_number": issue_number,
        "phases_executed": [],
        "phase_results": {},
        "success": True,
    }
    
    # Default phases if not specified
    if phases is None:
        phases = ["investigation", "planning", "implementation", "validation"]
    
    # Create executor
    original_cwd = os.getcwd()
    try:
        os.chdir(str(repo_path))
        executor = WorkflowExecutor(issue_number)
        
        # Execute each phase
        for phase in phases:
            try:
                # Mock external dependencies
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0, stdout="")
                    
                    # Get the method name for the phase
                    method_name = f"execute_{phase}"
                    if hasattr(executor, method_name):
                        phase_method = getattr(executor, method_name)
                        phase_result = phase_method({})
                    else:
                        raise AttributeError(f"Method {method_name} not found")
                    
                    results["phases_executed"].append(phase)
                    results["phase_results"][phase] = {
                        "status": "completed",
                        "result": phase_result,
                    }
            except Exception as e:
                results["success"] = False
                results["phase_results"][phase] = {
                    "status": "failed",
                    "error": str(e),
                }
                break
    finally:
        os.chdir(original_cwd)
    
    return results


def create_test_issue(template: str, repo_path: Path) -> int:
    """Create a temporary test issue from a template.
    
    Args:
        template: Template name (e.g., 'simple_function_addition')
        repo_path: Path to test repository
        
    Returns:
        Generated issue number
    """
    # Load template
    template_path = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "workflow_test_issues" / f"{template}.json"
    
    if template_path.exists():
        with open(template_path) as f:
            issue_data = json.load(f)
    else:
        # Default template if file doesn't exist
        issue_data = {
            "number": 99999,
            "title": f"Test Issue: {template}",
            "body": "Test issue for workflow testing",
        }
    
    # Generate unique issue number
    import random
    issue_number = random.randint(90000, 99999)
    issue_data["number"] = issue_number
    
    # Create issue metadata file (simulate GitHub issue)
    issue_file = repo_path / f".issue-{issue_number}.json"
    with open(issue_file, 'w') as f:
        json.dump(issue_data, f, indent=2)
    
    return issue_number


def verify_workflow_artifacts(
    repo_path: Path,
    issue_number: int,
    expected_artifacts: Optional[List[str]] = None,
) -> Dict[str, bool]:
    """Verify that workflow artifacts were created correctly.
    
    Args:
        repo_path: Path to repository
        issue_number: Issue number
        expected_artifacts: Optional list of expected artifacts
        
    Returns:
        Dictionary with verification results
    """
    if expected_artifacts is None:
        expected_artifacts = [
            f"context/trace/task-templates/issue-{issue_number}-*.md",
            f"context/trace/scratchpad/*-issue-{issue_number}-*.md",
            ".workflow-state-*.json",
        ]
    
    results = {}
    
    for artifact_pattern in expected_artifacts:
        # Check if any files match the pattern
        import glob
        matches = glob.glob(str(repo_path / artifact_pattern))
        results[artifact_pattern] = len(matches) > 0
    
    return results


def cleanup_test_repository(repo_path: Path):
    """Clean up a test repository.
    
    Args:
        repo_path: Path to repository to clean up
    """
    import shutil
    
    if repo_path.exists() and "tmp" in str(repo_path):
        shutil.rmtree(repo_path)
