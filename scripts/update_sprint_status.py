#!/usr/bin/env python3
"""
Update sprint status for GitHub Actions workflow
This extracts the inline Python from sprint-start.yml
"""

import sys
import yaml
from pathlib import Path


def update_sprint_status(sprint_id: str) -> int:
    """Update sprint status from planning to in_progress"""
    try:
        sprint_file = Path(f"context/sprints/{sprint_id}.yaml")

        if not sprint_file.exists():
            print(f"Sprint file not found: {sprint_file}")
            return 1

        with open(sprint_file, "r") as f:
            data = yaml.safe_load(f)

        if data["status"] == "planning":
            data["status"] = "in_progress"

            # Update first pending phase to in_progress
            for phase in data.get("phases", []):
                if phase["status"] == "pending":
                    phase["status"] = "in_progress"
                    break

            with open(sprint_file, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            print(f'Sprint {data["title"]} started successfully')
            return 0
        else:
            print(f'Sprint is already {data["status"]}')
            return 0

    except Exception as e:
        print(f"Error updating sprint: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_sprint_status.py <sprint-id>")
        sys.exit(1)

    sys.exit(update_sprint_status(sys.argv[1]))
