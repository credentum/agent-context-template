#!/usr/bin/env python3
"""
Post CI results to GitHub PR using Checks API or Status API.

This script parses claude-ci.sh output and posts standardized results
to GitHub for verification by the ci-local-verifier workflow.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def parse_claude_ci_output(output_file: str) -> Dict[str, Any]:
    """Parse claude-ci.sh JSON output into standardized format."""
    try:
        with open(output_file, "r") as f:
            claude_output = json.load(f)
    except FileNotFoundError:
        print(f"Error: Output file '{output_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in output file: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract relevant data from claude-ci output
    checks = {}

    # Coverage data
    if "coverage" in claude_output:
        coverage_data = claude_output["coverage"]
        checks["coverage"] = {
            "passed": coverage_data.get("percentage", 0) >= coverage_data.get("threshold", 85.0),
            "percentage": coverage_data.get("percentage", 0),
            "threshold": coverage_data.get("threshold", 85.0),
            "files_covered": coverage_data.get("files_covered", 0),
            "lines_covered": coverage_data.get("lines_covered", 0),
            "lines_total": coverage_data.get("lines_total", 0),
        }

    # Test results
    if "tests" in claude_output:
        test_data = claude_output["tests"]
        checks["tests"] = {
            "passed": test_data.get("failed", 0) == 0,
            "total": test_data.get("total", 0),
            "passed_count": test_data.get("passed", 0),
            "failed": test_data.get("failed", 0),
            "skipped": test_data.get("skipped", 0),
            "duration": test_data.get("duration", "0s"),
        }

    # Linting results
    if "lint" in claude_output:
        lint_data = claude_output["lint"]
        checks["linting"] = {
            "passed": lint_data.get("passed", False),
            "issues": lint_data.get("issues", []),
            "tools": lint_data.get("tools", {}),
        }

    # Type checking results
    if "type_check" in claude_output:
        type_data = claude_output["type_check"]
        checks["type_check"] = {
            "passed": type_data.get("passed", False),
            "errors": type_data.get("errors", 0),
            "files_checked": type_data.get("files_checked", 0),
        }

    return {
        "version": "1.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "commit_sha": get_current_commit_sha(),
        "branch": get_current_branch(),
        "runner": "local",
        "claude_ci_version": claude_output.get("version", "unknown"),
        "checks": checks,
        "summary": claude_output.get("summary", {}),
        "raw_output": claude_output,  # Include raw output for debugging
    }


def get_current_commit_sha() -> str:
    """Get the current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def get_current_branch() -> str:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"


