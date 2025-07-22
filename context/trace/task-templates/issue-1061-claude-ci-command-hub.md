# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1061-claude-ci-command-hub
# Generated from GitHub Issue #1061
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1061-claude-ci-command-hub`

## 🎯 Goal (≤ 2 lines)
> Create a unified CLI tool `scripts/claude-ci.sh` that provides all CI operations Claude needs with consistent interface and output format.

## 🧠 Context
- **GitHub Issue**: #1061 - Claude CI Command Hub
- **Sprint**: Not specified in labels
- **Phase**: Not specified in labels
- **Component**: ci (from labels)
- **Priority**: High (from issue description)
- **Why this matters**: Currently Claude uses multiple inconsistent scripts for CI tasks, causing confusion about which tool to use when
- **Dependencies**: Builds on existing claude-pre-commit.sh, claude-test-changed.sh, claude-post-edit.sh
- **Related**: Issues #1057, #1058, #1059, #1060 mentioned in implementation plan

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-ci.sh | create | Step-by-step implementation | Unified CLI interface with subcommands | Medium |
| CLAUDE.md | modify | Documentation update | Add claude-ci command reference | Low |
| scripts/claude-ci.sh | test | Manual testing | Verify all subcommands work correctly | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD automation and developer tooling.

**Context**
GitHub Issue #1061: Claude CI Command Hub
Problem: Claude Code currently uses various scripts (run-ci-docker.sh, pre-push-ci-check.sh, quick-pre-push.sh, claude-pre-commit.sh, claude-test-changed.sh, claude-post-edit.sh) leading to confusion about which tool to use when.
Current codebase follows bash scripting patterns with structured JSON output for AI integration.
Related files: scripts/claude-*.sh (existing tools), CLAUDE.md (documentation)

**Instructions**
1. **Primary Objective**: Create unified `scripts/claude-ci.sh` that provides single entry point for all CI operations
2. **Scope**: Implement subcommands (check, test, pre-commit, review, all) with consistent interface
3. **Constraints**:
   - Follow existing code patterns: bash with JSON output, structured error handling
   - Maintain backward compatibility with existing scripts
   - Keep public APIs of existing scripts unchanged
4. **Prompt Technique**: Step-by-step implementation because this involves creating new CLI interface with multiple subcommands
5. **Testing**: Manual testing of all subcommands, integration with existing CI pipeline
6. **Documentation**: Update CLAUDE.md with new unified command reference

**Technical Constraints**
• Expected diff ≤ 300 LoC, ≤ 2 files
• Context budget: ≤ 10k tokens
• Performance budget: Low complexity - wrapper around existing tools
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(ci): add unified claude-ci command hub

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Test all subcommands: `claude-ci check`, `claude-ci test`, `claude-ci pre-commit`, `claude-ci review`, `claude-ci all`
  - Verify JSON output format consistency
  - Test help system and error handling
- **Integration tests**: Verify integration with existing scripts

## ✅ Acceptance Criteria
- [ ] Single entry point for all CI operations
- [ ] Consistent command structure and output format
- [ ] Progressive validation (quick → standard → comprehensive)
- [ ] Clear help and usage information
- [ ] Integration with all other Claude CI improvements
- [ ] Documented in CLAUDE.md for easy reference

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 8000 (small script creation + documentation)
├── time_budget: 45 minutes (straightforward wrapper implementation)
├── cost_estimate: $0.02
├── complexity: Low (wrapper around existing tools)
└── files_affected: 2 (scripts/claude-ci.sh + CLAUDE.md)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1061
sprint: null
phase: null
component: ci
priority: high
complexity: low
dependencies: [claude-pre-commit.sh, claude-test-changed.sh, claude-post-edit.sh]
```
