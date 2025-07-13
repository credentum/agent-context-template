#!/usr/bin/env python3
"""
Generate a single-page coverage matrix showing test-to-module mapping.

This script analyzes test coverage data and generates both HTML and Markdown
reports showing which tests cover which modules.
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    "max_tests_shown": 5,
    "max_test_names": 3,
    "coverage_thresholds": {"high": 85, "medium": 70},
    "timeout_seconds": 120,
    "output_dir": ".",
    "docs_dir": "docs",
}


class CoverageMatrixError(Exception):
    """Base exception for coverage matrix generation errors."""

    pass


class CoverageDataValidator:
    """Validates coverage data structure."""

    @staticmethod
    def validate_summary(data: Dict[str, Any]) -> bool:
        """Validate coverage summary data structure."""
        required_fields = ["overall"]
        overall_fields = ["line_coverage", "branch_coverage", "tests_passed"]

        if not isinstance(data, dict):
            raise CoverageMatrixError("Coverage summary must be a dictionary")

        for field in required_fields:
            if field not in data:
                raise CoverageMatrixError(f"Missing required field: {field}")

        overall = data.get("overall", {})
        for field in overall_fields:
            if field not in overall:
                logger.warning(f"Missing overall field: {field}")

        return True

    @staticmethod
    def validate_coverage_json(data: Dict[str, Any]) -> bool:
        """Validate coverage.json data structure."""
        if not isinstance(data, dict):
            raise CoverageMatrixError("Coverage data must be a dictionary")

        if "files" not in data:
            raise CoverageMatrixError("Coverage data missing 'files' field")

        return True


class CoverageAnalyzer:
    """Analyzes test coverage data."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validator = CoverageDataValidator()

    def run_coverage_tests(self) -> Tuple[str, str]:
        """Run pytest with coverage and capture output."""
        logger.info("Running coverage tests...")

        cmd = ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=json", "-q"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["timeout_seconds"],
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Tests failed with return code: {result.returncode}")

            return result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            raise CoverageMatrixError(
                f"Coverage tests timed out after {self.config['timeout_seconds']} seconds"
            )
        except Exception as e:
            raise CoverageMatrixError(f"Failed to run coverage tests: {e}")

    def parse_coverage_json(self, coverage_file: Path) -> Dict[str, Set[str]]:
        """Parse coverage.json file for test-to-module mapping."""
        mapping = {}

        if not coverage_file.exists():
            logger.warning("coverage.json not found, running tests...")
            self.run_coverage_tests()

            if not coverage_file.exists():
                raise CoverageMatrixError("Failed to generate coverage.json")

        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            self.validator.validate_coverage_json(coverage_data)

            # Extract file coverage data
            for file_path, file_data in coverage_data.get("files", {}).items():
                if file_path.startswith("src/"):
                    tests = self._extract_tests_for_file(file_data)
                    if tests:
                        mapping[file_path] = tests

            logger.info(f"Parsed coverage for {len(mapping)} modules")
            return mapping

        except json.JSONDecodeError as e:
            raise CoverageMatrixError(f"Invalid JSON in coverage file: {e}")
        except IOError as e:
            raise CoverageMatrixError(f"Failed to read coverage file: {e}")

    def _extract_tests_for_file(self, file_data: Dict[str, Any]) -> Set[str]:
        """Extract test names that cover a specific file."""
        contexts = set()

        for line_contexts in file_data.get("contexts", {}).values():
            if isinstance(line_contexts, list):
                contexts.update(line_contexts)

        # Clean up test names
        tests = set()
        for context in contexts:
            if context and "|" in context:
                test_name = context.split("|")[0]
                if test_name.startswith("tests/"):
                    tests.add(test_name)

        return tests

    def load_coverage_summary(self, summary_path: Path) -> Dict[str, Any]:
        """Load and validate coverage summary."""
        if not summary_path.exists():
            logger.warning(f"Coverage summary not found at {summary_path}")
            return {}

        try:
            with open(summary_path) as f:
                data: Dict[str, Any] = json.load(f)

            self.validator.validate_summary(data)
            return data

        except json.JSONDecodeError as e:
            raise CoverageMatrixError(f"Invalid JSON in summary file: {e}")
        except IOError as e:
            raise CoverageMatrixError(f"Failed to read summary file: {e}")


