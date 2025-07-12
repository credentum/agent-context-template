#!/usr/bin/env python3
"""
Validate coverage-summary.json against schema
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Installing jsonschema...")
    import subprocess

    subprocess.run([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema


def validate_coverage_summary():
    """Validate coverage summary against schema"""
    # Load schema
    schema_path = Path("schemas/coverage-summary.schema.json")
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}")
        return False

    with open(schema_path) as f:
        schema = json.load(f)

    # Load summary
    summary_path = Path("coverage-summary.json")
    if not summary_path.exists():
        print(f"Error: Summary file not found: {summary_path}")
        return False

    with open(summary_path) as f:
        summary = json.load(f)

    # Validate
    try:
        jsonschema.validate(instance=summary, schema=schema)
        print("✓ coverage-summary.json is valid")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"✗ Validation error: {e.message}")
        print(f"  Path: {' -> '.join(str(p) for p in e.path)}")
        return False
    except jsonschema.exceptions.SchemaError as e:
        print(f"✗ Schema error: {e.message}")
        return False


if __name__ == "__main__":
    if not validate_coverage_summary():
        sys.exit(1)
