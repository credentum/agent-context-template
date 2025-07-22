# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1206-fix-workflow-documentation
# Generated from GitHub Issue #1206
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1206-workflow-documentation-pr-inclusion`

## 🎯 Goal (≤ 2 lines)
> Fix workflow documentation to ensure completion logs and final documentation are created before PR push, so all documentation artifacts are included in PRs automatically.

## 🧠 Context
- **GitHub Issue**: #1206 - [SPRINT-4.2] Fix workflow documentation to ensure final documentation is included in PRs
- **Sprint**: sprint-4.2
- **Phase**: Phase 1: Code Quality & Infrastructure
- **Component**: documentation
- **Priority**: medium
- **Why this matters**: Current workflow creates completion logs after PR push, leaving documentation only in local branch
- **Dependencies**: None
- **Related**: #1061 (where issue discovered), PR #1205 (example affected PR)

## 🛠️ Subtasks
Documentation workflow reordering to ensure all artifacts are in PR:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-issue.md | modify | Chain-of-Thought | Reorder Phase 4/5 steps for proper documentation timing | Low |
| .claude/workflows/workflow-issue.md | modify | Direct Instruction | Update Documentation Strategy table with correct timing | Low |
| .claude/workflows/workflow-issue.md | modify | Few-Shot Examples | Add verification steps to ensure docs in PR | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior technical writer fixing a critical workflow documentation issue.

**Context**
GitHub Issue #1206: Fix workflow documentation to ensure final documentation is included in PRs
Current problem: Completion logs are created in Phase 5 AFTER PR is pushed, leaving them only in local branch
This was discovered in issue #1061 where completion logs had to be manually pushed as follow-up
The workflow file at .claude/workflows/workflow-issue.md needs to be restructured

**Instructions**
1. **Primary Objective**: Reorder workflow steps so all documentation is created and committed before PR push
2. **Scope**: Focus on Phase 4 and Phase 5 documentation steps only
3. **Constraints**:
   - Maintain existing workflow structure and numbering
   - Keep all existing functionality intact
   - Ensure documentation strategy is clear and prevents future gaps
4. **Prompt Technique**: Chain-of-Thought for logical reordering of complex workflow steps
5. **Testing**: Verify the new flow makes logical sense and prevents documentation gaps
6. **Documentation**: Update the Documentation Strategy table to reflect correct timing

**Technical Constraints**
• Expected diff ≤ 100 LoC, 1 file
• Context budget: ≤ 5k tokens
• Performance budget: Minimal (documentation only)
• Code quality: Maintain markdown formatting standards
• CI compliance: No CI checks needed (documentation only)

**Output Format**
Return modified workflow with reordered steps ensuring all documentation is committed before PR creation.
Focus changes on Steps 9-12 and the Documentation Strategy table.

## 🔍 Verification & Testing
- Review modified workflow for logical flow
- Ensure all documentation artifacts are created before PR push
- Verify Documentation Strategy table accurately reflects new timing
- Check that verification steps are added to catch missing documentation
- Manual review: Follow the workflow mentally to ensure no gaps

## ✅ Acceptance Criteria
- Phase 4 includes completion log creation before PR push
- Phase 5 documentation strategy updated to focus on verification only
- Documentation table updated to reflect correct timing
- Workflow steps reordered to prevent documentation gaps
- Clear guidance on when each documentation artifact should be created and committed

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 5000
├── time_budget: 30 minutes
├── cost_estimate: $0.10
├── complexity: low (documentation reordering)
└── files_affected: 1

Actuals (to be filled):
├── tokens_used: ~4500
├── time_taken: 15 minutes
├── cost_actual: $0.08
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1206
sprint: sprint-4.2
phase: "Phase 1: Code Quality & Infrastructure"
component: documentation
priority: medium
complexity: low
dependencies: []
```