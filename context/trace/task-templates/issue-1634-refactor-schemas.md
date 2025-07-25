# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1634-refactor-context-schemas
# Generated from GitHub Issue #1634
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1634-refactor-context-schemas`

## 🎯 Goal (≤ 2 lines)
> Refactor context schema files from multi-document YAML to single-document format
> to enable standard YAML validation and remove pre-commit exclusions.

## 🧠 Context
- **GitHub Issue**: #1634 - [SPRINT-4.2] Refactor context schema files to avoid multi-document YAML issues
- **Sprint**: sprint-4-2
- **Phase**: Phase 2: Code Quality
- **Component**: context
- **Priority**: medium
- **Why this matters**: Currently schema files must be excluded from YAML validation due to multi-document format
- **Dependencies**: None
- **Related**: #1426, #1448, #1489

## 🛠️ Subtasks
Multiple schema files need refactoring (12 files total):

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| context/schemas/base.yaml | modify | Structural | Convert to single-doc | High |
| context/schemas/decision.yaml | modify | Structural | Convert to single-doc | Low |
| context/schemas/design.yaml | modify | Structural | Convert to single-doc | Med |
| context/schemas/log.yaml | modify | Structural | Convert to single-doc | Low |
| context/schemas/sprint.yaml | modify | Structural | Convert to single-doc | Med |
| context/schemas/trace.yaml | modify | Structural | Convert to single-doc | Low |
| context/schemas/*_full.yaml (6 files) | modify | Structural | Convert to single-doc | Med |
| .pre-commit-config.yaml | modify | Config | Remove schema exclusion | High |
| context/schemas/schema_loader.py | create | Implementation | Backward compatibility | High |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on YAML schema refactoring.

**Context**
GitHub Issue #1634: Schema files use multi-document YAML (--- separators) which breaks standard YAML validators.
Current codebase uses Yamale for schema validation.
Related files: 12 schema files in context/schemas/

**Instructions**
1. **Primary Objective**: Convert multi-document YAML to single-document nested format
2. **Scope**: All schema files in context/schemas/ directory
3. **Constraints**:
   - Maintain exact schema semantics
   - Preserve Yamale validation syntax
   - Keep backward compatibility if possible
4. **Prompt Technique**: Structural refactoring - preserve meaning while changing format
5. **Testing**: Ensure yamllint passes after changes
6. **Documentation**: Update if schema structure changes significantly

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 13 files
• Context budget: ≤ 15k tokens
• Performance budget: N/A (structure change only)
• Code quality: yamllint compliant
• CI compliance: All pre-commit hooks must pass

**Output Format**
Return implementation with converted schemas.
Use conventional commits: fix(context): refactor schemas to single-document YAML

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pre-commit run --all-files` (including check-yaml)
- `python -m src.agents.context_lint validate context/` (schema validation)
- `yamllint context/schemas/*.yaml` (YAML linting)

## ✅ Acceptance Criteria
- [ ] Schema files no longer use multi-document YAML format
- [ ] check-yaml pre-commit hook passes without exclusions
- [ ] Schema functionality remains unchanged
- [ ] All existing validation continues to work
- [ ] Documentation updated if schema structure changes

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15k
├── time_budget: 2h
├── cost_estimate: $0.50
├── complexity: medium
└── files_affected: 13

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1634
sprint: sprint-4-2
phase: Phase 2: Code Quality
component: context
priority: medium
complexity: medium
dependencies: []
```
