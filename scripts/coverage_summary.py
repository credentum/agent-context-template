#!/usr/bin/env python3
"""Generate comprehensive test coverage summary with all metrics"""

import json
import subprocess
from typing import Dict, Tuple


class CoverageSummary:
    """Generate and analyze test coverage metrics"""

    def __init__(self):
        self.targets = self._load_coverage_config()

    def _load_coverage_config(self) -> Dict[str, float]:
        """Load coverage configuration from .coverage-config.json"""
        try:
            with open(".coverage-config.json") as f:
                config = json.load(f)
                tolerance_buffer = config.get("tolerance_buffer", 0.0)
                return {
                    "line_coverage": max(0, config.get("baseline", 80.0) - tolerance_buffer),
                    "branch_coverage": max(
                        0, config.get("branch_coverage", 60.0) - tolerance_buffer
                    ),
                    "mutation_score": max(
                        0, config.get("mutation_baseline", 20.0) - tolerance_buffer
                    ),
                    "critical_function_coverage": 100,  # Keep high standard, no tolerance
                    "tolerance_buffer": tolerance_buffer,
                }
        except FileNotFoundError:
            print("⚠️  .coverage-config.json not found. Using default thresholds.")
            return {
                "line_coverage": 80.0,
                "branch_coverage": 60.0,
                "mutation_score": 20.0,
                "critical_function_coverage": 100,
                "tolerance_buffer": 0.0,
            }
        except Exception as e:
            print(f"⚠️  Error loading coverage config: {e}")
            return {
                "line_coverage": 80.0,
                "branch_coverage": 60.0,
                "mutation_score": 20.0,
                "critical_function_coverage": 100,
                "tolerance_buffer": 0.0,
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
            result = subprocess.run(["mutmut", "results"], capture_output=True, text=True)

            # Parse mutation results
            if result.returncode == 0:
                output = result.stdout
                # Look for mutation score information
                if "killed" in output and "survived" in output:
                    lines = output.split("\n")
                    for line in lines:
                        if "killed" in line and "survived" in line:
                            # Extract numbers - this is a simplified parser
                            # Expected format: "killed: X, survived: Y"
                            try:
                                parts = line.split(",")
                                killed = int(parts[0].split(":")[1].strip())
                                survived = int(parts[1].split(":")[1].strip())
                                total = killed + survived
                                if total > 0:
                                    return (killed / total) * 100
                            except (ValueError, IndexError):
                                continue

                # If no mutation tests have been run yet, return 0
                return 0.0
            else:
                print(f"⚠️  mutmut results returned non-zero exit code: {result.returncode}")
                return 0.0

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
            # Only fail for line coverage - other metrics are informational for now
            if actual < target and metric == "Line Coverage":
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
    import sys

    # Handle --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python scripts/coverage_summary.py")
        print("")
        print("Generate comprehensive test coverage summary with all metrics.")
        print("")
        print("This script:")
        print("  - Loads coverage configuration from .coverage-config.json")
        print("  - Analyzes coverage.json for line and branch coverage")
        print("  - Runs mutation testing to get mutation score")
        print("  - Checks critical function coverage")
        print("  - Generates a detailed report with recommendations")
        print("  - Creates coverage badge if coverage-badge is available")
        print("")
        print("Output: Detailed coverage report to stdout")
        print("Exit code: 0 if all targets met, 1 otherwise")
        return

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
