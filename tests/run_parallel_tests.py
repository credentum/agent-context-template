#!/usr/bin/env python3
"""
Run tests in parallel for faster execution
Distributes tests across multiple processes based on markers
"""

import argparse
import json
import multiprocessing
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class TestGroup:
    """Represents a group of tests to run together"""

    name: str
    markers: str
    max_workers: int = 4
    timeout: int = 300


# Define test groups for parallel execution
TEST_GROUPS = [
    TestGroup("unit", "not integration and not e2e and not slow and not benchmark", max_workers=8),
    TestGroup("integration", "integration and not e2e", max_workers=4),
    TestGroup("e2e", "e2e", max_workers=2),
    TestGroup("benchmark", "benchmark", max_workers=2),
    TestGroup("kv", "kv", max_workers=4),
]


def run_test_group(group: TestGroup, pytest_args: List[str]) -> Tuple[str, Dict]:
    """Run a test group and return results"""
    start_time = time.time()

    # Build pytest command
    cmd = [
        "python",
        "-m",
        "pytest",
        "-m",
        group.markers,
        f"--junit-xml=test-results/junit-{group.name}.xml",
        f"--cov=src",
        "--cov-branch",
        f"--cov-report=xml:coverage-{group.name}.xml",
        f"--cov-report=html:htmlcov-{group.name}",
        "--cov-report=term",
        "-n",
        str(group.max_workers),  # Use pytest-xdist for parallel execution
    ] + pytest_args

    # Run tests
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=group.timeout,
    )

    duration = time.time() - start_time

    # Parse results
    test_count = 0
    failures = 0
    errors = 0

    # Simple parsing of pytest output
    for line in result.stdout.split("\n"):
        if " passed" in line or " failed" in line or " error" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "passed":
                    test_count += int(parts[i - 1])
                elif part == "failed":
                    failures += int(parts[i - 1])
                elif part == "error":
                    errors += int(parts[i - 1])

    return group.name, {
        "duration": duration,
        "exit_code": result.returncode,
        "tests": test_count,
        "failures": failures,
        "errors": errors,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def merge_coverage_files(coverage_files: List[str], output_file: str):
    """Merge multiple coverage files into one"""
    cmd = ["coverage", "combine"] + coverage_files
    subprocess.run(cmd, check=True)

    # Generate final report
    subprocess.run(["coverage", "xml", "-o", output_file], check=True)
    subprocess.run(["coverage", "html", "-d", "htmlcov-combined"], check=True)
    subprocess.run(["coverage", "report"], check=True)


def main():
    parser = argparse.ArgumentParser(description="Run tests in parallel")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Maximum number of parallel test groups",
    )
    parser.add_argument(
        "--groups",
        nargs="+",
        choices=[g.name for g in TEST_GROUPS],
        help="Specific test groups to run",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first test group failure",
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest",
    )

    args = parser.parse_args()

    # Create output directories
    os.makedirs("test-results", exist_ok=True)

    # Filter test groups if specified
    groups_to_run = TEST_GROUPS
    if args.groups:
        groups_to_run = [g for g in TEST_GROUPS if g.name in args.groups]

    print(f"🚀 Running {len(groups_to_run)} test groups in parallel")
    print(f"   Max workers: {args.max_workers}")
    print(f"   Test groups: {', '.join(g.name for g in groups_to_run)}")
    print()

    # Run test groups in parallel
    results = {}
    failed_groups = []

    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all test groups
        future_to_group = {
            executor.submit(run_test_group, group, args.pytest_args): group
            for group in groups_to_run
        }

        # Process results as they complete
        for future in as_completed(future_to_group):
            group = future_to_group[future]
            try:
                group_name, result = future.result()
                results[group_name] = result

                # Print summary
                status = "✅ PASSED" if result["exit_code"] == 0 else "❌ FAILED"
                print(
                    f"{status} {group_name}: {result['tests']} tests in {result['duration']:.1f}s"
                )

                if result["failures"] > 0 or result["errors"] > 0:
                    print(f"       Failures: {result['failures']}, Errors: {result['errors']}")
                    failed_groups.append(group_name)

                    if args.fail_fast:
                        print(f"\n💥 Failing fast due to {group_name} failure")
                        executor.shutdown(wait=False)
                        break

            except Exception as e:
                print(f"❌ ERROR {group.name}: {e}")
                failed_groups.append(group.name)
                if args.fail_fast:
                    executor.shutdown(wait=False)
                    break

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    total_tests = sum(r["tests"] for r in results.values())
    total_failures = sum(r["failures"] for r in results.values())
    total_errors = sum(r["errors"] for r in results.values())
    total_duration = sum(r["duration"] for r in results.values())

    print(f"Total tests: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    print(f"Total duration: {total_duration:.1f}s")
    print(f"Parallel speedup: {total_duration / max(r['duration'] for r in results.values()):.1f}x")

    # Merge coverage files
    print("\n📈 Merging coverage reports...")
    coverage_files = [f"coverage-{name}.xml" for name in results.keys()]
    existing_coverage = [f for f in coverage_files if os.path.exists(f)]

    if existing_coverage:
        try:
            merge_coverage_files(existing_coverage, "coverage-combined.xml")
            print("✅ Coverage reports merged successfully")
        except Exception as e:
            print(f"⚠️  Failed to merge coverage: {e}")

    # Generate JSON report
    report = {
        "summary": {
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "total_duration": total_duration,
            "parallel_speedup": total_duration / max(r["duration"] for r in results.values()),
            "success": len(failed_groups) == 0,
        },
        "groups": results,
    }

    with open("test-results/parallel-test-report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Exit with appropriate code
    if failed_groups:
        print(f"\n❌ Failed test groups: {', '.join(failed_groups)}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
