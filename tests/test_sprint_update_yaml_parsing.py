"""
Tests for sprint-update workflow YAML parsing functionality.

Tests the Python-based YAML parsing logic used in the sprint-update workflow
to extract closes_issues for reliable issue auto-closing.
"""

import os
import tempfile
from unittest.mock import mock_open, patch

import pytest
import yaml


class TestSprintUpdateYAMLParsing:
    """Test suite for sprint-update workflow YAML parsing."""

    @pytest.fixture
    def sample_pr_metadata_with_issues(self):
        """Sample PR metadata with multiple issues to close."""
        return {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [150, 200, 300],
                "breaking_change": False,
                "priority": "high",
            }
        }

    @pytest.fixture
    def sample_pr_metadata_no_issues(self):
        """Sample PR metadata with no issues to close."""
        return {
            "pr_metadata": {
                "type": "docs",
                "closes_issues": [],
                "breaking_change": False,
                "priority": "low",
            }
        }

    @pytest.fixture
    def sample_pr_metadata_single_issue(self):
        """Sample PR metadata with single issue to close."""
        return {
            "pr_metadata": {
                "type": "fix",
                "closes_issues": [42],
                "breaking_change": False,
                "priority": "medium",
            }
        }

    def test_extract_closes_issues_multiple(self, sample_pr_metadata_with_issues):
        """Test extracting multiple issue numbers from YAML metadata."""
        # Simulate the Python code used in sprint-update workflow
        metadata = sample_pr_metadata_with_issues
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == [150, 200, 300]
        assert len(closes_issues) == 3

    def test_extract_closes_issues_empty(self, sample_pr_metadata_no_issues):
        """Test extracting issue numbers when none are specified."""
        metadata = sample_pr_metadata_no_issues
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == []
        assert len(closes_issues) == 0

    def test_extract_closes_issues_single(self, sample_pr_metadata_single_issue):
        """Test extracting single issue number from YAML metadata."""
        metadata = sample_pr_metadata_single_issue
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == [42]
        assert len(closes_issues) == 1

    def test_extract_closes_issues_missing_pr_metadata(self):
        """Test extracting issue numbers when pr_metadata section is missing."""
        metadata = {"some_other_key": "value"}
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == []

    def test_extract_closes_issues_invalid_metadata_type(self):
        """Test extracting issue numbers when metadata is not a dict."""
        metadata = "invalid_metadata_type"
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == []

    def test_complete_yaml_parsing_pipeline_with_issues(self, sample_pr_metadata_with_issues):
        """Test complete YAML parsing pipeline for sprint-update workflow."""
        # Step 1: Simulate YAML content extraction from PR body
        yaml_content = yaml.dump(sample_pr_metadata_with_issues, default_flow_style=False)

        # Step 2: Parse YAML content (as done in workflow)
        metadata = yaml.safe_load(yaml_content)

        # Step 3: Extract closes_issues (exact logic from workflow)
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        # Step 4: Print each issue number (as done in workflow)
        issue_nums = []
        for issue_num in closes_issues:
            issue_nums.append(str(issue_num))

        assert issue_nums == ["150", "200", "300"]

    def test_complete_yaml_parsing_pipeline_no_issues(self, sample_pr_metadata_no_issues):
        """Test complete YAML parsing pipeline when no issues to close."""
        yaml_content = yaml.dump(sample_pr_metadata_no_issues, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        issue_nums = []
        for issue_num in closes_issues:
            issue_nums.append(str(issue_num))

        assert issue_nums == []

    def test_yaml_parsing_with_special_characters_in_description(self):
        """Test YAML parsing with special characters that would break shell parsing."""
        metadata_with_special_chars = {
            "pr_metadata": {
                "type": "fix",
                "closes_issues": [150, 200],
                "breaking_change": False,
                "description": (
                    'Fix issues with $VARIABLES and `commands` and "quotes" and '
                    "'apostrophes' and <tags>"
                ),
                "notes": "This fixes closes #999 and resolves #888 mentioned in text",
            }
        }

        # This should parse correctly without shell injection issues
        yaml_content = yaml.dump(metadata_with_special_chars, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        # Should get the real closes_issues from YAML, not confused by text mentions
        assert closes_issues == [150, 200]
        expected_desc = (
            'Fix issues with $VARIABLES and `commands` and "quotes" and ' "'apostrophes' and <tags>"
        )
        assert pr_metadata["description"] == expected_desc

    def test_yaml_parsing_error_handling(self):
        """Test error handling when YAML parsing fails."""
        invalid_yaml = """
pr_metadata:
  type: "feature"
  closes_issues: [150, 200
  breaking_change: false
# Missing closing bracket - invalid YAML
"""

        try:
            metadata = yaml.safe_load(invalid_yaml)
            if metadata is None:
                closes_issues = []
            else:
                pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
                closes_issues = pr_metadata.get("closes_issues", [])
        except yaml.YAMLError:
            # Handle YAML parsing error gracefully
            closes_issues = []

        assert closes_issues == []

    @patch("builtins.open", new_callable=mock_open)
    def test_file_operations_workflow_simulation(self, mock_file, sample_pr_metadata_with_issues):
        """Test file operations as performed in the actual sprint-update workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_with_issues, default_flow_style=False)

        # Simulate writing YAML content to temporary file (as in workflow)
        with open("/tmp/pr_metadata.yaml", "w") as f:
            f.write(yaml_content)

        mock_file.assert_called_once_with("/tmp/pr_metadata.yaml", "w")
        mock_file().write.assert_called_once_with(yaml_content)

    @patch("builtins.open", new_callable=mock_open)
    def test_read_yaml_file_workflow_simulation(self, mock_file, sample_pr_metadata_with_issues):
        """Test reading YAML file as performed in the actual sprint-update workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_with_issues, default_flow_style=False)
        mock_file.return_value.read.return_value = yaml_content

        # Simulate reading and parsing YAML file (as in workflow)
        with open("/tmp/pr_metadata.yaml", "r") as f:
            content = f.read()
            metadata = yaml.safe_load(content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        mock_file.assert_called_once_with("/tmp/pr_metadata.yaml", "r")
        assert closes_issues == [150, 200, 300]

    def test_python_command_line_execution_simulation(self, sample_pr_metadata_with_issues):
        """Test simulating the Python one-liner used in the sprint-update workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_with_issues, default_flow_style=False)

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_file = f.name

        try:
            # Simulate the Python one-liner from the workflow
            python_code = f"""
import yaml
f = open('{temp_file}', 'r')
metadata = yaml.safe_load(f)
f.close()
pr_metadata = metadata.get('pr_metadata', {{}}) if isinstance(metadata, dict) else {{}}
closes_issues = pr_metadata.get('closes_issues', [])
for issue_num in closes_issues:
    print(issue_num)
"""

            # Capture output
            import contextlib
            import io

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(python_code)

            result = output.getvalue().strip().split("\n")
            assert result == ["150", "200", "300"]

        finally:
            # Clean up
            os.unlink(temp_file)

    def test_fallback_to_legacy_parsing_integration(self):
        """Test integration between YAML parsing and legacy text parsing fallback."""
        # PR body with YAML metadata
        pr_body_with_yaml = """---
pr_metadata:
  type: "feature"
  closes_issues: [150, 200]
  breaking_change: false
---

# Pull Request Description

This PR implements new functionality.
"""

        # PR body without YAML metadata (legacy format)
        pr_body_without_yaml = """# Pull Request Description

Closes #300 and fixes #400

This PR implements new functionality.
"""

        import re

        # Test YAML parsing path
        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", pr_body_with_yaml)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            metadata = yaml.safe_load(yaml_content)
            pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
            closes_issues = pr_metadata.get("closes_issues", [])
            yaml_issues = [str(issue) for issue in closes_issues]
        else:
            yaml_issues = []

        # Test legacy text parsing fallback
        yaml_match_legacy = re.search(r"---\s*\n([\s\S]*?)\n---", pr_body_without_yaml)
        if not yaml_match_legacy:
            # Fallback to legacy regex parsing
            combined_text = pr_body_without_yaml
            legacy_issues = re.findall(
                r"(?:closes?|fixes?|resolves?|implements?)\s+#(\d+)", combined_text, re.IGNORECASE
            )
        else:
            legacy_issues = []

        assert yaml_issues == ["150", "200"]
        assert legacy_issues == ["300", "400"]

    def test_edge_case_large_issue_numbers(self):
        """Test handling large issue numbers."""
        metadata_with_large_issues = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [
                    999999,
                    1000000,
                    2147483647,
                ],  # Large numbers including max 32-bit int
                "breaking_change": False,
            }
        }

        yaml_content = yaml.dump(metadata_with_large_issues, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert closes_issues == [999999, 1000000, 2147483647]

        # Test conversion to strings (as done in workflow)
        issue_strings = [str(issue) for issue in closes_issues]
        assert issue_strings == ["999999", "1000000", "2147483647"]

    def test_edge_case_duplicate_issue_numbers(self):
        """Test handling duplicate issue numbers in closes_issues."""
        metadata_with_duplicates = {
            "pr_metadata": {
                "type": "fix",
                "closes_issues": [150, 200, 150, 300, 200],  # Duplicates
                "breaking_change": False,
            }
        }

        yaml_content = yaml.dump(metadata_with_duplicates, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        # YAML parsing preserves duplicates (workflow handles deduplication later)
        assert closes_issues == [150, 200, 150, 300, 200]

        # Simulate deduplication as done in workflow
        unique_issues = list(dict.fromkeys(closes_issues))  # Preserves order, removes duplicates
        assert unique_issues == [150, 200, 300]

    def test_performance_large_issue_list(self):
        """Test performance with large list of issues."""
        # Create metadata with many issues
        large_issue_list = list(range(1, 1001))  # 1000 issues
        large_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": large_issue_list,
                "breaking_change": False,
            }
        }

        yaml_content = yaml.dump(large_metadata, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        closes_issues = pr_metadata.get("closes_issues", [])

        assert len(closes_issues) == 1000
        assert closes_issues[0] == 1
        assert closes_issues[-1] == 1000

    def test_comparison_yaml_vs_regex_parsing_reliability(self):
        """Test comparison between YAML parsing and regex parsing for reliability."""
        # Complex PR body that could confuse regex parsing
        complex_pr_body = """## ARC-Reviewer Comments

This PR fixes several issues mentioned in the comments.

---
pr_metadata:
  type: "fix"
  closes_issues: [150, 200]
  breaking_change: false
  description: "Fixes closes #999 mentioned in code comments and resolves #888 in documentation"
---

# Pull Request Description

This PR closes #150 and fixes #200 for real.

## Code Comments Include:
- Some code has comments like "// closes #999 when condition is met"
- Documentation mentions "resolves #888" as example
- Test data includes "fixes #777" in mock strings

## Real Issues
The actual issues being closed are specified in the YAML metadata above.

## Additional Notes
Text parsing would incorrectly find closes #999, resolves #888, fixes #777
but YAML parsing gives us the definitive list: [150, 200]
"""

        # YAML parsing approach (reliable)
        import re

        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", complex_pr_body)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            metadata = yaml.safe_load(yaml_content)
            pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
            yaml_closes_issues = pr_metadata.get("closes_issues", [])
        else:
            yaml_closes_issues = []

        # Regex parsing approach (unreliable - gets false positives)
        regex_issues = re.findall(
            r"(?:closes?|fixes?|resolves?)\s+#(\d+)", complex_pr_body, re.IGNORECASE
        )

        # YAML parsing gives correct, definitive result
        assert yaml_closes_issues == [150, 200]

        # Regex parsing includes false positives from comments and examples
        assert set(regex_issues) == {"999", "150", "888", "200", "777"}
        assert len(regex_issues) > len(yaml_closes_issues)

        # This demonstrates why YAML parsing is more reliable for automation
