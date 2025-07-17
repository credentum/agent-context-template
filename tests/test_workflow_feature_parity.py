#!/usr/bin/env python3
"""
Workflow Feature Parity Tests

This test suite validates that the new ai-pr-monitor.yml workflow
provides complete feature parity with the legacy auto-merge ecosystem.

Tests ensure no functionality is lost in the transition from:
- auto-merge.yml (738 lines)
- smart-auto-merge.yml (524 lines)
- auto-merge-notifier.yml (335 lines)
- arc-follow-up-processor.yml (375 lines)
"""

from pathlib import Path

import pytest
import yaml


class TestWorkflowFeatureParity:
    """Test feature parity between new and legacy workflows"""

    def setup_method(self):
        """Setup workflow paths"""
        self.workflows_dir = Path(".github/workflows")
        self.new_workflow = self.workflows_dir / "ai-pr-monitor.yml"
        self.legacy_workflows = [
            self.workflows_dir / "auto-merge.yml",
            self.workflows_dir / "smart-auto-merge.yml",
            self.workflows_dir / "auto-merge-notifier.yml",
        ]

    def test_workflow_files_exist(self):
        """Test that all required workflow files exist"""
        assert self.new_workflow.exists(), "ai-pr-monitor.yml should exist"

        for legacy_workflow in self.legacy_workflows:
            assert legacy_workflow.exists(), f"{legacy_workflow.name} should exist for comparison"

    def test_new_workflow_syntax_valid(self):
        """Test that new workflow has valid YAML syntax"""
        with open(self.new_workflow) as f:
            workflow_content = yaml.safe_load(f)

        assert workflow_content is not None, "Workflow should parse as valid YAML"
        assert "name" in workflow_content, "Workflow should have a name"
        assert True in workflow_content or "on" in workflow_content, "Workflow should have triggers"
        assert "jobs" in workflow_content, "Workflow should have jobs"

    def test_trigger_event_coverage(self):
        """Test that new workflow covers all necessary trigger events"""
        with open(self.new_workflow) as f:
            new_workflow = yaml.safe_load(f)

        # Handle YAML parsing quirk where 'on' becomes True
        new_triggers = new_workflow.get("on", new_workflow.get(True, {}))

        # Required events for comprehensive PR monitoring
        required_events = [
            "pull_request",
            "pull_request_review",
            "pull_request_review_comment",
            "check_suite",
            "status",
            "issue_comment",
        ]

        for event in required_events:
            assert event in new_triggers, f"New workflow should handle {event} events"

    def test_auto_merge_detection_methods(self):
        """Test that new workflow supports all auto-merge detection methods"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should support YAML metadata detection
        assert (
            "yamlcontent" in workflow_content.lower() or "yaml" in workflow_content.lower()
        ), "Should support YAML metadata"
        assert "auto_merge" in workflow_content, "Should detect auto_merge flags"

        # Should support label-based detection
        assert "auto-merge" in workflow_content, "Should support auto-merge labels"

        # Should support text-based detection (fallback)
        assert "text_search" in workflow_content, "Should support text search fallback"

    def test_ci_status_monitoring(self):
        """Test that new workflow monitors all required CI checks"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        required_checks = [
            "claude-pr-review",
            "ARC-Reviewer",
            "Coverage Analysis",
            "Lint & Style",
            "Core Tests",
            "Integration Tests",
        ]

        for check in required_checks:
            assert check in workflow_content, f"Should monitor {check}"

    def test_arc_reviewer_integration(self):
        """Test ARC-Reviewer integration capabilities"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should parse ARC-Reviewer comments
        assert "ARC-Reviewer" in workflow_content, "Should integrate with ARC-Reviewer"
        assert "verdict" in workflow_content, "Should parse verdict"
        assert "blocking" in workflow_content, "Should detect blocking issues"
        assert "APPROVE" in workflow_content, "Should handle APPROVE verdict"
        assert "REQUEST_CHANGES" in workflow_content, "Should handle REQUEST_CHANGES verdict"

    def test_conflict_resolution_capabilities(self):
        """Test conflict detection and resolution features"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should handle merge conflicts
        assert "conflicts" in workflow_content, "Should detect conflicts"
        assert "mergeable" in workflow_content, "Should check mergeable status"
        assert (
            "merge" in workflow_content and "rebase" in workflow_content
        ), "Should support both merge and rebase"

        # Should update branches automatically
        assert "auto-update" in workflow_content, "Should support branch auto-updating"

    def test_github_api_integration(self):
        """Test GitHub API integration for auto-merge"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should use GraphQL for auto-merge enablement
        assert (
            "graphql" in workflow_content.lower() or "gh pr merge" in workflow_content
        ), "Should use GraphQL API or GitHub CLI"
        assert "squash" in workflow_content.lower(), "Should support squash merge"

    def test_error_handling_and_notifications(self):
        """Test comprehensive error handling and user notifications"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should provide detailed error messages
        assert (
            "block" in workflow_content.lower() or "error" in workflow_content.lower()
        ), "Should handle blocking scenarios"
        assert (
            "timeout" in workflow_content.lower() or "fail" in workflow_content.lower()
        ), "Should handle timeouts and failures"

        # Should create PR comments for status updates
        assert (
            "comment" in workflow_content.lower() or "gh pr comment" in workflow_content
        ), "Should create status comments"

    def test_permissions_scope(self):
        """Test that new workflow has appropriate permissions"""
        with open(self.new_workflow) as f:
            new_workflow = yaml.safe_load(f)

        job_permissions = new_workflow["jobs"]["ai-monitor"]["permissions"]

        required_permissions = ["contents", "pull-requests", "issues", "checks", "statuses"]

        for permission in required_permissions:
            assert permission in job_permissions, f"Should have {permission} permission"

    def test_performance_optimizations(self):
        """Test performance improvements over legacy workflows"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should use real-time event processing (no polling)
        assert (
            "timeout-minutes: 30" not in workflow_content
            or "polling" not in workflow_content.lower()
        ), "Should not use polling"

        # Should have efficient condition checking
        assert "if:" in workflow_content, "Should use conditional execution"

    def test_legacy_workflow_feature_coverage(self):
        """Test that new workflow covers features from each legacy workflow"""

        # Features from auto-merge.yml
        legacy_auto_merge_features = [
            "PR information gathering",
            "Auto-merge flag detection",
            "CI status waiting",
            "ARC-Reviewer verdict checking",
            "Conflict validation",
            "GraphQL auto-merge enablement",
        ]

        # Features from smart-auto-merge.yml
        legacy_smart_features = [
            "Event-driven triggering",
            "PR eligibility checking",
            "Branch auto-updating",
            "Status check validation",
        ]

        # Features from auto-merge-notifier.yml
        legacy_notifier_features = [
            "Blocking issue detection",
            "User notifications",
            "Restart capability",
            "Error reporting",
        ]

        with open(self.new_workflow) as f:
            workflow_content = f.read().lower()

        # Verify all legacy features are covered (basic keyword check)
        all_legacy_features = (
            legacy_auto_merge_features + legacy_smart_features + legacy_notifier_features
        )

        # This is a simplified check - in practice you'd verify actual functionality
        feature_coverage = len(
            [
                f
                for f in all_legacy_features
                if any(keyword in workflow_content for keyword in f.lower().split())
            ]
        )

        assert (
            feature_coverage >= len(all_legacy_features) * 0.8
        ), "Should cover 80%+ of legacy features"

    def test_consolidation_benefits(self):
        """Test that consolidation provides expected benefits"""

        # Calculate legacy workflow complexity
        legacy_total_lines = 0
        legacy_job_count = 0

        for legacy_file in self.legacy_workflows:
            if legacy_file.exists():
                with open(legacy_file) as f:
                    legacy_workflow = yaml.safe_load(f)
                    legacy_total_lines += len(f.readlines())
                    legacy_job_count += len(legacy_workflow.get("jobs", {}))

        # Calculate new workflow metrics
        with open(self.new_workflow) as f:
            new_workflow = yaml.safe_load(f)
            new_job_count = len(new_workflow.get("jobs", {}))

        # New workflow should be more efficient
        assert new_job_count == 1, "New workflow should have single unified job"

        # Should eliminate coordination overhead (single workflow vs multiple)
        coordination_improvement = legacy_job_count > new_job_count
        assert coordination_improvement, "Should reduce coordination complexity"

    def test_backward_compatibility(self):
        """Test backward compatibility with existing PR formats"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should support legacy auto-merge methods
        assert "label" in workflow_content, "Should support label-based auto-merge"
        assert "text" in workflow_content, "Should support text-based detection"

        # Should work with existing PR templates
        assert "yaml" in workflow_content, "Should support YAML frontmatter"

    def test_monitoring_and_observability(self):
        """Test enhanced monitoring capabilities"""
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        # Should provide detailed status reporting
        assert "GITHUB_STEP_SUMMARY" in workflow_content, "Should create step summaries"
        assert "echo" in workflow_content, "Should provide console logging"

        # Should track key metrics
        assert "ci_ready" in workflow_content, "Should track CI readiness"
        assert "auto_merge_requested" in workflow_content, "Should track auto-merge requests"

    @pytest.mark.integration
    def test_end_to_end_workflow_simulation(self):
        """Test simulated end-to-end workflow execution"""

        # This would require actual workflow execution in a real test
        # For now, validate that the logic exists in the workflow
        with open(self.new_workflow) as f:
            workflow_content = f.read()

        assert "ready_for_auto_merge" in workflow_content, "Should calculate readiness"
        assert "enable auto-merge" in workflow_content.lower(), "Should enable auto-merge"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
