# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1678-[sprint-4.3]-fix-arc-reviewer-anthropic-import-iss
# Generated from GitHub Issue #1678
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1678-[sprint-4.3]-fix-arc-reviewer-anthropic-import-iss`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.3] Fix ARC reviewer anthropic import issues for LLM mode

## 🧠 Context
- **GitHub Issue**: #1678 - [SPRINT-4.3] Fix ARC reviewer anthropic import issues for LLM mode
- **Labels**: bug, sprint-current, component:ci
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Task Context
**Sprint**: sprint-4.3
**Phase**: Phase 3: Testing & Refinement
**Component**: ci-infrastructure

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation
- [ ] **Scope needs investigation** - Create investigation issue first (use investigation.md template)
- [ ] **Partially clear** - Some aspects need investigation (note below)

**Investigation Notes**: The fix is already in PR #1675 but needs to be completed

## Acceptance Criteria
- [ ] ARC reviewer can run in LLM mode when --llm flag is provided
- [ ] Anthropic package is properly imported with correct error handling
- [ ] LLM reviewer uses the CLAUDE_CODE_OAUTH_TOKEN when available
- [ ] Fallback to rule-based mode works gracefully when LLM unavailable
- [ ] MyPy type checking passes for both reviewer files

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (PR #1675)
- [x] **File scope estimated** (2 files, < 100 LoC expected)
- [x] **Dependencies mapped** (anthropic>=0.8.0)
- [x] **Test strategy defined** (existing tests)
- [x] **Breaking change assessment** (no breaking changes)

## Pre-Execution Context
**Key Files**: 
- `src/agents/arc_reviewer.py` (lines 28-100)
- `src/agents/llm_reviewer.py` (lines 17-50)

**External Dependencies**:
- anthropic package (>=0.8.0)
- CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY

**Configuration**: 
- Environment variables for API keys

**Related Issues/PRs**: 
- #1673 (Original issue)
- #1675 (Existing PR with partial fixes)
- #1677 (Two-phase CI architecture)

## Implementation Notes
### Current Issues
1. Import handling fails when anthropic package is installed
2. LLM mode is hardcoded to disabled (line 84 in arc_reviewer.py)
3. MyPy type errors in llm_reviewer.py

### Required Fixes
1. **Fix Import Handling**:
   ```python
   # Proper import with fallback
   try:
       from anthropic import Anthropic
       ANTHROPIC_AVAILABLE = True
   except ImportError:
       ANTHROPIC_AVAILABLE = False
   ```

2. **Enable LLM Mode Detection**:
   - Remove hardcoded `self.use_llm = False`
   - Restore auto-detection based on API key availability

3. **Fix OAuth Token Support**:
   - Use `auth_token` parameter for OAuth tokens
   - Use `api_key` parameter for standard API keys

4. **Fix MyPy Issues**:
   - Add proper type annotations
   - Handle optional imports correctly

### Testing
```bash
# Test LLM mode
python -m src.agents.arc_reviewer --llm --verbose

# Test fallback to rule-based
unset CLAUDE_CODE_OAUTH_TOKEN
python -m src.agents.arc_reviewer --verbose
```

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: 5000
**Completion Target**: 30 minutes

_This is a quick fix to unblock the two-phase CI architecture implementation._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
