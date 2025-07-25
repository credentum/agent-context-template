#!/usr/bin/env python3
"""
Workflow validator to ensure sub-agents follow the defined workflow.
This can be integrated into the workflow execution to enforce compliance.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


class WorkflowValidator:
    """Validates and enforces workflow compliance for sub-agents."""

    def __init__(self, issue_number: int, workflow_dir: Path = Path(".")):
        self.issue_number = issue_number
        self.workflow_dir = workflow_dir
        self.state_file = workflow_dir / f".workflow-state-{issue_number}.json"
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load workflow state from file."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {
            "issue_number": self.issue_number,
            "current_phase": 0,
            "phases_completed": [],
            "created_at": datetime.now().isoformat(),
            "validation_errors": [],
        }

    def _save_state(self):
        """Save workflow state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def validate_phase_prerequisites(self, phase: int) -> Tuple[bool, List[str]]:
        """Check if prerequisites for a phase are met."""
        errors = []

        # Phase 1 requires issue to be fetched
        if phase == 1:
            if not self._check_issue_accessible():
                errors.append(f"Cannot access issue #{self.issue_number}")

        # Phase 2 requires Phase 1 completion
        elif phase == 2:
            if not self._phase_completed(1):
                errors.append("Phase 1 (Planning) must be completed first")

            # Check for task template
            task_template = self.workflow_dir / f"issue_{self.issue_number}_tasks.md"
            if not task_template.exists():
                errors.append(f"Task template not found: {task_template}")

        # Phase 3 requires Phase 2 completion
        elif phase == 3:
            if not self._phase_completed(2):
                errors.append("Phase 2 (Implementation) must be completed first")

            # Check for git commits
            if not self._has_commits():
                errors.append("No commits found in current branch")

        # Phase 4 requires Phase 3 completion
        elif phase == 4:
            if not self._phase_completed(3):
                errors.append("Phase 3 (Testing) must be completed first")

            # Check CI status
            if not self._check_ci_status():
                errors.append("CI must pass before creating PR")

        return len(errors) == 0, errors

    def validate_phase_outputs(self, phase: int) -> Tuple[bool, List[str]]:
        """Validate outputs produced by a phase."""
        errors = []

        if phase == 1:
            # Check task template creation
            outputs = [
                f"issue_{self.issue_number}_tasks.md",
                f"context/trace/task-templates/issue-{self.issue_number}-*.md",
            ]
            for pattern in outputs:
                if not list(self.workflow_dir.glob(pattern)):
                    errors.append(f"Required output not found: {pattern}")

        elif phase == 2:
            # Check implementation
            if not self._has_commits():
                errors.append("Implementation phase must create commits")

            # Check pre-commit status
            result = subprocess.run(["pre-commit", "run", "--all-files"], capture_output=True)
            if result.returncode != 0:
                errors.append("Pre-commit checks must pass")

        elif phase == 3:
            # Check test execution
            if not self._check_tests_run():
                errors.append("Tests must be executed")

            # Check CI execution
            if not self._check_ci_run():
                errors.append("CI must be run locally")

        elif phase == 4:
            # Check PR creation
            if not self._check_pr_created():
                errors.append("PR must be created")

        return len(errors) == 0, errors

    def record_phase_start(self, phase: int, agent_type: str):
        """Record the start of a phase."""
        self.state["current_phase"] = phase
        phase_record = {
            "phase": phase,
            "agent_type": agent_type,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Remove any existing record for this phase
        self.state["phases_completed"] = [
            p for p in self.state["phases_completed"] if p["phase"] != phase
        ]
        self.state["phases_completed"].append(phase_record)
        self._save_state()

    def record_phase_completion(self, phase: int, outputs: Dict[str, Any]):
        """Record successful completion of a phase."""
        for p in self.state["phases_completed"]:
            if p["phase"] == phase:
                p["status"] = "completed"
                p["completed_at"] = datetime.now().isoformat()
                p["outputs"] = outputs
                break
        self._save_state()

    def record_phase_failure(self, phase: int, errors: List[str]):
        """Record phase failure."""
        for p in self.state["phases_completed"]:
            if p["phase"] == phase:
                p["status"] = "failed"
                p["failed_at"] = datetime.now().isoformat()
                p["errors"] = errors
                break
        self.state["validation_errors"].extend(errors)
        self._save_state()

    # Helper methods
    def _phase_completed(self, phase: int) -> bool:
        """Check if a phase was completed successfully."""
        for p in self.state["phases_completed"]:
            if p["phase"] == phase and p["status"] == "completed":
                return True
        return False

    def _check_issue_accessible(self) -> bool:
        """Check if the issue can be accessed."""
        result = subprocess.run(
            ["gh", "issue", "view", str(self.issue_number)], capture_output=True
        )
        return result.returncode == 0

    def _has_commits(self) -> bool:
        """Check if there are commits on the current branch."""
        result = subprocess.run(["git", "log", "--oneline", "HEAD", "^main"], capture_output=True)
        return len(result.stdout.decode().strip()) > 0

    def _check_ci_status(self) -> bool:
        """Check if CI has passed."""
        # Check for CI execution marker
        ci_marker = self.workflow_dir / ".last-ci-run"
        if ci_marker.exists():
            # Check if it's recent (within last hour)
            stat = ci_marker.stat()
            age = datetime.now().timestamp() - stat.st_mtime
            return age < 3600
        return False

    def _check_tests_run(self) -> bool:
        """Check if tests were run."""
        # Look for pytest cache or coverage reports
        return (self.workflow_dir / ".pytest_cache").exists()

    def _check_ci_run(self) -> bool:
        """Check if CI was run locally."""
        # Look for CI artifacts or logs
        return any(
            [
                (self.workflow_dir / ".last-ci-run").exists(),
                (self.workflow_dir / "ci-output.log").exists(),
            ]
        )

    def _check_pr_created(self) -> bool:
        """Check if PR was created."""
        result = subprocess.run(
            ["gh", "pr", "list", "--head", f"*{self.issue_number}*"], capture_output=True
        )
        return len(result.stdout.decode().strip()) > 0


def enforce_workflow_phase(issue_number: int, phase: int, agent_type: str) -> WorkflowValidator:
    """
    Enforce workflow compliance for a specific phase.
    This should be called at the start of each agent's execution.
    """
    validator = WorkflowValidator(issue_number)

    # Check prerequisites
    can_proceed, errors = validator.validate_phase_prerequisites(phase)
    if not can_proceed:
        print(f"❌ Cannot execute phase {phase}:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError(f"Phase {phase} prerequisites not met")

    # Record phase start
    validator.record_phase_start(phase, agent_type)
    print(f"✅ Starting phase {phase} with {agent_type} agent")

    return validator


def complete_workflow_phase(validator: WorkflowValidator, phase: int, outputs: Dict[str, Any]):
    """
    Mark a workflow phase as complete after validation.
    This should be called at the end of each agent's execution.
    """
    # Validate outputs
    valid, errors = validator.validate_phase_outputs(phase)
    if not valid:
        validator.record_phase_failure(phase, errors)
        print(f"❌ Phase {phase} validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError(f"Phase {phase} outputs invalid")

    # Record completion
    validator.record_phase_completion(phase, outputs)
    print(f"✅ Phase {phase} completed successfully")


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: workflow-validator.py <issue_number> <phase>")
        sys.exit(1)

    issue_num = int(sys.argv[1])
    phase_num = int(sys.argv[2])

    # Validate phase
    validator = WorkflowValidator(issue_num)
    can_proceed, errors = validator.validate_phase_prerequisites(phase_num)

    if can_proceed:
        print(f"✅ Phase {phase_num} prerequisites met")
    else:
        print(f"❌ Phase {phase_num} prerequisites not met:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
