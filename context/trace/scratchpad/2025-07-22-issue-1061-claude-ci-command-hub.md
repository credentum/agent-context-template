# Execution Plan: Issue #1061 - Claude CI Command Hub

## Issue Reference
- **GitHub Issue**: [#1061](https://github.com/droter/agent-context-template/issues/1061)
- **Sprint Reference**: Not specified
- **Task Template**: `context/trace/task-templates/issue-1061-claude-ci-command-hub.md`

## Analysis Summary
The issue requests creation of a unified `scripts/claude-ci.sh` command that consolidates multiple existing CI scripts into a single interface. Analysis shows:

**Existing Scripts (implemented)**:
- `claude-pre-commit.sh` - Pre-commit validation with JSON output
- `claude-test-changed.sh` - Smart test runner for changed files
- `claude-post-edit.sh` - Post-edit validation and formatting

**Missing**: Unified interface to bring these together under consistent command structure.

## Token Budget & Complexity
- **Estimated tokens**: 8,000 (low complexity wrapper)
- **Estimated time**: 45 minutes
- **Complexity**: Low - primarily wrapper around existing tools
- **Files affected**: 2 (new script + documentation update)

## Implementation Plan

### Phase 1: Create `scripts/claude-ci.sh`
1. **Command Structure**:
   ```bash
   claude-ci check <file>      # Validate single file (uses claude-post-edit.sh)
   claude-ci test             # Run smart tests (uses claude-test-changed.sh)
   claude-ci test --all       # Run full test suite
   claude-ci pre-commit       # Pre-commit checks (uses claude-pre-commit.sh)
   claude-ci pre-commit --fix # Auto-fix mode
   claude-ci review           # Local PR review simulation
   claude-ci all              # Complete CI pipeline
   claude-ci help             # Detailed help
   ```

2. **Implementation Details**:
   - Bash script with consistent error handling
   - JSON output format for all subcommands
   - Progressive validation modes (quick/standard/comprehensive)
   - Integration with existing scripts via delegation
   - Help system with examples

3. **Output Format**:
   ```json
   {
     "command": "check|test|pre-commit|review|all",
     "status": "PASSED|FAILED|SKIPPED",
     "target": "file/directory/all",
     "checks": {...},
     "errors": [...],
     "duration": "1.5s",
     "next_action": "..."
   }
   ```

### Phase 2: Update Documentation
1. **CLAUDE.md Updates**:
   - Add `claude-ci` to CLI cheat-sheet section
   - Update workflow recommendations to use unified command
   - Add examples for common use cases

### Phase 3: Testing Plan
1. **Manual Testing**:
   - Test each subcommand individually
   - Verify JSON output consistency
   - Test error handling and edge cases
   - Verify help system completeness

2. **Integration Testing**:
   - Test with existing CI pipeline
   - Verify backward compatibility maintained
   - Test progressive validation modes

## Success Criteria Validation
- [ ] Single entry point implemented
- [ ] Consistent command structure across all subcommands
- [ ] JSON output format standardized
- [ ] Help system comprehensive and useful
- [ ] Integration with existing tools working
- [ ] Documentation updated in CLAUDE.md

## Implementation Notes
- Leverage existing scripts rather than reimplementing functionality
- Maintain backward compatibility - existing scripts should continue to work
- Focus on consistency in interface and output format
- Provide clear error messages and guidance for next actions

## Risk Assessment
- **Low risk**: Wrapper around existing, working tools
- **Main risk**: Command parsing complexity - mitigate with thorough testing
- **Compatibility risk**: Minimal since delegating to existing scripts
