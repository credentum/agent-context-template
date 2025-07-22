# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1130-extract-arc-reviewer-logic
# Generated from GitHub Issue #1130
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1130-extract-arc-reviewer-logic`

## 🎯 Goal (≤ 2 lines)
> Extract ARC-Reviewer logic from GitHub Actions workflow YAML into standalone Python module for local execution capability while maintaining identical review criteria and output format.

## 🧠 Context
- **GitHub Issue**: #1130 - [Component: CI] Extract ARC-Reviewer logic to Python module
- **Sprint**: Current development sprint
- **Phase**: Implementation (from decomposed investigation #1060)
- **Component**: ci
- **Priority**: enhancement
- **Why this matters**: Enables local PR review simulation, reducing wasted pushes that fail review
- **Dependencies**: Part of investigation #1060, required for issues #1131, #1132, #1133
- **Related**: Original investigation #1060, follow-up issues #1131-#1133

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/claude-code-review.yml | read/analyze | Code Analysis | Extract core review logic and criteria | Low |
| src/agents/arc_reviewer.py | create | Structured Implementation | New Python module with review logic | Medium |
| tests/test_arc_reviewer.py | create | Test-Driven | Unit tests for review module | Medium |
| .github/workflows/claude-code-review.yml | modify | Refactoring | Update workflow to use Python module | High |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on CI/CD automation and code review systems.

**Context**
GitHub Issue #1130: Extract ARC-Reviewer logic to Python module
The ARC-Reviewer logic is currently embedded in a 838-line GitHub Actions workflow file (.github/workflows/claude-code-review.yml) making local execution impossible. Need to extract this logic into a standalone Python module while maintaining exact compatibility.

Current workflow contains:
- Review criteria (coverage thresholds, MCP compatibility, context integrity, code quality, security)
- YAML output format specification
- Coverage checking logic using .coverage-config.json
- Issue categorization (blocking/warnings/nits)
- Automated follow-up issue creation

Related files: .github/workflows/claude-code-review.yml, .coverage-config.json, src/agents/*.py

**Instructions**
1. **Primary Objective**: Extract ARC-Reviewer logic to standalone Python module
2. **Scope**: Create src/agents/arc_reviewer.py with identical review functionality
3. **Constraints**:
   - Follow existing code patterns: agent modules in src/agents/
   - Maintain backward compatibility with current workflow
   - Keep public APIs unchanged unless specified in issue
4. **Prompt Technique**: Structured Implementation because this requires careful extraction and refactoring
5. **Testing**: Create comprehensive unit tests covering all review criteria
6. **Documentation**: Update workflow comments and add module docstrings

**Technical Constraints**
• Expected diff ≤ 500 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: Fast execution for local use
• Code quality: Black formatting, coverage ≥ 78.0%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(ci): extract ARC-Reviewer logic to Python module

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Test module can produce identical YAML output
- **Integration tests**: Verify workflow still works with extracted module

## ✅ Acceptance Criteria
- [ ] ARC-Reviewer logic extracted to Python module
- [ ] Same YAML output format maintained
- [ ] All review criteria preserved
- [ ] GitHub Actions workflow updated to use module
- [ ] Local execution capability verified

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12000 (based on workflow file size)
├── time_budget: 45 minutes (extraction + testing)
├── cost_estimate: $0.15
├── complexity: Medium (refactoring embedded logic)
└── files_affected: 4 (workflow, new module, tests, possibly config)

Actuals (filled):
├── tokens_used: ~8000 (workflow analysis + implementation)
├── time_taken: 35 minutes (extraction + testing)
├── cost_actual: $0.10
├── iterations_needed: 2 (initial + test fixes)
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1130
sprint: current
phase: implementation
component: ci
priority: enhancement
complexity: medium
dependencies: ["investigation-1060"]
```
