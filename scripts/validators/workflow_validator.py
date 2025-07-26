#!/usr/bin/env python3
"""
Workflow Validator - Validates workflow compliance and integrates with enforcement.

This module bridges the existing workflow validation with the new enforcement system.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from workflow_enforcer import WorkflowEnforcer  # noqa: E402


class WorkflowValidator:
    """Validates workflow structure and compliance."""

    def __init__(self, issue_number: Optional[int] = None):
        """Initialize validator."""
        self.issue_number = issue_number
        self.enforcer = WorkflowEnforcer(issue_number) if issue_number else None
        self.workflow_dir = Path(".claude/workflows")

    def validate_workflow_phase(self, phase: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a workflow phase with enforcement.

        Args:
            phase: Phase name to validate
            context: Current execution context

        Returns:
            Validation result dictionary
        """
        result = {"phase": phase, "valid": True, "errors": [], "warnings": []}

        if not self.enforcer:
            result["warnings"].append("No issue number provided, enforcement disabled")
            return result

        # Use enforcer to validate
        is_valid, errors, warnings = self.enforcer.validate_workflow_state()

        if not is_valid:
            result["valid"] = False
            result["errors"].extend(errors)

        result["warnings"].extend(warnings)

        # Phase-specific validation
        phase_config = self.enforcer.config["phases"].get(phase, {})

        # Check required outputs if phase is completed
        if phase in self.enforcer.state["phases"]:
            phase_state = self.enforcer.state["phases"][phase]
            if phase_state["status"] == "completed":
                required_outputs = phase_config.get("required_outputs", [])
                outputs = phase_state.get("outputs", {})

                for output in required_outputs:
                    if output not in outputs:
                        result["warnings"].append(f"Missing output '{output}' in completed phase")

        return result

    def validate_phase_transition(
        self, from_phase: str, to_phase: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate transition between phases.

        Args:
            from_phase: Current phase
            to_phase: Target phase
            context: Execution context

        Returns:
            Validation result
        """
        result = {"from": from_phase, "to": to_phase, "valid": True, "errors": [], "warnings": []}

        if not self.enforcer:
            result["warnings"].append("No enforcement active")
            return result

        # Check phase order
        phase_order = self.enforcer.PHASE_ORDER
        if from_phase in phase_order and to_phase in phase_order:
            from_idx = phase_order.index(from_phase)
            to_idx = phase_order.index(to_phase)

            # Validate transition
            if to_idx != from_idx + 1 and to_idx > from_idx:
                # Skipping phases
                skipped = phase_order[from_idx + 1 : to_idx]
                result["warnings"].append(f"Skipping phases: {', '.join(skipped)}")

                # Check if skipped phases are skippable
                for skipped_phase in skipped:
                    if skipped_phase == "investigation":
                        if not self.enforcer.can_skip_phase("investigation", context):
                            result["valid"] = False
                            result["errors"].append(f"Cannot skip {skipped_phase} - scope unclear")
                    else:
                        result["valid"] = False
                        result["errors"].append(f"Cannot skip required phase: {skipped_phase}")

            elif to_idx < from_idx:
                result["errors"].append("Cannot go backwards in workflow")
                result["valid"] = False

        return result

    def validate_workflow_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Validate a workflow definition file.

        Args:
            filepath: Path to workflow file

        Returns:
            Validation result
        """
        result = {"file": str(filepath), "valid": True, "errors": [], "warnings": []}

        if not filepath.exists():
            result["valid"] = False
            result["errors"].append("File does not exist")
            return result

        try:
            content = filepath.read_text()

            # Check for required sections
            required_sections = [
                "## Overview",
                "## Prerequisites",
                "## Workflow Steps",
                "## Error Handling",
            ]

            for section in required_sections:
                if section not in content:
                    result["warnings"].append(f"Missing section: {section}")

            # Check for enforcement integration
            if "enforce_workflow_phase" not in content:
                result["warnings"].append("Workflow not integrated with enforcement")

            # Check for phase definitions
            phases = ["Phase 0:", "Phase 1:", "Phase 2:", "Phase 3:", "Phase 4:", "Phase 5:"]
            missing_phases = [p for p in phases if p not in content]
            if missing_phases:
                result["warnings"].append(f"Missing phases: {', '.join(missing_phases)}")

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error reading file: {str(e)}")

        return result

    def validate_all_workflows(self) -> Dict[str, Any]:
        """Validate all workflow files in the workflows directory."""
        results = {"total": 0, "valid": 0, "invalid": 0, "files": {}}

        if not self.workflow_dir.exists():
            results["errors"] = [f"Workflow directory not found: {self.workflow_dir}"]
            return results

        for workflow_file in self.workflow_dir.glob("*.md"):
            validation = self.validate_workflow_file(workflow_file)
            results["total"] += 1

            if validation["valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1

            results["files"][str(workflow_file)] = validation

        return results

    def validate_agent_integration(self, agent_type: str) -> Dict[str, Any]:
        """
        Validate that an agent is properly integrated with workflow enforcement.

        Args:
            agent_type: Type of agent to validate

        Returns:
            Validation result
        """
        result = {"agent": agent_type, "valid": True, "errors": [], "warnings": []}

        # Map agent types to expected files
        agent_files = {
            "issue-investigator": "src/agents/issue_investigator.py",
            "task-planner": "src/agents/task_planner.py",
            "test-runner": "src/agents/test_runner.py",
            "pr-manager": "src/agents/pr_manager.py",
        }

        expected_file = agent_files.get(agent_type)
        if not expected_file:
            result["warnings"].append(f"Unknown agent type: {agent_type}")
            return result

        # Check if agent file exists
        agent_path = Path(expected_file)
        if not agent_path.exists():
            result["warnings"].append(f"Agent file not found: {expected_file}")
            # Don't mark as invalid since agents might be in different locations
            return result

        try:
            content = agent_path.read_text()

            # Check for enforcement imports
            if "from agent_hooks import" not in content and "import agent_hooks" not in content:
                result["warnings"].append("Agent not importing enforcement hooks")

            # Check for hook usage
            if "pre_phase_hook" not in content and "workflow_decorator" not in content:
                result["warnings"].append("Agent not using enforcement hooks")

        except Exception as e:
            result["errors"].append(f"Error checking agent integration: {str(e)}")
            result["valid"] = False

        return result

    def generate_integration_report(self) -> str:
        """Generate a report on workflow enforcement integration status."""
        report = """# Workflow Enforcement Integration Report

## Overview
This report shows the current state of workflow enforcement integration.

"""
        # Check enforcement config
        config_path = Path(".claude/config/workflow-enforcement.yaml")
        if config_path.exists():
            report += "### ✅ Enforcement Configuration\n"
            report += f"- Config file exists: `{config_path}`\n"

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            enabled = config.get("enforcement", {}).get("enabled", False)
            report += f"- Enforcement enabled: {'✅ Yes' if enabled else '❌ No'}\n"
            report += f"- Strict mode: {config.get('enforcement', {}).get('strict_mode', False)}\n"
            report += (
                f"- Allow bypass: {config.get('enforcement', {}).get('allow_bypass', False)}\n"
            )
        else:
            report += "### ❌ Enforcement Configuration\n"
            report += "- Config file not found\n"

        report += "\n### Agent Integration Status\n\n"

        # Check each agent type
        for agent_type in ["issue-investigator", "task-planner", "test-runner", "pr-manager"]:
            validation = self.validate_agent_integration(agent_type)
            status = "✅" if not validation["warnings"] and not validation["errors"] else "⚠️"
            report += f"- {status} **{agent_type}**\n"

            for warning in validation["warnings"]:
                report += f"  - ⚠️ {warning}\n"
            for error in validation["errors"]:
                report += f"  - ❌ {error}\n"

        # Check workflow files
        report += "\n### Workflow Files\n\n"
        workflow_validation = self.validate_all_workflows()

        report += f"- Total workflow files: {workflow_validation['total']}\n"
        report += f"- Valid: {workflow_validation['valid']}\n"
        report += f"- Invalid: {workflow_validation['invalid']}\n"

        # Active workflows
        report += "\n### Active Workflows\n\n"
        active_count = 0
        for state_file in Path(".").glob(".workflow-state-*.json"):
            issue_number = state_file.stem.split("-")[-1]
            with open(state_file, "r") as f:
                state = json.load(f)
            phase = state.get("current_phase", "Unknown")
            report += f"- Issue #{issue_number}: {phase}\n"
            active_count += 1

        if active_count == 0:
            report += "- No active workflows\n"

        return report


def main():
    """CLI interface for workflow validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Workflow Validation Tool")
    parser.add_argument(
        "action",
        choices=["validate-phase", "validate-transition", "validate-all", "integration-report"],
        help="Validation action",
    )
    parser.add_argument("--issue", type=int, help="Issue number")
    parser.add_argument("--phase", help="Phase name")
    parser.add_argument("--from-phase", help="Transition from phase")
    parser.add_argument("--to-phase", help="Transition to phase")

    args = parser.parse_args()

    if args.action == "validate-phase":
        if not args.phase:
            parser.error("--phase required for validate-phase action")

        validator = WorkflowValidator(args.issue)
        result = validator.validate_workflow_phase(args.phase, {})
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    elif args.action == "validate-transition":
        if not args.from_phase or not args.to_phase:
            parser.error("--from-phase and --to-phase required")

        validator = WorkflowValidator(args.issue)
        result = validator.validate_phase_transition(args.from_phase, args.to_phase, {})
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["valid"] else 1)

    elif args.action == "validate-all":
        validator = WorkflowValidator()
        results = validator.validate_all_workflows()
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["invalid"] == 0 else 1)

    elif args.action == "integration-report":
        validator = WorkflowValidator()
        print(validator.generate_integration_report())


if __name__ == "__main__":
    main()
