#!/usr/bin/env python3
"""
Comprehensive test runner for all test types
Executes unit tests, integration tests, mutation tests, and e2e tests
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import click
import yaml


class TestRunner:
    """Run all test suites and generate reports"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.results = {}
        self.start_time = time.time()

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with pytest"""
        click.echo("\n=== Running Unit Tests ===")

        test_files = [
            "tests/test_hash_diff_embedder.py",
            "tests/test_agent_state_machines.py",
            "tests/test_metadata_validation.py",
            "tests/test_kv_validators.py",
            "tests/test_config_validator.py",
            "tests/test_context_analytics.py",
            "tests/test_vector_db_init.py",
        ]

        cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + test_files

        if self.verbose:
            cmd.append("-s")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            "suite": "unit_tests",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
        }

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        click.echo("\n=== Running Integration Tests ===")

        test_files = [
            "tests/test_integration_embedding_flow.py",
            "tests/test_integration_agent_flow.py",
            "tests/test_integration_ci_workflow.py",
        ]

        cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + test_files

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            "suite": "integration_tests",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
        }

    def run_mutation_tests(self) -> Dict[str, Any]:
        """Run mutation tests on core components"""
        click.echo("\n=== Running Mutation Tests ===")

        # Run mutation test setup
        cmd = ["python", "tests/mutation_testing_setup.py"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            "suite": "mutation_tests",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
        }

    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        click.echo("\n=== Running End-to-End Tests ===")

        cmd = [
            "python",
            "-m",
            "pytest",
            "-v",
            "--tb=short",
            "tests/test_e2e_project_lifecycle.py",
            "tests/test_sigstore_verification.py",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        return {
            "suite": "e2e_tests",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
        }

    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run tests with coverage analysis"""
        click.echo("\n=== Running Coverage Analysis ===")

        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-branch",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Parse coverage percentage from output
        coverage_percent = 0
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        coverage_percent = float(part.rstrip("%"))
                        break

        return {
            "suite": "coverage",
            "passed": coverage_percent >= 70,  # 70% threshold
            "coverage_percent": coverage_percent,
            "output": result.stdout,
        }

    def generate_test_report(self):
        """Generate comprehensive test report"""
        duration = time.time() - self.start_time

        report = {
            "test_run": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": round(duration, 2),
                "python_version": sys.version.split()[0],
            },
            "summary": {
                "total_suites": len(self.results),
                "passed_suites": sum(1 for r in self.results.values() if r.get("passed", False)),
                "failed_suites": sum(
                    1 for r in self.results.values() if not r.get("passed", False)
                ),
            },
            "results": self.results,
            "recommendations": [],
        }

        # Add recommendations based on results
        if "coverage" in self.results:
            cov = self.results["coverage"].get("coverage_percent", 0)
            if cov < 70:
                report["recommendations"].append(
                    f"Coverage is below 70% ({cov:.1f}%). Add more tests."
                )

        if "mutation_tests" in self.results and not self.results["mutation_tests"]["passed"]:
            report["recommendations"].append(
                "Mutation tests failed. Review test quality and coverage."
            )

        # Save report
        report_path = self.project_root / "test_report.yaml"
        with open(report_path, "w") as f:
            yaml.dump(report, f, default_flow_style=False)

        # Also save as JSON for CI integration
        import json

        json_path = self.project_root / "test_report.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        click.echo("\n" + "=" * 60)
        click.echo("TEST SUMMARY")
        click.echo("=" * 60)

        summary = report["summary"]
        click.echo(f"Total test suites: {summary['total_suites']}")
        click.echo(f"Passed: {summary['passed_suites']}")
        click.echo(f"Failed: {summary['failed_suites']}")
        click.echo(f"Duration: {report['test_run']['duration_seconds']}s")

        if "coverage" in self.results:
            cov = self.results["coverage"].get("coverage_percent", 0)
            click.echo(f"Code coverage: {cov:.1f}%")

        click.echo("\nResults by suite:")
        for suite_name, result in self.results.items():
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            click.echo(f"  {suite_name}: {status}")

        if report["recommendations"]:
            click.echo("\nRecommendations:")
            for rec in report["recommendations"]:
                click.echo(f"  - {rec}")

    def run_all_tests(self) -> bool:
        """Run all test suites"""
        # Run each test suite
        self.results["unit_tests"] = self.run_unit_tests()
        self.results["integration_tests"] = self.run_integration_tests()
        self.results["e2e_tests"] = self.run_e2e_tests()
        self.results["coverage"] = self.run_coverage_analysis()

        # Run mutation tests only if other tests pass
        if all(r.get("passed", False) for r in self.results.values()):
            self.results["mutation_tests"] = self.run_mutation_tests()
        else:
            click.echo("\n⚠️  Skipping mutation tests due to failures in other suites")

        # Generate report
        report = self.generate_test_report()
        self.print_summary(report)

        # Return overall success
        return all(r.get("passed", False) for r in self.results.values())


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--suite",
    type=click.Choice(["unit", "integration", "e2e", "mutation", "all"]),
    default="all",
    help="Test suite to run",
)
@click.option("--coverage", is_flag=True, help="Run with coverage analysis")
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
def main(verbose: bool, suite: str, coverage: bool, fail_fast: bool):
    """Run comprehensive test suite"""
    runner = TestRunner(verbose=verbose)

    if suite == "all":
        success = runner.run_all_tests()
    else:
        # Run specific suite
        if suite == "unit":
            result = runner.run_unit_tests()
        elif suite == "integration":
            result = runner.run_integration_tests()
        elif suite == "e2e":
            result = runner.run_e2e_tests()
        elif suite == "mutation":
            result = runner.run_mutation_tests()

        runner.results[f"{suite}_tests"] = result

        if coverage:
            runner.results["coverage"] = runner.run_coverage_analysis()

        report = runner.generate_test_report()
        runner.print_summary(report)

        success = result.get("passed", False)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
