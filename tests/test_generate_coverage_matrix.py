"""Tests for generate_coverage_matrix.py script."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Set
from unittest import mock
from unittest.mock import patch

import pytest

# Import the script modules
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_coverage_matrix import (  # noqa: E402  # type: ignore[import]
    DEFAULT_CONFIG,
    CoverageAnalyzer,
    CoverageDataValidator,
    CoverageMatrixError,
    CoverageMatrixGenerator,
    ReportGenerator,
)


class TestCoverageDataValidator:
    """Test coverage data validation."""

    def test_validate_summary_valid(self):
        """Test validation of valid summary data."""
        data = {"overall": {"line_coverage": 75.5, "branch_coverage": 60, "tests_passed": 100}}
        assert CoverageDataValidator.validate_summary(data) is True

    def test_validate_summary_missing_overall(self):
        """Test validation fails when overall is missing."""
        with pytest.raises(CoverageMatrixError, match="Missing required field: overall"):
            CoverageDataValidator.validate_summary({})

    def test_validate_summary_not_dict(self):
        """Test validation fails when data is not a dict."""
        with pytest.raises(CoverageMatrixError, match="must be a dictionary"):
            CoverageDataValidator.validate_summary([])

    def test_validate_coverage_json_valid(self):
        """Test validation of valid coverage.json data."""
        data: Dict[str, Any] = {"files": {"src/module.py": {"contexts": {}}}}
        assert CoverageDataValidator.validate_coverage_json(data) is True

    def test_validate_coverage_json_missing_files(self):
        """Test validation fails when files field is missing."""
        with pytest.raises(CoverageMatrixError, match="missing 'files' field"):
            CoverageDataValidator.validate_coverage_json({})


class TestCoverageAnalyzer:
    """Test coverage analyzer functionality."""

    def test_run_coverage_tests_success(self):
        """Test successful test run."""
        config = DEFAULT_CONFIG.copy()
        analyzer = CoverageAnalyzer(config)

        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="Tests passed", stderr="")

            stdout, stderr = analyzer.run_coverage_tests()
            assert stdout == "Tests passed"
            assert stderr == ""

    def test_run_coverage_tests_timeout(self):
        """Test timeout handling."""
        config = DEFAULT_CONFIG.copy()
        analyzer = CoverageAnalyzer(config)

        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 120)

            with pytest.raises(CoverageMatrixError, match="timed out"):
                analyzer.run_coverage_tests()

    def test_extract_tests_for_file(self):
        """Test extracting test names from file data."""
        analyzer = CoverageAnalyzer(DEFAULT_CONFIG.copy())

        file_data = {
            "contexts": {
                "10": ["tests/test_module.py|run"],
                "20": [
                    "tests/test_module.py|run",
                    "tests/test_other.py|run",
                ],
            }
        }

        tests = analyzer._extract_tests_for_file(file_data)
        assert tests == {"tests/test_module.py", "tests/test_other.py"}

    def test_parse_coverage_json_file_not_exists(self):
        """Test parsing when coverage.json doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coverage_file = Path(tmpdir) / "coverage.json"
            analyzer = CoverageAnalyzer(DEFAULT_CONFIG.copy())

            # Mock run_coverage_tests to not actually run tests
            with mock.patch.object(analyzer, "run_coverage_tests") as mock_run:
                mock_run.return_value = ("", "")

                with pytest.raises(CoverageMatrixError, match="Failed to generate coverage.json"):
                    analyzer.parse_coverage_json(coverage_file)

    def test_load_coverage_summary_valid(self):
        """Test loading valid coverage summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            summary_path = Path(tmpdir) / "coverage-summary.json"
            data = {"overall": {"line_coverage": 80}}

            with open(summary_path, "w") as f:
                json.dump(data, f)

            analyzer = CoverageAnalyzer(DEFAULT_CONFIG.copy())
            result = analyzer.load_coverage_summary(summary_path)

            assert result == data

    def test_load_coverage_summary_missing_file(self):
        """Test loading when summary file doesn't exist."""
        analyzer = CoverageAnalyzer(DEFAULT_CONFIG.copy())
        result = analyzer.load_coverage_summary(Path("nonexistent.json"))
        assert result == {}


