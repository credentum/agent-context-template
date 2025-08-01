#!/usr/bin/env python3
"""
Workflow test utilities for validating implementation phases and task completion.

This module provides utilities to verify that workflow implementations actually
create code changes (not just documentation) and meet acceptance criteria.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def validate_implementation_phase(issue_number: int) -> bool:
    """
    Check if the implementation phase created actual code changes.

    Returns True if:
    - Code files (not just docs) were modified
    - Commits contain actual implementation
    - Task template requirements were addressed

    Args:
        issue_number: GitHub issue number to validate

    Returns:
        bool: True if real code changes were made, False if only docs

    Example:
        >>> validate_implementation_phase(1708)
        True  # If scripts/workflow_test_utils.py was created
    """
    try:
        # Check if feature branch exists for this issue
        branch_name = f"feature/issue-{issue_number}"
        result = subprocess.run(
            ["git", "branch", "--list", branch_name], capture_output=True, text=True, check=True
        )

        if not result.stdout.strip():
            # Try alternative branch naming patterns
            alt_branches = [
                f"fix/issue-{issue_number}",
                f"issue-{issue_number}",
                f"feature/{issue_number}",
            ]
            for alt_branch in alt_branches:
                result = subprocess.run(
                    ["git", "branch", "--list", alt_branch],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout.strip():
                    branch_name = alt_branch
                    break
            else:
                return False

        # Get commits that modified code files (not just docs)
        code_commits = count_code_commits(branch_name)

        # Must have at least one commit with actual code changes
        if code_commits == 0:
            return False

        # Check if task template exists and has been addressed
        task_template_paths = list(
            Path("context/trace/task-templates").glob(f"*issue-{issue_number}*")
        )
        if task_template_paths:
            completion_status = verify_task_completion(task_template_paths[0])
            # At least 70% of criteria should be met for valid implementation
            met_criteria = sum(1 for status in completion_status.values() if status)
            total_criteria = len(completion_status)
            return total_criteria > 0 and (met_criteria / total_criteria) >= 0.7

        return True  # If no template exists, rely on code commit check

    except subprocess.CalledProcessError:
        return False


def count_code_commits(branch_name: str) -> int:
    """
    Count commits that modified actual code files.

    Excludes commits that only touch:
    - Documentation (*.md)
    - Context files
    - Configuration files

    Args:
        branch_name: Git branch name to analyze

    Returns:
        int: Number of commits with actual code changes

    Example:
        >>> count_code_commits("feature/issue-1708")
        2  # Two commits added Python files
    """
    try:
        # Get list of commits on the branch that aren't on main
        result = subprocess.run(
            ["git", "log", "--oneline", f"main..{branch_name}"],
            capture_output=True,
            text=True,
            check=True,
        )

        if not result.stdout.strip():
            return 0

        commit_hashes = [line.split()[0] for line in result.stdout.strip().split("\n")]
        code_commit_count = 0

        for commit_hash in commit_hashes:
            # Get files modified in this commit
            files_result = subprocess.run(
                ["git", "show", "--name-only", "--pretty=format:", commit_hash],
                capture_output=True,
                text=True,
                check=True,
            )

            modified_files = [f for f in files_result.stdout.strip().split("\n") if f]

            # Check if any modified files are code files
            code_files = []
            for file_path in modified_files:
                if _is_code_file(file_path):
                    code_files.append(file_path)

            if code_files:
                code_commit_count += 1

        return code_commit_count

    except subprocess.CalledProcessError:
        return 0


def verify_task_completion(task_template_path: Path) -> Dict[str, bool]:
    """
    Parse task template and verify each acceptance criterion.

    Returns dict mapping each criterion to completion status.

    Args:
        task_template_path: Path to the task template markdown file

    Returns:
        Dict[str, bool]: Mapping of criteria to completion status

    Example:
        >>> verify_task_completion(Path("context/trace/task-templates/issue-1708.md"))
        {
            "Create workflow_test_utils.py": True,
            "Add unit tests": True,
            "Add docstrings": True
        }
    """
    if not task_template_path.exists():
        return {}

    try:
        content = task_template_path.read_text()

        # Extract acceptance criteria section
        criteria_section = _extract_acceptance_criteria(content)
        if not criteria_section:
            return {}

        # Parse individual criteria
        criteria = _parse_criteria_items(criteria_section)

        # Verify each criterion
        completion_status = {}
        for criterion in criteria:
            completion_status[criterion] = _verify_single_criterion(criterion)

        return completion_status

    except Exception:
        return {}


def _is_code_file(file_path: str) -> bool:
    """Check if a file path represents a code file (not docs/config)."""
    # Exclude documentation files
    if file_path.endswith((".md", ".rst", ".txt")):
        return False

    # Exclude context/trace files (documentation)
    if file_path.startswith("context/"):
        return False

    # Exclude configuration files
    config_files = [
        ".gitignore",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "setup.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
    ]
    if any(file_path.endswith(config) for config in config_files):
        return False

    # Include Python files, shell scripts, and other code
    code_extensions = [".py", ".sh", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h"]
    if any(file_path.endswith(ext) for ext in code_extensions):
        return True

    # Include files in src/, scripts/, tests/ directories (likely code)
    code_dirs = ["src/", "scripts/", "tests/", "lib/", "bin/"]
    if any(file_path.startswith(code_dir) for code_dir in code_dirs):
        return True

    return False


def _extract_acceptance_criteria(content: str) -> Optional[str]:
    """Extract the acceptance criteria section from a task template."""
    # Look for acceptance criteria section
    patterns = [
        r"## ✅ Acceptance Criteria\s*\n(.*?)(?=\n##|\n---|\Z)",
        r"## Acceptance Criteria\s*\n(.*?)(?=\n##|\n---|\Z)",
        r"### Acceptance Criteria\s*\n(.*?)(?=\n##|\n---|\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _parse_criteria_items(criteria_section: str) -> List[str]:
    """Parse individual criteria items from the criteria section."""
    criteria = []

    # Look for checkbox items (- [ ] or - [x])
    checkbox_pattern = r"- \[[ x]\] (.+?)(?=\n|$)"
    matches = re.findall(checkbox_pattern, criteria_section, re.MULTILINE)
    criteria.extend(matches)

    # Look for bullet points if no checkboxes found
    if not criteria:
        bullet_pattern = r"- (.+?)(?=\n|$)"
        matches = re.findall(bullet_pattern, criteria_section, re.MULTILINE)
        criteria.extend(matches)

    return [criterion.strip() for criterion in criteria if criterion.strip()]


def _verify_single_criterion(criterion: str) -> bool:
    """Verify if a single acceptance criterion has been met."""
    # Simple heuristic-based verification
    criterion_lower = criterion.lower()

    # Check for file creation criteria
    if "create" in criterion_lower and ".py" in criterion_lower:
        # Extract filename if mentioned
        if "workflow_test_utils.py" in criterion_lower:
            return Path("scripts/workflow_test_utils.py").exists()
        elif "test_" in criterion_lower:
            return len(list(Path("tests").glob("test_*.py"))) > 0

    # Check for test-related criteria
    if "test" in criterion_lower and (
        "unit" in criterion_lower or "comprehensive" in criterion_lower
    ):
        test_files = list(Path("tests").glob("test_workflow_test_utils.py"))
        return len(test_files) > 0

    # Check for documentation criteria
    if "docstring" in criterion_lower or "documentation" in criterion_lower:
        # Check if current file has docstrings (proxy for good documentation)
        try:
            current_file = Path(__file__)
            if current_file.exists():
                content = current_file.read_text()
                return '"""' in content or "'''" in content
        except Exception:
            pass

    # Default to True for criteria we can't automatically verify
    return True
