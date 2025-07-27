#!/usr/bin/env python3
"""
ARC-Reviewer: Advanced Review and Coverage validator for Pull Requests

Extracted from GitHub Actions workflow claude-code-review.yml to enable local execution.
Maintains identical review criteria and YAML output format.

Usage:
    from src.agents.arc_reviewer import ARCReviewer

    reviewer = ARCReviewer()
    result = reviewer.review_pr(pr_number=123, base_branch="main")
    print(reviewer.format_yaml_output(result))
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Import LLMReviewer for LLM-based review mode
try:
    from .llm_reviewer import LLMReviewer

    LLMREVIEWER_AVAILABLE = True
except ImportError:
    LLMREVIEWER_AVAILABLE = False


class ARCReviewer:
    """
    Advanced Review and Coverage validator for Pull Requests.

    Implements the same review logic as the GitHub Actions workflow
    claude-code-review.yml but in a standalone Python module for local execution.
    """

    def __init__(
        self,
        verbose: bool = False,
        timeout: int = 120,
        skip_coverage: bool = False,
        use_llm: Optional[bool] = None,
    ):
        """Initialize the ARC-Reviewer.

        Args:
            verbose: Enable verbose output
            timeout: Maximum seconds for command execution (default: 120)
            skip_coverage: Skip coverage check for faster execution
            use_llm: Force LLM mode (True), rule-based mode (False), or auto-detect (None)
        """
        self.verbose = verbose
        self.timeout = timeout
        self.skip_coverage = skip_coverage
        self.coverage_config = self._load_coverage_config()
        self.repo_root = Path(__file__).parent.parent.parent

        # Determine review mode
        self.use_llm = use_llm
        if self.use_llm is None:
            # Auto-detect: use LLM if API key is available
            api_key = os.getenv("ANTHROPIC_API_KEY")
            self.use_llm = bool(api_key and LLMREVIEWER_AVAILABLE)

        # Initialize LLM reviewer if requested and available
        self.llm_reviewer = None
        if self.use_llm:
            if not LLMREVIEWER_AVAILABLE:
                if self.verbose:
                    print("❌ LLM mode requested but anthropic package not available")
                self.use_llm = False
            else:
                try:
                    self.llm_reviewer = LLMReviewer(verbose=verbose, timeout=timeout)
                    if self.verbose:
                        print("✅ LLM mode enabled with Claude API")
                except Exception as e:
                    if self.verbose:
                        print(f"❌ Failed to initialize LLM reviewer: {e}")
                    self.use_llm = False

        if not self.use_llm and self.verbose:
            print("📋 Using rule-based review mode")

    def _load_coverage_config(self) -> Dict[str, Any]:
        """Load coverage configuration from .coverage-config.json."""
        config_path = Path(__file__).parent.parent.parent / ".coverage-config.json"
        try:
            with open(config_path, "r") as f:
                config_data: Dict[str, Any] = json.load(f)
                return config_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if self.verbose:
                print(f"Warning: Could not load coverage config: {e}")
            return {"baseline": 78.0, "target": 85.0, "validator_target": 90.0}

    def _run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        if cwd is None:
            cwd = self.repo_root

        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=self.timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {self.timeout} seconds"
        except Exception as e:
            return 1, "", str(e)

    def _get_changed_files(self, base_branch: str = "main") -> List[str]:
        """Get list of files changed in current branch vs base."""
        cmd = ["git", "diff", "--name-only", f"origin/{base_branch}...HEAD"]
        exit_code, stdout, stderr = self._run_command(cmd)

        if exit_code != 0:
            if self.verbose:
                print(f"Warning: Could not get changed files: {stderr}")
            return []

        return [f.strip() for f in stdout.split("\n") if f.strip()]

    def _check_coverage(self) -> Dict[str, Any]:
        """Check test coverage and return coverage data."""
        # First check if coverage.json exists and is recent
        coverage_json_path = self.repo_root / "coverage.json"
        if coverage_json_path.exists():
            # Check if file is less than 5 minutes old
            import time

            file_age = time.time() - coverage_json_path.stat().st_mtime
            if file_age < 300:  # 5 minutes
                if self.verbose:
                    print("📊 Using cached coverage data (< 5 minutes old)")
                # Skip running pytest, just read existing coverage
                coverage_data = {
                    "current_pct": 0.0,
                    "status": "FAIL",
                    "meets_baseline": False,
                    "details": {},
                }
                try:
                    with open(coverage_json_path, "r") as f:
                        cov_data = json.load(f)
                        total = cov_data.get("totals", {})
                        current_pct = total.get("percent_covered", 0.0)
                        coverage_data["current_pct"] = round(current_pct, 2)
                        coverage_data["meets_baseline"] = (
                            current_pct >= self.coverage_config["baseline"]
                        )
                        coverage_data["status"] = (
                            "PASS" if coverage_data["meets_baseline"] else "FAIL"
                        )

                        # Extract validator-specific coverage
                        validator_coverage = {}
                        for filename, file_data in cov_data.get("files", {}).items():
                            if "validators/" in filename:
                                validator_coverage[filename] = file_data.get("summary", {}).get(
                                    "percent_covered", 0.0
                                )
                        coverage_data["details"] = {
                            "validators": validator_coverage,
                            "total_lines": total.get("num_statements", 0),
                            "covered_lines": total.get("covered_lines", 0),
                        }
                except (json.JSONDecodeError, KeyError) as e:
                    if self.verbose:
                        print(f"Warning: Could not parse cached coverage.json: {e}")
                    # Fall through to run pytest
                else:
                    return coverage_data

        # Run pytest with coverage (with reduced timeout for ARC reviewer)
        if self.verbose:
            print("📊 Running pytest with coverage...")
        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=json",
            "--cov-report=term-missing",
            "-m",
            "not integration and not e2e",
            "--quiet",
            "--maxfail=1",  # Stop after first failure to save time
        ]

        exit_code, stdout, stderr = self._run_command(cmd)

        coverage_data = {
            "current_pct": 0.0,
            "status": "FAIL",
            "meets_baseline": False,
            "details": {},
        }

        # Try to read coverage.json if it exists
        coverage_json_path = self.repo_root / "coverage.json"
        if coverage_json_path.exists():
            try:
                with open(coverage_json_path, "r") as f:
                    cov_data = json.load(f)

                current_pct = cov_data.get("totals", {}).get("percent_covered", 0.0)
                coverage_data["current_pct"] = round(current_pct, 2)
                coverage_data["meets_baseline"] = current_pct >= self.coverage_config["baseline"]
                coverage_data["status"] = "PASS" if coverage_data["meets_baseline"] else "FAIL"

                # Check validator modules specifically
                validator_coverage = {}
                for filename, file_data in cov_data.get("files", {}).items():
                    if "validators/" in filename:
                        validator_coverage[filename] = file_data.get("summary", {}).get(
                            "percent_covered", 0.0
                        )

                coverage_data["details"] = {
                    "validators": validator_coverage,
                    "overall": current_pct,
                }

            except (json.JSONDecodeError, FileNotFoundError) as e:
                if self.verbose:
                    print(f"Warning: Could not parse coverage.json: {e}")

        return coverage_data

    def _check_code_quality(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Check code quality using pre-commit hooks."""
        issues = []

        # Run pre-commit on all files
        cmd = ["pre-commit", "run", "--all-files"]
        exit_code, stdout, stderr = self._run_command(cmd)

        if exit_code != 0:
            issues.append(
                {
                    "description": "Pre-commit hooks failed",
                    "file": "multiple",
                    "line": 0,
                    "category": "code_quality",
                    "fix_guidance": "Run 'pre-commit run --all-files' locally and fix issues",
                }
            )

        return issues

    def _check_context_integrity(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Check context system integrity."""
        issues = []

        # Check for context files without schema_version
        context_files = [
            f for f in changed_files if f.startswith("context/") and f.endswith((".yml", ".yaml"))
        ]

        for file_path in context_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                try:
                    # First check for document start marker
                    with open(full_path, "r") as f:
                        first_line = f.readline().strip()
                        if first_line != "---":
                            issues.append(
                                {
                                    "description": (
                                        "Missing document start marker (---) in YAML file"
                                    ),
                                    "file": file_path,
                                    "line": 1,
                                    "category": "context_integrity",
                                    "fix_guidance": "Add '---' as the first line of the YAML file",
                                }
                            )
                        # Reset file pointer
                        f.seek(0)
                        content = yaml.safe_load(f)

                    if isinstance(content, dict) and "schema_version" not in content:
                        issues.append(
                            {
                                "description": "Missing schema_version in context file",
                                "file": file_path,
                                "line": 1,
                                "category": "context_integrity",
                                "fix_guidance": "Add 'schema_version: \"1.0\"' to the YAML file",
                            }
                        )
                except (yaml.YAMLError, FileNotFoundError) as e:
                    issues.append(
                        {
                            "description": f"Invalid YAML in context file: {e}",
                            "file": file_path,
                            "line": 1,
                            "category": "context_integrity",
                            "fix_guidance": "Fix YAML syntax errors",
                        }
                    )

        return issues

    def _check_test_coverage_specific(
        self, changed_files: List[str], coverage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check specific test coverage requirements."""
        issues = []

        # Check validators coverage specifically
        validator_files = [f for f in changed_files if "src/validators/" in f and f.endswith(".py")]
        validator_target = self.coverage_config.get("validator_target", 90.0)

        for validator_file in validator_files:
            file_coverage = (
                coverage_data.get("details", {}).get("validators", {}).get(validator_file, 0.0)
            )
            if file_coverage < validator_target:
                issues.append(
                    {
                        "description": (
                            f"Validator coverage {file_coverage}% below target "
                            f"{validator_target}%"
                        ),
                        "file": validator_file,
                        "line": 0,
                        "category": "test_coverage",
                        "fix_guidance": (
                            f"Add tests to achieve {validator_target}% coverage for " f"validators"
                        ),
                    }
                )

        return issues

    def _check_security(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Check for security issues."""
        issues = []

        # Check for potential secrets in code
        secret_patterns = ["password", "secret", "key", "token", "api_key"]

        for file_path in changed_files:
            # Skip this file itself to avoid false positives from the patterns list
            if file_path.endswith("arc_reviewer.py"):
                continue

            if file_path.endswith((".py", ".yaml", ".yml", ".json")):
                full_path = self.repo_root / file_path
                if full_path.exists():
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read().lower()

                        # Check line by line for more accurate detection
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            line_lower = line.lower()
                            for pattern in secret_patterns:
                                # Look for pattern in quotes with assignment
                                if (
                                    f'"{pattern}"' in line_lower or f"'{pattern}'" in line_lower
                                ) and ("=" in line or ":" in line):
                                    # Skip if it's in a patterns list definition
                                    if "patterns" in line_lower and "[" in line:
                                        continue
                                    # Skip if it's clearly a variable name
                                    if f"{pattern}_" in line_lower or f"_{pattern}" in line_lower:
                                        continue
                                    # Skip if it's in test data (dictionary literal)
                                    if (
                                        "{" in line
                                        and "}" in line
                                        and file_path.startswith("tests/")
                                    ):
                                        continue
                                    # Skip if it's just a dictionary key without actual secret value
                                    if f'"{pattern}":' in line and (
                                        "value" in line or "[" in line or "{" in line
                                    ):
                                        continue

                                    issues.append(
                                        {
                                            "description": f"Potential hardcoded secret: {pattern}",
                                            "file": file_path,
                                            "line": i + 1,
                                            "category": "security",
                                            "fix_guidance": (
                                                "Use environment variables or secrets management"
                                            ),
                                        }
                                    )
                    except (UnicodeDecodeError, FileNotFoundError):
                        pass  # Skip files that can't be read as text

        return issues

    def _check_runtime_errors(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """
        Check for runtime errors in Python scripts.

        Args:
            changed_files: List of changed file paths

        Returns:
            List of runtime issues found
        """
        runtime_issues = []

        for file_path in changed_files:
            if not file_path.endswith(".py"):
                continue

            # Skip test files for runtime validation
            if "test" in file_path or file_path.startswith("tests/"):
                continue

            # Check if it's an executable script
            full_path = self.repo_root / file_path
            if not full_path.exists():
                continue

            # Try to run the script with --help to detect basic runtime errors
            if file_path.startswith("scripts/"):
                cmd = ["python", str(full_path), "--help"]
                exit_code, stdout, stderr = self._run_command(cmd)

                if exit_code != 0 and "usage:" not in stderr.lower():
                    # Check for specific known issues
                    if "unrecognized arguments" in stderr:
                        runtime_issues.append(
                            {
                                "severity": "high",
                                "file": file_path,
                                "line": 0,
                                "message": (
                                    f"Script has command line parsing error: {stderr.strip()}"
                                ),
                                "category": "runtime_error",
                            }
                        )
                    elif "AttributeError" in stderr or "ImportError" in stderr:
                        runtime_issues.append(
                            {
                                "severity": "high",
                                "file": file_path,
                                "line": 0,
                                "message": f"Script has runtime error: {stderr.strip()}",
                                "category": "runtime_error",
                            }
                        )

        return runtime_issues

    def review_pr(
        self, pr_number: Optional[int] = None, base_branch: str = "main", runtime_test: bool = False
    ) -> Dict[str, Any]:
        """
        Perform complete PR review and return structured results.

        Args:
            pr_number: PR number (optional, used for metadata)
            base_branch: Base branch to compare against
            runtime_test: Enable runtime validation of Python scripts

        Returns:
            Dictionary with review results
        """
        # Delegate to LLM reviewer if available and enabled
        if self.use_llm and self.llm_reviewer:
            if self.verbose:
                print("🤖 Using LLM-based review mode")
            return self.llm_reviewer.review_pr(pr_number=pr_number, base_branch=base_branch)

        # Fall back to rule-based review
        if self.verbose:
            print("🔍 Starting rule-based ARC-Reviewer analysis...")

        # Get changed files
        changed_files = self._get_changed_files(base_branch)
        if self.verbose:
            print(f"📁 Analyzing {len(changed_files)} changed files")

        # Check coverage (unless skipped)
        if self.skip_coverage:
            if self.verbose:
                print("⚡ Skipping coverage check for faster execution")
            coverage_data = {
                "current_pct": 0.0,
                "status": "SKIPPED",
                "meets_baseline": True,  # Don't fail on skipped coverage
                "details": {},
            }
        else:
            coverage_data = self._check_coverage()
            if self.verbose:
                baseline = self.coverage_config["baseline"]
                current = coverage_data["current_pct"]
                print(f"📊 Coverage: {current}% (baseline: {baseline}%)")

        # Collect all issues
        blocking_issues: List[Dict[str, Any]] = []
        warning_issues: List[Dict[str, Any]] = []
        nit_issues: List[Dict[str, Any]] = []

        # Coverage check (blocking if below baseline and not skipped)
        if not coverage_data["meets_baseline"] and coverage_data["status"] != "SKIPPED":
            blocking_issues.append(
                {
                    "description": (
                        f"Coverage {coverage_data['current_pct']}% below baseline "
                        f"{self.coverage_config['baseline']}%"
                    ),
                    "file": "overall",
                    "line": 0,
                    "category": "test_coverage",
                    "fix_guidance": (
                        f"Add tests to achieve {self.coverage_config['baseline']}% " f"coverage"
                    ),
                }
            )

        # Code quality checks
        quality_issues = self._check_code_quality(changed_files)
        blocking_issues.extend(quality_issues)

        # Context integrity checks
        context_issues = self._check_context_integrity(changed_files)
        warning_issues.extend(context_issues)

        # Specific coverage checks
        coverage_issues = self._check_test_coverage_specific(changed_files, coverage_data)
        warning_issues.extend(coverage_issues)

        # Security checks
        security_issues = self._check_security(changed_files)
        blocking_issues.extend(security_issues)

        # Runtime validation checks (if enabled)
        if runtime_test:
            if self.verbose:
                print("🏃 Performing runtime validation...")
            runtime_issues = self._check_runtime_errors(changed_files)
            blocking_issues.extend(runtime_issues)

        # Determine verdict
        verdict = "APPROVE" if not blocking_issues else "REQUEST_CHANGES"

        # Create summary
        issue_count = len(blocking_issues) + len(warning_issues) + len(nit_issues)
        if issue_count == 0:
            summary = "All checks passed - ready for merge"
        else:
            summary = (
                f"Found {len(blocking_issues)} blocking, {len(warning_issues)} "
                f"warning, {len(nit_issues)} nit issues"
            )

        return {
            "schema_version": "1.0",
            "pr_number": pr_number or 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reviewer": "ARC-Reviewer",
            "verdict": verdict,
            "summary": summary,
            "coverage": coverage_data,
            "issues": {
                "blocking": blocking_issues,
                "warnings": warning_issues,
                "nits": nit_issues,
            },
            "automated_issues": [],  # Could be populated with follow-up suggestions
        }

    def format_yaml_output(self, review_data: Dict[str, Any]) -> str:
        """Format review results as YAML string matching workflow output."""
        return yaml.dump(review_data, default_flow_style=False, sort_keys=False)

    def review_and_output(
        self, pr_number: Optional[int] = None, base_branch: str = "main", runtime_test: bool = False
    ) -> None:
        """Perform review and print YAML output."""
        results = self.review_pr(pr_number, base_branch, runtime_test=runtime_test)
        print(self.format_yaml_output(results))

        # Exit with non-zero code if verdict is REQUEST_CHANGES
        if results.get("verdict") == "REQUEST_CHANGES":
            import sys

            sys.exit(1)


def main():
    """Command line interface for ARC-Reviewer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ARC-Reviewer: Advanced Review and Coverage validator"
    )
    parser.add_argument("--pr", type=int, help="PR number (optional)")
    parser.add_argument("--base", default="main", help="Base branch to compare against")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--runtime-test", action="store_true", help="Enable runtime validation of Python scripts"
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Timeout in seconds for commands (default: 120)"
    )
    parser.add_argument(
        "--skip-coverage", action="store_true", help="Skip coverage check for faster execution"
    )
    parser.add_argument(
        "--llm", action="store_true", help="Force LLM mode (requires ANTHROPIC_API_KEY)"
    )
    parser.add_argument("--no-llm", action="store_true", help="Force rule-based mode (disable LLM)")

    args = parser.parse_args()

    # Determine LLM mode from arguments
    use_llm = None
    if args.llm and args.no_llm:
        parser.error("Cannot specify both --llm and --no-llm")
    elif args.llm:
        use_llm = True
    elif args.no_llm:
        use_llm = False

    reviewer = ARCReviewer(
        verbose=args.verbose,
        timeout=args.timeout,
        skip_coverage=args.skip_coverage,
        use_llm=use_llm,
    )
    reviewer.review_and_output(
        pr_number=args.pr, base_branch=args.base, runtime_test=args.runtime_test
    )


if __name__ == "__main__":
    main()
