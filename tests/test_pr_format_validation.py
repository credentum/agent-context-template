"""
Tests for PR format validation functionality.

Tests the PR format validation workflow components including:
- YAML frontmatter parsing
- Schema validation
- Issue reference checking
- Error handling scenarios
"""

from unittest.mock import mock_open, patch

import jsonschema
import pytest
import yaml


class TestPRFormatValidation:
    """Test suite for PR format validation functionality."""

    @pytest.fixture
    def sample_valid_metadata(self):
        """Sample valid PR metadata for testing."""
        return {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [150, 200],
                "priority": "high",
                "breaking_change": False,
                "affects_components": ["workflow", "automation"],
                "test_coverage": {"added": True, "percentage": 85, "requirements_met": True},
                "risk_assessment": "medium",
                "review_requirements": {"security_review": False, "architecture_review": True},
                "automation_flags": {"auto_merge": True, "skip_ci": False, "update_docs": False},
            }
        }

    @pytest.fixture
    def sample_pr_body_with_yaml(self, sample_valid_metadata):
        """Sample PR body with YAML frontmatter."""
        yaml_content = yaml.dump(sample_valid_metadata, default_flow_style=False)
        return f"""---
{yaml_content}---

# Pull Request Description

Closes #150

## Summary
This is a test PR description with proper YAML frontmatter.

## What Changed
- Added new functionality
- Updated existing code
- Fixed bugs
"""

    @pytest.fixture
    def sample_pr_body_without_yaml(self):
        """Sample PR body without YAML frontmatter."""
        return """# Pull Request Description

Closes #150

## Summary
This is a test PR description without YAML frontmatter.

## What Changed
- Added new functionality
- Updated existing code
- Fixed bugs
"""

    @pytest.fixture
    def pr_schema(self):
        """Load the PR metadata schema."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "pr_metadata": {
                    "type": "object",
                    "required": ["type", "closes_issues", "breaking_change"],
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["feature", "fix", "docs", "refactor", "test", "chore"],
                        },
                        "closes_issues": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 1},
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "default": "medium",
                        },
                        "breaking_change": {"type": "boolean", "default": False},
                        "affects_components": {"type": "array", "items": {"type": "string"}},
                        "test_coverage": {
                            "type": "object",
                            "properties": {
                                "added": {"type": "boolean"},
                                "percentage": {"type": "number"},
                                "requirements_met": {"type": "boolean"},
                            },
                        },
                        "risk_assessment": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "default": "low",
                        },
                        "review_requirements": {
                            "type": "object",
                            "properties": {
                                "security_review": {"type": "boolean", "default": False},
                                "architecture_review": {"type": "boolean", "default": False},
                            },
                        },
                        "automation_flags": {
                            "type": "object",
                            "properties": {
                                "auto_merge": {"type": "boolean", "default": False},
                                "skip_ci": {"type": "boolean", "default": False},
                                "update_docs": {"type": "boolean", "default": False},
                            },
                        },
                    },
                }
            },
            "required": ["pr_metadata"],
        }
        return schema_content

    def test_extract_yaml_frontmatter_valid(self, sample_pr_body_with_yaml):
        """Test extracting valid YAML frontmatter from PR body."""
        import re

        # Simulate the regex used in workflows
        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", sample_pr_body_with_yaml)

        assert yaml_match is not None, "Should find YAML frontmatter"
        yaml_content = yaml_match.group(1)

        # Parse the YAML content
        metadata = yaml.safe_load(yaml_content)

        assert metadata is not None
        assert "pr_metadata" in metadata
        assert metadata["pr_metadata"]["type"] == "feature"
        assert metadata["pr_metadata"]["closes_issues"] == [150, 200]

    def test_extract_yaml_frontmatter_missing(self, sample_pr_body_without_yaml):
        """Test handling missing YAML frontmatter."""
        import re

        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", sample_pr_body_without_yaml)

        assert yaml_match is None, "Should not find YAML frontmatter"

    def test_yaml_syntax_validation_valid(self, sample_valid_metadata):
        """Test YAML syntax validation with valid metadata."""
        yaml_content = yaml.dump(sample_valid_metadata, default_flow_style=False)

        # Should not raise exception
        parsed = yaml.safe_load(yaml_content)
        assert parsed == sample_valid_metadata

    def test_yaml_syntax_validation_invalid(self):
        """Test YAML syntax validation with invalid YAML."""
        invalid_yaml = """