class TestReportGenerator:
    """Test report generation functionality."""

    def test_generate_html_styles(self):
        """Test CSS generation."""
        reporter = ReportGenerator(DEFAULT_CONFIG.copy())
        styles = reporter.generate_html_styles()

        assert "body {" in styles
        assert ".coverage-high" in styles
        assert ".coverage-medium" in styles
        assert ".coverage-low" in styles

    def test_generate_html_metrics(self):
        """Test HTML metrics generation."""
        reporter = ReportGenerator(DEFAULT_CONFIG.copy())
        overall = {"line_coverage": 75.5, "branch_coverage": 60, "tests_passed": 100}
        mapping: Dict[str, Set[str]] = {"src/module1.py": set(), "src/module2.py": set()}

        html = reporter.generate_html_metrics(overall, mapping)

        assert "75.5%" in html
        assert "60%" in html
        assert "100" in html
        assert "2" in html  # Number of modules

    def test_generate_html_table_row(self):
        """Test HTML table row generation."""
        config = DEFAULT_CONFIG.copy()
        reporter = ReportGenerator(config)

        # Test with high coverage and tests
        html = reporter.generate_html_table_row(
            "src/module.py", 90.5, {"tests/test_module.py", "tests/test_integration.py"}
        )

        assert "src/module.py" in html
        assert "90.5%" in html
        assert "coverage-high" in html
        assert "test_module.py" in html

    def test_generate_html_table_row_no_tests(self):
        """Test HTML table row with no tests."""
        reporter = ReportGenerator(DEFAULT_CONFIG.copy())

        html = reporter.generate_html_table_row("src/module.py", 30.0, set())

        assert "coverage-low" in html
        assert "No direct test coverage" in html

    def test_collect_all_modules(self):
        """Test collecting modules from summary and mapping."""
        reporter = ReportGenerator(DEFAULT_CONFIG.copy())

        summary = {
            "top_modules": [
                {"name": "src/module1.py", "coverage": 90},
                {"name": "src/module2.py", "coverage": 85},
            ],
            "critical_modules": [{"name": "src/module3.py", "coverage": 30}],
        }

        mapping = {
            "src/module4.py": {"tests/test_module4.py"},
            "src/module1.py": {"tests/test_module1.py"},
        }

        modules = reporter._collect_all_modules(summary, mapping)

        assert modules == {
            "src/module1.py": 90,
            "src/module2.py": 85,
            "src/module3.py": 30,
            "src/module4.py": 0.0,
        }

    def test_generate_markdown(self):
        """Test Markdown report generation."""
        reporter = ReportGenerator(DEFAULT_CONFIG.copy())

        summary = {
            "overall": {"line_coverage": 75.5, "branch_coverage": 60, "tests_passed": 100},
            "top_modules": [{"name": "src/module.py", "coverage": 90}],
        }

        mapping = {"src/module.py": {"tests/test_module.py"}}

        md = reporter.generate_markdown(mapping, summary)

        assert "# Test Coverage Matrix" in md
        assert "75.5%" in md
        assert "src/module.py" in md
        assert "✅" in md  # High coverage indicator


class TestCoverageMatrixGenerator:
    """Test the main generator class."""

    def test_generate_html_report_success(self):
        """Test successful HTML report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DEFAULT_CONFIG.copy()
            config["output_dir"] = tmpdir

            generator = CoverageMatrixGenerator(config)

            # Mock the reporter
            with mock.patch.object(generator.reporter, "generate_html") as mock_gen:
                mock_gen.return_value = "<html>Test</html>"

                generator._generate_html_report({}, {})

                html_path = Path(tmpdir) / "coverage-matrix.html"
                assert html_path.exists()
                assert html_path.read_text() == "<html>Test</html>"

    def test_generate_markdown_report_success(self):
        """Test successful Markdown report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DEFAULT_CONFIG.copy()
            config["docs_dir"] = tmpdir

            generator = CoverageMatrixGenerator(config)

            # Mock the reporter
            with mock.patch.object(generator.reporter, "generate_markdown") as mock_gen:
                mock_gen.return_value = "# Test Report"

                generator._generate_markdown_report({}, {})

                md_path = Path(tmpdir) / "coverage-matrix.md"
                assert md_path.exists()
                assert md_path.read_text() == "# Test Report"

    def test_update_gitignore(self):
        """Test updating .gitignore file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Work in temp directory without changing cwd
            tmpdir_path = Path(tmpdir)
            gitignore_path = tmpdir_path / ".gitignore"

            # Create initial .gitignore
            with open(gitignore_path, "w") as f:
                f.write("*.pyc\n")

            # Mock the current directory to be the temp directory for Path operations
            with (
                patch("pathlib.Path.cwd", return_value=tmpdir_path),
                patch(
                    "generate_coverage_matrix.Path",
                    side_effect=lambda p: tmpdir_path / p if p == ".gitignore" else Path(p),
                ),
            ):
                generator = CoverageMatrixGenerator(DEFAULT_CONFIG.copy())
                generator._update_gitignore()

            content = gitignore_path.read_text()
            assert "coverage-matrix.html" in content

    def test_generate_error_handling(self):
        """Test error handling in main generate method."""
        generator = CoverageMatrixGenerator(DEFAULT_CONFIG.copy())

        # Mock analyzer to raise an error
        with mock.patch.object(generator.analyzer, "parse_coverage_json") as mock_parse:
            mock_parse.side_effect = CoverageMatrixError("Test error")

            with pytest.raises(SystemExit):
                generator.generate()


class TestCommandLineArgs:
    """Test command line argument parsing."""

    def test_parse_args_defaults(self):
        """Test default argument values."""
        from generate_coverage_matrix import parse_args

        with mock.patch("sys.argv", ["script.py"]):
            args = parse_args()

            assert args.max_tests_shown == 5
            assert args.max_test_names == 3
            assert args.high_threshold == 85
            assert args.medium_threshold == 70
            assert args.timeout == 120
            assert args.output_dir == "."
            assert args.docs_dir == "docs"
            assert args.debug is False

    def test_parse_args_custom(self):
        """Test custom argument values."""
        from generate_coverage_matrix import parse_args

        with mock.patch(
            "sys.argv",
            ["script.py", "--max-tests-shown", "10", "--high-threshold", "90", "--debug"],
        ):
            args = parse_args()

            assert args.max_tests_shown == 10
            assert args.high_threshold == 90
            assert args.debug is True
