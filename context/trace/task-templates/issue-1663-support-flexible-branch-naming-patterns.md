---
schema_version: "1.0"
---

# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1663-support-flexible-branch-naming-patterns
# Generated from GitHub Issue #1663
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1663-support-flexible-branch-naming-patterns`

## 🎯 Goal (≤ 2 lines)
> Enhance workflow validation to support flexible branch naming patterns beyond the current rigid fix/ and feature/ prefixes, enabling custom regex patterns and configurable branch prefixes for diverse development workflows

## 🧠 Context
- **GitHub Issue**: #1663 - Support flexible branch naming patterns
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: workflow-automation
- **Priority**: enhancement
- **Why this matters**: Current workflow validator only accepts fix/ and feature/ branch patterns, limiting teams that use other naming conventions like hotfix/, refactor/, chore/, docs/, etc.
- **Dependencies**: WorkflowValidator class, workflow-enforcement.yaml configuration, GitHub CLI (gh)
- **Related**: #1662 (CI validation flexibility), #1661 (path validation), #1659 (workflow validation fixes)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `.claude/workflows/workflow-validator.py` | modify | direct-implementation | Update `_check_pr_created()` method | Low |
| `.claude/config/workflow-enforcement.yaml` | modify | structured-config | Add branch pattern configuration | Low |
| `tests/test_workflow_validator.py` | create/modify | test-driven | Comprehensive test coverage for patterns | Med |
| `context/trace/scratchpad/2025-07-27-issue-1663-support-flexible-branch-naming-patterns.md` | create | documentation | Track implementation progress | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on workflow automation and validation systems with expertise in branch naming conventions and configuration management.

**Context**
GitHub Issue #1663: Support flexible branch naming patterns
Current implementation in workflow_validator.py only supports hardcoded fix/ and feature/ branch prefixes
Need to extend to support:
- Custom branch prefixes (hotfix/, refactor/, chore/, docs/, style/, test/, etc.)
- Custom regex patterns for complex naming schemes
- Configurable patterns via workflow-enforcement.yaml
- Backward compatibility with existing patterns
Related files: .claude/workflows/workflow-validator.py, .claude/config/workflow-enforcement.yaml

**Instructions**
1. **Primary Objective**: Enhance branch pattern validation to support flexible naming patterns while maintaining security
2. **Scope**: Modify _check_pr_created() and related methods to use configurable patterns
3. **Constraints**:
   - Follow existing code patterns: secure input validation, safe regex usage
   - Maintain backward compatibility with fix/ and feature/ patterns
   - Implement security measures for custom regex patterns (prevent ReDoS attacks)
   - Keep public APIs unchanged
4. **Prompt Technique**: Direct implementation because requirements are clear and architecture is established
5. **Testing**: Add comprehensive test coverage for all pattern types and edge cases
6. **Documentation**: Update configuration schema and add inline documentation for security considerations

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: Low impact (validation code)
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass
• Security: Validate regex patterns to prevent ReDoS attacks

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(workflow): add flexible branch naming pattern support

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing tests/test_workflow_validator.py` (focused test suite)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Test various branch patterns (fix/, feature/, hotfix/, refactor/, chore/, docs/, style/, test/)
- **Security tests**: Test regex validation and ReDoS prevention
- **Configuration tests**: Test YAML configuration loading and fallback behavior
- **Backward compatibility**: Ensure existing fix/ and feature/ patterns still work

## ✅ Acceptance Criteria
- [ ] Support configurable branch prefixes via workflow-enforcement.yaml
- [ ] Enable custom regex patterns for complex naming schemes
- [ ] Implement security validation for custom regex patterns
- [ ] Add comprehensive test coverage for all pattern types
- [ ] Maintain backward compatibility with existing fix/ and feature/ patterns
- [ ] Provide graceful fallback behavior when configuration is invalid
- [ ] Add input sanitization for branch prefixes and patterns
- [ ] Document security considerations and configuration options
- [ ] Create trace files with schema_version: '1.0' header

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12000 (moderate complexity with security considerations)
├── time_budget: 3 hours (implementation + comprehensive testing)
├── cost_estimate: $0.75 (medium complexity)
├── complexity: Medium (new feature with security requirements)
└── files_affected: 4 (validator, config, tests, documentation)

Actuals (completed):
├── tokens_used: ~12000 (within estimate)
├── time_taken: ~3 hours (as estimated)
├── cost_actual: ~$0.75 (as estimated)
├── iterations_needed: 3 (implementation + security fixes + test coverage)
└── context_clears: 0 (stayed within budget)
```

## 🏷️ Metadata
```yaml
github_issue: 1663
sprint: sprint-current
phase: Phase 2: Implementation
component: workflow-automation
priority: enhancement
complexity: Medium
dependencies: workflow-enforcement.yaml, WorkflowValidator, GitHub CLI
security_considerations: regex_validation, input_sanitization
```
