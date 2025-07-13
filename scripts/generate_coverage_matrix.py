#!/usr/bin/env python3
"""
Generate a single-page coverage matrix showing test-to-module mapping
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def get_test_module_mapping() -> Dict[str, Set[str]]:
    """Get mapping of which tests cover which modules"""
    print("Analyzing test coverage mapping...")

    # Run pytest with coverage and capture detailed output
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=json", "-q"],
        capture_output=True,
        text=True,
    )

    # Parse coverage.json for detailed mapping
    mapping = {}
    coverage_file = Path("coverage.json")

    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)

        # Extract file coverage data
        for file_path, file_data in coverage_data.get("files", {}).items():
            if file_path.startswith("src/"):
                # Get contexts (test functions) that executed this file
                contexts = set()
                for line_contexts in file_data.get("contexts", {}).values():
                    contexts.update(line_contexts)

                # Clean up test names
                tests = set()
                for context in contexts:
                    if context and "|" in context:
                        test_name = context.split("|")[0]
                        if test_name.startswith("tests/"):
                            tests.add(test_name)

                if tests:
                    mapping[file_path] = tests

    return mapping


def load_coverage_summary() -> Dict[str, Any]:
    """Load current coverage summary"""
    summary_path = Path("coverage-summary.json")
    if summary_path.exists():
        with open(summary_path) as f:
            data: Dict[str, Any] = json.load(f)
            return data
    return {}


def generate_matrix_html(mapping: Dict[str, Set[str]], summary: Dict) -> str:
    """Generate HTML matrix report"""
    overall = summary.get("overall", {})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Coverage Matrix - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #0366d6;
        }}
        .metric-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #e1e4e8;
        }}
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f6f8fa;
        }}
        .coverage-bar {{
            background-color: #e1e4e8;
            height: 20px;
            border-radius: 3px;
            overflow: hidden;
            position: relative;
        }}
        .coverage-fill {{
            height: 100%;
            background-color: #28a745;
            transition: width 0.3s ease;
        }}
        .coverage-text {{
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            font-weight: 600;
        }}
        .coverage-low {{ background-color: #dc3545; }}
        .coverage-medium {{ background-color: #ffc107; }}
        .coverage-high {{ background-color: #28a745; }}
        .test-list {{
            font-size: 0.85em;
            color: #666;
            max-height: 100px;
            overflow-y: auto;
        }}
        .no-tests {{
            color: #dc3545;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Coverage Matrix</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

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

        <h2>Module Test Coverage Matrix</h2>
        <table>
            <thead>
                <tr>
                    <th>Module</th>
                    <th>Coverage</th>
                    <th>Test Files</th>
                </tr>
            </thead>
            <tbody>
"""

    # Get all modules from coverage summary
    all_modules = {}
    for module_list in ["top_modules", "critical_modules"]:
        for module in summary.get(module_list, []):
            all_modules[module["name"]] = module["coverage"]

    # Add modules from mapping
    for module in mapping:
        if module not in all_modules:
            all_modules[module] = 0.0

    # Sort by coverage (descending)
    sorted_modules = sorted(all_modules.items(), key=lambda x: x[1], reverse=True)

    for module, coverage in sorted_modules:
        tests = mapping.get(module, set())
        coverage_class = (
            "coverage-high"
            if coverage >= 85
            else "coverage-medium"
            if coverage >= 70
            else "coverage-low"
        )

        test_list = ""
        if tests:
            test_names = sorted([t.replace("tests/", "") for t in tests])[:5]  # Show first 5
            test_list = "<br>".join(test_names)
            if len(tests) > 5:
                test_list += f"<br><i>... and {len(tests) - 5} more</i>"
        else:
            test_list = '<span class="no-tests">No direct test coverage</span>'

        html += f"""
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

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    return html


def generate_matrix_markdown(mapping: Dict[str, Set[str]], summary: Dict) -> str:
    """Generate Markdown matrix report"""
    overall = summary.get("overall", {})

    md = f"""# Test Coverage Matrix

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Line Coverage**: {overall.get('line_coverage', 0):.1f}%
- **Branch Coverage**: {overall.get('branch_coverage', 0)}%
- **Tests Passed**: {overall.get('tests_passed', 0)}
- **Modules Tested**: {len(mapping)}

## Module Test Coverage Matrix

| Module | Coverage | Test Count | Primary Tests |
|--------|----------|------------|---------------|
"""

    # Get all modules
    all_modules = {}
    for module_list in ["top_modules", "critical_modules"]:
        for module in summary.get(module_list, []):
            all_modules[module["name"]] = module["coverage"]

    for module in mapping:
        if module not in all_modules:
            all_modules[module] = 0.0

    # Sort by coverage (descending)
    sorted_modules = sorted(all_modules.items(), key=lambda x: x[1], reverse=True)

    for module, coverage in sorted_modules:
        tests = mapping.get(module, set())
        status = "✅" if coverage >= 85 else "🟡" if coverage >= 70 else "🔴"

        if tests:
            test_names = sorted([t.replace("tests/", "").replace("test_", "") for t in tests])[:3]
            test_info = f"{len(tests)} | {', '.join(test_names)}"
            if len(tests) > 3:
                test_info += " ..."
        else:
            test_info = "0 | ⚠️ No direct tests"

        md += f"| `{module}` | {coverage:.1f}% {status} | {test_info} |\n"

    return md


def main():
    """Main function"""
    # Get test-to-module mapping
    mapping = get_test_module_mapping()

    # Load coverage summary
    summary = load_coverage_summary()

    # Generate HTML matrix
    html_content = generate_matrix_html(mapping, summary)
    html_path = Path("coverage-matrix.html")
    with open(html_path, "w") as f:
        f.write(html_content)
    print(f"✅ Generated HTML matrix: {html_path}")

    # Generate Markdown matrix
    md_content = generate_matrix_markdown(mapping, summary)
    md_path = Path("docs/coverage-matrix.md")
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"✅ Generated Markdown matrix: {md_path}")

    # Update .gitignore if needed
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if "coverage-matrix.html" not in content:
            with open(gitignore, "a") as f:
                f.write("\n# Coverage matrix (HTML version)\ncoverage-matrix.html\n")
            print("✅ Added coverage-matrix.html to .gitignore")


if __name__ == "__main__":
    main()
