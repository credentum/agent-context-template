# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1683-[sprint-4.3]-fix-local-docker-ci-to-match-github-a
# Generated from GitHub Issue #1683
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1683-[sprint-4.3]-fix-local-docker-ci-to-match-github-a`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.3] Fix Local Docker CI to Match GitHub Actions Checks

## 🧠 Context
- **GitHub Issue**: #1683 - [SPRINT-4.3] Fix Local Docker CI to Match GitHub Actions Checks
- **Labels**: bug, sprint-current, claude-ready
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

**Investigation Notes**: Root causes have been identified through analysis of PR #1682 review failures

## Acceptance Criteria
- [ ] Docker CI catches all formatting issues that GitHub Actions catches
- [ ] Pre-commit hooks run successfully within Claude's 2-minute timeout
- [ ] MyPy configuration no longer causes "source file found twice" errors
- [ ] Quick CI mode available for rapid developer feedback
- [ ] Clear progress indicators show which checks are running
- [ ] Documentation updated with CI best practices and timeout guidance

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (PR #1682, test-comprehensive-ci.sh)
- [x] **File scope estimated** (< 6 files, < 200 LoC expected)
- [x] **Dependencies mapped** (Docker, pre-commit, mypy, black, isort)
- [x] **Test strategy defined** (manual verification against known issues)
- [x] **Breaking change assessment** (backward compatible, adds new options)

## Pre-Execution Context
**Key Files**: 
- `scripts/run-ci-docker.sh`
- `scripts/test-comprehensive-ci.sh`
- `mypy.ini`
- `.pre-commit-config.yaml`
- `docker-compose.ci.yml`

**External Dependencies**: Docker, Docker Compose, pre-commit framework
**Configuration**: CI timeout settings, tool execution order
**Related Issues/PRs**: #1681, #1682

## Implementation Notes
### Root Cause Analysis
1. **Timeout Issue**: Docker CI terminated after 2 minutes due to Claude's tool timeout, not Docker's 12-minute limit
2. **Check Order**: Pre-commit hooks (section 7) never ran because timeout occurred during MyPy checks (section 1)
3. **Missing Checks**: Pre-commit includes additional checks (trailing-whitespace, end-of-file-fixer) not in individual tool runs
4. **MyPy Config**: `mypy_path = scripts` causes duplicate module discovery

### Solution Approach
1. **Split CI Commands**: Create focused commands that complete within timeout
   - `lint` - Black, isort, Flake8
   - `typecheck` - MyPy only
   - `pre-commit` - Pre-commit hooks only
   - `quick` - Essential checks only
2. **Reorder Checks**: Move pre-commit to run first as it includes most other checks
3. **Fix MyPy**: Remove `mypy_path` or add `--explicit-package-bases`
4. **Add Progress**: Show section numbers and time estimates
5. **Update Docs**: Add timeout guidance to CLAUDE.md

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: ~5000 tokens
**Completion Target**: 30-45 minutes

_This issue will be updated during Claude Code execution with progress and results._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
