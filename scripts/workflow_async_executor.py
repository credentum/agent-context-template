#!/usr/bin/env python3
"""
Async workflow executor that runs phases in background with progress tracking.
Avoids timeout by launching workflow in background and providing status updates.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class AsyncWorkflowExecutor:
    """Execute workflow asynchronously with progress tracking."""

    def __init__(self, issue_number: int):
        self.issue_number = issue_number
        self.log_file = Path(f".workflow-async-{issue_number}.log")
        self.pid_file = Path(f".workflow-async-{issue_number}.pid")
        self.status_file = Path(f".workflow-async-{issue_number}.status")

    def start_workflow(self, hybrid: bool = False, skip_phases: Optional[list] = None):
        """Start workflow in background."""
        # Check if already running
        if self._is_running():
            print(f"❌ Workflow already running for issue #{self.issue_number}")
            print(f"💡 Check status: python {__file__} status {self.issue_number}")
            return False

        # Build command
        cmd = [
            "python",
            "/workspaces/agent-context-template/scripts/workflow_phase_runner.py",
            str(self.issue_number),
        ]

        if hybrid:
            cmd.append("--hybrid")

        if skip_phases:
            cmd.extend(["--skip-phases"] + [str(p) for p in skip_phases])

        # Start in background
        with open(self.log_file, "w") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
            )

        # Save PID
        with open(self.pid_file, "w") as f:
            f.write(str(process.pid))

        # Initial status
        self._update_status("running", "Workflow started")

        print(f"✅ Workflow started in background (PID: {process.pid})")
        print(f"📋 Check status: python {__file__} status {self.issue_number}")
        print(f"📄 View logs: tail -f {self.log_file}")
        return True

    def check_status(self) -> Dict:
        """Check workflow status."""
        if not self.status_file.exists():
            return {"status": "not_found", "message": "No workflow found"}

        try:
            with open(self.status_file) as f:
                status = json.load(f)

            # Check if process is still running
            if status.get("status") == "running" and not self._is_running():
                status["status"] = "completed"
                status["message"] = "Workflow completed"
                self._update_status("completed", "Workflow completed")

            return status
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_logs(self, tail_lines: int = 50) -> str:
        """Get recent log lines."""
        if not self.log_file.exists():
            return "No logs found"

        try:
            result = subprocess.run(
                ["tail", f"-{tail_lines}", str(self.log_file)], capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            return f"Error reading logs: {e}"

    def stop_workflow(self) -> bool:
        """Stop running workflow."""
        if not self._is_running():
            print("No running workflow found")
            return False

        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())

            # Terminate process group
            import signal
            import os

            os.killpg(os.getpgid(pid), signal.SIGTERM)

            self._update_status("stopped", "Workflow stopped by user")
            print(f"✅ Workflow stopped (PID: {pid})")
            return True
        except Exception as e:
            print(f"❌ Error stopping workflow: {e}")
            return False

    def _is_running(self) -> bool:
        """Check if workflow process is running."""
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())

            # Check if process exists
            import os

            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            return False

    def _update_status(self, status: str, message: str):
        """Update status file."""
        data = {
            "status": status,
            "message": message,
            "updated": datetime.now().isoformat(),
            "issue_number": self.issue_number,
        }

        with open(self.status_file, "w") as f:
            json.dump(data, f, indent=2)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Async workflow executor")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start workflow")
    start_parser.add_argument("issue_number", type=int)
    start_parser.add_argument("--hybrid", action="store_true")
    start_parser.add_argument("--skip-phases", type=int, nargs="+")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check status")
    status_parser.add_argument("issue_number", type=int)

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View logs")
    logs_parser.add_argument("issue_number", type=int)
    logs_parser.add_argument("--tail", type=int, default=50)

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop workflow")
    stop_parser.add_argument("issue_number", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    executor = AsyncWorkflowExecutor(args.issue_number)

    if args.command == "start":
        success = executor.start_workflow(args.hybrid, args.skip_phases)
        sys.exit(0 if success else 1)
    elif args.command == "status":
        status = executor.check_status()
        print(json.dumps(status, indent=2))
    elif args.command == "logs":
        print(executor.get_logs(args.tail))
    elif args.command == "stop":
        executor.stop_workflow()


if __name__ == "__main__":
    main()
