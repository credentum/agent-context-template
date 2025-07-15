# Issue #34: MCP skeleton & contract JSON

**Issue Link:** https://github.com/user/repo/issues/34
**Sprint:** sprint-5
**Priority:** blocking
**Status:** In Progress

## Problem Description

Create MCP (Model Context Protocol) skeleton and contract JSON defining the interface for:
- `store_context` - Store context data in the system
- `retrieve_context` - Retrieve context data from the system
- `get_agent_state` - Get current agent state information

## Requirements Analysis

- **File Location:** Based on existing structure, should be `context/mcp_contracts/context_v0.json`
- **Schema:** JSON Schema draft-07 format
- **Validation:** Must pass `yamale` validation
- **Examples:** Include examples section for each tool/method
- **Contract Status:** Frozen for Sprint 5 (no breaking changes)

## Implementation Plan

### Task 1: Create JSON Schema Structure
- Define base JSON Schema draft-07 structure
- Include metadata (title, version, description)
- Set up methods/tools array structure

### Task 2: Define Method Schemas
- `store_context`: Define input parameters (key, value, metadata, ttl)
- `retrieve_context`: Define input parameters (key, query options) and response format
- `get_agent_state`: Define response format for agent state

### Task 3: Add Examples
- Provide concrete examples for each method showing:
  - Valid request/response formats
  - Common use cases
  - Error scenarios

### Task 4: Validation & Testing
- Ensure JSON Schema is valid draft-07
- Test with yamale validation if schema file is needed
- Verify contract meets acceptance criteria

### Task 5: Documentation
- Update any relevant documentation
- Consider if schema validation file is needed in `context/schemas/`

## Context Research

- Existing structure uses `context/mcp_contracts/` directory
- MCP is referenced in system architecture as "Model Context Protocol (MCP) for inter-agent communication"
- Tests expect this directory to exist
- No existing contracts found in the directory (empty)

## Acceptance Criteria Checklist

- [ ] Contract file created at correct location
- [ ] Uses JSON Schema draft-07 format
- [ ] Covers all three required methods
- [ ] Includes examples section for each tool
- [ ] Passes yamale validation
- [ ] Contract frozen for Sprint 5

## Dependencies

None identified - this is a foundational task that enables other MCP work.

## Notes

- Path clarification needed: Issue mentions `mcp/contracts/context_v0.json` but existing structure suggests `context/mcp_contracts/context_v0.json`
- Will proceed with existing structure pattern for consistency
- This contract will enable implementation of actual MCP server in subsequent issues
