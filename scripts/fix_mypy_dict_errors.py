#!/usr/bin/env python3
"""Fix common MyPy dictionary indexing errors"""

import re
from pathlib import Path

# Common fixes for dictionary indexing errors
FIXES = [
    # test_traceability_matrix.py - Add type annotations for report dict
    {
        "file": "tests/test_traceability_matrix.py",
        "line": 120,
        "old": "        report = {",
        "new": "        report: dict[str, Any] = {"
    },
    {
        "file": "tests/test_traceability_matrix.py", 
        "line": 8,
        "old": "from typing import Dict",
        "new": "from typing import Any, Dict"
    },
    
    # test_metadata_validation.py - Add str() casts for datetime operations
    {
        "file": "tests/test_metadata_validation.py",
        "line": 51,
        "old": '        start = datetime.fromisoformat(sprint_metadata["start_date"])',
        "new": '        start = datetime.fromisoformat(str(sprint_metadata["start_date"]))'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 52,
        "old": '        end = datetime.fromisoformat(sprint_metadata["end_date"])',
        "new": '        end = datetime.fromisoformat(str(sprint_metadata["end_date"]))'
    },
    
    # Add str() casts for string operations
    {
        "file": "tests/test_metadata_validation.py",
        "line": 70,
        "old": '        assert decision_metadata["decision_id"].startswith("DEC-")',
        "new": '        assert str(decision_metadata["decision_id"]).startswith("DEC-")'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 95,
        "old": '        assert trace_metadata["trace_id"].startswith("trace-")',
        "new": '        assert str(trace_metadata["trace_id"]).startswith("trace-")'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 177,
        "old": '        assert agent_metadata["agent_name"].endswith("_agent")',
        "new": '        assert str(agent_metadata["agent_name"]).endswith("_agent")'
    },
    
    # Add int() casts for numeric operations
    {
        "file": "tests/test_metadata_validation.py",
        "line": 180,
        "old": '        assert agent_metadata["max_retries"] >= 0',
        "new": '        assert int(agent_metadata["max_retries"]) >= 0'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 181,
        "old": '        assert agent_metadata["timeout_seconds"] > 0',
        "new": '        assert int(agent_metadata["timeout_seconds"]) > 0'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 197,
        "old": '        assert connection_metadata["port"] > 0',
        "new": '        assert int(connection_metadata["port"]) > 0'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 198,
        "old": '        assert connection_metadata["port"] <= 65535',
        "new": '        assert int(connection_metadata["port"]) <= 65535'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 200,
        "old": '        assert connection_metadata["connection_timeout"] > 0',
        "new": '        assert int(connection_metadata["connection_timeout"]) > 0'
    },
    {
        "file": "tests/test_metadata_validation.py",
        "line": 201,
        "old": '        assert connection_metadata["read_timeout"] >= connection_metadata["connection_timeout"]',
        "new": '        assert int(connection_metadata["read_timeout"]) >= int(connection_metadata["connection_timeout"])'
    }
]

def apply_fixes():
    """Apply all fixes"""
    for fix in FIXES:
        file_path = Path(fix["file"])
        if not file_path.exists():
            print(f"Skip: {file_path} does not exist")
            continue
            
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Apply fix at specific line (0-indexed)
        line_idx = fix["line"] - 1
        if line_idx < len(lines):
            if fix["old"] in lines[line_idx]:
                lines[line_idx] = lines[line_idx].replace(fix["old"], fix["new"])
                print(f"Fixed: {file_path}:{fix['line']}")
            else:
                print(f"Skip: Line {fix['line']} in {file_path} doesn't match expected")
        
        # Write back
        file_path.write_text('\n'.join(lines))

if __name__ == "__main__":
    apply_fixes()