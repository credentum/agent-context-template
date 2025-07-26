# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1653-enhance-workflow-system-with-hybrid-sub-agent-specialists
# Generated from GitHub Issue #1653
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1653-hybrid-workflow-enhancement`

## 🎯 Goal (≤ 2 lines)
> Enhance WorkflowExecutor with specialist sub-agents as consultants for complex analysis,
> validation, and research tasks while maintaining direct execution and state persistence.

## 🧠 Context
- **GitHub Issue**: #1653 - [SPRINT-4.4] Enhance workflow system with hybrid sub-agent specialists
- **Sprint**: sprint-4.4
- **Phase**: Phase 4: Enhancement & Optimization
- **Component**: workflow-automation
- **Priority**: medium
- **Why this matters**: Combines strengths of WorkflowExecutor persistence with sub-agent specialist expertise
- **Dependencies**: Working WorkflowExecutor from #1652 (completed)
- **Related**: #1652 (foundation WorkflowExecutor fix)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/hybrid_workflow_executor.py | create | Implementation | Create HybridWorkflowExecutor class | High |
| scripts/workflow_cli.py | modify | Enhancement | Add --hybrid flag support | Medium |
| scripts/workflow_executor.py | modify | Integration | Add hook points for specialists | Low |
| tests/test_hybrid_workflow.py | create | Testing | Test hybrid execution mode | Medium |
| .claude/config/specialist-agents.yaml | create | Configuration | Define specialist configurations | Low |
| .claude/workflows/workflow-issue.md | modify | Documentation | Document hybrid capabilities | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer enhancing the workflow automation system with hybrid sub-agent capabilities.

**Context**
GitHub Issue #1653: Enhance workflow system with hybrid sub-agent specialists
- Working WorkflowExecutor (from #1652) handles persistence and state management
- Sub-agents proven excellent as specialists, not orchestrators
- Need to integrate specialist consultants while maintaining direct execution
- Current workflow: scripts/workflow_executor.py, scripts/workflow_cli.py
Related architecture analysis shows optimal pattern is WorkflowExecutor as orchestrator with sub-agents as consultants.

**Instructions**
1. **Primary Objective**: Create HybridWorkflowExecutor that enhances WorkflowExecutor with specialist sub-agents
2. **Scope**:
   - Maintain WorkflowExecutor as orchestrator (handles all persistence, git ops, state)
   - Add sub-agents as consultants (provide analysis, research, insights)
   - Enable parallel specialist processing where beneficial
   - Ensure graceful degradation if specialists fail
3. **Constraints**:
   - Follow existing WorkflowExecutor patterns
   - Maintain backward compatibility with basic mode
   - Keep all persistence in WorkflowExecutor
   - No sub-agent persistence of state
4. **Prompt Technique**: Implementation with inheritance pattern
5. **Testing**: Compare hybrid vs basic performance, validate specialist integration
6. **Documentation**: Update workflow docs with hybrid capabilities

**Technical Constraints**
• Expected diff ≤ 600 LoC, ≤ 6 files
• Context budget: ≤ 15k tokens
• Performance budget: Parallel specialists should improve speed
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete HybridWorkflowExecutor implementation with:
- Specialist integration for investigation, validation phases
- Parallel processing capabilities
- Fallback to basic mode on failure
- Tests demonstrating improvements
Use conventional commits: feat(workflow): add hybrid sub-agent specialist support

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest tests/test_hybrid_workflow.py` (hybrid execution tests)
- `python scripts/workflow_cli.py workflow-issue 123 --hybrid` (manual testing)
- **Issue-specific tests**:
  - Compare hybrid vs basic execution times
  - Validate specialist insights improve quality
  - Test graceful degradation on specialist failure
- **Integration tests**: Ensure state persistence remains reliable

## ✅ Acceptance Criteria
- [x] Sub-agents integrated as specialist consultants within WorkflowExecutor phases
- [x] Parallel sub-agent processing for research and analysis tasks
- [x] Enhanced investigation phase with issue-investigator specialist
- [x] Improved validation phase with test-runner and security-analyzer specialists
- [x] Context research capabilities using general-purpose agents
- [x] Workflow orchestration remains in WorkflowExecutor (no sub-agent persistence)
- [x] Performance improvement through parallel specialist analysis
- [x] Backward compatibility with basic WorkflowExecutor mode

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 45-60 minutes
├── cost_estimate: ~$1.50
├── complexity: Medium-High
└── files_affected: 6

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1653
sprint: sprint-4.4
phase: Phase 4: Enhancement & Optimization
component: workflow-automation
priority: medium
complexity: medium-high
dependencies: [1652]
```
