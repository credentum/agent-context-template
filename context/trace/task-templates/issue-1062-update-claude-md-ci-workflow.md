# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1062-update-claude-md-ci-workflow
# Generated from GitHub Issue #1062
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1062-update-claude-md-ci-workflow`

## 🎯 Goal (≤ 2 lines)
> Update CLAUDE.md documentation to provide Claude Code with clear guidance on using the new CI workflow tools during development, including commands, examples, and troubleshooting.

## 🧠 Context
- **GitHub Issue**: #1062 - Update CLAUDE.md with New CI Workflow for Claude Code
- **Sprint**: Not yet assigned (documentation task)
- **Phase**: Documentation
- **Component**: documentation
- **Priority**: Medium
- **Why this matters**: Claude Code needs explicit instructions on when and how to use new CI tools to catch errors early and provide structured feedback
- **Dependencies**: CI tool implementations from issues #1057-1061
- **Related**: New CI scripts (claude-ci.sh, claude-test-changed.sh, claude-post-edit.sh, claude-pre-commit.sh)

## 🛠️ Subtasks
Documentation updates focused on integrating new CI tools into existing workflows:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| CLAUDE.md | modify | Chain of Thought | Add new CI Integration section after Recommended Workflows | High |
| CLAUDE.md | modify | Direct Edit | Update existing workflow examples to include CI commands | Medium |
| CLAUDE.md | modify | Direct Edit | Update quick reference and cheat sheet sections | Low |
| CLAUDE.md | modify | Chain of Thought | Add CI troubleshooting section | Medium |
| CLAUDE.md | modify | Direct Edit | Update testing workflow section with new commands | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a technical documentation writer updating the CLAUDE.md file to help Claude Code effectively use new CI tools.

**Context**
GitHub Issue #1062: Update CLAUDE.md with New CI Workflow for Claude Code

The project has introduced several new CI scripts that provide structured feedback:
- claude-ci.sh: Unified CI command hub
- claude-test-changed.sh: Smart test runner
- claude-post-edit.sh: Post-edit validation
- claude-pre-commit.sh: Pre-commit integration

Current CLAUDE.md has basic mentions but lacks:
- Clear guidance on when to use each tool
- Command examples with expected outputs
- Integration with existing workflows
- Troubleshooting for common issues
- Progressive validation strategies

**Instructions**
1. **Primary Objective**: Add comprehensive CI workflow documentation to CLAUDE.md
2. **Scope**: Focus on practical usage guidance for Claude Code during development
3. **Constraints**:
   - Maintain existing document structure and style
   - Keep examples concise and practical
   - Show JSON output examples for Claude parsing
   - Integrate naturally with existing sections
4. **Prompt Technique**: Chain of Thought for new sections, Direct Edit for updates
5. **Testing**: Ensure all command examples are accurate
6. **Documentation**: Use clear headings, code blocks, and tables

**Technical Constraints**
• Expected diff ≤ 300 LoC, ≤ 1 file
• Context budget: ≤ 10k tokens
• Performance budget: Documentation only, no runtime impact
• Code quality: Markdown formatting, clear examples
• CI compliance: N/A (documentation only)

**Output Format**
Return updated CLAUDE.md with integrated CI workflow documentation.
Use conventional commits: docs(claude): add CI workflow guidance for Claude Code

## 🔍 Verification & Testing
- Validate Markdown syntax and formatting
- Check all command examples are accurate
- Verify links and references work
- Ensure consistency with existing documentation style
- Review for completeness against issue requirements

## ✅ Acceptance Criteria
From GitHub issue #1062:
- [x] Clear section on CI workflow for Claude Code
- [x] Step-by-step instructions for each development phase
- [x] Command examples with expected outputs
- [x] Integration with existing Claude workflows
- [x] Troubleshooting section for common CI issues
- [x] Updated command reference with new tools

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 8,000
├── time_budget: 30 minutes
├── cost_estimate: $0.15
├── complexity: Medium (documentation task)
└── files_affected: 1 (CLAUDE.md)

Actuals (to be filled):
├── tokens_used: ~7,500
├── time_taken: 25 minutes
├── cost_actual: $0.12
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1062
sprint: unassigned
phase: documentation
component: documentation
priority: medium
complexity: medium
dependencies: ["1057", "1058", "1059", "1060", "1061"]
```
