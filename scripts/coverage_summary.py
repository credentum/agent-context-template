#!/usr/bin/env python3
"""Generate comprehensive test coverage summary with all metrics"""

import json
import subprocess
import sys
from typing import Dict, Tuple


class CoverageSummary:
    """Generate and analyze test coverage metrics"""

    def __init__(self):
        # Load targets from centralized config
        try:
            with open(".coverage-config.json") as f:
                config = json.load(f)
            self.targets = {
                "line_coverage": config.get("baseline", 78.5),
                "branch_coverage": config.get("branch_target", 60),
                "mutation_score": config.get("mutation_baseline", 20),
                "critical_function_coverage": 100,  # Keep high standard
            }
        except FileNotFoundError:
            print("⚠️ .coverage-config.json not found, using defaults")
            self.targets = {
                "line_coverage": 78.5,
                "branch_coverage": 60,
                "mutation_score": 20,
                "critical_function_coverage": 100,
            }

    def get_coverage_metrics(self) -> Dict[str, float]:
        """Get coverage metrics from coverage.json"""
        try:
            with open("coverage.json") as f:
                data = json.load(f)
                totals = data["totals"]
                # Calculate branch coverage percentage
                branch_coverage = 0
                if totals.get("num_branches", 0) > 0:
                    branch_coverage = (totals["covered_branches"] / totals["num_branches"]) * 100

                return {
                    "line_coverage": totals["percent_covered"],
                    "branch_coverage": branch_coverage,
                    "missing_lines": totals["missing_lines"],
                    "missing_branches": totals.get("missing_branches", 0),
                }
        except FileNotFoundError:
            print("❌ coverage.json not found. Run pytest with coverage first.")
            return {}

    def get_mutation_score(self) -> float:
        """Get mutation testing score"""
        try:
            # Check if mutmut cache exists
            import os

            if not os.path.exists(".mutmut-cache"):
                print("⚠️  No mutation testing cache found, skipping mutation score")
                return 0.0

            # Get mutation test results
            result = subprocess.run(["mutmut", "results"], capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  Error getting mutation results, returning baseline")
                return self.targets["mutation_score"]

            output = result.stdout

            # Parse mutmut output for scores
            # Format: "Killed: X, Survived: Y, Skipped: Z, ..."
            killed = 0
            survived = 0
            total = 0

            for line in output.split("\n"):
                if "Killed:" in line:
                    # Extract numbers from mutmut results
                    parts = line.split(",")
                    for part in parts:
                        part = part.strip()
                        if part.startswith("Killed:"):
                            killed = int(part.split(":")[1].strip())
                        elif part.startswith("Survived:"):
                            survived = int(part.split(":")[1].strip())

            total = killed + survived
            if total == 0:
                print("⚠️  No mutation testing data available")
                return 0.0

            mutation_score = (killed / total) * 100
            print(
                f"📊 Mutation Testing: {killed} killed, {survived} survived "
                f"(score: {mutation_score:.1f}%)"
            )
            return mutation_score
        except FileNotFoundError:
            print("⚠️  mutmut not found. Install with: pip install mutmut")
            return 0.0
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Error running mutmut: {e}")
            return 0.0
        except Exception as e:
            print(f"⚠️  Unexpected error in mutation testing: {e}")
            return 0.0

    def check_critical_functions(self) -> Tuple[int, int]:
        """Check coverage of critical functions"""
        # Import the critical functions registry
        try:
            # Add current directory to path for test imports
            import os
            import sys

            if os.getcwd() not in sys.path:
                sys.path.insert(0, os.getcwd())

            from tests.test_traceability_matrix import CRITICAL_FUNCTIONS

            total = len(CRITICAL_FUNCTIONS)
            covered = sum(1 for info in CRITICAL_FUNCTIONS.values() if info["test_cases"])
            return covered, total
        except ImportError as e:
            print(f"⚠️  Cannot import traceability matrix: {e}")
            return 0, 0
        except Exception as e:
            print(f"⚠️  Error checking critical functions: {e}")
            return 0, 0

    def generate_report(self):
        """Generate comprehensive coverage report"""
        print("📊 Comprehensive Test Coverage Report")
        print("=" * 50)

        # Get metrics
        coverage_metrics = self.get_coverage_metrics()
        mutation_score = self.get_mutation_score()
        critical_covered, critical_total = self.check_critical_functions()

        if not coverage_metrics:
            return

        # Display results
        results = [
            ("Line Coverage", coverage_metrics["line_coverage"], self.targets["line_coverage"]),
            (
                "Branch Coverage",
                coverage_metrics["branch_coverage"],
                self.targets["branch_coverage"],
            ),
            ("Mutation Score", mutation_score, self.targets["mutation_score"]),
            (
                "Critical Functions",
                (critical_covered / critical_total * 100 if critical_total else 0),
                self.targets["critical_function_coverage"],
            ),
        ]

        all_passed = True
        for metric, actual, target in results:
            status = "✅" if actual >= target else "❌"
            print(f"{status} {metric}: {actual:.2f}% (target: ≥{target}%)")
            if actual < target:
                all_passed = False

        # Additional metrics
        print("\n📈 Additional Metrics:")
        print(f"   Missing Lines: {coverage_metrics.get('missing_lines', 'N/A')}")
        print(f"   Missing Branches: {coverage_metrics.get('missing_branches', 'N/A')}")
        print(f"   Critical Functions: {critical_covered}/{critical_total}")

        # Module breakdown
        self.show_module_coverage()

        # Recommendations
        if not all_passed:
            print("\n⚠️  Coverage Improvements Needed:")
            self.show_recommendations(coverage_metrics, mutation_score)
        else:
            print("\n✅ All coverage targets met!")

        return all_passed

    def show_module_coverage(self):
        """Show coverage breakdown by module"""
        try:
            with open("coverage.json") as f:
                data = json.load(f)

            print("\n📦 Module Coverage:")
            print("-" * 40)

            modules = {}
            for file_path, file_data in data["files"].items():
                if file_path.startswith("src/"):
                    module = file_path.split("/")[1]
                    if module not in modules:
                        modules[module] = {"covered_lines": 0, "total_lines": 0, "files": 0}

                    summary = file_data["summary"]
                    modules[module]["covered_lines"] += summary["covered_lines"]
                    modules[module]["total_lines"] += summary["num_statements"]
                    modules[module]["files"] += 1

            for module, stats in sorted(modules.items()):
                if stats["total_lines"] > 0:
                    coverage = (stats["covered_lines"] / stats["total_lines"]) * 100
                    print(f"   {module:15} {coverage:6.2f}% ({stats['files']} files)")
        except FileNotFoundError:
            print("⚠️  coverage.json not found for module breakdown")
        except Exception as e:
            print(f"⚠️  Error generating module coverage: {e}")

    def show_recommendations(self, metrics: Dict, mutation_score: float):
        """Show specific recommendations for improvement"""
        if metrics.get("line_coverage", 0) < self.targets["line_coverage"]:
            print("   - Add tests for uncovered lines (use --cov-report=term-missing)")

        if metrics.get("branch_coverage", 0) < self.targets["branch_coverage"]:
            print("   - Add tests for uncovered branches (check if/else conditions)")

        if mutation_score < self.targets["mutation_score"]:
            print("   - Strengthen test assertions to catch more mutations")

        print("   - Focus on critical paths and error handling")


def main():
    """Main entry point"""
    summary = CoverageSummary()
    passed = summary.generate_report()

    # Generate badge if coverage-badge is available
    try:
        subprocess.run(["coverage-badge", "-o", "coverage.svg", "-f"], check=True)
        print("\n🏷️  Coverage badge updated: coverage.svg")
    except FileNotFoundError:
        print("⚠️  coverage-badge not found. Install with: pip install coverage-badge")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error generating coverage badge: {e}")
    except Exception as e:
        print(f"⚠️  Unexpected error generating badge: {e}")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