def post_to_github_checks(results: Dict[str, Any], repo: str, token: str) -> bool:
    """Post results to GitHub using Checks API."""
    # For Phase 1, we'll use gh CLI which handles auth automatically
    commit_sha = results["commit_sha"]

    # Determine overall status
    all_passed = all(check.get("passed", False) for check in results["checks"].values())

    conclusion = "success" if all_passed else "failure"

    # Build summary
    summary_lines = [
        f"# CI Results - {results['timestamp']}",
        f"**Runner**: {results['runner']}",
        f"**Branch**: {results['branch']}",
        f"**Commit**: {commit_sha[:8]}",
        "",
        "## Check Results",
    ]

    for check_name, check_data in results["checks"].items():
        status = "✅" if check_data.get("passed") else "❌"
        summary_lines.append(f"- {status} **{check_name.title()}**")

        if check_name == "coverage":
            summary_lines.append(
                f"  - Coverage: {check_data['percentage']:.1f}% "
                f"(threshold: {check_data['threshold']:.1f}%)"
            )
        elif check_name == "tests":
            summary_lines.append(
                f"  - Tests: {check_data['passed_count']}/{check_data['total']} passed"
            )
            if check_data["failed"] > 0:
                summary_lines.append(f"  - Failed: {check_data['failed']}")
        elif check_name == "linting":
            if check_data["issues"]:
                summary_lines.append(f"  - Issues: {len(check_data['issues'])}")

    summary = "\n".join(summary_lines)

    # Create check run using gh CLI
    cmd = [
        "gh",
        "api",
        f"/repos/{repo}/check-runs",
        "--method",
        "POST",
        "--field",
        "name=Local CI Results",
        "--field",
        f"head_sha={commit_sha}",
        "--field",
        "status=completed",
        "--field",
        f"conclusion={conclusion}",
        "--field",
        f'completed_at={results["timestamp"]}',
        "--field",
        "output[title]=Local CI Execution Results",
        "--field",
        f"output[summary]={summary}",
    ]

    # Add annotations for failures
    annotations = []
    for check_name, check_data in results["checks"].items():
        if not check_data.get("passed"):
            if check_name == "linting" and check_data.get("issues"):
                for issue in check_data["issues"][:10]:  # Limit to 10 annotations
                    annotations.append(
                        {
                            "path": issue.get("file", "unknown"),
                            "start_line": issue.get("line", 1),
                            "end_line": issue.get("line", 1),
                            "annotation_level": "failure",
                            "message": issue.get("message", "Linting issue"),
                            "title": f"{check_name}: {issue.get('code', 'issue')}",
                        }
                    )

    if annotations:
        cmd.extend(["--field", f"output[annotations]={json.dumps(annotations)}"])

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully posted check run: {conclusion}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error posting to GitHub: {e}", file=sys.stderr)
        print(f"stdout: {e.stdout}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return False


def post_as_pr_comment(results: Dict[str, Any], repo: str, pr_number: str) -> bool:
    """Post results as a PR comment (fallback method)."""
    # Build comment body
    comment_lines = [
        "## 🤖 Local CI Results",
        "",
        f"**Timestamp**: {results['timestamp']}",
        f"**Commit**: {results['commit_sha'][:8]}",
        f"**Branch**: {results['branch']}",
        "",
        "### Check Results",
        "",
    ]

    all_passed = True
    for check_name, check_data in results["checks"].items():
        passed = check_data.get("passed", False)
        all_passed &= passed
        status = "✅" if passed else "❌"

        if check_name == "coverage":
            comment_lines.append(
                f"{status} **Coverage**: {check_data['percentage']:.1f}% "
                f"(threshold: {check_data['threshold']:.1f}%)"
            )
        elif check_name == "tests":
            comment_lines.append(
                f"{status} **Tests**: {check_data['passed_count']}/{check_data['total']} passed"
            )
            if check_data["failed"] > 0:
                comment_lines.append(f"  - ❌ {check_data['failed']} tests failed")
        elif check_name == "linting":
            issues_count = len(check_data.get("issues", []))
            linting_status = "Passed" if passed else f"{issues_count} issues"
            comment_lines.append(f"{status} **Linting**: {linting_status}")
        elif check_name == "type_check":
            errors_count = check_data.get("errors", 0)
            type_check_status = "Passed" if passed else f"{errors_count} errors"
            comment_lines.append(f"{status} **Type Check**: {type_check_status}")

    comment_lines.extend(
        [
            "",
            "---",
            f"*Overall Result*: {'✅ **PASSED**' if all_passed else '❌ **FAILED**'}",
            "",
            "<details>",
            "<summary>View raw results</summary>",
            "",
            "```json",
            json.dumps(results, indent=2),
            "```",
            "</details>",
        ]
    )

    comment_body = "\n".join(comment_lines)

    # Post comment using gh CLI
    cmd = ["gh", "pr", "comment", pr_number, "--repo", repo, "--body", comment_body]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully posted PR comment to #{pr_number}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error posting PR comment: {e}", file=sys.stderr)
        return False


def save_results_artifact(results: Dict[str, Any], output_dir: str = ".") -> str:
    """Save results to a JSON file for artifact storage."""
    filename = (
        f"ci-results-{results['commit_sha'][:8]}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    filepath = Path(output_dir) / filename

    with open(filepath, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {filepath}")
    return str(filepath)


def main():
    parser = argparse.ArgumentParser(description="Post CI results to GitHub")
    parser.add_argument("output_file", help="Path to claude-ci.sh JSON output file")
    parser.add_argument(
        "--repo",
        default=None,
        help="GitHub repository (owner/repo). If not provided, detected from git remote",
    )
    parser.add_argument("--pr", type=str, help="PR number to post results to (uses comment method)")
    parser.add_argument(
        "--method",
        choices=["checks", "comment", "both"],
        default="checks",
        help="Method to use for posting results",
    )
    parser.add_argument(
        "--save-artifact", action="store_true", help="Save results as JSON artifact"
    )
    parser.add_argument("--artifact-dir", default=".", help="Directory to save artifacts")

    args = parser.parse_args()

    # Parse CI results
    results = parse_claude_ci_output(args.output_file)

    # Detect repository if not provided
    if not args.repo:
        try:
            # Get repo from git remote
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "owner,name"],
                capture_output=True,
                text=True,
                check=True,
            )
            repo_info = json.loads(result.stdout)
            args.repo = f"{repo_info['owner']['login']}/{repo_info['name']}"
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            print("Error: Could not detect repository. Please provide --repo", file=sys.stderr)
            sys.exit(1)

    print(f"Posting results for repo: {args.repo}")

    # Save artifact if requested
    if args.save_artifact:
        save_results_artifact(results, args.artifact_dir)

    # Post results
    success = False

    if args.method in ["checks", "both"]:
        # Check if we have required permissions
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            print("Warning: GITHUB_TOKEN not set, using gh CLI auth", file=sys.stderr)

        success = post_to_github_checks(results, args.repo, token)

    if args.method in ["comment", "both"] and args.pr:
        success = post_as_pr_comment(results, args.repo, args.pr) or success
    elif args.method == "comment" and not args.pr:
        print("Error: --pr required when using comment method", file=sys.stderr)
        sys.exit(1)

    if success:
        print("Results posted successfully!")

        # Output overall status for scripting
        all_passed = all(check.get("passed", False) for check in results["checks"].values())
        sys.exit(0 if all_passed else 1)
    else:
        print("Failed to post results", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
