#!/usr/bin/env python3
"""
Phase-based workflow runner that executes phases individually to avoid timeouts.
Each phase runs in its own process with automatic progression.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from workflow_config import WorkflowConfig
from workflow_enforcer import WorkflowEnforcer


class PhaseRunner:
    """Runs workflow phases individually with timeout protection."""

    PHASES = [
        ("investigation", 0, "Analyze issue scope and requirements"),
        ("planning", 1, "Create implementation plan"),
        ("implementation", 2, "Execute code changes"),
        ("validation", 3, "Run tests and quality checks"),
        ("pr_creation", 4, "Create pull request"),
        ("monitoring", 5, "Set up PR monitoring"),
    ]

    def __init__(self, issue_number: int, hybrid: bool = False):
        # Validate issue_number to prevent command injection
        if not isinstance(issue_number, int) or issue_number <= 0:
            raise ValueError(f"Issue number must be a positive integer, got: {issue_number}")

        self.issue_number = issue_number
        self.hybrid = hybrid
        self.completed_phases: List[int] = []
        # Use WorkflowEnforcer's state file for unified state management
        self.state_file = Path(f".workflow-state-{issue_number}.json")
        self.enforcer = WorkflowEnforcer(issue_number)

    def run_all_phases(self, skip_phases: Optional[List[int]] = None) -> bool:
        """
        Run all workflow phases with automatic progression.

        Args:
            skip_phases: Optional list of phase numbers (0-5) to skip

        Returns:
            bool: True if all phases completed successfully, False if any phase failed

        The method will load any previous state, execute each phase in order,
        save state after each successful phase, and clean up state on completion.
        """
        skip_phases = skip_phases or []

        print(f"🚀 Starting phase-based workflow for issue #{self.issue_number}")
        if self.hybrid:
            print("🔄 Using hybrid mode with specialist sub-agents")

        # Load any previous state
        self._load_state()

        for phase_name, phase_num, description in self.PHASES:
            if phase_num in skip_phases:
                print(f"\n⏭️  Skipping phase {phase_num}: {phase_name}")
                continue

            if phase_num in self.completed_phases:
                print(f"\n✅ Phase {phase_num} already completed: {phase_name}")
                continue

            print(f"\n{'='*60}")
            print(f"📍 Phase {phase_num}: {phase_name} - {description}")
            print(f"⏱️  Starting at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            success = self._run_single_phase(phase_num)

            if success:
                # Mark phase as completed in WorkflowEnforcer
                phase_name, _, _ = self.PHASES[phase_num]
                outputs = {f"phase_{phase_num}_complete": True}
                
                # For phases that were executed, mark them as complete
                # This ensures state synchronization
                if phase_name not in self.enforcer.state.get("phases", {}):
                    # Phase wasn't tracked by enforcer, add it
                    self.enforcer.state["phases"][phase_name] = {
                        "phase_name": phase_name,
                        "status": "completed",
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "outputs": outputs,
                        "errors": [],
                        "agent_type": "phase-runner"
                    }
                    self.enforcer._save_state()
                
                self.completed_phases.append(phase_num)
                print(f"✅ Phase {phase_num} completed successfully")

                # Brief pause between phases
                time.sleep(2)
            else:
                print(f"❌ Phase {phase_num} failed - workflow paused")
                print(f"💡 To resume: python {__file__} {self.issue_number} --resume")
                return False

        print(f"\n🎉 All phases completed for issue #{self.issue_number}")
        self._cleanup_state()
        return True

    def _run_single_phase(self, phase_num: int) -> bool:
        """Run a single phase with timeout protection."""
        # Build command for single phase
        cmd = [
            "python",
            "/workspaces/agent-context-template/scripts/workflow_cli.py",
            "workflow-issue",
            str(self.issue_number),
            "--skip-phases",
        ]

        # Skip all phases except the one we want
        for i in range(len(self.PHASES)):
            if i != phase_num:
                cmd.append(str(i))

        if self.hybrid:
            cmd.append("--hybrid")

        try:
            # Run with configurable timeout per phase (under 2-minute limit)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=WorkflowConfig.PHASE_TIMEOUT_SECONDS,
                cwd=Path.cwd(),
                shell=False,  # Explicit for security
            )

            if result.returncode == 0:
                return True
            else:
                print(f"❌ Phase failed with exit code: {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏱️  Phase timed out after {WorkflowConfig.PHASE_TIMEOUT_SECONDS} seconds")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def _load_state(self) -> None:
        """Load previous execution state from WorkflowEnforcer."""
        # Get state from WorkflowEnforcer
        state = self.enforcer.get_current_state()
        
        # Convert phase names to phase numbers
        self.completed_phases = []
        for phase_name, phase_num, _ in self.PHASES:
            if phase_name in state.get("phases", {}):
                phase_state = state["phases"][phase_name]
                if phase_state.get("status") == "completed":
                    self.completed_phases.append(phase_num)
        
        if self.completed_phases:
            print(f"📂 Loaded state: {len(self.completed_phases)} phases completed")

    def _save_state(self) -> None:
        """Save execution state through WorkflowEnforcer."""
        # State is already saved by WorkflowEnforcer after each phase completion
        # This method is kept for compatibility but doesn't need to do anything
        pass

    def _cleanup_state(self) -> None:
        """Remove state file after successful completion."""
        # Keep the state file for workflow history
        # Only mark workflow as complete
        if hasattr(self, 'enforcer'):
            self.enforcer.state["workflow_complete"] = True
            self.enforcer.state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            self.enforcer._save_state()


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase-based workflow runner")
    parser.add_argument("issue_number", type=int, help="GitHub issue number")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid mode")
    parser.add_argument("--resume", action="store_true", help="Resume from last phase")
    parser.add_argument("--skip-phases", type=int, nargs="+", help="Phases to skip")

    args = parser.parse_args()

    runner = PhaseRunner(args.issue_number, args.hybrid)

    # Handle resume
    if args.resume:
        runner._load_state()

    success = runner.run_all_phases(args.skip_phases)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
