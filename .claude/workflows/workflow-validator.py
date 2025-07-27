#!/usr/bin/env python3
"""
Workflow validator to ensure sub-agents follow the defined workflow.
This can be integrated into the workflow execution to enforce compliance.
"""

import glob
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


class WorkflowValidator:
    """Validates and enforces workflow compliance for sub-agents."""

    def __init__(self, issue_number: int, workflow_dir: Path = Path(".")):
        # Validate issue_number to prevent injection
        if not isinstance(issue_number, int) or issue_number <= 0 or issue_number > 999999:
            raise ValueError(f"Invalid issue number: {issue_number}")

        self.issue_number = issue_number
        self.workflow_dir = Path(workflow_dir).resolve()

        # Validate workflow_dir is within expected bounds
        if not self.workflow_dir.is_dir():
            raise ValueError(f"Invalid workflow directory: {workflow_dir}")

        # Secure state file path to prevent traversal
        safe_filename = f".workflow-state-{issue_number}.json"
        if not re.match(r"^\.workflow-state-\d+\.json$", safe_filename):
            raise ValueError("Invalid state filename")

        self.state_file = self.workflow_dir / safe_filename
        self.config = self._load_config()
        self.state = self._load_state()

    def _load_config(self) -> Dict[str, Any]:
        """Load workflow configuration from YAML file."""
        config_path = self.workflow_dir / ".claude" / "config" / "workflow-enforcement.yaml"
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    return config if config is not None else {}
            else:
                # Return default configuration for backward compatibility
                return self._get_default_config()
        except Exception:
            # Return default configuration on any error
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for backward compatibility."""
        return {
            "phases": {
                "validation": {
                    "ci_validation": {
                        "require_ci": True,
                        "max_age_hours": 1,  # Backward compatible 1-hour default
                        "marker_files": [".last-ci-run"],
                        "allow_test_only": False,
                    }
                }
            },
            "branch_patterns": {
                "prefixes": [
                    "fix",
                    "feature", 
                    "hotfix",
                    "refactor",
                    "chore",
                    "docs",
                    "style",
                    "test"
                ],
                "custom_regex": None
            }
        }

    def _load_state(self) -> Dict[str, Any]:
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

    def _save_state(self) -> None:
        """Save workflow state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def validate_phase_prerequisites(self, phase: int) -> Tuple[bool, List[str]]:
        """Check if prerequisites for a phase are met."""
        errors = []

        # Phase 0 requires issue to be accessible
        if phase == 0:
            if not self._check_issue_accessible():
                errors.append(f"Cannot access issue #{self.issue_number}")

        # Phase 1 requires Phase 0 completion
        elif phase == 1:
            if not self._phase_completed(0):
                errors.append("Phase 0 (Investigation) must be completed first")

            if not self._check_issue_accessible():
                errors.append(f"Cannot access issue #{self.issue_number}")

        # Phase 2 requires Phase 1 completion
        elif phase == 2:
            if not self._phase_completed(1):
                errors.append("Phase 1 (Planning) must be completed first")

            # Check for task template
            task_template_pattern = f"context/trace/task-templates/issue-{self.issue_number}-*.md"
            if not self._check_file_exists(task_template_pattern):
                errors.append(f"Task template not found matching pattern: {task_template_pattern}")

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

    def validate_phase_outputs(self, phase: int, outputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate outputs produced by a phase."""
        errors = []

        if phase == 0:
            # Phase 0: Investigation phase
            # Check if investigation was skipped
            if outputs.get("skipped", False):
                # Validate scope was clear
                if not outputs.get("scope_clarity") == "clear":
                    errors.append("Investigation skipped but scope not marked as clear")
            else:
                # Check investigation outputs
                investigation_report = (
                    self.workflow_dir
                    / "context"
                    / "trace"
                    / "investigations"
                    / f"issue-{self.issue_number}-investigation.md"
                )
                if not investigation_report.exists():
                    errors.append(f"Investigation report not found: {investigation_report}")

                if not outputs.get("root_cause_identified"):
                    errors.append("Investigation must identify root cause")

                if not outputs.get("investigation_completed"):
                    errors.append("Investigation must be marked as completed")

        elif phase == 1:
            # Check task template creation
            template_patterns = [
                f"issue_{self.issue_number}_tasks.md",
                f"context/trace/task-templates/issue-{self.issue_number}-*.md",
            ]
            for pattern in template_patterns:
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

    def record_phase_start(self, phase: int, agent_type: str) -> None:
        """Record the start of a phase.

        Args:
            phase: Phase number (0-5)
            agent_type: Type of agent executing the phase
        """
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

    def record_phase_completion(self, phase: int, outputs: Dict[str, Any]) -> None:
        """Record successful completion of a phase.

        Args:
            phase: Phase number that was completed
            outputs: Dictionary of outputs produced by the phase
        """
        for p in self.state["phases_completed"]:
            if p["phase"] == phase:
                p["status"] = "completed"
                p["completed_at"] = datetime.now().isoformat()
                p["outputs"] = outputs
                break
        self._save_state()

    def record_phase_failure(self, phase: int, errors: List[str]) -> None:
        """Record phase failure.

        Args:
            phase: Phase number that failed
            errors: List of error messages explaining the failure
        """
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
        # issue_number already validated in __init__
        result = subprocess.run(
            ["gh", "issue", "view", str(self.issue_number)],
            capture_output=True,
            shell=False,  # Explicitly disable shell
            text=True,
        )
        return result.returncode == 0

    def _has_commits(self) -> bool:
        """Check if there are commits on the current branch."""
        result = subprocess.run(["git", "log", "--oneline", "HEAD", "^main"], capture_output=True)
        return len(result.stdout.decode().strip()) > 0

    def _check_ci_status(self) -> bool:
        """Check if CI has passed with configurable validation."""
        # Get CI validation configuration
        ci_config = self.config.get("phases", {}).get("validation", {}).get("ci_validation", {})

        # Extract configuration with defaults
        require_ci = ci_config.get("require_ci", True)
        max_age_hours = ci_config.get("max_age_hours", 1)
        marker_files = ci_config.get("marker_files", [".last-ci-run"])
        allow_test_only = ci_config.get("allow_test_only", False)

        # Check for any CI marker files
        for marker_file in marker_files:
            marker_path = self.workflow_dir / marker_file
            if marker_path.exists():
                # If max_age_hours is 0, no time restriction
                if max_age_hours == 0:
                    return True

                # Check age only if configured
                stat = marker_path.stat()
                age_hours = (datetime.now().timestamp() - stat.st_mtime) / 3600
                if age_hours <= max_age_hours:
                    return True

        # If CI not required and tests might have passed another way
        if not require_ci:
            # Check for test indicators even without CI
            if allow_test_only and self._check_tests_run():
                return True

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

    def _validate_custom_regex(self, pattern: str) -> bool:
        """Validate custom regex pattern for security."""
        if not isinstance(pattern, str):
            return False
        
        # Check for reasonable length to prevent DoS
        if len(pattern) > 1000:
            return False
        
        # Check for dangerous regex patterns that could cause ReDoS
        dangerous_patterns = [
            r"\(\?\!",  # Negative lookahead
            r"\(\?\=",  # Positive lookahead
            r"\(\?\<\!",  # Negative lookbehind
            r"\(\?\<\=",  # Positive lookbehind
            r"\(\?\:",  # Non-capturing group (can be misused)
            r"\*\+",  # Catastrophic backtracking pattern
            r"\+\*",  # Catastrophic backtracking pattern
            r"\{\d+,\}",  # Unbounded quantifiers
        ]
        
        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                return False
        
        # Ensure pattern has exactly one {issue} placeholder
        if pattern.count("{issue}") != 1:
            return False
        
        # Verify it's a valid regex by compiling a test version
        try:
            test_pattern = pattern.format(issue=123)
            re.compile(test_pattern)
        except (re.error, ValueError, KeyError):
            return False
        
        return True

    def _validate_branch_prefixes(self, prefixes: List[str]) -> List[str]:
        """Validate and sanitize branch prefix list."""
        if not isinstance(prefixes, list):
            return ["fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"]
        
        validated_prefixes = []
        for prefix in prefixes:
            if not isinstance(prefix, str):
                continue
            
            # Remove any dangerous characters
            sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", prefix)
            
            # Ensure prefix is not empty and reasonable length
            if sanitized and 1 <= len(sanitized) <= 50:
                validated_prefixes.append(sanitized)
        
        # Return default if no valid prefixes
        if not validated_prefixes:
            return ["fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"]
        
        return validated_prefixes

    def _check_pr_created(self) -> bool:
        """Check if PR was created with flexible branch pattern matching."""
        # Get configured branch prefixes or use defaults
        branch_config = self.config.get("branch_patterns", {})
        raw_prefixes = branch_config.get("prefixes", [
            "fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"
        ])
        
        # Validate and sanitize branch prefixes
        branch_prefixes = self._validate_branch_prefixes(raw_prefixes)
        
        try:
            # Get all PRs to search through - using JSON for safer parsing
            result = subprocess.run(
                ["gh", "pr", "list", "--json", "headRefName", "--limit", "50"],
                capture_output=True,
                shell=False,  # Explicitly disable shell
                text=True,
            )
            
            if result.returncode == 0:
                prs = json.loads(result.stdout)
                
                issue_pattern = f"{self.issue_number}-"
                
                # Check if any PR branch contains our issue number
                for pr in prs:
                    branch_name = pr.get("headRefName", "")
                    if not isinstance(branch_name, str):
                        continue
                    
                    # Check standard patterns: prefix/issue_number-*
                    for prefix in branch_prefixes:
                        if branch_name.startswith(f"{prefix}/{issue_pattern}"):
                            return True
                    
                    # Check custom regex if configured
                    custom_pattern = branch_config.get("custom_regex")
                    if custom_pattern and self._validate_custom_regex(custom_pattern):
                        try:
                            pattern = custom_pattern.format(issue=self.issue_number)
                            if re.match(pattern, branch_name):
                                return True
                        except (re.error, ValueError):
                            # Invalid regex or format string, skip
                            continue
            
            return False
        except (json.JSONDecodeError, Exception):
            # Fall back to original behavior if JSON parsing fails
            result = subprocess.run(
                ["gh", "pr", "list", "--head", f"fix/{self.issue_number}-", "--limit", "10"],
                capture_output=True,
                shell=False,
                text=True,
            )
            output = result.stdout.strip()
            return (
                f"fix/{self.issue_number}-" in output or f"feature/{self.issue_number}-" in output
            )

    def _check_file_exists(self, pattern: str) -> bool:
        """Check if a file matching the pattern exists."""
        files = glob.glob(pattern)
        return len(files) > 0


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


def complete_workflow_phase(
    validator: WorkflowValidator, phase: int, outputs: Dict[str, Any]
) -> None:
    """
    Mark a workflow phase as complete after validation.
    This should be called at the end of each agent's execution.
    """
    # Validate outputs
    valid, errors = validator.validate_phase_outputs(phase, outputs)
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
