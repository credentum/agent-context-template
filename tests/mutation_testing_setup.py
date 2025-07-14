#!/usr/bin/env python3
"""
Mutation testing setup and configuration
Uses mutmut for Python mutation testing on core agents
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import click
import yaml


class MutationTestRunner:
    """Configure and run mutation tests on core components"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path.cwd()
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"

        # Core agents to test
        self.core_agents = [
            "src/agents/cleanup_agent.py",
            "src/agents/update_sprint.py",
            "src/agents/context_lint.py",
        ]

        # Critical validators
        self.critical_validators = [
            "src/validators/config_validator.py",
            "src/validators/kv_validators.py",
        ]

        # Summarization logic
        self.summarization_modules = ["src/storage/hash_diff_embedder.py"]

    def check_mutmut_installed(self) -> bool:
        """Check if mutmut is installed"""
        try:
            result = subprocess.run(["mutmut", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def install_mutmut(self) -> bool:
        """Install mutmut if not present"""
        if self.check_mutmut_installed():
            return True

        click.echo("Installing mutmut...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "mutmut"], check=True, timeout=300
            )
            return True
        except subprocess.CalledProcessError:
            click.echo("Failed to install mutmut", err=True)
            return False

    def create_mutmut_config(self):
        """Create .mutmut-config file"""
        config_content = """# Mutmut configuration
[mutmut]
paths_to_mutate = src/agents/,src/validators/,src/storage/
backup = False
runner = python -m pytest
tests_dir = tests/
dict_synonyms = Dict, OrderedDict

# Exclude files
[mutmut.exclude]
__pycache__/
*.pyc
.git/
"""

        config_path = self.project_root / ".mutmut-config"
        with open(config_path, "w") as f:
            f.write(config_content)

        if self.verbose:
            click.echo(f"Created mutation testing config at {config_path}")

    def run_baseline_tests(self) -> bool:
        """Run baseline tests to ensure they pass"""
        click.echo("Running baseline tests...")

        result = subprocess.run(["python", "-m", "pytest", "-xvs"], cwd=self.project_root)

        if result.returncode != 0:
            click.echo("Baseline tests failed! Fix tests before running mutations.", err=True)
            return False

        click.echo("✓ Baseline tests passed")
        return True

    def run_mutation_tests(self, target: str) -> Dict[str, Any]:
        """Run mutation tests on specific target"""
        click.echo(f"\nRunning mutation tests on {target}...")

        # Determine test file
        if "agents" in target:
            test_pattern = "tests/test_agent_*.py"
        elif "validators" in target:
            test_pattern = "tests/test_*validators.py"
        else:
            test_pattern = "tests/test_*.py"

        cmd = [
            "mutmut",
            "run",
            "--paths-to-mutate",
            target,
            "--tests",
            test_pattern,
            "--simple-output",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)

        # Parse results
        output = result.stdout
        stats = self.parse_mutmut_output(output)

        return {
            "target": target,
            "total_mutants": stats.get("total", 0),
            "killed": stats.get("killed", 0),
            "survived": stats.get("survived", 0),
            "timeout": stats.get("timeout", 0),
            "suspicious": stats.get("suspicious", 0),
            "mutation_score": stats.get("score", 0.0),
        }

    def parse_mutmut_output(self, output: str) -> Dict[str, Any]:
        """Parse mutmut output for statistics"""
        stats = {
            "total": 0,
            "killed": 0,
            "survived": 0,
            "timeout": 0,
            "suspicious": 0,
            "score": 0.0,
        }

        # Parse output lines
        for line in output.split("\n"):
            if "Killed" in line:
                try:
                    stats["killed"] = int(line.split()[1])
                except (IndexError, ValueError):
                    pass
            elif "Survived" in line:
                try:
                    stats["survived"] = int(line.split()[1])
                except (IndexError, ValueError):
                    pass
            elif "Timeout" in line:
                try:
                    stats["timeout"] = int(line.split()[1])
                except (IndexError, ValueError):
                    pass

        # Calculate totals and score
        stats["total"] = stats["killed"] + stats["survived"] + stats["timeout"]
        if stats["total"] > 0:
            stats["score"] = (stats["killed"] / stats["total"]) * 100

        return stats

    def generate_html_report(self):
        """Generate HTML report of mutation results"""
        click.echo("Generating HTML report...")

        subprocess.run(["mutmut", "html"], cwd=self.project_root)

        report_path = self.project_root / "html"
        if report_path.exists():
            click.echo(f"✓ HTML report generated at {report_path}")
        else:
            click.echo("Failed to generate HTML report", err=True)

    def show_surviving_mutants(self, limit: int = 10):
        """Show details of surviving mutants"""
        click.echo(f"\nTop {limit} surviving mutants:")

        result = subprocess.run(
            ["mutmut", "show", "all"], capture_output=True, text=True, cwd=self.project_root
        )

        if result.returncode == 0:
            lines = result.stdout.split("\n")[:limit]
            for line in lines:
                if line.strip():
                    click.echo(f"  {line}")

    def run_all_mutation_tests(self) -> List[Dict[str, Any]]:
        """Run mutation tests on all core components"""
        if not self.install_mutmut():
            return []

        self.create_mutmut_config()

        if not self.run_baseline_tests():
            return []

        results = []

        # Test core agents
        click.echo("\n=== Testing Core Agents ===")
        for agent in self.core_agents:
            if Path(agent).exists():
                result = self.run_mutation_tests(agent)
                results.append(result)
                self.print_result_summary(result)

        # Test critical validators
        click.echo("\n=== Testing Critical Validators ===")
        for validator in self.critical_validators:
            if Path(validator).exists():
                result = self.run_mutation_tests(validator)
                results.append(result)
                self.print_result_summary(result)

        # Test summarization logic
        click.echo("\n=== Testing Summarization Logic ===")
        for module in self.summarization_modules:
            if Path(module).exists():
                result = self.run_mutation_tests(module)
                results.append(result)
                self.print_result_summary(result)

        return results

    def print_result_summary(self, result: Dict[str, Any]):
        """Print summary of mutation test results"""
        click.echo(f"\n{result['target']}:")
        click.echo(f"  Total mutants: {result['total_mutants']}")
        click.echo(
            f"  Killed: {result['killed']} "
            f"({result['killed']/max(1, result['total_mutants'])*100:.1f}%)"
        )
        click.echo(f"  Survived: {result['survived']}")
        click.echo(f"  Timeout: {result['timeout']}")
        click.echo(f"  Mutation Score: {result['mutation_score']:.1f}%")

        if result["mutation_score"] < 80:
            click.echo("  ⚠️  Low mutation score - consider improving tests")

    def create_mutation_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create detailed mutation testing report"""
        recommendations: List[str] = []
        report = {
            "timestamp": str(Path.cwd()),
            "summary": {
                "total_files_tested": len(results),
                "average_mutation_score": (
                    sum(r["mutation_score"] for r in results) / len(results) if results else 0
                ),
                "total_mutants": sum(r["total_mutants"] for r in results),
                "total_killed": sum(r["killed"] for r in results),
                "total_survived": sum(r["survived"] for r in results),
            },
            "details": results,
            "recommendations": recommendations,
        }

        # Add recommendations
        for result in results:
            if result["mutation_score"] < 60:
                recommendations.append(
                    f"Critical: {result['target']} has very low mutation coverage "
                    f"({result['mutation_score']:.1f}%)"
                )
            elif result["mutation_score"] < 80:
                recommendations.append(
                    f"Warning: {result['target']} could use better test coverage "
                    f"({result['mutation_score']:.1f}%)"
                )

        # Save report
        report_path = self.project_root / "mutation_test_report.yaml"
        with open(report_path, "w") as f:
            yaml.dump(report, f, default_flow_style=False)

        click.echo(f"\n✓ Mutation test report saved to {report_path}")

        return report


@click.command()
@click.option("--target", help="Specific file to test")
@click.option("--show-survivors", is_flag=True, help="Show surviving mutants")
@click.option("--html", is_flag=True, help="Generate HTML report")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(target: str, show_survivors: bool, html: bool, verbose: bool):
    """Run mutation tests on core agents and components"""
    runner = MutationTestRunner(verbose=verbose)

    if target:
        # Test specific target
        if not runner.install_mutmut():
            return

        runner.create_mutmut_config()

        if not runner.run_baseline_tests():
            return

        result = runner.run_mutation_tests(target)
        runner.print_result_summary(result)
    else:
        # Test all core components
        results = runner.run_all_mutation_tests()

        if results:
            runner.create_mutation_report(results)

    if show_survivors:
        runner.show_surviving_mutants()

    if html:
        runner.generate_html_report()


if __name__ == "__main__":
    main()
