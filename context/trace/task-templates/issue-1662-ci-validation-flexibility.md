# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1662-ci-validation-flexibility
# Generated from GitHub Issue #1662
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1662-ci-validation-flexibility`

## 🎯 Goal (≤ 2 lines)
> Make Phase 3/4 CI validation in workflow-validator.py more flexible and less restrictive by removing hard time limits and supporting multiple CI environments

## 🧠 Context
- **GitHub Issue**: #1662 - [SPRINT-X.Y] Make Phase 3/4 CI validation more flexible and less restrictive
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: enhancement + bug
- **Why this matters**: Current CI validation is too restrictive with 1-hour time limits and hardcoded marker files, causing workflow failures in valid scenarios
- **Dependencies**: Existing workflow-enforcement.yaml configuration system
- **Related**: #1659, #1660, #1661 (other workflow validation fixes)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .claude/workflows/workflow-validator.py | modify | direct implementation | Make _check_ci_status() flexible | Low |
| .claude/config/workflow-enforcement.yaml | modify | yaml enhancement | Add CI validation config options | Low |
| tests/test_workflow_validator.py | create/modify | test-driven | Unit tests for new CI validation | Med |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation and validation systems.

**Context**
GitHub Issue #1662: Make Phase 3/4 CI validation more flexible and less restrictive
Current implementation at workflow-validator.py:246-255 has hardcoded 1-hour CI validation that fails in resumed workflows and non-Docker environments.
Codebase follows Python best practices with YAML configuration management.
Related files: .claude/workflows/workflow-validator.py (lines 246-255, 99-100), .claude/config/workflow-enforcement.yaml

**Instructions**
1. **Primary Objective**: Make CI validation flexible for different environments and resume scenarios
2. **Scope**: Modify _check_ci_status() method and add configuration support while maintaining backward compatibility
3. **Constraints**:
   - Follow existing code patterns: secure subprocess calls, path validation
   - Maintain backward compatibility unless breaking change approved
   - Keep public APIs unchanged unless specified in issue
4. **Prompt Technique**: Direct implementation because requirements are clear and scope is well-defined
5. **Testing**: Add unit tests covering various CI scenarios and configuration options
6. **Documentation**: Update configuration schema and add inline documentation

**Technical Constraints**
• Expected diff ≤ 100 LoC, ≤ 3 files
• Context budget: ≤ 10k tokens
• Performance budget: Low impact (validation code)
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: fix(workflow): improve CI validation flexibility

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Test various CI marker scenarios, time limits, resume workflows
- **Integration tests**: Test with/without Docker, different CI environments

## ✅ Acceptance Criteria
- [ ] Make CI validation more flexible and environment-aware
- [ ] Remove or make configurable the 1-hour time restriction
- [ ] Support multiple CI marker files or patterns
- [ ] Allow validation to pass if CI is not available but tests pass
- [ ] Add configuration options for CI validation behavior
- [ ] Maintain backward compatibility with existing workflows

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 8000 (small focused change)
├── time_budget: 2 hours (clear requirements + testing)
├── cost_estimate: $0.50 (low complexity)
├── complexity: Low (well-defined enhancement)
└── files_affected: 3 (validator, config, tests)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1662
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: enhancement + bug
complexity: Low
dependencies: workflow-enforcement.yaml
```