pr_metadata:
  type: "feature"
  closes_issues: [150
  # Missing closing bracket - invalid YAML
"""

        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_yaml)

    def test_schema_validation_valid(self, sample_valid_metadata, pr_schema):
        """Test schema validation with valid metadata."""
        # Should not raise exception
        jsonschema.validate(sample_valid_metadata, pr_schema)

    def test_schema_validation_missing_required_field(self, pr_schema):
        """Test schema validation with missing required field."""
        invalid_metadata = {
            "pr_metadata": {
                "type": "feature",
                # Missing required 'closes_issues' and 'breaking_change'
                "priority": "high",
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_metadata, pr_schema)

    def test_schema_validation_invalid_type(self, pr_schema):
        """Test schema validation with invalid type value."""
        invalid_metadata = {
            "pr_metadata": {
                "type": "invalid_type",  # Not in enum
                "closes_issues": [150],
                "breaking_change": False,
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_metadata, pr_schema)

    def test_schema_validation_invalid_issue_number(self, pr_schema):
        """Test schema validation with invalid issue number."""
        invalid_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": [0],  # Invalid: must be >= 1
                "breaking_change": False,
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_metadata, pr_schema)

    def test_schema_validation_invalid_closes_issues_type(self, pr_schema):
        """Test schema validation with wrong type for closes_issues."""
        invalid_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": "150",  # Should be array, not string
                "breaking_change": False,
            }
        }

        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_metadata, pr_schema)

    def test_business_logic_validation_valid(self, sample_valid_metadata):
        """Test business logic validation with valid metadata."""
        pr_metadata = sample_valid_metadata["pr_metadata"]

        # Check required fields
        required_fields = ["type", "closes_issues", "breaking_change"]
        for field in required_fields:
            assert field in pr_metadata, f"Missing required field: {field}"

        # Validate type
        valid_types = ["feature", "fix", "docs", "refactor", "test", "chore"]
        assert pr_metadata["type"] in valid_types

        # Validate closes_issues is list of integers
        assert isinstance(pr_metadata["closes_issues"], list)
        for issue_num in pr_metadata["closes_issues"]:
            assert isinstance(issue_num, int)
            assert issue_num >= 1

    def test_business_logic_validation_invalid_type(self):
        """Test business logic validation with invalid type."""
        pr_metadata = {"type": "invalid_type", "closes_issues": [150], "breaking_change": False}

        valid_types = ["feature", "fix", "docs", "refactor", "test", "chore"]
        assert pr_metadata["type"] not in valid_types

    def test_business_logic_validation_invalid_issue_numbers(self):
        """Test business logic validation with invalid issue numbers."""
        pr_metadata = {
            "type": "feature",
            "closes_issues": [0, -1, "invalid"],
            "breaking_change": False,
        }

        invalid_issues = []
        for issue_num in pr_metadata["closes_issues"]:
            if not isinstance(issue_num, int) or issue_num < 1:
                invalid_issues.append(issue_num)

        assert len(invalid_issues) == 3  # All three are invalid

    @patch("builtins.open", new_callable=mock_open)
    def test_file_operations_write_yaml(self, mock_file, sample_valid_metadata):
        """Test writing YAML metadata to file."""
        yaml_content = yaml.dump(sample_valid_metadata, default_flow_style=False)

        # Simulate writing to file (as done in workflow)
        with open("pr_metadata.yaml", "w") as f:
            f.write(yaml_content)

        mock_file.assert_called_once_with("pr_metadata.yaml", "w")
        mock_file().write.assert_called_once_with(yaml_content)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="pr_metadata:\n  type: feature\n  closes_issues: [150]\n  breaking_change: false",
    )
    def test_file_operations_read_yaml(self, mock_file):
        """Test reading YAML metadata from file."""
        with open("pr_metadata.yaml", "r") as f:
            content = f.read()
            metadata = yaml.safe_load(content)

        mock_file.assert_called_once_with("pr_metadata.yaml", "r")
        assert metadata["pr_metadata"]["type"] == "feature"
        assert metadata["pr_metadata"]["closes_issues"] == [150]
        assert metadata["pr_metadata"]["breaking_change"] is False

    def test_error_handling_empty_yaml_content(self):
        """Test error handling for empty YAML content."""
        empty_yaml = ""

        result = yaml.safe_load(empty_yaml)
        assert result is None

    def test_error_handling_malformed_yaml(self):
        """Test error handling for malformed YAML."""
        malformed_yaml = """
pr_metadata:
  type: "feature"
  closes_issues: [150
    priority: "high"
  # Indentation error and missing bracket
"""

        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(malformed_yaml)

    def test_error_handling_yaml_with_special_characters(self):
        """Test YAML parsing with special characters that cause shell issues."""
        yaml_with_special_chars = """pr_metadata:
  type: "feature"
  closes_issues: [150]
  breaking_change: false
  description: "Test with $special &chars <and> quotes and apostrophes and backticks"
"""

        # Should parse without issues (this is what we're fixing with structured parsing)
        metadata = yaml.safe_load(yaml_with_special_chars)
        assert (
            metadata["pr_metadata"]["description"]
            == "Test with $special &chars <and> quotes and apostrophes and backticks"
        )

    def test_integration_full_validation_pipeline(self, sample_pr_body_with_yaml, pr_schema):
        """Test the complete validation pipeline as used in workflow."""
        import re

        # Step 1: Extract YAML frontmatter
        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", sample_pr_body_with_yaml)
        assert yaml_match is not None

        yaml_content = yaml_match.group(1)

        # Step 2: Parse YAML
        metadata = yaml.safe_load(yaml_content)
        assert metadata is not None

        # Step 3: Schema validation
        jsonschema.validate(metadata, pr_schema)

        # Step 4: Business logic validation
        pr_metadata = metadata["pr_metadata"]

        # Check required fields
        required_fields = ["type", "closes_issues", "breaking_change"]
        for field in required_fields:
            assert field in pr_metadata

        # Validate type
        valid_types = ["feature", "fix", "docs", "refactor", "test", "chore"]
        assert pr_metadata["type"] in valid_types

        # Validate closes_issues
        assert isinstance(pr_metadata["closes_issues"], list)
        for issue_num in pr_metadata["closes_issues"]:
            assert isinstance(issue_num, int) and issue_num >= 1

        # Step 5: Extract metadata for workflow use
        pr_type = pr_metadata["type"]
        closes_issues = pr_metadata["closes_issues"]
        breaking_change = pr_metadata.get("breaking_change", False)
        priority = pr_metadata.get("priority", "medium")
        auto_merge = pr_metadata.get("automation_flags", {}).get("auto_merge", False)

        assert pr_type == "feature"
        assert closes_issues == [150, 200]
        assert breaking_change is False
        assert priority == "high"
        assert auto_merge is True

    def test_integration_fallback_to_legacy_parsing(self, sample_pr_body_without_yaml):
        """Test fallback to legacy text parsing when YAML is missing."""
        import re

        # Step 1: Try to extract YAML frontmatter
        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", sample_pr_body_without_yaml)
        assert yaml_match is None

        # Step 2: Fallback to legacy text parsing
        combined_text = sample_pr_body_without_yaml
        issue_nums_match = re.findall(
            r"(?:closes?|fixes?|resolves?|implements?)\s+#(\d+)", combined_text, re.IGNORECASE
        )

        assert len(issue_nums_match) == 1
        assert issue_nums_match[0] == "150"

    def test_performance_large_yaml_content(self):
        """Test performance with large YAML content."""
        # Create large metadata structure
        large_metadata = {
            "pr_metadata": {
                "type": "feature",
                "closes_issues": list(range(1, 101)),  # 100 issues
                "breaking_change": False,
                "affects_components": [f"component_{i}" for i in range(50)],  # 50 components
                "description": "x" * 10000,  # Large description
                "test_coverage": {
                    "added": True,
                    "percentage": 85.5,
                    "requirements_met": True,
                    "details": {f"file_{i}": f"coverage_{i}" for i in range(100)},  # 100 files
                },
            }
        }

        # Should handle large content efficiently
        yaml_content = yaml.dump(large_metadata, default_flow_style=False)
        parsed = yaml.safe_load(yaml_content)

        assert parsed == large_metadata
        assert len(parsed["pr_metadata"]["closes_issues"]) == 100
        assert len(parsed["pr_metadata"]["affects_components"]) == 50

    def test_edge_case_arc_reviewer_content_before_yaml(self):
        """Test handling YAML when ARC-Reviewer adds content before it."""
        pr_body_with_prefix = """## 🤖 ARC-Reviewer Report

![Coverage](https://img.shields.io/badge/coverage-78.7%25-yellow)

---
pr_metadata:
  type: "feature"
  closes_issues: [150]
  breaking_change: false
---

# Pull Request Description

Closes #150
"""

        # The regex should still find YAML even with content before it
        import re

        yaml_match = re.search(r"---\s*\n([\s\S]*?)\n---", pr_body_with_prefix)

        assert yaml_match is not None
        yaml_content = yaml_match.group(1)
        metadata = yaml.safe_load(yaml_content)

        assert metadata["pr_metadata"]["type"] == "feature"
        assert metadata["pr_metadata"]["closes_issues"] == [150]
