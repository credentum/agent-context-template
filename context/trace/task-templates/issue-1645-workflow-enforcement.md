# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1645-workflow-enforcement
# Generated from GitHub Issue #1645
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1645-workflow-enforcement`

## 🎯 Goal (≤ 2 lines)
> Implement standard workflow enforcement system that automatically validates phase prerequisites, tracks state, and ensures all workflow steps are followed for every issue resolution.

## 🧠 Context
- **GitHub Issue**: #1645 - [SPRINT-4.2] Implement standard workflow enforcement for all issue resolutions
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: High (Critical gap in process enforcement)
- **Why this matters**: Recent execution of #1644 revealed workflow steps are being skipped, leading to incomplete documentation and quality issues
- **Dependencies**: Existing workflow validator in tests/test_workflow_validator.py
- **Related**: PR #1643 (workflow enforcement integration), Issue #1644 (revealed gaps)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/workflow_enforcer.py | Create | Structured generation | Core enforcement engine with phase validation | High |
| scripts/agent_hooks.py | Create | Chain of thought | Integration hooks for all agent types | High |
| scripts/workflow_cli.py | Create | Sequential refinement | CLI interface with enforcement | Medium |
| scripts/validators/workflow_validator.py | Modify | Focused edit | Integrate with enforcer | Medium |
| .claude/config/workflow-enforcement.yaml | Create | Template fill | Configuration for enforcement rules | Low |
| tests/test_workflow_enforcer.py | Create | Test-driven | Unit tests for enforcement | Low |
| tests/test_agent_hooks.py | Create | Test-driven | Integration tests for hooks | Low |
| .claude/guides/workflow-enforcement.md | Create | Documentation | User guide for enforcement | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer implementing a critical workflow enforcement system to ensure quality and compliance in the development process.

**Context**
GitHub Issue #1645: Implement standard workflow enforcement for all issue resolutions
- The workflow process is well-documented in `.claude/workflows/workflow-issue.md`
- Recent executions have shown steps being skipped, especially documentation and testing
- A workflow validator exists but isn't being used during actual workflow execution
- The system needs to enforce phase prerequisites and track state across agent executions

Current codebase follows:
- Python 3.x with type hints
- YAML for configuration
- Conventional commits
- 71.82% minimum coverage requirement

Related files:
- `.claude/workflows/workflow-issue.md` (1151 lines of workflow documentation)
- `tests/test_workflow_validator.py` (existing validator tests)
- `scripts/validators/security.py` (references WorkflowValidator)

**Instructions**
1. **Primary Objective**: Create an enforcement system that prevents workflow violations
2. **Scope**:
   - Implement phase entry/exit validation
   - Add state persistence across executions
   - Integrate hooks into all agent types
   - Provide clear error messages and recovery options
3. **Constraints**:
   - Must be backward compatible (enforcement can be disabled)
   - Follow existing Python patterns in the codebase
   - Maintain test coverage above 71.82%
   - All enforcement must be configurable
4. **Prompt Technique**: Structured generation for core components, chain of thought for complex integrations
5. **Testing**: Create comprehensive unit and integration tests
6. **Documentation**: Update workflow docs and create enforcement guide

**Technical Constraints**
• Expected diff ≤ 2000 LoC, ≤ 10 files
• Context budget: ≤ 30k tokens
• Performance budget: Minimal overhead (<100ms per phase validation)
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation with proper error handling and logging.
Use conventional commits: feat(workflow): implement enforcement system

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest tests/test_workflow_enforcer.py tests/test_agent_hooks.py --cov`
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Test phase validation logic
  - Test state persistence and recovery
  - Test agent hook integration
  - Test CLI with enforcement
- **Integration tests**: Full workflow execution with enforcement

## ✅ Acceptance Criteria
### Core Enforcement System
- [x] Workflow validator is automatically invoked for all issue resolutions
- [x] State persistence works across all agent executions
- [x] Phase prerequisites are validated before each phase starts
- [x] Phase outputs are validated after each phase completes
- [x] Resume capability works from any interrupted phase

### Documentation Enforcement
- [x] Task templates are created in `context/trace/task-templates/`
- [x] Scratchpads are created in `context/trace/scratchpad/`
- [x] Documentation is committed BEFORE implementation (Phase 1)
- [x] Completion logs are created in `context/trace/logs/`
- [x] All documentation is included in PRs

### CI/Testing Enforcement
- [x] `./scripts/run-ci-docker.sh` is run during Phase 3
- [x] `pre-commit run --all-files` is executed
- [x] Test coverage is verified to stay above 71.82%
- [x] `./scripts/validate-branch-for-pr.sh` is run before PR creation

### Agent Integration
- [x] issue-investigator agent uses validation hooks
- [x] task-planner agent uses validation hooks
- [x] main-claude uses validation hooks
- [x] test-runner agent uses validation hooks
- [x] pr-manager agent uses validation hooks

### Error Handling
- [x] Validation failures prevent phase progression
- [x] Clear error messages guide resolution
- [x] State recovery works after failures
- [x] Workflow can resume from any phase

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 30,000
├── time_budget: 6 hours
├── cost_estimate: $2.50
├── complexity: High
└── files_affected: 10

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1645
sprint: sprint-4.2
phase: implementation
component: workflow-automation
priority: high
complexity: high
dependencies:
  - workflow-validator
  - agent-framework
```
