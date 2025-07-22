# Issue #1130 Execution Plan - ARC-Reviewer Logic Extraction

**Issue Link**: https://github.com/credentum/agent-context-template/issues/1130
**Sprint**: Current development sprint
**Task Template**: context/trace/task-templates/issue-1130-extract-arc-reviewer-logic.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 12,000 (based on 838-line workflow analysis)
- **Estimated time**: 45 minutes
- **Complexity**: Medium (extraction and refactoring)
- **Files to modify**: 4 (workflow, new module, tests, possibly config)

## Step-by-Step Implementation Plan

### Phase 1: Analysis and Extraction
1. **Deep analysis of workflow file** (Lines 70-137: direct_prompt section)
   - Extract review criteria logic
   - Identify coverage checking mechanism
   - Document YAML output structure
   - Note allowed tools and permissions

2. **Identify key components to extract**:
   - Review criteria validation
   - Coverage threshold checking using .coverage-config.json
   - YAML output generation
   - Issue categorization logic

### Phase 2: Module Creation
3. **Create src/agents/arc_reviewer.py**:
   - Class-based design following existing agent patterns
   - Methods for each review criterion
   - Coverage calculation matching CI environment
   - YAML output generation

4. **Implement core functionality**:
   - `ARCReviewer` class with `review_pr()` method
   - Coverage checking using .coverage-config.json
   - Issue detection and categorization
   - Structured YAML output matching workflow format

### Phase 3: Testing and Integration
5. **Create comprehensive tests**:
   - Unit tests for each review criterion
   - Coverage calculation verification
   - YAML output format validation
   - Mock PR environment testing

6. **Update GitHub Actions workflow**:
   - Replace embedded logic with Python module call
   - Ensure identical behavior and output
   - Maintain all current functionality

### Phase 4: Validation
7. **Verify local execution capability**:
   - Test module can run outside GitHub Actions
   - Validate coverage calculations match CI
   - Confirm YAML output is identical

## Context Management Strategy
- Use task template for prompt technique guidance
- Monitor token usage during workflow analysis
- Use `/clear` if context approaches 20k tokens
- Reference scratchpad for implementation decisions

## Success Metrics
- [ ] Module extracts cleanly from workflow
- [ ] All tests pass with ≥78% coverage maintained
- [ ] Local execution works identically to GitHub Actions
- [ ] Workflow integration preserves existing behavior
- [ ] CI checks pass completely

**Start Time**: $(date)
**Status**: Planning complete, ready for implementation
