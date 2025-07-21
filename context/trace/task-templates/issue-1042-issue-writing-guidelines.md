# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1042-issue-writing-guidelines
# Generated from GitHub Issue #1042
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1042-issue-writing-guidelines`

## 🎯 Goal (≤ 2 lines)
> Create comprehensive issue writing guidelines and investigation templates to prevent scope underestimation and support systematic problem discovery.

## 🧠 Context
- **GitHub Issue**: #1042 - [SPRINT-5.2] Create issue writing guidelines and investigation templates
- **Sprint**: sprint-5-2
- **Phase**: Phase 2: Implementation
- **Component**: documentation, tooling
- **Priority**: medium
- **Why this matters**: Issue #1029 revealed how "simple fixes" can hide complex problems requiring 1300+ line changes
- **Dependencies**: GitHub issue templates, sprint workflow system
- **Related**: Issue #1029 (false positive warnings case study), PR #1034 (scope discovery example)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| docs/issue-writing-guide.md | create | Multi-shot learning | Comprehensive guide for writing effective issues | High |
| .github/ISSUE_TEMPLATE/investigation.md | create | Template design | Template for unclear scope problems | Medium |
| .github/ISSUE_TEMPLATE/sprint-task.md | modify | Incremental update | Add investigation phase section | Low |
| .claude/workflows/workflow-issue.md | modify | Context-aware editing | Add investigation workflow phases | Medium |
| src/agents/sprint_issue_linker.py | modify | Code enhancement | Support issue template usage | Medium |
| context/trace/scratchpad/$(date +%Y-%m-%d)-issue-1042-investigation.md | create | Documentation | Document implementation findings | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior technical writer and developer workflow architect creating documentation to prevent the "simple fix becomes complex implementation" problem.

**Context**
GitHub Issue #1042: Create issue writing guidelines and investigation templates
Case Study: Issue #1029 appeared to be a 1-line syntax fix but revealed 3 interconnected problems requiring 1300+ lines of changes.
Current state: Only one issue template exists (sprint-task.md), no issue writing documentation, sprint_issue_linker.py doesn't use templates.

**Instructions**
1. **Primary Objective**: Create guidelines and templates that encourage thorough problem investigation before implementation
2. **Scope**: Focus on preventing scope underestimation through better issue documentation practices
3. **Constraints**:
   - Follow existing GitHub issue template format
   - Integrate with current sprint workflow system
   - Maintain backward compatibility with sprint_issue_linker.py
4. **Prompt Technique**: Multi-shot learning for guide creation, template design for new templates
5. **Testing**: Validate templates render correctly, documentation is clear and actionable
6. **Documentation**: Create examples based on issue #1029 case study

**Technical Constraints**
• Expected diff ≤ 800 LoC, ≤ 6 files
• Context budget: ≤ 10k tokens
• Performance budget: minimal (documentation only)
• Code quality: Markdown formatting, clear examples
• CI compliance: All documentation must pass linting

**Output Format**
Create comprehensive documentation and templates that guide users through:
1. Problem-first issue writing (symptoms before solutions)
2. Investigation phase for unclear scope
3. Sub-issue decomposition patterns
4. Scope discovery protocols

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (validate markdown formatting)
- Manual review of template rendering in GitHub
- Test sprint_issue_linker.py changes with mock data
- Review documentation clarity with examples

## ✅ Acceptance Criteria
- [ ] Create comprehensive issue writing guidelines document
- [ ] Create investigation issue template for unclear scope problems
- [ ] Update sprint task template with investigation phase
- [ ] Enhance workflow-issue.md with investigation phases
- [ ] Update sprint_issue_linker.py to support issue templates
- [ ] Document scope discovery patterns and best practices

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 10,000 (mostly documentation)
├── time_budget: 2-3 hours
├── cost_estimate: $0.30-0.45
├── complexity: medium (mostly documentation)
└── files_affected: 5-6

Actuals (to be filled):
├── tokens_used: ~8,000
├── time_taken: 1.5 hours
├── cost_actual: $0.25
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1042
sprint: sprint-5-2
phase: "Phase 2: Implementation"
component: ["documentation", "tooling"]
priority: medium
complexity: medium
dependencies: ["GitHub issue templates", "sprint workflow"]
```
