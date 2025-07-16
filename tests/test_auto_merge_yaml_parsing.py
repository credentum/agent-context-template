"""
Tests for auto-merge workflow YAML parsing functionality.

Tests the Python-based YAML parsing logic used in the auto-merge workflow
to extract automation flags and prevent shell parsing errors.
"""

import os
import tempfile
from unittest.mock import mock_open, patch

import pytest
import yaml


class TestAutoMergeYAMLParsing:
    """Test suite for auto-merge workflow YAML parsing."""

    @pytest.fixture
    def sample_pr_metadata_auto_merge_enabled(self):
        """Sample PR metadata with auto-merge enabled."""
        return {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [150],
                "breaking_change": False,
                "automation_flags": {"auto_merge": True, "skip_ci": False, "update_docs": False},
            }
        }

    @pytest.fixture
    def sample_pr_metadata_auto_merge_disabled(self):
        """Sample PR metadata with auto-merge disabled."""
        return {
            "pr_metadata": {
                "type": "fix",
                "closes_issues": [200],
                "breaking_change": False,
                "automation_flags": {"auto_merge": False, "skip_ci": False, "update_docs": True},
            }
        }

    @pytest.fixture
    def sample_pr_metadata_no_automation_flags(self):
        """Sample PR metadata without automation_flags section."""
        return {"pr_metadata": {"type": "docs", "closes_issues": [], "breaking_change": False}}

    def test_extract_auto_merge_flag_enabled(self, sample_pr_metadata_auto_merge_enabled):
        """Test extracting auto_merge flag when enabled."""
        # Simulate the Python code used in auto-merge workflow
        metadata = sample_pr_metadata_auto_merge_enabled
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is True

    def test_extract_auto_merge_flag_disabled(self, sample_pr_metadata_auto_merge_disabled):
        """Test extracting auto_merge flag when disabled."""
        metadata = sample_pr_metadata_auto_merge_disabled
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is False

    def test_extract_auto_merge_flag_missing_automation_flags(
        self, sample_pr_metadata_no_automation_flags
    ):
        """Test extracting auto_merge flag when automation_flags section is missing."""
        metadata = sample_pr_metadata_no_automation_flags
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is False  # Default value

    def test_extract_auto_merge_flag_missing_pr_metadata(self):
        """Test extracting auto_merge flag when pr_metadata section is missing."""
        metadata = {"some_other_key": "value"}
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is False

    def test_extract_auto_merge_flag_invalid_metadata_type(self):
        """Test extracting auto_merge flag when metadata is not a dict."""
        metadata = "invalid_metadata_type"
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is False

    def test_complete_yaml_parsing_pipeline_auto_merge_enabled(
        self, sample_pr_metadata_auto_merge_enabled
    ):
        """Test complete YAML parsing pipeline for auto-merge workflow (enabled case)."""
        # Step 1: Simulate YAML content extraction from PR body
        yaml_content = yaml.dump(sample_pr_metadata_auto_merge_enabled, default_flow_style=False)

        # Step 2: Parse YAML content (as done in workflow)
        metadata = yaml.safe_load(yaml_content)

        # Step 3: Extract auto_merge flag (exact logic from workflow)
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        # Step 4: Convert to string for shell output (as in workflow)
        auto_merge_flag = "true" if auto_merge else "false"

        assert auto_merge_flag == "true"

    def test_complete_yaml_parsing_pipeline_auto_merge_disabled(
        self, sample_pr_metadata_auto_merge_disabled
    ):
        """Test complete YAML parsing pipeline for auto-merge workflow (disabled case)."""
        yaml_content = yaml.dump(sample_pr_metadata_auto_merge_disabled, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)
        auto_merge_flag = "true" if auto_merge else "false"

        assert auto_merge_flag == "false"

    def test_yaml_parsing_with_special_characters(self):
        """Test YAML parsing with special characters that would break shell parsing."""
        metadata_with_special_chars = {
            "pr_metadata": {
                "type": "fix",
                "closes_issues": [150],
                "breaking_change": False,
                "description": "Fix issue with $VAR and `command` and \"quotes\" and 'apostrophes'",
                "automation_flags": {"auto_merge": True, "skip_ci": False},
            }
        }

        # This should parse correctly without shell injection issues
        yaml_content = yaml.dump(metadata_with_special_chars, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is True
        assert (
            pr_metadata["description"]
            == "Fix issue with $VAR and `command` and \"quotes\" and 'apostrophes'"
        )

    def test_yaml_parsing_error_handling(self):
        """Test error handling when YAML parsing fails."""
        invalid_yaml = """
pr_metadata:
  type: "feature"
  closes_issues: [150
  automation_flags:
    auto_merge: true
# Missing closing bracket - invalid YAML
"""

        try:
            metadata = yaml.safe_load(invalid_yaml)
            # If YAML is invalid, safe_load might return None or raise exception
            if metadata is None:
                auto_merge_flag = "false"
            else:
                pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
                automation_flags = pr_metadata.get("automation_flags", {})
                auto_merge = automation_flags.get("auto_merge", False)
                auto_merge_flag = "true" if auto_merge else "false"
        except yaml.YAMLError:
            # Handle YAML parsing error gracefully
            auto_merge_flag = "false"

        assert auto_merge_flag == "false"

    @patch("builtins.open", new_callable=mock_open)
    def test_file_operations_workflow_simulation(
        self, mock_file, sample_pr_metadata_auto_merge_enabled
    ):
        """Test file operations as performed in the actual workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_auto_merge_enabled, default_flow_style=False)

        # Simulate writing YAML content to temporary file (as in workflow)
        with open("/tmp/pr_metadata.yaml", "w") as f:
            f.write(yaml_content)

        mock_file.assert_called_once_with("/tmp/pr_metadata.yaml", "w")
        mock_file().write.assert_called_once_with(yaml_content)

    @patch("builtins.open", new_callable=mock_open)
    def test_read_yaml_file_workflow_simulation(
        self, mock_file, sample_pr_metadata_auto_merge_enabled
    ):
        """Test reading YAML file as performed in the actual workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_auto_merge_enabled, default_flow_style=False)
        mock_file.return_value.read.return_value = yaml_content

        # Simulate reading and parsing YAML file (as in workflow)
        with open("/tmp/pr_metadata.yaml", "r") as f:
            content = f.read()
            metadata = yaml.safe_load(content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        mock_file.assert_called_once_with("/tmp/pr_metadata.yaml", "r")
        assert auto_merge is True

    def test_python_command_line_execution_simulation(self, sample_pr_metadata_auto_merge_enabled):
        """Test simulating the Python one-liner used in the workflow."""
        yaml_content = yaml.dump(sample_pr_metadata_auto_merge_enabled, default_flow_style=False)

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
automation_flags = pr_metadata.get('automation_flags', {{}})
auto_merge = automation_flags.get('auto_merge', False)
print('true' if auto_merge else 'false')
"""

            # Execute the code
            exec_globals = {}
            exec(python_code, exec_globals)

            # The code should execute without errors
            # In real workflow, this would output 'true' or 'false'

        finally:
            # Clean up
            os.unlink(temp_file)

    def test_edge_case_nested_yaml_structures(self):
        """Test parsing complex nested YAML structures."""
        complex_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [150, 200, 300],
                "breaking_change": False,
                "automation_flags": {
                    "auto_merge": True,
                    "skip_ci": False,
                    "update_docs": True,
                    "custom_flags": {
                        "nested_flag": True,
                        "nested_config": {"deep_setting": "value"},
                    },
                },
                "complex_data": {
                    "matrix": [[1, 2, 3], [4, 5, 6]],
                    "mappings": {"key1": {"subkey": "value1"}, "key2": {"subkey": "value2"}},
                },
            }
        }

        yaml_content = yaml.dump(complex_metadata, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is True
        assert pr_metadata["complex_data"]["matrix"][1][2] == 6
        assert automation_flags["custom_flags"]["nested_config"]["deep_setting"] == "value"

    def test_performance_large_yaml_auto_merge(self):
        """Test performance with large YAML content focusing on auto_merge extraction."""
        # Create large metadata with auto_merge flag
        large_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": list(range(1, 1001)),  # 1000 issues
                "breaking_change": False,
                "large_data": {
                    f"key_{i}": f"value_{i}" for i in range(1000)
                },  # 1000 key-value pairs
                "automation_flags": {
                    "auto_merge": True,
                    "skip_ci": False,
                    "large_config": {f"config_{i}": i for i in range(100)},  # 100 config items
                },
            }
        }

        yaml_content = yaml.dump(large_metadata, default_flow_style=False)
        metadata = yaml.safe_load(yaml_content)

        # Should efficiently extract auto_merge flag even with large data
        pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
        automation_flags = pr_metadata.get("automation_flags", {})
        auto_merge = automation_flags.get("auto_merge", False)

        assert auto_merge is True
        assert len(pr_metadata["closes_issues"]) == 1000
        assert len(pr_metadata["large_data"]) == 1000

    def test_comparison_with_legacy_text_parsing(self):
        """Test comparison between new YAML parsing and legacy text parsing."""
        # PR body with both YAML metadata and text content that could confuse text parsing
        pr_body = """---
pr_metadata:
  type: "fix"
  closes_issues: [150]
  breaking_change: false
  automation_flags:
    auto_merge: true
---

# Fix Auto-Merge Issues

This PR fixes issues with auto-merge functionality.

## Text that could confuse regex parsing:
- Some text mentioning "auto merge" functionality
- Discussion about "auto_merge: false" in comments
- Code examples with auto_merge settings

## Summary
The real auto_merge setting is in the YAML metadata above.
"""

        # YAML parsing approach (new, reliable)
        import re

        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", pr_body)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            metadata = yaml.safe_load(yaml_content)
            pr_metadata = metadata.get("pr_metadata", {}) if isinstance(metadata, dict) else {}
            automation_flags = pr_metadata.get("automation_flags", {})
            yaml_auto_merge = automation_flags.get("auto_merge", False)
        else:
            yaml_auto_merge = False

        # Legacy text parsing approach (old, unreliable)
        text_auto_merge_matches = re.findall(r"auto.*merge", pr_body, re.IGNORECASE)
        text_suggests_auto_merge = len(text_auto_merge_matches) > 0

        # YAML parsing gives definitive result
        assert yaml_auto_merge is True

        # Text parsing gives ambiguous result (multiple matches)
        assert text_suggests_auto_merge is True
        assert len(text_auto_merge_matches) >= 3  # Multiple false positives

        # This demonstrates why YAML parsing is more reliable
