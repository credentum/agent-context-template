# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1702-[sprint-4.2]-fix-docker-ci-read-only-filesystem-an
# Generated from GitHub Issue #1702
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1702-[sprint-4.2]-fix-docker-ci-read-only-filesystem-an`

## 🎯 Goal (≤ 2 lines)
> [SPRINT-4.2] Fix Docker CI read-only filesystem and pre-commit hook failures

## 🧠 Context
- **GitHub Issue**: #1702 - [SPRINT-4.2] Fix Docker CI read-only filesystem and pre-commit hook failures
- **Labels**: bug, sprint-current, claude-ready
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Task Context
**Sprint**: sprint-4-2
**Phase**: Phase 3: Bug Fix & CI Improvement
**Component**: ci-infrastructure

## Scope Assessment
- [x] **Scope is clear** - Requirements are well-defined, proceed with implementation

## Problem Description
During CI execution in Docker containers, pre-commit hooks fail with read-only filesystem errors:
- `OSError: [Errno 30] Read-only file system` when trying to write to `.github/workflows/` and other files
- Pre-commit hooks `trailing-whitespace` and `end-of-file-fixer` cannot modify files
- This prevents successful CI validation even when code is properly formatted

## Acceptance Criteria
- [ ] Docker CI can run pre-commit hooks without read-only filesystem errors
- [ ] All formatting checks pass in Docker environment (Black, isort, flake8)
- [ ] Pre-commit hooks can auto-fix issues when running in CI mode
- [ ] CI maintains security by not allowing arbitrary writes to critical files
- [ ] Solution works for both `run-ci-docker.sh` and `run-two-phase-ci.sh`

## Claude Code Readiness Checklist
- [x] **Context URLs identified** (Docker compose files, CI scripts)
- [x] **File scope estimated** (< 4 files: docker-compose.ci.yml, Dockerfile.ci, run-ci-docker.sh)
- [x] **Dependencies mapped** (Docker volumes, pre-commit configuration)
- [x] **Test strategy defined** (Run CI checks to verify fixes)
- [x] **Breaking change assessment** (No breaking changes, only CI improvements)

## Pre-Execution Context
**Key Files**: 
- `docker-compose.ci.yml` - Docker CI service configurations
- `Dockerfile.ci` - CI container image definition
- `scripts/run-ci-docker.sh` - CI runner script
- `.pre-commit-config.yaml` - Pre-commit hook configuration

**External Dependencies**: 
- Docker volume mounts
- Pre-commit framework

**Configuration**: 
- Volume mount permissions in docker-compose.ci.yml
- Pre-commit hook configurations

**Related Issues/PRs**: 
- This issue discovered during workflow-issue --hybrid for issue 993
- Affects all CI runs in Docker environment

## Implementation Notes
### Root Cause
The docker-compose.ci.yml mounts several directories as read-only:
```yaml
- ./.github:/app/.github:ro
- ./mypy.ini:/app/mypy.ini:ro
- ./pyproject.toml:/app/pyproject.toml:ro
- ./.pre-commit-config.yaml:/app/.pre-commit-config.yaml:ro
```

### Proposed Solutions
1. **Option A**: Create a writable overlay for pre-commit operations
   - Mount source as read-only
   - Create writable temp directory
   - Copy files needing modification
   - Run pre-commit on copies

2. **Option B**: Add pre-commit skip flag for CI
   - Skip auto-fixing hooks in CI
   - Only run validation hooks
   - Separate fix vs check modes

3. **Option C**: Adjust volume mounts
   - Make specific directories writable during pre-commit
   - Add security controls to limit write scope
   - Restore read-only after pre-commit phase

### Recommendation
Implement Option A with writable overlay to maintain security while allowing pre-commit to function properly.

---

## Claude Code Execution
**Session Started**: <\!-- timestamp -->
**Task Template Created**: <\!-- link to generated template -->
**Token Budget**: Medium (focused CI configuration changes)
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
