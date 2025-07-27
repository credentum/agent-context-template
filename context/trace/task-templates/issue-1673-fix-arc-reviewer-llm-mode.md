# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1673-fix-arc-reviewer-llm-mode
# Generated from GitHub Issue #1673
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1673-arc-reviewer-llm-mode-anthropic-package`

## 🎯 Goal (≤ 2 lines)
> Fix ARC reviewer's LLM mode to properly work with the anthropic package, enabling Claude API-based PR reviews when --llm flag is provided.

## 🧠 Context
- **GitHub Issue**: #1673 - [SPRINT-4.3] Fix ARC reviewer LLM mode to work with anthropic package
- **Sprint**: sprint-4.3
- **Phase**: Phase 3: Testing & Refinement
- **Component**: ci-infrastructure
- **Priority**: medium
- **Why this matters**: Enables intelligent PR reviews using Claude API for better code quality feedback
- **Dependencies**: anthropic Python package (>=0.8.0), CLAUDE_CODE_OAUTH_TOKEN
- **Related**: #1651 (CI pipeline fixes), #1672 (PR with CI fixes)

## 🛠️ Subtasks
Analysis shows the anthropic package is installed but import handling needs fixing.

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| src/agents/arc_reviewer.py | modify | Tree-of-Thought | Fix LLM mode initialization and import handling | Low |
| src/agents/llm_reviewer.py | modify | Debug-First | Fix anthropic import and MyPy type issues | Medium |
| tests/test_arc_reviewer.py | modify/create | Test-Driven | Add tests for LLM mode functionality | Low |
| tests/test_arc_reviewer_llm_integration.py | review | Chain-of-Thought | Ensure integration tests work | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on the CI infrastructure component, specifically fixing the ARC reviewer's LLM integration.

**Context**
GitHub Issue #1673: Fix ARC reviewer LLM mode to work with anthropic package
- Current issue: "anthropic package not available" error when running with --llm flag
- The anthropic package (0.59.0) is installed and in requirements.txt
- CLAUDE_CODE_OAUTH_TOKEN is available in ~/.bashrc
- The import handling in llm_reviewer.py may have issues
- Multiple MyPy type errors exist in llm_reviewer.py

Current codebase follows modular Python patterns with separate modules for rule-based and LLM review.
Related files:
- src/agents/arc_reviewer.py (main reviewer entry point)
- src/agents/llm_reviewer.py (LLM implementation)
- tests/test_arc_reviewer.py (main tests)
- tests/test_arc_reviewer_llm_integration.py (integration tests)

**Instructions**
1. **Primary Objective**: Fix the anthropic package import issue to enable LLM mode
2. **Scope**:
   - Fix import handling in both arc_reviewer.py and llm_reviewer.py
   - Ensure proper fallback when LLM unavailable
   - Fix MyPy type checking errors
   - Maintain backward compatibility with rule-based mode
3. **Constraints**:
   - Follow existing code patterns and module structure
   - Maintain backward compatibility - rule-based mode must still work
   - Keep public APIs unchanged
   - anthropic package version must remain >=0.8.0
4. **Prompt Technique**: Debug-First approach to identify exact import failure
5. **Testing**: Ensure both LLM and rule-based modes work correctly
6. **Documentation**: Update any relevant docstrings if API behavior changes

**Technical Constraints**
• Expected diff ≤ 100 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: Import handling should be fast
• Code quality: Black formatting, MyPy compliance
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation fixing the import issues.
Use conventional commits: fix(ci): enable ARC reviewer LLM mode with anthropic package

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest tests/test_arc_reviewer.py -v` (unit tests)
- `pytest tests/test_arc_reviewer_llm_integration.py -v` (integration tests)
- `mypy src/agents/arc_reviewer.py src/agents/llm_reviewer.py` (type checking)
- `python src/agents/arc_reviewer.py --llm --verbose` (manual test with LLM mode)
- `python src/agents/arc_reviewer.py --verbose` (manual test rule-based mode)

## ✅ Acceptance Criteria
- [x] ARC reviewer can run in LLM mode when --llm flag is provided
- [x] Anthropic package is properly imported with correct error handling
- [x] LLM reviewer uses the CLAUDE_CODE_OAUTH_TOKEN when available
- [x] Fallback to rule-based mode works gracefully when LLM unavailable
- [x] Both src/agents/arc_reviewer.py and src/agents/llm_reviewer.py work correctly
- [x] MyPy type checking passes for both reviewer files

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 20 minutes
├── cost_estimate: $0.15
├── complexity: medium
└── files_affected: 4

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1673
sprint: sprint-4.3
phase: "Phase 3: Testing & Refinement"
component: ci-infrastructure
priority: medium
complexity: medium
dependencies: ["anthropic>=0.8.0", "CLAUDE_CODE_OAUTH_TOKEN"]
```
