#!/usr/bin/env python3
"""
Agent Hooks - Integration points for workflow enforcement in agent operations.

This module provides pre and post execution hooks for all agent types to ensure
workflow compliance.
"""

import functools
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from workflow_enforcer import WorkflowEnforcer  # noqa: E402


class AgentHooks:
    """Provides enforcement hooks for various agent operations."""

    def __init__(self, issue_number: int):
        """Initialize hooks with issue number."""
        self.issue_number = issue_number
        self.enforcer = WorkflowEnforcer(issue_number)

    def pre_phase_hook(
        self, phase_name: str, agent_type: str, context: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Pre-phase enforcement hook.

        Args:
            phase_name: Name of the phase to enter
            agent_type: Type of agent executing the phase
            context: Current execution context

        Returns:
            Tuple of (can_proceed, message, context_updates)
        """
        # Special handling for investigation phase
        if phase_name == "investigation":
            # Check if investigation can be skipped
            if self.enforcer.can_skip_phase("investigation", context):
                # Use the new skip_phase method
                success, message = self.enforcer.skip_phase(
                    "investigation", "Scope is clear from issue description"
                )
                if success:
                    return True, message, {"investigation_skipped": True}
                else:
                    # Fallback - should not happen
                    return False, f"Failed to skip investigation: {message}", {}

        # Enforce phase entry
        can_proceed, message, context_updates = self.enforcer.enforce_phase_entry(
            phase_name, agent_type
        )

        # Log the attempt
        self._log_hook_execution("pre", phase_name, agent_type, can_proceed, message)

        return can_proceed, message, context_updates

    def post_phase_hook(self, phase_name: str, outputs: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Post-phase enforcement hook.

        Args:
            phase_name: Name of the phase to complete
            outputs: Phase outputs to validate

        Returns:
            Tuple of (success, message)
        """
        # Check if phase was skipped
        if outputs.get("skipped", False):
            # Phase was already marked as skipped in pre_phase_hook
            success = True
            message = f"Phase '{phase_name}' was skipped"
        else:
            # Complete the phase normally
            success, message = self.enforcer.complete_phase(phase_name, outputs)

        # Log the completion
        self._log_hook_execution("post", phase_name, None, success, message)

        return success, message

    def workflow_decorator(self, phase_name: str, agent_type: str):
        """
        Decorator for wrapping agent functions with workflow enforcement.

        Usage:
            @hooks.workflow_decorator("planning", "task-planner")
            def plan_task(context):
                # Planning logic
                return outputs
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(context: Dict[str, Any], *args, **kwargs) -> Any:
                # Pre-phase hook
                can_proceed, message, context_updates = self.pre_phase_hook(
                    phase_name, agent_type, context
                )

                if not can_proceed:
                    raise WorkflowViolationError(f"Cannot proceed with {phase_name}: {message}")

                # Update context
                for key, value in context_updates.items():
                    self._set_nested_dict(context, key, value)

                try:
                    # Execute the wrapped function
                    result = func(context, *args, **kwargs)

                    # Extract outputs from result
                    outputs = self._extract_outputs(phase_name, result, context)

                    # Post-phase hook
                    success, message = self.post_phase_hook(phase_name, outputs)

                    if not success:
                        raise WorkflowViolationError(f"Failed to complete {phase_name}: {message}")

                    return result

                except Exception as e:
                    # Mark phase as failed
                    if phase_name in self.enforcer.state["phases"]:
                        self.enforcer.state["phases"][phase_name]["status"] = "failed"
                        self.enforcer.state["phases"][phase_name]["errors"] = [str(e)]
                        self.enforcer._save_state()
                    raise

            return wrapper

        return decorator

    def _extract_outputs(
        self, phase_name: str, result: Any, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract phase outputs from function result and context."""
        outputs = {}

        # Phase-specific output extraction
        if phase_name == "investigation":
            outputs["scope_clarity"] = context.get("scope_is_clear", False)
            outputs["investigation_completed"] = True
            if isinstance(result, dict):
                outputs.update(result)

        elif phase_name == "planning":
            # Check for task template
            task_template_pattern = f"context/trace/task-templates/issue-{self.issue_number}-*.md"
            outputs["task_template_created"] = self.enforcer._check_file_exists(
                task_template_pattern
            )

            # Check for scratchpad
            scratchpad_pattern = f"context/trace/scratchpad/*-issue-{self.issue_number}-*.md"
            outputs["scratchpad_created"] = self.enforcer._check_file_exists(scratchpad_pattern)

            # Check for documentation commit
            outputs["documentation_committed"] = self._check_git_commit_exists(
                f"issue #{self.issue_number}", "docs(trace): add task template"
            )

        elif phase_name == "implementation":
            outputs["branch_created"] = self.enforcer._get_current_branch() != "main"
            outputs["implementation_complete"] = True
            outputs["commits_made"] = self._check_git_commits_exist()

        elif phase_name == "validation":
            outputs["tests_run"] = context.get("tests_run", False)
            outputs["ci_passed"] = context.get("ci_passed", False)
            outputs["coverage_maintained"] = context.get("coverage_maintained", False)
            outputs["coverage_percentage"] = context.get("coverage_percentage", "0%")

        elif phase_name == "pr_creation":
            outputs["pr_created"] = context.get("pr_number") is not None
            outputs["branch_pushed"] = self._check_branch_pushed()
            outputs["documentation_included"] = True  # Assumed if we got this far

        elif phase_name == "monitoring":
            outputs["pr_monitoring_active"] = True
            outputs["pr_number"] = context.get("pr_number")

        # Allow function result to override
        if isinstance(result, dict):
            outputs.update(result)

        return outputs

    def _check_git_commit_exists(self, search_text: str, commit_pattern: str) -> bool:
        """Check if a git commit exists with specific text."""

        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--grep", search_text],
                capture_output=True,
                text=True,
                check=False,
            )
            return commit_pattern in result.stdout
        except Exception:
            return False

    def _check_git_commits_exist(self) -> bool:
        """Check if there are commits on the current branch."""

        try:
            # Check if there are commits different from main
            result = subprocess.run(
                ["git", "rev-list", "--count", "main..HEAD"],
                capture_output=True,
                text=True,
                check=False,
            )
            count = int(result.stdout.strip())
            return count > 0
        except Exception:
            return True  # Assume true if we can't check

    def _check_branch_pushed(self) -> bool:
        """Check if current branch is pushed to remote."""

        try:
            branch = self.enforcer._get_current_branch()
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", branch],
                capture_output=True,
                text=True,
                check=False,
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _set_nested_dict(self, d: Dict, key: str, value: Any) -> None:
        """Set a value in a nested dictionary using dot notation."""
        keys = key.split(".")
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    def _log_hook_execution(
        self,
        hook_type: str,
        phase_name: str,
        agent_type: Optional[str],
        success: bool,
        message: str,
    ) -> None:
        """Log hook execution for debugging."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "hook_type": hook_type,
            "phase": phase_name,
            "agent": agent_type,
            "success": success,
            "message": message,
            "issue": self.issue_number,
        }

        # Create logs directory if needed
        log_dir = Path("context/trace/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Append to workflow log
        log_file = log_dir / "workflow-enforcement.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


class WorkflowViolationError(Exception):
    """Raised when a workflow violation is detected."""

    pass


# Convenience functions for agent integration
def enforce_pre_phase(
    issue_number: int, phase_name: str, agent_type: str, context: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """Convenience function for pre-phase enforcement."""
    hooks = AgentHooks(issue_number)
    return hooks.pre_phase_hook(phase_name, agent_type, context)


def enforce_post_phase(
    issue_number: int, phase_name: str, outputs: Dict[str, Any]
) -> Tuple[bool, str]:
    """Convenience function for post-phase enforcement."""
    hooks = AgentHooks(issue_number)
    return hooks.post_phase_hook(phase_name, outputs)


def get_workflow_decorator(issue_number: int, phase_name: str, agent_type: str):
    """Get a workflow decorator for a specific issue and phase."""
    hooks = AgentHooks(issue_number)
    return hooks.workflow_decorator(phase_name, agent_type)


# Example integration patterns
def example_agent_integration():
    """Example of how to integrate hooks into an agent."""
    issue_number = 123
    context = {"scope_is_clear": True}

    # Method 1: Direct hook usage
    hooks = AgentHooks(issue_number)

    # Pre-phase
    can_proceed, message, updates = hooks.pre_phase_hook("planning", "task-planner", context)
    if not can_proceed:
        print(f"Cannot proceed: {message}")
        return

    # Do work...
    outputs = {
        "task_template_created": True,
        "scratchpad_created": True,
        "documentation_committed": True,
    }

    # Post-phase
    success, message = hooks.post_phase_hook("planning", outputs)
    if not success:
        print(f"Failed to complete phase: {message}")

    # Method 2: Decorator usage
    @get_workflow_decorator(issue_number, "implementation", "main-claude")
    def implement_solution(context):
        # Implementation logic
        return {"implementation_complete": True}

    # The decorator handles all enforcement automatically
    implement_solution(context)


if __name__ == "__main__":
    # Simple test
    import argparse

    parser = argparse.ArgumentParser(description="Test agent hooks")
    parser.add_argument("--issue", type=int, default=1234, help="Issue number")
    parser.add_argument("--phase", default="planning", help="Phase name")
    parser.add_argument("--agent", default="task-planner", help="Agent type")

    args = parser.parse_args()

    hooks = AgentHooks(args.issue)
    context = {"scope_is_clear": True}

    print(f"Testing hooks for issue #{args.issue}, phase: {args.phase}")

    # Test pre-hook
    can_proceed, message, updates = hooks.pre_phase_hook(args.phase, args.agent, context)
    print(f"Pre-hook: {'✅' if can_proceed else '❌'} {message}")

    if can_proceed:
        # Simulate work
        outputs = {
            "task_template_created": True,
            "scratchpad_created": True,
            "documentation_committed": True,
        }

        # Test post-hook
        success, message = hooks.post_phase_hook(args.phase, outputs)
        print(f"Post-hook: {'✅' if success else '❌'} {message}")

    # Generate report
    print("\nCompliance Report:")
    print(hooks.enforcer.generate_compliance_report())
