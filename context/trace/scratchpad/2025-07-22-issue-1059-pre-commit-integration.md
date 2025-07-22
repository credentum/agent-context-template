# Scratchpad: Issue #1059 - Pre-Commit Integration for Claude Code CLI

## Issue Link
https://github.com/[org]/[repo]/issues/1059

## Task Template
context/trace/task-templates/issue-1059-pre-commit-integration.md

## Token Budget
- Estimated: 15,000 tokens
- Complexity: Medium
- Files to create/modify: 5

## Implementation Plan

### Step 1: Analyze existing pre-commit configuration
- Review .pre-commit-config.yaml for all hooks
- Understand output format of each hook
- Identify which hooks support auto-fix

### Step 2: Create main wrapper script
- scripts/claude-pre-commit.sh
- Parse pre-commit output for each hook type
- Generate structured JSON output
- Support --fix mode

### Step 3: Create hook integration
- .claude/hooks/pre-commit.sh
- Similar pattern to post-edit.sh
- Provide helper functions for Claude

### Step 4: Create unit tests
- tests/test_claude_pre_commit.py
- Test parsing for each hook type
- Test auto-fix functionality
- Test error handling

### Step 5: Update documentation
- Update CLAUDE.md with usage instructions
- Document JSON output format
- Provide examples

### Step 6: Integrate with existing scripts
- Update validate-branch-for-pr.sh to use new wrapper
- Ensure backward compatibility

## Key Design Decisions

### Output Format
- JSON for easy parsing by Claude
- Include both summary and detailed information
- Provide actionable fix instructions

### Auto-Fix Strategy
- Only auto-fix safe operations (black, isort, trailing whitespace)
- Report what was changed
- Require explicit --fix flag

### Error Handling
- Graceful degradation if pre-commit not installed
- Clear error messages
- Preserve exit codes for CI

## Progress Tracking
- [ ] Created task template
- [ ] Created scratchpad
- [ ] Implementation started
- [ ] Tests written
- [ ] Documentation updated
- [ ] PR created
