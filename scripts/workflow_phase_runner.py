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


class PhaseRunner:
    """Runs workflow phases individually with timeout protection."""

    # Configurable timeout per phase
    PHASE_TIMEOUT_SECONDS = 90
    
    PHASES = [
        ("investigation", 0, "Analyze issue scope and requirements"),
        ("planning", 1, "Create implementation plan"),
        ("implementation", 2, "Execute code changes"),
        ("validation", 3, "Run tests and quality checks"),
        ("pr_creation", 4, "Create pull request"),
        ("monitoring", 5, "Set up PR monitoring"),
    ]

    def __init__(self, issue_number: int, hybrid: bool = False):
        self.issue_number = issue_number
        self.hybrid = hybrid
        self.completed_phases = []
        self.state_file = Path(f".workflow-phase-state-{issue_number}.json")

    def run_all_phases(self, skip_phases: Optional[List[int]] = None) -> bool:
        """Run all phases with automatic progression."""
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
                self.completed_phases.append(phase_num)
                self._save_state()
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
                cmd, capture_output=True, text=True, timeout=self.PHASE_TIMEOUT_SECONDS, cwd=Path.cwd()
            )

            if result.returncode == 0:
                return True
            else:
                print(f"❌ Phase failed with exit code: {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏱️  Phase timed out after {self.PHASE_TIMEOUT_SECONDS} seconds")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    def _load_state(self) -> None:
        """Load previous execution state."""
        if self.state_file.exists():

            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.completed_phases = data.get("completed_phases", [])
                    print(f"📂 Loaded state: {len(self.completed_phases)} phases completed")
            except Exception as e:
                print(f"⚠️  Could not load state: {e}")

    def _save_state(self) -> None:
        """Save execution state."""

        try:
            with open(self.state_file, "w") as f:
                json.dump({"completed_phases": self.completed_phases}, f)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")

    def _cleanup_state(self) -> None:
        """Remove state file after successful completion."""
        if self.state_file.exists():
            self.state_file.unlink()


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
