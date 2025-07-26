#!/usr/bin/env python3
"""
Workflow Enforcer - Ensures standard workflow compliance for issue resolution.

This module provides the core enforcement engine that validates phase prerequisites,
tracks workflow state, and ensures all required steps are followed.
"""

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass
class PhaseState:
    """Represents the state of a workflow phase."""

    phase_name: str
    status: str = "pending"  # pending, in_progress, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    agent_type: Optional[str] = None


class WorkflowEnforcer:
    """Enforces workflow standards across all phases."""

    # Phase order and dependencies
    PHASE_ORDER = [
        "investigation",
        "planning",
        "implementation",
        "validation",
        "pr_creation",
        "monitoring",
    ]

    PHASE_AGENTS = {
        "investigation": "issue-investigator",
        "planning": "task-planner",
        "implementation": "main-claude",
        "validation": "test-runner",
        "pr_creation": "pr-manager",
        "monitoring": "pr-manager",
    }

    def __init__(self, issue_number: int, config_path: Optional[str] = None):
        """Initialize enforcer for a specific issue."""
        self.issue_number = issue_number
        self.state_file = Path(f".workflow-state-{issue_number}.json")
        self.config_path = Path(config_path or ".claude/config/workflow-enforcement.yaml")
        self.config = self._load_config()
        self.state = self._load_state()

    def _load_config(self) -> Dict[str, Any]:
        """Load enforcement configuration."""
        if not self.config_path.exists():
            # Create default config if it doesn't exist
            default_config = {
                "enforcement": {
                    "enabled": True,
                    "strict_mode": True,
                    "allow_bypass": True,
                    "require_state_file": True,
                },
                "phases": {
                    "investigation": {
                        "required_outputs": ["scope_clarity", "investigation_completed"],
                        "max_duration_hours": 4,
                        "skippable_if": ["scope_is_clear"],
                    },
                    "planning": {
                        "required_outputs": [
                            "task_template_created",
                            "scratchpad_created",
                            "documentation_committed",
                        ],
                        "required_files": [
                            "context/trace/task-templates/issue-{issue_number}-*.md",
                            "context/trace/scratchpad/*-issue-{issue_number}-*.md",
                        ],
                        "max_duration_hours": 2,
                    },
                    "implementation": {
                        "required_outputs": [
                            "branch_created",
                            "implementation_complete",
                            "commits_made",
                        ],
                        "prevent_on_main": True,
                        "max_duration_hours": 8,
                    },
                    "validation": {
                        "required_outputs": ["tests_run", "ci_passed", "coverage_maintained"],
                        "min_coverage": 71.82,
                        "required_commands": [
                            "./scripts/run-ci-docker.sh",
                            "pre-commit run --all-files",
                        ],
                        "max_duration_hours": 2,
                    },
                    "pr_creation": {
                        "required_outputs": [
                            "pr_created",
                            "branch_pushed",
                            "documentation_included",
                        ],
                        "required_labels": ["workflow-enforced"],
                        "max_duration_hours": 1,
                    },
                    "monitoring": {
                        "required_outputs": ["pr_monitoring_active"],
                        "max_wait_hours": 48,
                    },
                },
            }

            os.makedirs(self.config_path.parent, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

            return default_config

        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _load_state(self) -> Dict[str, Any]:
        """Load workflow state from file."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)

        # Initialize new state
        return {
            "issue_number": self.issue_number,
            "created_at": datetime.now().isoformat(),
            "current_phase": None,
            "phases": {},
            "metadata": {"enforcer_version": "1.0.0", "workflow_version": "1.0.0"},
        }

    def _save_state(self) -> None:
        """Save workflow state to file."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def enforce_phase_entry(
        self, phase_name: str, agent_type: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enforce requirements before entering a phase.

        Returns:
            Tuple of (can_proceed, message, context_updates)
        """
        if not self.config["enforcement"]["enabled"]:
            return True, "Enforcement disabled", {}

        # Validate phase name
        if phase_name not in self.PHASE_ORDER:
            return False, f"Unknown phase: {phase_name}", {}

        # Check if phase is already completed
        if phase_name in self.state["phases"]:
            phase_state = self.state["phases"][phase_name]
            if phase_state["status"] == "completed":
                return False, f"Phase '{phase_name}' already completed", {}
            if phase_state["status"] == "in_progress":
                return False, f"Phase '{phase_name}' already in progress", {}

        # Check phase dependencies
        phase_idx = self.PHASE_ORDER.index(phase_name)
        if phase_idx > 0:
            # Check if previous phases are completed (except investigation which can be skipped)
            for i in range(phase_idx):
                prev_phase = self.PHASE_ORDER[i]
                if prev_phase == "investigation":
                    # Investigation can be skipped if scope is clear
                    continue

                if prev_phase not in self.state["phases"]:
                    return False, f"Previous phase '{prev_phase}' not started", {}

                prev_state = self.state["phases"][prev_phase]
                if prev_state["status"] != "completed":
                    return False, f"Previous phase '{prev_phase}' not completed", {}

        # Phase-specific checks
        if phase_name == "implementation":
            # Check if on main branch
            current_branch = self._get_current_branch()
            if current_branch == "main" and self.config["phases"]["implementation"].get(
                "prevent_on_main", True
            ):
                return False, "Cannot implement on main branch", {}

        # Create phase state
        phase_state = PhaseState(
            phase_name=phase_name,
            status="in_progress",
            started_at=datetime.now().isoformat(),
            agent_type=agent_type,
        )

        # Update state
        self.state["phases"][phase_name] = asdict(phase_state)
        self.state["current_phase"] = phase_name
        self._save_state()

        context_updates = {
            f"workflow.phase.{phase_name}.status": "in_progress",
            f"workflow.phase.{phase_name}.started": phase_state.started_at,
            "workflow.current_phase": phase_name,
        }

        return True, f"Entering phase '{phase_name}'", context_updates

    def complete_phase(self, phase_name: str, outputs: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Mark a phase as complete after validating outputs.

        Returns:
            Tuple of (success, message)
        """
        if phase_name not in self.state["phases"]:
            return False, f"Phase '{phase_name}' not started"

        phase_state = self.state["phases"][phase_name]
        if phase_state["status"] != "in_progress":
            return False, f"Phase '{phase_name}' not in progress"

        # Validate required outputs
        phase_config = self.config["phases"].get(phase_name, {})
        required_outputs = phase_config.get("required_outputs", [])

        missing_outputs = []
        for output in required_outputs:
            if output not in outputs or not outputs[output]:
                missing_outputs.append(output)

        if missing_outputs:
            return False, f"Missing required outputs: {', '.join(missing_outputs)}"

        # Validate required files
        required_files = phase_config.get("required_files", [])
        for file_pattern in required_files:
            # Replace placeholders
            file_pattern = file_pattern.replace("{issue_number}", str(self.issue_number))
            if not self._check_file_exists(file_pattern):
                return False, f"Required file not found: {file_pattern}"

        # Phase-specific validation
        if phase_name == "validation":
            # Check coverage
            min_coverage = phase_config.get("min_coverage", 0)
            if "coverage_percentage" in outputs:
                try:
                    coverage = float(outputs["coverage_percentage"].rstrip("%"))
                    if coverage < min_coverage:
                        return False, f"Coverage {coverage}% below minimum {min_coverage}%"
                except (ValueError, TypeError):
                    pass

        # Update state
        phase_state["status"] = "completed"
        phase_state["completed_at"] = datetime.now().isoformat()
        phase_state["outputs"] = outputs
        self.state["phases"][phase_name] = phase_state
        self.state["current_phase"] = None
        self._save_state()

        return True, f"Phase '{phase_name}' completed successfully"

    def get_current_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        return self.state.copy()

    def validate_workflow_state(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the current workflow state.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check if enforcement is required
        if not self.config["enforcement"]["enabled"]:
            warnings.append("Workflow enforcement is disabled")
            return True, errors, warnings

        # Check state file
        if self.config["enforcement"].get("require_state_file", True):
            if not self.state_file.exists():
                errors.append("Workflow state file not found")

        # Check current phase
        current_phase = self.state.get("current_phase")
        if current_phase:
            # Check duration
            phase_state = self.state["phases"].get(current_phase, {})
            if phase_state.get("started_at"):
                started = datetime.fromisoformat(phase_state["started_at"])
                duration = datetime.now() - started
                max_hours = self.config["phases"][current_phase].get(
                    "max_duration_hours", float("inf")
                )
                if duration.total_seconds() > max_hours * 3600:
                    warnings.append(
                        f"Phase '{current_phase}' exceeds maximum duration of {max_hours} hours"
                    )

        # Check for incomplete phases
        for phase_name, phase_state in self.state.get("phases", {}).items():
            if phase_state["status"] == "in_progress":
                warnings.append(f"Phase '{phase_name}' is still in progress")
            elif phase_state["status"] == "failed":
                errors.append(f"Phase '{phase_name}' failed")

        return len(errors) == 0, errors, warnings

    def can_skip_phase(self, phase_name: str, context: Dict[str, Any]) -> bool:
        """Check if a phase can be skipped based on conditions."""
        phase_config = self.config["phases"].get(phase_name, {})
        skip_conditions = phase_config.get("skippable_if", [])

        for condition in skip_conditions:
            if condition == "scope_is_clear" and context.get("scope_is_clear", False):
                return True

        return False

    def resume_workflow(self) -> Optional[str]:
        """
        Determine where to resume the workflow.

        Returns:
            Next phase to execute or None if workflow is complete
        """
        # Find the last completed phase
        last_completed_idx = -1
        for i, phase_name in enumerate(self.PHASE_ORDER):
            if phase_name in self.state["phases"]:
                phase_state = self.state["phases"][phase_name]
                if phase_state["status"] == "completed":
                    last_completed_idx = i
                elif phase_state["status"] == "in_progress":
                    return phase_name  # Resume current phase

        # Return next phase
        if last_completed_idx < len(self.PHASE_ORDER) - 1:
            return self.PHASE_ORDER[last_completed_idx + 1]

        return None

    def generate_compliance_report(self) -> str:
        """Generate a compliance report for the workflow."""
        is_valid, errors, warnings = self.validate_workflow_state()

        report = f"""# Workflow Compliance Report

**Issue**: #{self.issue_number}
**Generated**: {datetime.now().isoformat()}
**Status**: {'✅ COMPLIANT' if is_valid else '❌ NON-COMPLIANT'}
**Enforcement**: {'Enabled' if self.config["enforcement"]["enabled"] else 'Disabled'}

## Phase Status

"""
        # Phase status
        for phase_name in self.PHASE_ORDER:
            if phase_name in self.state["phases"]:
                phase_state = self.state["phases"][phase_name]
                status_emoji = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "failed": "❌",
                    "pending": "⏳",
                }.get(phase_state["status"], "❓")

                report += f"### {status_emoji} {phase_name.replace('_', ' ').title()}\n"
                report += f"- **Status**: {phase_state['status']}\n"
                if phase_state.get("started_at"):
                    report += f"- **Started**: {phase_state['started_at']}\n"
                if phase_state.get("completed_at"):
                    report += f"- **Completed**: {phase_state['completed_at']}\n"
                if phase_state.get("agent_type"):
                    report += f"- **Agent**: {phase_state['agent_type']}\n"
                report += "\n"
            else:
                report += f"### ⏳ {phase_name.replace('_', ' ').title()}\n"
                report += "- **Status**: Not started\n\n"

        # Errors and warnings
        if errors:
            report += "## ❌ Errors\n\n"
            for error in errors:
                report += f"- {error}\n"
            report += "\n"

        if warnings:
            report += "## ⚠️ Warnings\n\n"
            for warning in warnings:
                report += f"- {warning}\n"
            report += "\n"

        # Recommendations
        report += "## 📋 Recommendations\n\n"
        next_phase = self.resume_workflow()
        if next_phase:
            report += f"- Resume workflow from phase: **{next_phase}**\n"
            report += f"- Use agent: **{self.PHASE_AGENTS.get(next_phase, 'main-claude')}**\n"
        else:
            report += "- Workflow is complete\n"

        return report

    # Helper methods
    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _check_file_exists(self, pattern: str) -> bool:
        """Check if a file matching the pattern exists."""
        import glob

        files = glob.glob(pattern)
        return len(files) > 0


def main():
    """CLI interface for workflow enforcement."""
    import argparse

    parser = argparse.ArgumentParser(description="Workflow Enforcement Tool")
    parser.add_argument(
        "action", choices=["check", "report", "resume", "reset"], help="Action to perform"
    )
    parser.add_argument("--issue", type=int, required=True, help="Issue number")
    parser.add_argument("--phase", help="Phase name for check action")
    parser.add_argument("--agent", help="Agent type for check action")

    args = parser.parse_args()

    enforcer = WorkflowEnforcer(args.issue)

    if args.action == "check":
        if not args.phase or not args.agent:
            parser.error("--phase and --agent required for check action")

        can_proceed, message, _ = enforcer.enforce_phase_entry(args.phase, args.agent)
        print(f"{'✅' if can_proceed else '❌'} {message}")
        sys.exit(0 if can_proceed else 1)

    elif args.action == "report":
        report = enforcer.generate_compliance_report()
        print(report)

    elif args.action == "resume":
        next_phase = enforcer.resume_workflow()
        if next_phase:
            print(f"Resume from phase: {next_phase}")
            print(f"Use agent: {enforcer.PHASE_AGENTS.get(next_phase, 'main-claude')}")
        else:
            print("Workflow is complete")

    elif args.action == "reset":
        if enforcer.state_file.exists():
            enforcer.state_file.unlink()
            print(f"Reset workflow state for issue #{args.issue}")
        else:
            print(f"No workflow state found for issue #{args.issue}")


if __name__ == "__main__":
    main()
