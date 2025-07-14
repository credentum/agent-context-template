#!/usr/bin/env python3
"""
Update coverage metrics from pytest output and generate reports
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def run_coverage_test():
    """Run pytest with coverage and capture output"""
    print("Running coverage tests...")
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "tests/",
            "--cov=src",
            "--cov-report=term-missing",
            "--tb=short",
            "-q",
        ],
        capture_output=True,
        text=True,
    )
    return result.stdout, result.stderr


def parse_coverage_output(output):
    """Parse coverage output to extract metrics"""
    metrics: Dict[str, Any] = {"modules": {}, "overall": {}}

    # Parse module coverage
    module_pattern = r"^(src/[\w/]+\.py)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%"
    for line in output.split("\n"):
        match = re.match(module_pattern, line)
        if match:
            module_path = match.group(1)
            metrics["modules"][module_path] = {
                "statements": int(match.group(2)),
                "missing": int(match.group(3)),
                "branch": int(match.group(4)),
                "branch_partial": int(match.group(5)),
                "coverage": float(match.group(6)),
            }

    # Parse overall coverage
    total_pattern = r"^TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%"
    for line in output.split("\n"):
        match = re.match(total_pattern, line)
        if match:
            metrics["overall"] = {
                "statements": int(match.group(1)),
                "missing": int(match.group(2)),
                "branch": int(match.group(3)),
                "branch_partial": int(match.group(4)),
                "line_coverage": float(match.group(5)),
            }
            # Calculate branch coverage
            if metrics["overall"]["branch"] > 0:
                branch_covered = metrics["overall"]["branch"] - metrics["overall"]["branch_partial"]
                metrics["overall"]["branch_coverage"] = round(
                    (branch_covered / metrics["overall"]["branch"]) * 100, 2
                )
            else:
                metrics["overall"]["branch_coverage"] = 0.0

    # Parse test summary
    test_pattern = r"(\d+) passed(?:, (\d+) skipped)?"
    for line in output.split("\n"):
        if "passed" in line:
            match = re.search(test_pattern, line)
            if match:
                metrics["overall"]["tests_passed"] = int(match.group(1))
                metrics["overall"]["tests_skipped"] = int(match.group(2)) if match.group(2) else 0

    return metrics


def update_coverage_summary(metrics):
    """Update coverage-summary.json with new metrics"""
    summary_path = Path("coverage-summary.json")

    # Load existing summary
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    else:
        summary = {}

    # Update with new metrics
    summary["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary["overall"] = {
        "line_coverage": metrics["overall"]["line_coverage"],
        "branch_coverage": metrics["overall"]["branch_coverage"],
        "statements": metrics["overall"]["statements"],
        "missing": metrics["overall"]["missing"],
        "tests_passed": metrics["overall"].get("tests_passed", 0),
        "tests_skipped": metrics["overall"].get("tests_skipped", 0),
    }

    # Keep existing targets
    if "targets" not in summary:
        summary["targets"] = {"line_coverage": 85, "branch_coverage": 70, "mutation_score": 80}

    # Update top and critical modules
    sorted_modules = sorted(
        metrics["modules"].items(), key=lambda x: x[1]["coverage"], reverse=True
    )

    summary["top_modules"] = [
        {"name": name.replace("src/", ""), "coverage": data["coverage"]}
        for name, data in sorted_modules[:5]
    ]

    summary["critical_modules"] = [
        {"name": name.replace("src/", ""), "coverage": data["coverage"]}
        for name, data in sorted_modules
        if data["coverage"] < 40
    ][:5]

    # Save updated summary
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def update_readme_badges(summary):
    """Update README.md badges with current metrics"""
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    with open(readme_path) as f:
        content = f.read()

    # Update coverage badge
    coverage = summary["overall"]["line_coverage"]
    color = "green" if coverage >= 85 else "yellow" if coverage >= 70 else "red"
    coverage_badge = f"![Coverage](https://img.shields.io/badge/coverage-{coverage}%25-{color})"

    # Update branch coverage badge
    branch_coverage = summary["overall"]["branch_coverage"]
    branch_color = (
        "green" if branch_coverage >= 70 else "yellow" if branch_coverage >= 50 else "red"
    )
    branch_badge = (
        f"![Branch Coverage](https://img.shields.io/badge/"
        f"branch%20coverage-{branch_coverage}%25-{branch_color})"
    )

    # Replace badges in content
    content = re.sub(r"!\[Coverage\]\([^)]+\)", coverage_badge, content)

    # Add branch coverage badge if not present
    if "Branch Coverage" not in content:
        content = content.replace(coverage_badge, f"{coverage_badge}\n{branch_badge}")
    else:
        content = re.sub(r"!\[Branch Coverage\]\([^)]+\)", branch_badge, content)

    # Update test count
    tests_passed = summary["overall"]["tests_passed"]
    tests_badge = f"![Tests](https://img.shields.io/badge/tests-{tests_passed}%20passed-green)"
    content = re.sub(r"!\[Tests\]\([^)]+\)", tests_badge, content)

    with open(readme_path, "w") as f:
        f.write(content)


def main():
    """Main function"""
    # Run coverage tests
    stdout, stderr = run_coverage_test()

    if "TOTAL" not in stdout:
        print("Error: Could not parse coverage output")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        sys.exit(1)

    # Parse metrics
    metrics = parse_coverage_output(stdout)

    # Update files
    summary = update_coverage_summary(metrics)
    update_readme_badges(summary)

    # Print summary
    print("\nCoverage updated:")
    print(f"  Line Coverage: {summary['overall']['line_coverage']}%")
    print(f"  Branch Coverage: {summary['overall']['branch_coverage']}%")
    print(
        f"  Tests: {summary['overall']['tests_passed']} passed, "
        f"{summary['overall']['tests_skipped']} skipped"
    )
    print("\nFiles updated:")
    print("  - coverage-summary.json")
    print("  - README.md")


if __name__ == "__main__":
    main()
