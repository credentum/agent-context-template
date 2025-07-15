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
    config_path = Path(".coverage-config.json")

    if not config_path.exists():
        print("Error: .coverage-config.json not found", file=sys.stderr)
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
