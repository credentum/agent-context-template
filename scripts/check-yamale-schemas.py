#!/usr/bin/env python3
"""
Custom YAML checker for Yamale schema files.
Validates YAML syntax while accepting multi-document format.
"""

import sys
from pathlib import Path

import yaml


def check_yaml_file(filepath: Path) -> bool:
    """Check if a YAML file is syntactically valid."""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Try to parse all documents
        list(yaml.safe_load_all(content))
        return True
    except yaml.YAMLError as e:
        print(f"Error in {filepath}: {e}")
        return False


def main():
    """Check all schema files passed as arguments."""
    if len(sys.argv) < 2:
        print("Usage: check-yamale-schemas.py <file1> [file2] ...")
        sys.exit(1)

    # Get the repository root for validation
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent
    allowed_dir = repo_root / "context" / "schemas"

    all_valid = True
    for filepath in sys.argv[1:]:
        path = Path(filepath).resolve()

        # Validate path is within allowed directory
        try:
            path.relative_to(allowed_dir)
        except ValueError:
            print(f"Error: File {filepath} is outside allowed schemas directory")
            sys.exit(1)

        if path.exists() and path.suffix in [".yaml", ".yml"]:
            if not check_yaml_file(path):
                all_valid = False
        else:
            print(f"Skipping non-YAML file: {filepath}")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
