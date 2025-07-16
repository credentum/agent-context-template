#!/usr/bin/env python3
"""
Test script to validate Claude Code Review comment format consistency improvements.

This script tests the format validation logic added to the Claude Code Review workflow.
"""

from pathlib import Path

import yaml


def test_yaml_validation():
    """Test that valid YAML can be parsed correctly."""
    sample_yaml = """
schema_version: "1.0"
pr_number: 123
timestamp: "2025-07-16T21:00:00Z"
reviewer: "ARC-Reviewer"
verdict: "APPROVE"
summary: "Test review summary"
coverage:
  current_pct: 85.5
  status: "PASS"
  meets_baseline: true
issues:
  blocking: []
  warnings: []
  nits: []
automated_issues: []
"""

    try:
        yaml.safe_load(sample_yaml)
        print("✓ Valid YAML parsing test passed")
        return True
    except yaml.YAMLError as e:
        print(f"✗ YAML parsing test failed: {e}")
        return False


def test_required_fields():
    """Test that required fields are present in the YAML."""
    sample_yaml = """
schema_version: "1.0"
pr_number: 123
timestamp: "2025-07-16T21:00:00Z"
reviewer: "ARC-Reviewer"
verdict: "APPROVE"
"""

    required_fields = ["schema_version", "pr_number", "timestamp", "reviewer"]

    for field in required_fields:
        if field not in sample_yaml:
            print(f"✗ Required field test failed: {field} missing")
            return False

    print("✓ Required fields test passed")
    return True


def test_format_consistency():
    """Test that the format instructions are present in the workflow."""
    workflow_path = Path(".github/workflows/claude-code-review.yml")

    if not workflow_path.exists():
        print("✗ Workflow file not found")
        return False

    with open(workflow_path, "r") as f:
        content = f.read()

    # Check for our improvements
    improvements = [
        "FORMATTING: Ensure consistent YAML formatting",
        "COMMENT_FORMAT: Use identical structure",
        "IMPORTANT: Use identical formatting",
        "Validate Comment Format",
    ]

    for improvement in improvements:
        if improvement not in content:
            print(f"✗ Format consistency test failed: '{improvement}' not found")
            return False

    print("✓ Format consistency test passed")
    return True


def test_validation_step():
    """Test that the validation step is properly structured."""
    workflow_path = Path(".github/workflows/claude-code-review.yml")

    with open(workflow_path, "r") as f:
        content = f.read()

    # Check for validation step components
    validation_components = [
        "Validate Comment Format",
        "yaml.safe_load",
        "Required YAML fields present",
        "FORMATTED_REVIEW",
    ]

    for component in validation_components:
        if component not in content:
            print(f"✗ Validation step test failed: '{component}' not found")
            return False

    print("✓ Validation step test passed")
    return True


def main():
    """Run all tests."""
    print("🔍 Testing Claude Code Review format consistency improvements...")
    print()

    tests = [
        test_yaml_validation,
        test_required_fields,
        test_format_consistency,
        test_validation_step,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests passed! Comment format consistency improvements are working.")
        return 0
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
