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

    all_valid = True
    for filepath in sys.argv[1:]:
        path = Path(filepath)
        if path.exists() and path.suffix in [".yaml", ".yml"]:
            if not check_yaml_file(path):
                all_valid = False
        else:
            print(f"Skipping non-YAML file: {filepath}")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
