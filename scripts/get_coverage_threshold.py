#!/usr/bin/env python3
"""
Get coverage threshold from centralized configuration.
Used by CI workflows to avoid hardcoded values.
"""

import json
import sys
from pathlib import Path


def get_coverage_threshold():
    """Get the minimum coverage threshold (baseline - tolerance_buffer)."""
    # Try multiple possible locations for the config file
    possible_paths = [
        Path(".coverage-config.json"),  # Current directory
        Path(__file__).parent.parent / ".coverage-config.json",  # Project root
        Path.cwd() / ".coverage-config.json",  # Explicit current working directory
    ]

    config_path = None
    for path in possible_paths:
        if path.exists():
            config_path = path
            break

    if config_path is None:
        print(
            f"Error: .coverage-config.json not found in any of: {[str(p) for p in possible_paths]}",
            file=sys.stderr,
        )
        print(f"Current working directory: {Path.cwd()}", file=sys.stderr)
        print(f"Script location: {Path(__file__).parent}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path) as f:
            config = json.load(f)

        baseline = config.get("baseline", 80.0)
        tolerance_buffer = config.get("tolerance_buffer", 5.0)
        minimum_threshold = baseline - tolerance_buffer

        return minimum_threshold

    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error reading coverage config: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    threshold = get_coverage_threshold()
    print(f"{threshold:.1f}")
