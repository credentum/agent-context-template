#!/usr/bin/env python3
"""Script to help fix MyPy type errors systematically"""

import re
import subprocess
from collections import defaultdict


def run_mypy():
    """Run mypy and collect errors"""
    result = subprocess.run(["mypy", "tests/"], capture_output=True, text=True)
    return result.stdout


def parse_errors(output):
    """Parse mypy output into structured format"""
    errors = defaultdict(list)
    pattern = r"(.*?):(\d+): error: (.*?) \[(.*?)\]"

    for line in output.split("\n"):
        match = re.match(pattern, line)
        if match:
            file_path, line_num, error_msg, error_code = match.groups()
            errors[file_path].append(
                {"line": int(line_num), "message": error_msg, "code": error_code}
            )

    return errors


def categorize_errors(errors):
    """Categorize errors by type"""
    categories = defaultdict(list)

    for file_path, file_errors in errors.items():
        for error in file_errors:
            msg = error["message"]

            if 'Value of type "object" is not indexable' in msg:
                categories["object_indexing"].append((file_path, error))
            elif "has no attribute" in msg:
                categories["no_attribute"].append((file_path, error))
            elif "Argument" in msg and "has incompatible type" in msg:
                categories["arg_type"].append((file_path, error))
            elif 'Value of type "Collection[str]"' in msg:
                categories["collection_indexing"].append((file_path, error))
            elif "Unsupported" in msg and "operand" in msg:
                categories["operand_type"].append((file_path, error))
            elif 'Unused "type: ignore"' in msg:
                categories["unused_ignore"].append((file_path, error))
            else:
                categories["other"].append((file_path, error))

    return categories


def main():
    print("Running MyPy to collect errors...")
    output = run_mypy()

    errors = parse_errors(output)
    categories = categorize_errors(errors)

    print(f"\nTotal files with errors: {len(errors)}")
    print(f"Total errors: {sum(len(e) for e in errors.values())}")

    print("\nError categories:")
    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {category}: {len(items)} errors")

    # Focus on object indexing errors first
    print("\n\nObject indexing errors (top 10):")
    for file_path, error in categories["object_indexing"][:10]:
        print(f"  {file_path}:{error['line']}")
        print(f"    {error['message']}")


if __name__ == "__main__":
    main()
