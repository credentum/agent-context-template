#!/usr/bin/env python3
"""Comprehensive MyPy fixes for all test files"""

import re
import subprocess
from pathlib import Path
from typing import List, Tuple

def get_mypy_errors():
    """Get all MyPy errors"""
    result = subprocess.run(["mypy", "tests/"], capture_output=True, text=True)
    return result.stdout

def parse_error_line(line: str) -> Tuple[str, int, str]:
    """Parse a mypy error line"""
    match = re.match(r'(.*?):(\d+): error: (.*)', line)
    if match:
        return match.group(1), int(match.group(2)), match.group(3)
    return None, 0, ""

def fix_dict_indexing_errors():
    """Fix dictionary indexing errors by adding type casts"""
    errors = get_mypy_errors()
    fixes = []
    
    for line in errors.split('\n'):
        if 'Value of type "Collection[str]" is not indexable' in line:
            file_path, line_num, _ = parse_error_line(line)
            if file_path:
                fixes.append((file_path, line_num, "collection_indexing"))
        elif 'has no attribute' in line and '"object"' in line:
            file_path, line_num, _ = parse_error_line(line)
            if file_path:
                fixes.append((file_path, line_num, "object_attribute"))
        elif 'Unsupported operand types' in line:
            file_path, line_num, _ = parse_error_line(line)
            if file_path:
                fixes.append((file_path, line_num, "operand_type"))
    
    return fixes

def apply_common_fixes():
    """Apply common type fixes across all test files"""
    
    # Fix test_metadata_validation.py - remaining issues
    fixes = [
        ("tests/test_metadata_validation.py", 258, 
         'assert ref["type"] in ["decision", "design", "sprint", "trace"]',
         'assert ref.get("type") in ["decision", "design", "sprint", "trace"]'),
        
        ("tests/test_metadata_validation.py", 259,
         'assert isinstance(ref["id"], str)',
         'assert isinstance(ref.get("id"), str)'),
         
        ("tests/test_metadata_validation.py", 260,
         'assert len(ref["id"]) > 0',
         'assert len(str(ref.get("id", ""))) > 0'),
         
        ("tests/test_metadata_validation.py", 272,
         'current_version = float(document["schema_version"])',
         'current_version = float(str(document["schema_version"]))'),
         
        ("tests/test_metadata_validation.py", 273,
         'min_version = float(document["min_compatible_version"])',
         'min_version = float(str(document["min_compatible_version"]))'),
         
        ("tests/test_metadata_validation.py", 327,
         'name_parts = metric_metadata["metric_name"].split(".")',
         'name_parts = str(metric_metadata["metric_name"]).split(".")'),
    ]
    
    # Apply fixes
    for file_path, line_num, old_text, new_text in fixes:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            lines = content.split('\n')
            
            if line_num - 1 < len(lines):
                if old_text in lines[line_num - 1]:
                    lines[line_num - 1] = lines[line_num - 1].replace(old_text, new_text)
                    path.write_text('\n'.join(lines))
                    print(f"Fixed {file_path}:{line_num}")

def add_type_ignores_for_complex_cases():
    """Add type: ignore comments for complex cases that are hard to fix"""
    
    # Files with complex typing issues
    complex_files = [
        "tests/test_property_based_extended.py",
        "tests/test_reproducibility.py", 
        "tests/test_integration_ci_workflow.py",
        "tests/test_sigstore_verification.py"
    ]
    
    for file_path in complex_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            
            # Add type annotations import if not present
            if "from typing import" not in content:
                lines = content.split('\n')
                # Find first non-comment, non-docstring line
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                        if 'import' in line:
                            insert_idx = i + 1
                            break
                
                lines.insert(insert_idx, "from typing import Any, Dict, List, Optional")
                content = '\n'.join(lines)
                path.write_text(content)
                print(f"Added typing imports to {file_path}")

def main():
    print("Applying comprehensive MyPy fixes...")
    
    # Apply common fixes
    apply_common_fixes()
    
    # Add type imports
    add_type_ignores_for_complex_cases()
    
    print("\nDone! Run 'mypy tests/' to check remaining errors.")

if __name__ == "__main__":
    main()