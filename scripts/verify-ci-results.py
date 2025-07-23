#!/usr/bin/env python3
"""
Verify CI results meet quality thresholds.

This script is used by the ci-local-verifier workflow to validate
that posted CI results meet the project's quality standards.
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


class CIResultsVerifier:
    """Verify CI results against configured thresholds."""

    def __init__(self, config_file: str = ".coverage-config.json"):
        """Initialize verifier with configuration."""
        self.config = self._load_config(config_file)
        self.failures: List[str] = []
        self.warnings: List[str] = []

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load coverage and quality configuration."""
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                return {
                    "coverage_threshold": config.get("baseline", 85.0),
                    "coverage_target": config.get("target", 85.0),
                    "validator_target": config.get("validator_target", 90.0),
                    "allow_test_failures": False,
                    "allow_lint_warnings": True,
                    "require_type_check": True,
                }
        except FileNotFoundError:
            # Default configuration if config file doesn't exist
            return {
                "coverage_threshold": 85.0,
                "coverage_target": 85.0,
                "validator_target": 90.0,
                "allow_test_failures": False,
                "allow_lint_warnings": True,
                "require_type_check": True,
            }

    def verify_results(self, results: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify CI results meet quality thresholds.

        Returns:
            Tuple of (passed: bool, message: str)
        """
        self.failures = []
        self.warnings = []

        # Validate result format
        if "checks" not in results:
            return False, "Invalid results format: missing 'checks' field"

        checks = results["checks"]

        # Verify each type of check
        self._verify_coverage(checks.get("coverage", {}))
        self._verify_tests(checks.get("tests", {}))
        self._verify_linting(checks.get("linting", {}))
        self._verify_type_check(checks.get("type_check", {}))

        # Check for required fields
        if not checks:
            self.failures.append("No CI checks found in results")

        # Build result message
        if self.failures:
            message = "CI verification failed:\n"
            message += "\n".join(f"❌ {failure}" for failure in self.failures)
            if self.warnings:
                message += "\n\nWarnings:\n"
                message += "\n".join(f"⚠️  {warning}" for warning in self.warnings)
            return False, message

        message = "✅ All CI checks passed verification"
        if self.warnings:
            message += "\n\nWarnings:\n"
            message += "\n".join(f"⚠️  {warning}" for warning in self.warnings)

        return True, message

    def _verify_coverage(self, coverage: Dict[str, Any]) -> None:
        """Verify coverage meets thresholds."""
        if not coverage:
            self.failures.append("Coverage data missing from results")
            return

        percentage = coverage.get("percentage", 0)
        threshold = self.config["coverage_threshold"]
        target = self.config["coverage_target"]

        if percentage < threshold:
            self.failures.append(
                f"Coverage {percentage:.1f}% is below required threshold {threshold:.1f}%"
            )
        elif percentage < target:
            self.warnings.append(f"Coverage {percentage:.1f}% is below target {target:.1f}%")

        # Additional coverage checks
        if "lines_total" in coverage and coverage["lines_total"] == 0:
            self.failures.append("No lines found to cover - possible analysis error")

    def _verify_tests(self, tests: Dict[str, Any]) -> None:
        """Verify test results."""
        if not tests:
            self.failures.append("Test results missing from results")
            return

        total = tests.get("total", 0)
        failed = tests.get("failed", 0)

        if total == 0:
            self.failures.append("No tests found - test discovery may have failed")
            return

        if failed > 0 and not self.config["allow_test_failures"]:
            self.failures.append(f"{failed} test(s) failed out of {total} total tests")

        # Check for test/code ratio
        if total < 50:  # Arbitrary minimum for this project
            self.warnings.append(f"Only {total} tests found - consider adding more test coverage")

    def _verify_linting(self, linting: Dict[str, Any]) -> None:
        """Verify linting results."""
        if not linting:
            self.warnings.append("Linting results missing from results")
            return

        passed = linting.get("passed", False)
        issues = linting.get("issues", [])

        if not passed:
            if self.config["allow_lint_warnings"]:
                # Check if these are just warnings or actual errors
                error_count = sum(1 for issue in issues if issue.get("severity") == "error")
                if error_count > 0:
                    self.failures.append(
                        f"Linting failed with {error_count} error(s) "
                        f"out of {len(issues)} total issues"
                    )
                else:
                    self.warnings.append(f"Linting has {len(issues)} warning(s)")
            else:
                self.failures.append(f"Linting failed with {len(issues)} issue(s)")

        # Check for specific critical linting rules
        critical_codes = ["E999", "F401", "F841"]  # Syntax errors, unused imports/variables
        critical_issues = [issue for issue in issues if issue.get("code") in critical_codes]
        if critical_issues:
            codes = ", ".join(issue["code"] for issue in critical_issues)
            self.failures.append(f"Critical linting issues found: {codes}")

    def _verify_type_check(self, type_check: Dict[str, Any]) -> None:
        """Verify type checking results."""
        if not type_check and self.config["require_type_check"]:
            self.warnings.append("Type checking results missing from results")
            return

        if type_check:
            passed = type_check.get("passed", False)
            errors = type_check.get("errors", 0)

            if not passed and self.config["require_type_check"]:
                self.failures.append(f"Type checking failed with {errors} error(s)")


def verify_from_file(
    results_file: str, config_file: str = ".coverage-config.json"
) -> Tuple[bool, str]:
    """Verify results from a JSON file."""
    try:
        with open(results_file, "r") as f:
            results = json.load(f)
    except FileNotFoundError:
        return False, f"Results file '{results_file}' not found"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in results file: {e}"

    verifier = CIResultsVerifier(config_file)
    return verifier.verify_results(results)


def main():
    parser = argparse.ArgumentParser(description="Verify CI results meet quality thresholds")
    parser.add_argument("results_file", help="Path to CI results JSON file")
    parser.add_argument(
        "--config",
        default=".coverage-config.json",
        help="Path to coverage/quality configuration file",
    )
    parser.add_argument(
        "--output-format", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args()

    # Verify results
    passed, message = verify_from_file(args.results_file, args.config)

    # Output results
    if args.output_format == "json":
        output = {
            "passed": passed,
            "message": message,
            "details": message.split("\n") if "\n" in message else [message],
        }
        print(json.dumps(output, indent=2))
    else:
        print(message)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
