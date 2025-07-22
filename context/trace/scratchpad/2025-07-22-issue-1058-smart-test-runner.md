# Issue 1058: Smart Test Runner Implementation Plan

## Issue Link
https://github.com/agent-context-template/issues/1058

## Task Template
Reference: context/trace/task-templates/issue-1058-smart-test-runner.md

## Token Budget & Complexity
- Estimated tokens: 10k
- Complexity: Medium
- Files to create/modify: 4

## Implementation Plan

### Step 1: Create the main smart test runner script
- Create `scripts/claude-test-changed.sh`
- Implement git diff detection for changed files
- Add source-to-test file mapping logic
- Integrate pytest execution with targeted coverage
- Format output as structured JSON

### Step 2: Create test mapping utilities
- Create `scripts/test-mapping-utils.sh`
- Helper functions for complex mapping scenarios
- Handle edge cases (integration tests, multiple test files)

### Step 3: Test the script
- Create test script to validate functionality
- Test various scenarios (no changes, single file, multiple files)
- Verify JSON output format

### Step 4: Update documentation
- Update CLAUDE.md with usage instructions
- Add to Testing Workflow section
- Include examples of structured output

### Key Design Decisions:
1. Use git diff to detect changes (both staged and unstaged)
2. Support multiple test file patterns (test_module.py, module/test_*.py)
3. JSON output for easy parsing by Claude
4. Fallback to full test suite with --all flag
5. Include performance metrics in output

### Edge Cases to Handle:
- No changes detected
- New files without tests
- Deleted files
- Changes only in test files
- Integration tests that cover multiple modules

### Success Metrics:
- Execution time < 30 seconds for typical changes
- Accurate test file mapping
- Clear, parseable output
- Seamless integration with existing workflow
