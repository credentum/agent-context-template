#!/usr/bin/env python3
"""
GitHub Label Validation Utility

Validates that labels exist before use and suggests alternatives.
Helps prevent workflow failures from non-existent labels.
"""

import json
import subprocess
import sys
from difflib import get_close_matches
from typing import List, Optional, Tuple


def get_existing_labels() -> List[str]:
    """Fetch all existing labels from the repository."""
    try:
        result = subprocess.run(
            ["gh", "label", "list", "--json", "name"],
            capture_output=True,
            text=True,
            check=True,
        )
        labels = json.loads(result.stdout)
        return [label["name"] for label in labels]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error fetching labels: {e}", file=sys.stderr)
        return []


def validate_label(label: str, existing_labels: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate if a label exists and suggest alternatives if not.

    Returns:
        Tuple of (is_valid, suggested_alternative)
    """
    if label in existing_labels:
        return True, None

    # Find close matches
    close_matches = get_close_matches(label, existing_labels, n=1, cutoff=0.6)
    if close_matches:
        return False, close_matches[0]

    # Default fallback based on common patterns
    if "test" in label.lower():
        return False, "component:testing"
    elif "infra" in label.lower():
        return False, "component:infra"
    elif "bug" in label.lower():
        return False, "bug"
    elif "feat" in label.lower():
        return False, "enhancement"
    elif "phase" in label.lower():
        # Extract phase number if present
        import re

        match = re.search(r"phase[:\-_]?(\d+)", label, re.IGNORECASE)
        if match:
            phase_num = match.group(1)
            phase_label = f"phase:{phase_num}"
            if phase_label in existing_labels:
                return False, phase_label

    return False, "sprint-current"  # Safe default


def ensure_label_exists(label: str) -> str:
    """
    Check if label exists and return a valid alternative if not.

    This is the main function workflows should use.
    """
    existing_labels = get_existing_labels()
    is_valid, suggestion = validate_label(label, existing_labels)

    if is_valid:
        return label

    if suggestion:
        print(
            f"Warning: Label '{label}' does not exist. Using '{suggestion}' instead.",
            file=sys.stderr,
        )
        return suggestion

    # Should not reach here due to default in validate_label
    print(
        f"Warning: Label '{label}' does not exist. Using 'sprint-current' as default.",
        file=sys.stderr,
    )
    return "sprint-current"


def main():
    """CLI interface for label validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate GitHub labels")
    parser.add_argument("labels", nargs="+", help="Labels to validate")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only validate, don't suggest alternatives",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    existing_labels = get_existing_labels()
    results = []

    for label in args.labels:
        is_valid, suggestion = validate_label(label, existing_labels)
        result = {
            "label": label,
            "valid": is_valid,
            "suggestion": suggestion if not args.dry_run else None,
        }
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        all_valid = True
        for result in results:
            if result["valid"]:
                print(f"✓ '{result['label']}' is valid")
            else:
                all_valid = False
                if args.dry_run:
                    print(f"✗ '{result['label']}' does not exist")
                else:
                    print(
                        f"✗ '{result['label']}' does not exist → suggest: '{result['suggestion']}'"
                    )

        sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
