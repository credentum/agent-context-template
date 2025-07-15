"""
Integration tests for MCP contract validation.

Tests the MCP contract JSON schema against expected usage patterns
and validates the contract structure for real-world MCP server integration.
"""

import json
from pathlib import Path
from typing import Any, Dict

import jsonschema
import pytest


class TestMCPContractValidation:
    """Test MCP contract validation and structure."""

    @pytest.fixture
    def contract_path(self) -> Path:
        """Path to the MCP contract file."""
        return Path(__file__).parent.parent / "context" / "mcp_contracts" / "context_v0.json"

    @pytest.fixture
    def contract_schema(self, contract_path: Path) -> Dict[str, Any]:
        """Load the MCP contract schema."""
        with open(contract_path, "r") as f:
            return json.load(f)

    def test_contract_file_exists(self, contract_path: Path):
        """Test that the MCP contract file exists."""
        assert contract_path.exists(), f"MCP contract not found at {contract_path}"

    def test_contract_is_valid_json(self, contract_path: Path):
        """Test that the contract is valid JSON."""
        with open(contract_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict), "Contract should be a JSON object"

    def test_contract_schema_compliance(self, contract_schema: Dict[str, Any]):
        """Test that the contract follows JSON Schema draft-07."""
        # Validate against JSON Schema meta-schema
        meta_schema = jsonschema.Draft7Validator.META_SCHEMA
        try:
            jsonschema.validate(contract_schema, meta_schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Contract schema validation failed: {e}")

    def test_required_metadata_fields(self, contract_schema: Dict[str, Any]):
        """Test that required metadata fields are present."""
        required_fields = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": str,
            "description": str,
            "schema_version": str,
            "version": str,
            "type": "object",
        }

        for field, expected_type in required_fields.items():
            assert field in contract_schema, f"Required field '{field}' missing"
            if isinstance(expected_type, str):
                assert (
                    contract_schema[field] == expected_type
                ), f"Field '{field}' should be '{expected_type}'"
            else:
                assert isinstance(
                    contract_schema[field], expected_type
                ), f"Field '{field}' should be type {expected_type}"

    def test_required_mcp_tools_defined(self, contract_schema: Dict[str, Any]):
        """Test that all required MCP tools are defined."""
        required_tools = {"store_context", "retrieve_context", "get_agent_state"}
        definitions = contract_schema.get("definitions", {})

        defined_tools = set(definitions.keys())
        missing_tools = required_tools - defined_tools

        assert not missing_tools, f"Missing required MCP tools: {missing_tools}"

    def test_tool_structure_compliance(self, contract_schema: Dict[str, Any]):
        """Test that each tool follows the expected structure."""
        definitions = contract_schema.get("definitions", {})

        for tool_name, tool_def in definitions.items():
            # Each tool should have required fields
            required_fields = {"name", "description", "inputSchema", "outputSchema"}
            tool_required = set(tool_def.get("required", []))

            assert required_fields.issubset(
                tool_required
            ), f"{tool_name} missing required fields in 'required' array"

            # Check properties exist
            properties = tool_def.get("properties", {})
            assert "name" in properties, f"{tool_name} missing 'name' property"
            assert "description" in properties, f"{tool_name} missing 'description' property"
            assert "inputSchema" in properties, f"{tool_name} missing 'inputSchema' property"
            assert "outputSchema" in tool_def, f"{tool_name} missing 'outputSchema' property"

    def test_input_schema_structure(self, contract_schema: Dict[str, Any]):
        """Test that input schemas are properly structured."""
        definitions = contract_schema.get("definitions", {})

        for tool_name, tool_def in definitions.items():
            input_schema = tool_def["properties"]["inputSchema"]

            assert input_schema["properties"]["type"]["const"] == "object"
            assert "properties" in input_schema["properties"]
            assert "required" in input_schema["properties"]

    def test_output_schema_structure(self, contract_schema: Dict[str, Any]):
        """Test that output schemas are properly structured."""
        definitions = contract_schema.get("definitions", {})

        for tool_name, tool_def in definitions.items():
            output_schema = tool_def["outputSchema"]

            assert output_schema["type"] == "object"
            assert "properties" in output_schema
            assert "description" in output_schema

    def test_store_context_specific_validation(self, contract_schema: Dict[str, Any]):
        """Test store_context specific schema requirements."""
        store_def = contract_schema["definitions"]["store_context"]
        output_schema = store_def["outputSchema"]

        # Check required response fields
        required_response_fields = {"success", "key"}
        properties = output_schema["properties"]

        for field in required_response_fields:
            assert field in properties, f"store_context output missing required field: {field}"

        # Validate success field is boolean
        assert properties["success"]["type"] == "boolean"
        assert properties["key"]["type"] == "string"

    def test_retrieve_context_specific_validation(self, contract_schema: Dict[str, Any]):
        """Test retrieve_context specific schema requirements."""
        retrieve_def = contract_schema["definitions"]["retrieve_context"]
        output_schema = retrieve_def["outputSchema"]

        properties = output_schema["properties"]

        # Should have results array
        assert "results" in properties
        assert properties["results"]["type"] == "array"

        # Should have metadata fields
        assert "total_found" in properties
        assert properties["total_found"]["type"] == "integer"

    def test_get_agent_state_specific_validation(self, contract_schema: Dict[str, Any]):
        """Test get_agent_state specific schema requirements."""
        agent_state_def = contract_schema["definitions"]["get_agent_state"]
        output_schema = agent_state_def["outputSchema"]

        properties = output_schema["properties"]
        required_fields = output_schema.get("required", [])

        # Check essential agent state fields
        essential_fields = {"agent_id", "status", "capabilities", "version"}
        for field in essential_fields:
            assert field in properties, f"get_agent_state output missing field: {field}"
            assert field in required_fields, f"get_agent_state field '{field}' should be required"

    def test_examples_coverage(self, contract_schema: Dict[str, Any]):
        """Test that examples are provided for all tools."""
        required_tools = {"store_context", "retrieve_context", "get_agent_state"}
        examples = contract_schema.get("examples", [])

        example_tools = {ex.get("tool") for ex in examples}
        missing_examples = required_tools - example_tools

        assert not missing_examples, f"Missing examples for tools: {missing_examples}"

    def test_examples_structure(self, contract_schema: Dict[str, Any]):
        """Test that examples follow the expected structure."""
        examples = contract_schema.get("examples", [])

        for example_group in examples:
            assert "tool" in example_group, "Example group missing 'tool' field"
            assert "description" in example_group, "Example group missing 'description' field"
            assert "examples" in example_group, "Example group missing 'examples' array"

            for example in example_group["examples"]:
                assert "name" in example, "Example missing 'name' field"
                assert "description" in example, "Example missing 'description' field"
                assert "input" in example, "Example missing 'input' field"

    def test_schema_versioning(self, contract_schema: Dict[str, Any]):
        """Test that schema versioning follows semantic versioning."""
        schema_version = contract_schema.get("schema_version")
        contract_version = contract_schema.get("version")

        assert schema_version is not None, "schema_version field is required"
        assert contract_version is not None, "version field is required"

        # Basic semantic versioning check (X.Y.Z format)
        version_parts = schema_version.split(".")
        assert (
            len(version_parts) == 3
        ), f"schema_version should be semantic version (X.Y.Z): {schema_version}"

        for part in version_parts:
            assert part.isdigit(), f"Version part should be numeric: {part}"

    @pytest.mark.parametrize("tool_name", ["store_context", "retrieve_context", "get_agent_state"])
    def test_tool_name_consistency(self, contract_schema: Dict[str, Any], tool_name: str):
        """Test that tool names are consistent between definition key and name property."""
        tool_def = contract_schema["definitions"][tool_name]
        name_const = tool_def["properties"]["name"]["const"]

        assert (
            name_const == tool_name
        ), f"Tool name mismatch: definition key '{tool_name}' vs name const '{name_const}'"

    def test_contract_ready_for_mcp_server_integration(self, contract_schema: Dict[str, Any]):
        """Test that the contract contains all elements needed for MCP server integration."""
        # Check for MCP-specific structure
        assert "tools" in contract_schema["properties"], "Contract should define 'tools' property"

        tools_property = contract_schema["properties"]["tools"]
        assert tools_property["type"] == "array", "Tools should be an array"
        assert "items" in tools_property, "Tools array should define item schema"

        # Check that tool references exist
        tool_items = tools_property["items"]["oneOf"]
        expected_refs = [
            "#/definitions/store_context",
            "#/definitions/retrieve_context",
            "#/definitions/get_agent_state",
        ]

        actual_refs = [item["$ref"] for item in tool_items]
        assert set(actual_refs) == set(
            expected_refs
        ), f"Tool references mismatch: {actual_refs} vs {expected_refs}"


