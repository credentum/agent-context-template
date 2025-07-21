---
schema_version: 1.0
---

# Scratchpad: Issue 1057 - Auto-Format After Claude Edits
Date: 2025-07-21
Issue: https://github.com/credentum/agent-context-template/issues/1057

## Task Reference
Template: context/trace/task-templates/issue-1057-auto-format-after-claude-edits.md

## Token Budget & Complexity
- Estimated tokens: 5,000
- Complexity: Medium
- Time estimate: 2 hours

## Implementation Plan

### Step 1: Create validate-file-format.sh
- Single-file validation script
- Accepts file path as argument
- Runs appropriate formatters based on file type
- Returns structured output for Claude

### Step 2: Create claude-post-edit.sh
- Main orchestrator script
- Detects file type and calls validate-file-format.sh
- Handles multiple files if needed
- Provides summary output

### Step 3: Create hook integration
- Create .claude/hooks/post-edit.sh
- Integrates with Claude's workflow
- Can be sourced or called directly

### Step 4: Update CLAUDE.md
- Add section on auto-formatting workflow
- Document how to use the scripts
- Provide examples of output format

### Step 5: Create test files
- Python file with formatting issues
- Test the complete workflow
- Verify output format is parseable

## Technical Decisions
1. Use existing pre-commit infrastructure (Black, isort, flake8)
2. Structured output format for Claude parsing
3. Performance target: < 2 seconds per file
4. Support both validation and auto-fix modes

## Files to Create/Modify
1. scripts/validate-file-format.sh (new)
2. scripts/claude-post-edit.sh (new)
3. .claude/hooks/post-edit.sh (new)
4. CLAUDE.md (modify)
5. tests/test_formatting_issues.py (new - for testing)

## Current Status
- [x] Issue analyzed
- [x] Context gathered
- [x] Task template created
- [x] Execution plan created
- [ ] Implementation started
- [ ] Testing completed
- [ ] PR created

## Notes
- Investigation issue shows clear need for immediate feedback
- Existing infrastructure can be leveraged
- Focus on Python files initially (most common use case)
