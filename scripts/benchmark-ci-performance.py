#!/usr/bin/env python3
"""
CI Performance Benchmark Tool
Measures and compares CI pipeline execution times
"""

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class CIBenchmark:
    def __init__(self) -> None:
        self.results: Dict[str, Any] = {"timestamp": datetime.now().isoformat(), "benchmarks": {}}
        # Allowed commands for security validation
        self.allowed_commands = {
            "scripts/run-ci-docker.sh",
            "scripts/run-ci-optimized.sh",
            "docker-compose",
            "pytest",
            "python",
        }

    def _validate_command(self, command: List[str]) -> bool:
        """Validate command for security - only allow whitelisted commands"""
        if not command:
            return False

        # Check if the base command is in our allowlist
        base_cmd = command[0]

        # Allow relative paths to our scripts
        if base_cmd.startswith("./"):
            base_cmd = base_cmd[2:]

        # Check against allowed commands
        for allowed in self.allowed_commands:
            if base_cmd == allowed or base_cmd.endswith(f"/{allowed}"):
                return True

        return False

    def run_command(
        self, command: List[str], description: str, timeout: int = 1800
    ) -> Dict[str, Any]:
        """Run a command and measure execution time with security validation"""
        # Security validation
        if not self._validate_command(command):
            print(f"❌ {description} blocked: Command not allowed for security reasons")
            return {
                "duration": 0,
                "success": False,
                "returncode": -3,
                "error": "Command blocked by security policy",
            }

        print(f"🔄 Running: {description}")
        print(f"   Command: {' '.join(command)}")

        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path(__file__).parent.parent,
            )
            end_time = time.time()
            duration = end_time - start_time

            success = result.returncode == 0

            if success:
                print(f"✅ {description} completed in {duration:.1f}s")
            else:
                print(f"❌ {description} failed in {duration:.1f}s")
                print(f"   Error: {result.stderr[:200]}")

            return {
                "duration": duration,
                "success": success,
                "returncode": result.returncode,
                "stdout_lines": len(result.stdout.splitlines()),
                "stderr_lines": len(result.stderr.splitlines()),
            }

        except subprocess.TimeoutExpired:
            print(f"⏰ {description} timed out after {timeout}s")
            return {"duration": timeout, "success": False, "returncode": -1, "timeout": True}
        except Exception as e:
            print(f"💥 {description} crashed: {e}")
            return {"duration": 0, "success": False, "returncode": -2, "error": str(e)}

    def benchmark_legacy_ci(self) -> float:
        """Benchmark legacy CI pipeline"""
        print("\n🕰️  Benchmarking Legacy CI Pipeline")
        print("=" * 50)

        benchmarks = []

        # Individual legacy components
        tests = [
            (["scripts/run-ci-docker.sh", "black"], "Legacy Black formatting"),
            (["scripts/run-ci-docker.sh", "mypy"], "Legacy MyPy type checking"),
            (["scripts/run-ci-docker.sh", "flake8"], "Legacy Flake8 linting"),
            (["scripts/run-ci-docker.sh", "unit"], "Legacy Unit tests"),
            (["scripts/run-ci-docker.sh", "coverage"], "Legacy Coverage analysis"),
        ]

        total_start = time.time()

        for command, description in tests:
            result = self.run_command(command, description)
            benchmarks.append({"name": description, "command": " ".join(command), **result})

        total_time = time.time() - total_start

        self.results["benchmarks"]["legacy"] = {
            "total_time": total_time,
            "components": benchmarks,
            "success_rate": sum(1 for b in benchmarks if b["success"]) / len(benchmarks),
        }

        print(f"\n📊 Legacy CI Total Time: {total_time:.1f}s")
        return total_time

    def benchmark_optimized_ci(self) -> float:
        """Benchmark optimized CI pipeline"""
        print("\n🚀 Benchmarking Optimized CI Pipeline")
        print("=" * 50)

        benchmarks = []

        # Test optimized components
        tests = [
            (["scripts/run-ci-optimized.sh", "fast"], "Optimized Fast Pipeline"),
            (["scripts/run-ci-optimized.sh", "parallel"], "Optimized Parallel Pipeline"),
        ]

        total_start = time.time()

        for command, description in tests:
            result = self.run_command(command, description)
            benchmarks.append({"name": description, "command": " ".join(command), **result})

        total_time = time.time() - total_start

        self.results["benchmarks"]["optimized"] = {
            "total_time": total_time,
            "components": benchmarks,
            "success_rate": sum(1 for b in benchmarks if b["success"]) / len(benchmarks),
        }

        print(f"\n📊 Optimized CI Total Time: {total_time:.1f}s")
        return total_time

    def benchmark_individual_components(self) -> None:
        """Benchmark individual components for detailed analysis"""
        print("\n🔍 Benchmarking Individual Components")
        print("=" * 50)

        components = [
            (
                [
                    "docker-compose",
                    "-f",
                    "docker-compose.ci-optimized.yml",
                    "run",
                    "--rm",
                    "ci-lint-black",
                ],
                "Optimized Black",
            ),
            (
                [
                    "docker-compose",
                    "-f",
                    "docker-compose.ci-optimized.yml",
                    "run",
                    "--rm",
                    "ci-lint-mypy",
                ],
                "Optimized MyPy",
            ),
            (
                [
                    "docker-compose",
                    "-f",
                    "docker-compose.ci-optimized.yml",
                    "run",
                    "--rm",
                    "ci-test-core",
                ],
                "Optimized Core Tests",
            ),
        ]

        benchmarks = []
        for command, description in components:
            result = self.run_command(command, description, timeout=600)
            benchmarks.append({"name": description, "command": " ".join(command), **result})

        self.results["benchmarks"]["components"] = benchmarks

    def generate_report(self) -> None:
        """Generate comprehensive performance report"""
        print("\n📊 Performance Report")
        print("=" * 50)

        if "legacy" in self.results["benchmarks"] and "optimized" in self.results["benchmarks"]:
            legacy_time = self.results["benchmarks"]["legacy"]["total_time"]
            optimized_time = self.results["benchmarks"]["optimized"]["total_time"]

            if legacy_time > 0:
                improvement = ((legacy_time - optimized_time) / legacy_time) * 100
                time_saved = legacy_time - optimized_time

                print(f"Legacy CI Pipeline:    {legacy_time:.1f}s")
                print(f"Optimized CI Pipeline: {optimized_time:.1f}s")
                print(f"Performance Improvement: {improvement:.1f}%")
                print(f"Time Saved: {time_saved:.1f}s")

                if improvement > 0:
                    print("🎉 Optimization successful!")
                else:
                    print("⚠️  Optimization needs work")

            # Success rates
            legacy_success = self.results["benchmarks"]["legacy"]["success_rate"]
            optimized_success = self.results["benchmarks"]["optimized"]["success_rate"]

            print("\nSuccess Rates:")
            print(f"Legacy: {legacy_success:.1%}")
            print(f"Optimized: {optimized_success:.1%}")

        # Component breakdown
        if "components" in self.results["benchmarks"]:
            print("\n🔍 Component Performance:")
            for component in self.results["benchmarks"]["components"]:
                status = "✅" if component["success"] else "❌"
                print(f"  {status} {component['name']}: {component['duration']:.1f}s")

    def save_results(self, filename: str = "ci-benchmark-results.json") -> None:
        """Save benchmark results to file"""
        results_file = Path(__file__).parent.parent / filename
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")

    def load_and_compare_results(self, filename: str = "ci-benchmark-results.json") -> None:
        """Load previous results and compare"""
        results_file = Path(__file__).parent.parent / filename
        if results_file.exists():
            with open(results_file, "r") as f:
                previous = json.load(f)

            print(f"\n📈 Comparing with previous run ({previous['timestamp']})")

            # Compare if both have legacy and optimized results
            if (
                "legacy" in previous["benchmarks"]
                and "optimized" in previous["benchmarks"]
                and "legacy" in self.results["benchmarks"]
                and "optimized" in self.results["benchmarks"]
            ):

                prev_improvement = (
                    (
                        previous["benchmarks"]["legacy"]["total_time"]
                        - previous["benchmarks"]["optimized"]["total_time"]
                    )
                    / previous["benchmarks"]["legacy"]["total_time"]
                ) * 100

                current_improvement = (
                    (
                        self.results["benchmarks"]["legacy"]["total_time"]
                        - self.results["benchmarks"]["optimized"]["total_time"]
                    )
                    / self.results["benchmarks"]["legacy"]["total_time"]
                ) * 100

                print(f"Previous improvement: {prev_improvement:.1f}%")
                print(f"Current improvement: {current_improvement:.1f}%")

                if current_improvement > prev_improvement:
                    print("🚀 Performance improved since last run!")
                elif current_improvement < prev_improvement - 5:
                    print("⚠️  Performance regression detected")
                else:
                    print("📊 Performance stable")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark CI pipeline performance")
    parser.add_argument(
        "--mode",
        choices=["legacy", "optimized", "compare", "components"],
        default="compare",
        help="Benchmark mode",
    )
    parser.add_argument(
        "--output", default="ci-benchmark-results.json", help="Output file for results"
    )
    parser.add_argument("--compare-with", help="Compare with previous results file")

    args = parser.parse_args()

    benchmark = CIBenchmark()

    print("🏁 CI Performance Benchmark Tool")
    print("=" * 50)

    if args.mode == "legacy":
        benchmark.benchmark_legacy_ci()
    elif args.mode == "optimized":
        benchmark.benchmark_optimized_ci()
    elif args.mode == "components":
        benchmark.benchmark_individual_components()
    elif args.mode == "compare":
        benchmark.benchmark_legacy_ci()
        benchmark.benchmark_optimized_ci()
        benchmark.benchmark_individual_components()

    benchmark.generate_report()

    if args.compare_with:
        benchmark.load_and_compare_results(args.compare_with)

    benchmark.save_results(args.output)


if __name__ == "__main__":
    main()
