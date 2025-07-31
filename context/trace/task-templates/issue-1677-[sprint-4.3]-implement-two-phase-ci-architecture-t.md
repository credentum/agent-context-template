# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1677-[sprint-4.3]-implement-two-phase-ci-architecture-t
# Generated from GitHub Issue #1677
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1677-[sprint-4.3]-implement-two-phase-ci-architecture-t`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.3] Implement two-phase CI architecture to run ARC reviewer with LLM mode outside Docker

## 🧠 Context
- **GitHub Issue**: #1677 - [SPRINT-4.3] Implement two-phase CI architecture to run ARC reviewer with LLM mode outside Docker
- **Labels**: sprint-current, component:ci
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

**Investigation Notes**: N/A - OAuth token is automatically available in Claude Code sessions

## Acceptance Criteria
- [ ] Docker CI runs all tests and generates coverage artifacts without running ARC reviewer
- [ ] Coverage files (coverage.json, coverage.xml) are accessible from host after Docker run
- [ ] ARC reviewer can be run separately in Claude Code session with --llm flag
- [ ] LLM mode works with CLAUDE_CODE_OAUTH_TOKEN from the session
- [ ] Documentation updated to reflect new two-phase workflow

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (docs, specs, related PRs)
- [x] **File scope estimated** (< 4 files, < 400 LoC expected)
- [x] **Dependencies mapped** (external APIs, config, other services)
- [x] **Test strategy defined** (unit, integration, edge cases)
- [x] **Breaking change assessment** (backward compatibility)

## Pre-Execution Context
**Key Files**: 
- `docker-compose.ci.yml`
- `scripts/test-comprehensive-ci.sh`
- `scripts/run-ci-docker.sh`
- `src/agents/arc_reviewer.py`
- `src/agents/llm_reviewer.py`

**External Dependencies**:
- Docker/Docker Compose
- anthropic package (>=0.8.0)
- CLAUDE_CODE_OAUTH_TOKEN (automatically available in Claude Code)

**Configuration**: 
- Coverage output paths in pyproject.toml
- Docker volume mounts for test artifacts

**Related Issues/PRs**: 
- #1673 (Fix ARC reviewer LLM mode)
- #1675 (PR for fixing ARC reviewer)

## Implementation Notes
### Architecture Overview
Split CI workflow into two phases:
1. **Phase 1 (Docker)**: Run all tests, linting, type checking, coverage generation
2. **Phase 2 (Claude Code)**: Run ARC reviewer with LLM mode using session's OAuth token

### Key Changes Needed
1. **Docker Volume Mount**: Add volume in docker-compose.ci.yml to share test artifacts
   ```yaml
   volumes:
     - ./test-artifacts:/app/test-artifacts
   ```

2. **Update Test Scripts**: Modify scripts to output coverage to shared directory
   - coverage.json → test-artifacts/coverage.json
   - coverage.xml → test-artifacts/coverage.xml

3. **Create Two-Phase Script**: New script to orchestrate the workflow
   ```bash
   # Phase 1: Run Docker tests
   ./scripts/run-ci-docker.sh --no-arc-reviewer
   
   # Phase 2: Run ARC reviewer in Claude Code
   python -m src.agents.arc_reviewer --llm --coverage-file test-artifacts/coverage.json
   ```

4. **Fix Import Issues**: Ensure llm_reviewer.py properly imports anthropic package

### Benefits
- OAuth token stays secure in Claude Code environment
- No need to pass sensitive tokens to Docker
- Enables full LLM-powered code reviews
- Maintains test isolation and reproducibility

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: 15000
**Completion Target**: 1-2 hours

_This issue will be updated during Claude Code execution with progress and results._

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
