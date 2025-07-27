#!/usr/bin/env python3
"""
Security fixes for workflow validator custom regex patterns.
This file contains the security validation method to be added to workflow-validator.py
"""

import json
import re
import subprocess
from typing import List


def _validate_custom_regex(self, pattern: str) -> bool:
    """
    Validate custom regex pattern for security.

    Args:
        pattern: The custom regex pattern to validate

    Returns:
        bool: True if pattern is safe to use, False otherwise
    """
    if not isinstance(pattern, str):
        return False

    # Check for reasonable length to prevent DoS
    if len(pattern) > 1000:
        return False

    # Check for dangerous regex patterns that could cause ReDoS
    dangerous_patterns = [
        r"\(\?\!",  # Negative lookahead
        r"\(\?\=",  # Positive lookahead
        r"\(\?\<\!",  # Negative lookbehind
        r"\(\?\<\=",  # Positive lookbehind
        r"\(\?\:",  # Non-capturing group (can be misused)
        r"\*\+",  # Catastrophic backtracking pattern
        r"\+\*",  # Catastrophic backtracking pattern
        r"\{\d+,\}",  # Unbounded quantifiers
    ]

    for dangerous in dangerous_patterns:
        if re.search(dangerous, pattern):
            return False

    # Ensure pattern has exactly one {issue} placeholder
    if pattern.count("{issue}") != 1:
        return False

    # Verify it's a valid regex by compiling a test version
    try:
        test_pattern = pattern.format(issue=123)
        re.compile(test_pattern)
    except (re.error, ValueError, KeyError):
        return False

    return True


def _validate_branch_prefixes(self, prefixes: List[str]) -> List[str]:
    """
    Validate and sanitize branch prefix list.

    Args:
        prefixes: List of branch prefixes to validate

    Returns:
        List[str]: Validated and sanitized prefixes
    """
    if not isinstance(prefixes, list):
        return []

    validated_prefixes = []
    for prefix in prefixes:
        if not isinstance(prefix, str):
            continue

        # Remove any dangerous characters
        sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", prefix)

        # Ensure prefix is not empty and reasonable length
        if sanitized and 1 <= len(sanitized) <= 50:
            validated_prefixes.append(sanitized)

    # Return default if no valid prefixes
    if not validated_prefixes:
        return ["fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"]

    return validated_prefixes


# Updated _check_pr_created method with security fixes
def _check_pr_created_secure(self) -> bool:
    """Check if PR was created with flexible branch pattern matching and security validation."""
    # Get configured branch prefixes or use defaults
    branch_config = self.config.get("branch_patterns", {})
    raw_prefixes = branch_config.get(
        "prefixes", ["fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"]
    )

    # Validate and sanitize branch prefixes
    branch_prefixes = self._validate_branch_prefixes(raw_prefixes)

    try:
        # Get all PRs to search through - using JSON for safer parsing
        result = subprocess.run(
            ["gh", "pr", "list", "--json", "headRefName", "--limit", "50"],
            capture_output=True,
            shell=False,  # Explicitly disable shell
            text=True,
        )

        if result.returncode == 0:
            prs = json.loads(result.stdout)

            issue_pattern = f"{self.issue_number}-"

            # Check if any PR branch contains our issue number
            for pr in prs:
                branch_name = pr.get("headRefName", "")
                if not isinstance(branch_name, str):
                    continue

                # Check standard patterns: prefix/issue_number-*
                for prefix in branch_prefixes:
                    if branch_name.startswith(f"{prefix}/{issue_pattern}"):
                        return True

                # Check custom regex if configured
                custom_pattern = branch_config.get("custom_regex")
                if custom_pattern and self._validate_custom_regex(custom_pattern):
                    try:
                        pattern = custom_pattern.format(issue=self.issue_number)
                        if re.match(pattern, branch_name):
                            return True
                    except (re.error, ValueError):
                        # Invalid regex or format string, skip
                        continue

        return False
    except (json.JSONDecodeError, Exception):
        # Fall back to original behavior if JSON parsing fails
        result = subprocess.run(
            ["gh", "pr", "list", "--head", f"fix/{self.issue_number}-", "--limit", "10"],
            capture_output=True,
            shell=False,
            text=True,
        )
        output = result.stdout.strip()
        return f"fix/{self.issue_number}-" in output or f"feature/{self.issue_number}-" in output
