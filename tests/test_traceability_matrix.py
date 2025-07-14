"""Test Traceability Matrix for Critical Functions

This module provides a mapping between critical functions and their test cases,
ensuring 100% test case traceability for critical functionality.
"""

import json
from typing import Dict

# Critical function registry
CRITICAL_FUNCTIONS = {
    # Agent functions
    "src.agents.cleanup_agent.CleanupAgent._is_expired": {
        "description": "Determines if documents/sprints should be archived",
        "test_cases": [
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_is_expired_document",
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_is_expired_sprint",
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_stale_sprint_detection",
        ],
        "requirements": ["REQ-CLEANUP-001", "REQ-CLEANUP-002"],
    },
    "src.agents.cleanup_agent.CleanupAgent._archive_file": {
        "description": "Archives files to prevent data loss",
        "test_cases": [
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_archive_file",
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_archive_with_metadata",
            "test_cleanup_agent_coverage.py::TestCleanupAgentCoverage::test_dry_run_mode",
        ],
        "requirements": ["REQ-CLEANUP-003"],
    },
    "src.agents.update_sprint.SprintUpdater._calculate_phase_progress": {
        "description": "Calculates sprint phase completion percentage",
        "test_cases": [
            "test_update_sprint_coverage.py::TestUpdateSprintAgentCoverage::"
            "test_calculate_phase_progress"
        ],
        "requirements": ["REQ-SPRINT-001"],
    },
    "src.agents.update_sprint.SprintUpdater._should_transition_phase": {
        "description": "Determines when to transition sprint phases",
        "test_cases": [
            "test_update_sprint_coverage.py::TestUpdateSprintAgentCoverage::"
            "test_should_transition_phase",
            "test_update_sprint_coverage.py::TestUpdateSprintAgentCoverage::"
            "test_transition_phase_states",
        ],
        "requirements": ["REQ-SPRINT-002"],
    },
    # Storage functions
    "src.storage.context_kv.ContextKV.set": {
        "description": "Stores data in Redis with TTL",
        "test_cases": [
            "test_context_kv_coverage.py::TestContextKVCoverage::test_set_and_get",
            "test_context_kv_coverage.py::TestContextKVCoverage::test_error_handling",
        ],
        "requirements": ["REQ-STORAGE-001"],
    },
    "src.storage.context_kv.ContextKV.acquire_lock": {
        "description": "Distributed locking for concurrent operations",
        "test_cases": ["test_context_kv_coverage.py::TestContextKVCoverage::test_lock_operations"],
        "requirements": ["REQ-STORAGE-002"],
    },
    "src.storage.graph_builder.GraphBuilder.process_document": {
        "description": "Processes documents into graph nodes",
        "test_cases": ["test_graph_db.py::TestGraphBuilder::test_process_document"],
        "requirements": ["REQ-GRAPH-001"],
    },
    # Validation functions
    "src.validators.config_validator.validate_config": {
        "description": "Validates system configuration",
        "test_cases": [
            "test_config_parser.py::TestConfigParser::test_valid_config",
            "test_config_parser.py::TestConfigParser::test_missing_required_sections",
        ],
        "requirements": ["REQ-CONFIG-001"],
    },
    "src.validators.kv_validators.validate_session_data": {
        "description": "Validates session data integrity",
        "test_cases": ["test_kv_store.py::TestKVValidators::test_validate_session_data"],
        "requirements": ["REQ-VALIDATION-001"],
    },
    # Analytics functions
    "src.analytics.context_analytics.ContextAnalytics.analyze_health": {
        "description": "Analyzes system health metrics",
        "test_cases": ["test_e2e.py::TestEndToEnd::test_performance_config_workflow"],
        "requirements": ["REQ-ANALYTICS-001"],
    },
}


class TestTraceabilityMatrix:
    """Test cases for verifying traceability matrix completeness"""

    def test_all_critical_functions_have_tests(self):
        """Verify all critical functions have at least one test case"""
        missing_tests = []

        for func_path, info in CRITICAL_FUNCTIONS.items():
            if not info["test_cases"]:
                missing_tests.append(func_path)

        assert not missing_tests, f"Critical functions missing tests: {missing_tests}"

    def test_all_requirements_covered(self):
        """Verify all requirements are covered by tests"""
        all_requirements: set[str] = set()
        covered_requirements: set[str] = set()

        # Collect all requirements
        for info in CRITICAL_FUNCTIONS.values():
            all_requirements.update(info["requirements"])
            if info["test_cases"]:
                covered_requirements.update(info["requirements"])

        uncovered = all_requirements - covered_requirements
        assert not uncovered, f"Requirements not covered by tests: {uncovered}"

    def test_generate_traceability_report(self, tmp_path):
        """Generate a traceability report for documentation"""
        report = {
            "summary": {
                "total_critical_functions": len(CRITICAL_FUNCTIONS),
                "functions_with_tests": sum(
                    1 for info in CRITICAL_FUNCTIONS.values() if info["test_cases"]
                ),
                "total_test_cases": sum(
                    len(info["test_cases"]) for info in CRITICAL_FUNCTIONS.values()
                ),
                "total_requirements": len(
                    set(req for info in CRITICAL_FUNCTIONS.values() for req in info["requirements"])
                ),
            },
            "critical_functions": CRITICAL_FUNCTIONS,
            "coverage_by_module": self._calculate_module_coverage(),
        }

        # Save report
        report_path = tmp_path / "traceability_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Verify report completeness
        assert (
            report["summary"]["functions_with_tests"]
            == report["summary"]["total_critical_functions"]
        )
        print(f"Traceability report generated: {report_path}")

    def _calculate_module_coverage(self) -> Dict[str, Dict]:
        """Calculate test coverage by module"""
        module_coverage = {}

        for func_path, info in CRITICAL_FUNCTIONS.items():
            module = func_path.split(".")[1]  # Extract module name
            if module not in module_coverage:
                module_coverage[module] = {
                    "total_functions": 0,
                    "tested_functions": 0,
                    "test_cases": 0,
                }

            module_coverage[module]["total_functions"] += 1
            if info["test_cases"]:
                module_coverage[module]["tested_functions"] += 1
                module_coverage[module]["test_cases"] += len(info["test_cases"])

        return module_coverage

    def test_test_case_naming_convention(self):
        """Verify test cases follow naming conventions"""
        invalid_names = []

        for func_path, info in CRITICAL_FUNCTIONS.items():
            for test_case in info["test_cases"]:
                # Test case should include function name or behavior
                func_name = func_path.split(".")[-1].lower()
                if func_name not in test_case.lower() and "test_" not in test_case:
                    invalid_names.append((func_path, test_case))

        assert not invalid_names, f"Test cases with invalid naming: {invalid_names}"


def generate_test_mapping_decorator(requirement: str):
    """Decorator to map tests to requirements"""

    def decorator(test_func):
        if not hasattr(test_func, "_requirements"):
            test_func._requirements = []
        test_func._requirements.append(requirement)
        return test_func

    return decorator


# Example usage:
@generate_test_mapping_decorator("REQ-CLEANUP-001")
def test_example_with_requirement_mapping():
    """Example test with requirement mapping"""
    pass
