# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1644-implement-llm-based-arc-reviewer
# Generated from GitHub Issue #1644
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`implement-llm-based-arc-reviewer-to-match-github-actions`

## 🎯 Goal (≤ 2 lines)
> Implement LLM-based ARC Reviewer using Claude API to exactly match GitHub Actions behavior with identical tool access, prompt template, and YAML output format

## 🧠 Context
- **GitHub Issue**: #1644 - [SPRINT-4.2] Implement LLM-based ARC Reviewer to match GitHub Actions behavior
- **Sprint**: sprint-4.2
- **Phase**: Phase 2: Implementation
- **Component**: ci-pipeline
- **Priority**: enhancement
- **Why this matters**: Enable local execution of the same LLM-powered review logic used in GitHub Actions, providing consistency and faster feedback
- **Dependencies**: Anthropic Python SDK, existing ARC Reviewer infrastructure
- **Related**: GitHub Actions workflow `.github/workflows/claude-code-review.yml`, current `src/agents/arc_reviewer.py`

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `requirements.txt` | modify | Direct edit | Add anthropic SDK dependency | Low |
| `src/agents/llm_reviewer.py` | create | Class design | New LLMReviewer class with Claude integration | Med |
| `src/agents/arc_reviewer.py` | modify | Integration pattern | Update to use LLMReviewer when configured | Med |
| `.env.example` | modify | Documentation | Add ANTHROPIC_API_KEY example | Low |
| `tests/test_llm_reviewer.py` | create | Test-driven | Unit tests with mocked API | Med |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on CI/Pipeline infrastructure.

**Context**
GitHub Issue #1644: Implement LLM-based ARC Reviewer to match GitHub Actions behavior
Current codebase has rule-based ARC Reviewer in `src/agents/arc_reviewer.py` (~584 LoC).
GitHub Actions uses Claude via `anthropics/claude-code-action@beta` with specific tools and prompt.
Need local equivalent that produces identical YAML output format and review quality.

Related files:
- `src/agents/arc_reviewer.py` (current rule-based implementation)
- `.github/workflows/claude-code-review.yml` (GitHub Actions reference)
- `.coverage-config.json` (coverage thresholds configuration)

**Instructions**
1. **Primary Objective**: Create LLMReviewer class that wraps Claude API and integrates with existing ARCReviewer
2. **Scope**: Add LLM mode alongside existing rule-based mode, maintaining backward compatibility
3. **Constraints**:
   - Follow existing code patterns: class-based design, type hints, comprehensive error handling
   - Maintain backward compatibility - existing CLI interface unchanged
   - Keep public APIs unchanged unless specified in issue requirements
4. **Prompt Technique**: Class design with dependency injection for API client
5. **Testing**: Mock Anthropic API for unit tests, ensure coverage ≥71.82%
6. **Documentation**: Update `.env.example` with API key configuration

**Technical Constraints**
• Expected diff ≤ 800 LoC, ≤ 5 files
• Context budget: ≤ 15k tokens
• Performance budget: <30s for typical PR review
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(ci): implement LLM-based ARC reviewer

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Mock API tests, integration with existing ARCReviewer
- **Integration tests**: Test with environment variable configuration

## ✅ Acceptance Criteria
- [ ] Local ARC Reviewer uses Claude API to match GitHub Actions behavior exactly
- [ ] Implements the same tool access (Bash, Read, Grep, Glob) as GitHub workflow
- [ ] Uses identical prompt template from `.github/workflows/claude-code-review.yml`
- [ ] Produces YAML output in exact same format as GitHub Actions version
- [ ] Supports API key configuration via environment variables
- [ ] Includes fallback to rule-based review when API is unavailable
- [ ] Maintains backward compatibility with existing CI pipeline integration
- [ ] Coverage and security checks remain functional
- [ ] Performance is acceptable (<30s for typical PR review)

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12000 (API integration + tests)
├── time_budget: 90 minutes (implementation + testing)
├── cost_estimate: $8-15 (Claude API calls during testing)
├── complexity: Medium (API integration with existing infrastructure)
└── files_affected: 5

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1644
sprint: sprint-4.2
phase: Phase 2: Implementation
component: ci-pipeline
priority: enhancement
complexity: medium
dependencies: ["anthropic-sdk", "existing-arc-reviewer"]
```
