# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1058-smart-test-runner
# Generated from GitHub Issue #1058
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1058-smart-test-runner`

## 🎯 Goal (≤ 2 lines)
> Create a smart test runner script that detects changed files and runs only relevant tests with coverage,
> providing faster feedback for Claude Code CLI when making code modifications.

## 🧠 Context
- **GitHub Issue**: #1058 - Smart Test Runner for Claude Code CLI
- **Sprint**: Not specified in labels
- **Phase**: Not specified in labels
- **Component**: ci, testing
- **Priority**: High (affects development velocity)
- **Why this matters**: Current full test suite runs take 3-5 minutes; smart runner will reduce to 10-30 seconds
- **Dependencies**: Git for change detection, pytest for test execution
- **Related**: #1057 (Auto-Format After Claude Edits)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-test-changed.sh | create | Script generation | Main smart test runner script | Low |
| scripts/test-mapping-utils.sh | create | Helper functions | Utilities for mapping source to test files | Low |
| CLAUDE.md | modify | Documentation update | Add smart test runner to workflow | Low |
| tests/scripts/test_claude_test_changed.sh | create | Test creation | Validate script functionality | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer creating a smart test runner for efficient CI/CD workflows.

**Context**
GitHub Issue #1058: Smart Test Runner for Claude Code CLI
- Current behavior: Full test suite runs take 3-5 minutes after each change
- Desired: Run only tests relevant to changed files (10-30 seconds)
- Current test structure: Well-organized with clear module-to-test mapping
- Tests use pytest with markers for categorization
- Related files: pytest.ini, pyproject.toml define test configuration

**Instructions**
1. **Primary Objective**: Create scripts/claude-test-changed.sh that detects changed files and runs relevant tests
2. **Scope**:
   - Detect changed files using git diff
   - Map source files to test files (handle multiple patterns)
   - Run pytest with coverage for affected modules only
   - Provide structured JSON output for Claude parsing
   - Support --all flag for full test suite
3. **Constraints**:
   - Follow existing bash script patterns in scripts/
   - Maintain compatibility with current pytest configuration
   - Ensure script works with both staged and unstaged changes
   - Handle edge cases (new files, deleted files, no changes)
4. **Prompt Technique**: Script generation with structured output
5. **Testing**: Create test script to validate functionality
6. **Documentation**: Update CLAUDE.md with usage instructions

**Technical Constraints**
• Expected diff ≤ 300 LoC, ≤ 4 files
• Context budget: ≤ 10k tokens
• Performance budget: Script execution < 5 seconds overhead
• Code quality: Shellcheck compliant, error handling
• CI compliance: Must integrate with existing CI pipeline

**Output Format**
Create complete bash script with:
- Change detection logic
- File mapping algorithm
- Pytest execution with coverage
- JSON output formatting
- Error handling and fallbacks

## 🔍 Verification & Testing
- `shellcheck scripts/claude-test-changed.sh` (bash syntax validation)
- `./scripts/claude-test-changed.sh --dry-run` (test mapping logic)
- `./scripts/claude-test-changed.sh` (run on actual changes)
- **Script-specific tests**:
  - Test with no changes
  - Test with single file change
  - Test with multiple file changes
  - Test with new/deleted files
- **Integration tests**: Verify JSON output parsing

## ✅ Acceptance Criteria
- Script detects which files Claude has modified
- Automatically maps source files to their test files
- Runs only relevant tests with coverage
- Provides structured output Claude can parse
- Falls back to full test suite when needed
- Integrates seamlessly with Claude's workflow

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 10k
├── time_budget: 1-2 hours
├── cost_estimate: $0.50
├── complexity: Medium
└── files_affected: 4

Actuals (to be filled):
├── tokens_used: ~8k
├── time_taken: 45 minutes
├── cost_actual: ~$0.40
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1058
sprint: null
phase: null
component: [ci, testing]
priority: high
complexity: medium
dependencies: [git, pytest, bash]
```
