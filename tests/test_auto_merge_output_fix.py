#!/usr/bin/env python3
"""
Test for Auto-Merge Controller output format fix

This test verifies that the auto-merge workflow correctly handles
complex JSON objects and shell artifacts without corrupting
GitHub Actions output format.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestAutoMergeOutputFix:
    """Test auto-merge workflow output format fixes"""

    def test_complex_json_object_handling(self):
        """Test that complex JSON objects don't corrupt GitHub Actions output"""
        # Simulate the problematic auto_merge object from GitHub API
        complex_auto_merge_object = {
            "enabled_by": {
                "login": "github-actions[bot]",
                "id": 41898282,
                "node_id": "MDM6Qm90NDE4OTgyODI=",
                "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
                "type": "Bot",
            },
            "merge_method": "squash",
            "commit_title": None,
            "commit_message": None,
        }

        pr_info = {
            "number": 154,
            "head_sha": "4c33210a9d78091828ef8cb8176a966c9f476681",
            "base_ref": "main",
            "mergeable": True,
            "mergeable_state": "blocked",
            "auto_merge": complex_auto_merge_object,
            "title": "test PR",
            "body": "test body",
            "user": "testuser",
            "labels": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pr_info, f)
            temp_json_path = f.name

        try:
            # Test the old problematic approach - show it produces invalid output
            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'echo "auto_merge=$(cat {temp_json_path} | '
                    f"jq -r '.auto_merge')\" > /tmp/test_output_old",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            with open("/tmp/test_output_old", "r") as f:
                old_output = f.read().strip()

            # Verify the old output contains problematic characters
            assert "{" in old_output  # Contains JSON braces
            assert '"' in old_output  # Contains quotes
            assert "enabled_by" in old_output  # Contains complex object data

            # Test the new fixed approach (should work)
            subprocess.run(
                [
                    "bash",
                    "-c",
                    f'echo "github_auto_merge_enabled=$(cat {temp_json_path} | '
                    f"jq -r '.auto_merge != null')\" > /tmp/test_output_fixed",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Verify the output is clean and valid
            with open("/tmp/test_output_fixed", "r") as f:
                output = f.read().strip()

            assert output == "github_auto_merge_enabled=true"
            assert "{" not in output  # No JSON braces
            assert '"' not in output  # No quotes that could break GitHub Actions

        finally:
            Path(temp_json_path).unlink()
            Path("/tmp/test_output_old").unlink(missing_ok=True)
            Path("/tmp/test_output_fixed").unlink(missing_ok=True)

    def test_shell_artifact_cleaning(self):
        """Test that shell artifacts are properly cleaned from PR body"""
        problematic_pr_body = """---
# 🤖 Machine-Readable Metadata (required for automation)
pr_metadata:
  type: "feature"  # feature < /dev/null | fix|docs|refactor|test|chore
  closes_issues: [150]  # [123, 456] - list of issue numbers this PR closes
  automation_flags:
    auto_merge: true  # true to enable auto-merge when conditions are met
---

# Pull Request Description
This is a test PR.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(problematic_pr_body)
            temp_body_path = f.name

        try:
            # Test the cleaning process
            subprocess.run(
                [
                    "bash",
                    "-c",
                    f"cat {temp_body_path} | "
                    f"sed 's/< \\/dev\\/null |//g' > /tmp/cleaned_body.txt",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            with open("/tmp/cleaned_body.txt", "r") as f:
                cleaned_content = f.read()

            # Verify shell artifact was removed
            assert "< /dev/null |" not in cleaned_content
            assert "feature  fix|docs|refactor|test|chore" in cleaned_content
            assert "auto_merge: true" in cleaned_content

        finally:
            Path(temp_body_path).unlink()
            Path("/tmp/cleaned_body.txt").unlink(missing_ok=True)

    def test_yaml_parsing_after_cleaning(self):
        """Test that YAML parsing works correctly after shell artifact removal"""
        import yaml

        problematic_yaml = """pr_metadata:
  type: "feature"  # feature < /dev/null | fix|docs|refactor|test|chore
  closes_issues: [150]
  automation_flags:
    auto_merge: true"""

        # Clean the content
        cleaned_yaml = problematic_yaml.replace("< /dev/null |", "")

        # Verify it parses correctly
        data = yaml.safe_load(cleaned_yaml)

        assert data["pr_metadata"]["type"] == "feature"
        assert data["pr_metadata"]["closes_issues"] == [150]
        assert data["pr_metadata"]["automation_flags"]["auto_merge"] is True

    def test_github_actions_output_format_validation(self):
        """Test that our output format is valid for GitHub Actions"""
        # Valid GitHub Actions output format requirements:
        # - No newlines in values
        # - No special characters that need escaping
        # - Simple key=value format

        test_outputs = [
            "github_auto_merge_enabled=true",
            "github_auto_merge_enabled=false",
            "auto_merge_method=yaml_metadata",
            "auto_merge_method=label",
        ]

        for output in test_outputs:
            # Should not contain problematic characters
            assert "\n" not in output
            assert "{" not in output
            assert "}" not in output
            assert '"enabled_by"' not in output

            # Should be simple key=value format
            assert "=" in output
            key, value = output.split("=", 1)
            assert key.strip() == key  # No leading/trailing whitespace
            assert value.strip() == value  # No leading/trailing whitespace

    def test_boolean_extraction_logic(self):
        """Test the boolean extraction logic for auto_merge detection"""
        test_cases = [
            ({"auto_merge": None}, "false"),
            ({"auto_merge": {"enabled_by": "user"}}, "true"),
            ({}, "false"),  # Missing auto_merge field
        ]

        for pr_data, expected in test_cases:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(pr_data, f)
                temp_path = f.name

            try:
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        f"cat {temp_path} | jq -r '.auto_merge != null'",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                assert result.stdout.strip() == expected

            finally:
                Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
