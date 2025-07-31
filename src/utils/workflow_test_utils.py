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

from typing import Any, Dict


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