class ReportGenerator:
    """Generates coverage matrix reports."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def generate_html_styles(self) -> str:
        """Generate CSS styles for HTML report."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1, h2 {
            color: #333;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #0366d6;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        tr:hover {
            background-color: #f6f8fa;
        }
        .coverage-bar {
            background-color: #e1e4e8;
            height: 20px;
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }
        .coverage-fill {
            height: 100%;
            background-color: #28a745;
            transition: width 0.3s ease;
        }
        .coverage-text {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            font-weight: 600;
        }
        .coverage-low { background-color: #dc3545; }
        .coverage-medium { background-color: #ffc107; }
        .coverage-high { background-color: #28a745; }
        .test-list {
            font-size: 0.85em;
            color: #666;
            max-height: 100px;
            overflow-y: auto;
        }
        .no-tests {
            color: #dc3545;
            font-style: italic;
        }
        """

    def generate_html_metrics(self, overall: Dict[str, Any], mapping: Dict[str, Set[str]]) -> str:
        """Generate HTML metrics section."""
        return f"""
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{overall.get('line_coverage', 0):.1f}%</div>
                <div class="metric-label">Line Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{overall.get('branch_coverage', 0)}%</div>
                <div class="metric-label">Branch Coverage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{overall.get('tests_passed', 0)}</div>
                <div class="metric-label">Tests Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{len(mapping)}</div>
                <div class="metric-label">Modules Tested</div>
            </div>
        </div>
        """

    def generate_html_table_row(self, module: str, coverage: float, tests: Set[str]) -> str:
        """Generate a single HTML table row."""
        thresholds = self.config["coverage_thresholds"]
        coverage_class = (
            "coverage-high"
            if coverage >= thresholds["high"]
            else "coverage-medium"
            if coverage >= thresholds["medium"]
            else "coverage-low"
        )

        test_list = ""
        if tests:
            test_names = sorted([t.replace("tests/", "") for t in tests])[
                : self.config["max_tests_shown"]
            ]
            test_list = "<br>".join(test_names)
            if len(tests) > self.config["max_tests_shown"]:
                test_list += (
                    f"<br><i>... and {len(tests) - self.config['max_tests_shown']} more</i>"
                )
        else:
            test_list = '<span class="no-tests">No direct test coverage</span>'

        return f"""
        <tr>
            <td><code>{module}</code></td>
            <td>
                <div class="coverage-bar">
                    <div class="coverage-fill {coverage_class}" style="width: {coverage}%"></div>
                    <div class="coverage-text">{coverage:.1f}%</div>
                </div>
            </td>
            <td class="test-list">{test_list}</td>
        </tr>
        """

    def generate_html(self, mapping: Dict[str, Set[str]], summary: Dict[str, Any]) -> str:
        """Generate complete HTML report."""
        overall = summary.get("overall", {})
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build HTML document
        html_parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f"<title>Test Coverage Matrix - {timestamp.split()[0]}</title>",
            "<style>",
            self.generate_html_styles(),
            "</style>",
            "</head>",
            "<body>",
            '<div class="container">',
            "<h1>Test Coverage Matrix</h1>",
            f"<p>Generated on {timestamp}</p>",
            self.generate_html_metrics(overall, mapping),
            "<h2>Module Test Coverage Matrix</h2>",
            "<table>",
            "<thead>",
            "<tr>",
            "<th>Module</th>",
            "<th>Coverage</th>",
            "<th>Test Files</th>",
            "</tr>",
            "</thead>",
            "<tbody>",
        ]

        # Get all modules and their coverage
        all_modules = self._collect_all_modules(summary, mapping)
        sorted_modules = sorted(all_modules.items(), key=lambda x: x[1], reverse=True)

        # Add table rows
        for module, coverage in sorted_modules:
            tests = mapping.get(module, set())
            html_parts.append(self.generate_html_table_row(module, coverage, tests))

        # Close HTML
        html_parts.extend(["</tbody>", "</table>", "</div>", "</body>", "</html>"])

        return "\n".join(html_parts)

    def generate_markdown(self, mapping: Dict[str, Set[str]], summary: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        overall = summary.get("overall", {})
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        thresholds = self.config["coverage_thresholds"]

        # Build markdown content
        md_parts = [
            "# Test Coverage Matrix",
            "",
            f"Generated on {timestamp}",
            "",
            "## Summary",
            "",
            f'- **Line Coverage**: {overall.get("line_coverage", 0):.1f}%',
            f'- **Branch Coverage**: {overall.get("branch_coverage", 0)}%',
            f'- **Tests Passed**: {overall.get("tests_passed", 0)}',
            f"- **Modules Tested**: {len(mapping)}",
            "",
            "## Module Test Coverage Matrix",
            "",
            "| Module | Coverage | Test Count | Primary Tests |",
            "|--------|----------|------------|---------------|",
        ]

        # Get all modules and sort by coverage
        all_modules = self._collect_all_modules(summary, mapping)
        sorted_modules = sorted(all_modules.items(), key=lambda x: x[1], reverse=True)

        # Add table rows
        for module, coverage in sorted_modules:
            tests = mapping.get(module, set())
            status = (
                "✅"
                if coverage >= thresholds["high"]
                else "🟡"
                if coverage >= thresholds["medium"]
                else "🔴"
            )

            if tests:
                test_names = sorted([t.replace("tests/", "").replace("test_", "") for t in tests])[
                    : self.config["max_test_names"]
                ]
                test_info = f"{len(tests)} | {', '.join(test_names)}"
                if len(tests) > self.config["max_test_names"]:
                    test_info += " ..."
            else:
                test_info = "0 | ⚠️ No direct tests"

            md_parts.append(f"| `{module}` | {coverage:.1f}% {status} | {test_info} |")

        return "\n".join(md_parts)

    def _collect_all_modules(
        self, summary: Dict[str, Any], mapping: Dict[str, Set[str]]
    ) -> Dict[str, float]:
        """Collect all modules from summary and mapping."""
        all_modules = {}

        # Get modules from summary
        for module_list in ["top_modules", "critical_modules"]:
            for module in summary.get(module_list, []):
                if isinstance(module, dict) and "name" in module and "coverage" in module:
                    all_modules[module["name"]] = module["coverage"]

        # Add modules from mapping
        for module in mapping:
            if module not in all_modules:
                all_modules[module] = 0.0

        return all_modules


class CoverageMatrixGenerator:
    """Main class for generating coverage matrix reports."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer = CoverageAnalyzer(config)
        self.reporter = ReportGenerator(config)

    def generate(self) -> None:
        """Generate coverage matrix reports."""
        try:
            # Get test-to-module mapping
            coverage_file = Path("coverage.json")
            mapping = self.analyzer.parse_coverage_json(coverage_file)

            # Load coverage summary
            summary_path = Path("coverage-summary.json")
            summary = self.analyzer.load_coverage_summary(summary_path)

            # Generate HTML report
            self._generate_html_report(mapping, summary)

            # Generate Markdown report
            self._generate_markdown_report(mapping, summary)

            # Update .gitignore if needed
            self._update_gitignore()

        except CoverageMatrixError as e:
            logger.error(f"Coverage matrix generation failed: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            sys.exit(1)

    def _generate_html_report(self, mapping: Dict[str, Set[str]], summary: Dict[str, Any]) -> None:
        """Generate and save HTML report."""
        html_content = self.reporter.generate_html(mapping, summary)
        html_path = Path(self.config["output_dir"]) / "coverage-matrix.html"

        try:
            with open(html_path, "w") as f:
                f.write(html_content)
            logger.info(f"✅ Generated HTML matrix: {html_path}")
        except IOError as e:
            raise CoverageMatrixError(f"Failed to write HTML report: {e}")

    def _generate_markdown_report(
        self, mapping: Dict[str, Set[str]], summary: Dict[str, Any]
    ) -> None:
        """Generate and save Markdown report."""
        md_content = self.reporter.generate_markdown(mapping, summary)
        md_path = Path(self.config["docs_dir"]) / "coverage-matrix.md"

        try:
            # Create docs directory if it doesn't exist
            md_path.parent.mkdir(parents=True, exist_ok=True)

            with open(md_path, "w") as f:
                f.write(md_content)
            logger.info(f"✅ Generated Markdown matrix: {md_path}")
        except IOError as e:
            raise CoverageMatrixError(f"Failed to write Markdown report: {e}")

    def _update_gitignore(self) -> None:
        """Update .gitignore if needed."""
        gitignore_path = Path(".gitignore")

        if not gitignore_path.exists():
            return

        try:
            content = gitignore_path.read_text()
            if "coverage-matrix.html" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n# Coverage matrix (HTML version)\ncoverage-matrix.html\n")
                logger.info("✅ Added coverage-matrix.html to .gitignore")
        except IOError as e:
            logger.warning(f"Failed to update .gitignore: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate test coverage matrix reports",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--max-tests-shown",
        type=int,
        default=DEFAULT_CONFIG["max_tests_shown"],
        help="Maximum number of tests to show in HTML report",
    )

    parser.add_argument(
        "--max-test-names",
        type=int,
        default=DEFAULT_CONFIG["max_test_names"],
        help="Maximum number of test names to show in Markdown report",
    )

    parser.add_argument(
        "--high-threshold",
        type=int,
        default=DEFAULT_CONFIG["coverage_thresholds"]["high"],
        help="Coverage threshold for high coverage",
    )

    parser.add_argument(
        "--medium-threshold",
        type=int,
        default=DEFAULT_CONFIG["coverage_thresholds"]["medium"],
        help="Coverage threshold for medium coverage",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_CONFIG["timeout_seconds"],
        help="Timeout in seconds for running tests",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_CONFIG["output_dir"],
        help="Output directory for HTML report",
    )

    parser.add_argument(
        "--docs-dir",
        type=str,
        default=DEFAULT_CONFIG["docs_dir"],
        help="Output directory for Markdown report",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Build config from arguments
    config = DEFAULT_CONFIG.copy()
    config.update(
        {
            "max_tests_shown": args.max_tests_shown,
            "max_test_names": args.max_test_names,
            "coverage_thresholds": {"high": args.high_threshold, "medium": args.medium_threshold},
            "timeout_seconds": args.timeout,
            "output_dir": args.output_dir,
            "docs_dir": args.docs_dir,
        }
    )

    # Generate reports
    generator = CoverageMatrixGenerator(config)
    generator.generate()


if __name__ == "__main__":
    main()