class TestMCPContractExamples:
    """Test MCP contract examples for realistic usage patterns."""

    @pytest.fixture
    def contract_schema(self) -> Dict[str, Any]:
        """Load the MCP contract schema."""
        contract_path = (
            Path(__file__).parent.parent / "context" / "mcp_contracts" / "context_v0.json"
        )
        with open(contract_path, "r") as f:
            return json.load(f)

    def test_store_context_examples_realistic(self, contract_schema: Dict[str, Any]):
        """Test that store_context examples represent realistic usage."""
        examples = next(ex for ex in contract_schema["examples"] if ex["tool"] == "store_context")

        example_inputs = [ex["input"] for ex in examples["examples"]]

        # Should have variety of input types
        keys = [inp["key"] for inp in example_inputs]
        assert len(set(keys)) == len(keys), "Example keys should be unique"

        # Should demonstrate different value types
        value_types = set()
        for inp in example_inputs:
            value = inp["value"]
            if isinstance(value, str):
                value_types.add("string")
            elif isinstance(value, dict):
                value_types.add("object")
            elif isinstance(value, list):
                value_types.add("array")

        assert len(value_types) > 1, "Examples should demonstrate multiple value types"

    def test_retrieve_context_examples_realistic(self, contract_schema: Dict[str, Any]):
        """Test that retrieve_context examples represent realistic usage."""
        examples = next(
            ex for ex in contract_schema["examples"] if ex["tool"] == "retrieve_context"
        )

        # Should demonstrate both key-based and query-based retrieval
        input_methods = set()
        for example in examples["examples"]:
            inp = example["input"]
            if "key" in inp:
                input_methods.add("key_based")
            if "query" in inp:
                input_methods.add("query_based")

        assert "key_based" in input_methods, "Should demonstrate key-based retrieval"
        assert "query_based" in input_methods, "Should demonstrate query-based retrieval"

    def test_get_agent_state_examples_realistic(self, contract_schema: Dict[str, Any]):
        """Test that get_agent_state examples represent realistic usage."""
        examples = next(ex for ex in contract_schema["examples"] if ex["tool"] == "get_agent_state")

        # Should demonstrate different levels of detail
        detail_levels = set()
        for example in examples["examples"]:
            inp = example["input"]
            if not inp:  # Empty input = default behavior
                detail_levels.add("default")
            elif inp.get("include_metrics") is True:
                detail_levels.add("with_metrics")
            elif inp.get("include_session") is False:
                detail_levels.add("minimal")

        assert len(detail_levels) > 1, "Should demonstrate different detail levels"
