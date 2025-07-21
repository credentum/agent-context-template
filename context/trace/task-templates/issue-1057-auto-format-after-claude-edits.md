---
schema_version: 1.0
---

# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1057-auto-format-after-claude-edits
# Generated from GitHub Issue #1057
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1057-auto-format-after-claude-edits`

## 🎯 Goal (≤ 2 lines)
> Create a post-edit hook system that automatically runs formatting checks after Claude uses Edit/MultiEdit/Write tools, providing immediate feedback to prevent formatting errors from accumulating.

## 🧠 Context
- **GitHub Issue**: [#1057](https://github.com/credentum/agent-context-template/issues/1057) - [INVESTIGATION] Auto-Format After Claude Edits
- **Sprint**: Not specified
- **Phase**: Investigation
- **Component**: CI
- **Priority**: Enhancement
- **Why this matters**: Reduces round trips fixing formatting, saves tokens, catches issues immediately
- **Dependencies**: Pre-commit hooks, CI scripts
- **Related**: CI pipeline rework

## 🛠️ Subtasks
Based on investigation findings, implementing a claude-post-edit.sh script:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-post-edit.sh | Create | Template | Post-edit validation script | Low |
| CLAUDE.md | Modify | Direct | Document new workflow | Low |
| scripts/validate-file-format.sh | Create | Template | Single file formatter | Low |
| .claude/hooks/post-edit.sh | Create | Template | Hook integration | Low |
| context/trace/logs/claude-edits.log | Create | Direct | Track Claude edits | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD pipelines and developer experience automation.

**Context**
GitHub Issue #1057: Auto-Format After Claude Edits
Current state: Claude edits files but formatting errors aren't caught until pre-commit/CI runs
Existing infrastructure: pre-commit hooks configured (Black, isort, flake8), CI scripts available
Key finding: validate-branch-for-pr.sh already has auto-formatting logic that could be adapted

**Instructions**
1. **Primary Objective**: Create post-edit hooks that run after Claude file modifications
2. **Scope**:
   - Script to validate/format single files after edit
   - Integration with Claude's workflow
   - Structured output Claude can parse
3. **Constraints**:
   - Must not disrupt normal Claude operations
   - Should be fast (< 2 seconds per file)
   - Output must be parseable by Claude
   - Leverage existing pre-commit infrastructure
4. **Prompt Technique**: Template-based for scripts, direct modification for docs
5. **Testing**: Test with Python files using Black/isort formatting
6. **Documentation**: Update CLAUDE.md with clear usage instructions

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 5 files
• Context budget: ≤ 10k tokens
• Performance budget: < 2 seconds per file validation
• Code quality: Bash best practices, error handling
• CI compliance: Compatible with existing CI pipeline

**Output Format**
Create scripts with structured output format:
```
CLAUDE_FORMAT_CHECK:START
status: success|warning|error
file: <filepath>
issues_found: <count>
auto_fixed: <count>
remaining_issues: <count>
details:
  - type: <formatter>
    message: <issue description>
CLAUDE_FORMAT_CHECK:END
```

## 🔍 Verification & Testing
- Test script with intentionally misformatted Python files
- Verify Black, isort, flake8 integration
- Test output parsing format
- Measure performance on typical files
- Test error handling for missing files

## ✅ Acceptance Criteria
From investigation findings:
- [ ] Script runs automatically after Claude edits
- [ ] Provides immediate, parseable feedback
- [ ] Integrates with existing pre-commit hooks
- [ ] Performance < 2 seconds per file
- [ ] Clear documentation in CLAUDE.md
- [ ] Handles Python files with Black/isort/flake8
- [ ] Option for auto-fix vs validation-only

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000
├── time_budget: 2 hours
├── cost_estimate: $0.50
├── complexity: medium
└── files_affected: 5

Actuals (to be filled):
├── tokens_used: ~4000
├── time_taken: 45 minutes
├── cost_actual: $0.40
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1057
sprint: none
phase: investigation
component: ci
priority: enhancement
complexity: medium
dependencies: [pre-commit, ci-scripts]
```
