# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1059-pre-commit-integration
# Generated from GitHub Issue #1059
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1059-pre-commit-integration`

## 🎯 Goal (≤ 2 lines)
> Create a Claude-friendly wrapper for pre-commit that provides structured, parseable output with clear failure reasons and actionable fix instructions.

## 🧠 Context
- **GitHub Issue**: #1059 - Pre-Commit Integration for Claude Code CLI
- **Sprint**: N/A
- **Phase**: N/A
- **Component**: ci
- **Priority**: High
- **Why this matters**: Claude often encounters cryptic pre-commit failures that require multiple attempts to fix
- **Dependencies**: Pre-commit configuration, existing claude-post-edit scripts (#1057)
- **Related**: #1057 (Auto-Format), #1058 (Smart Test Runner)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-pre-commit.sh | create | Implementation | Main wrapper script | Low |
| tests/test_claude_pre_commit.py | create | Test-Driven | Unit tests for wrapper | Low |
| .claude/hooks/pre-commit.sh | create | Integration | Hook integration | Low |
| CLAUDE.md | modify | Documentation | Update workflow docs | Low |
| scripts/validate-branch-for-pr.sh | modify | Integration | Integrate new script | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer creating developer tooling for AI agents, with expertise in bash scripting and CI/CD integration.

**Context**
GitHub Issue #1059: Pre-Commit Integration for Claude Code CLI
- Claude currently struggles with human-readable pre-commit output
- Need structured output (JSON) that Claude can parse
- Should provide clear fix instructions and auto-fix capabilities
- Related work: claude-post-edit.sh already handles formatting (#1057)
- Pre-commit hooks include: black, isort, flake8, mypy, yamllint

**Instructions**
1. **Primary Objective**: Create claude-pre-commit.sh wrapper that outputs structured JSON
2. **Scope**:
   - Capture pre-commit output and parse it
   - Provide JSON output with status, failures, and fix instructions
   - Support --fix mode for auto-fixable issues
   - Track what files were modified during auto-fix
3. **Constraints**:
   - Follow existing script patterns from claude-post-edit.sh
   - Maintain compatibility with existing CI scripts
   - Output must be easily parseable by Claude
   - Preserve exit codes for CI integration
4. **Prompt Technique**: Implementation-focused with clear structure
5. **Testing**: Create comprehensive tests covering all pre-commit hooks
6. **Documentation**: Update CLAUDE.md with usage instructions

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 5 files
• Context budget: ≤ 15k tokens
• Performance budget: Must complete within 30 seconds
• Code quality: Shellcheck clean, comprehensive error handling
• CI compliance: Must integrate with existing validation scripts

**Output Format**
Return complete implementation with structured JSON output format.
Use conventional commits: feat(ci): add claude-pre-commit wrapper

## 🔍 Verification & Testing
- `shellcheck scripts/claude-pre-commit.sh` (shell script quality)
- `pytest tests/test_claude_pre_commit.py` (unit tests)
- `./scripts/claude-pre-commit.sh --all-files` (manual testing)
- `./scripts/claude-pre-commit.sh --fix` (auto-fix testing)
- Integration test with validate-branch-for-pr.sh

## ✅ Acceptance Criteria
- [X] Wrapper script provides structured output (JSON/YAML)
- [X] Clear indication of which checks passed/failed
- [X] Actionable fix instructions for each failure
- [X] Auto-fix capability with clear change reporting
- [X] Integration with Claude's commit workflow
- [X] Graceful handling of pre-commit hook failures

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15,000
├── time_budget: 2-3 hours
├── cost_estimate: $0.30
├── complexity: Medium
└── files_affected: 5

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1059
sprint: null
phase: null
component: ci
priority: high
complexity: medium
dependencies: ["pre-commit-config", "claude-post-edit"]
```
