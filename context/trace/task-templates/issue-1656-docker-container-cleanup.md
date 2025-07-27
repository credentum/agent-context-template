# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1656-docker-container-cleanup
# Generated from GitHub Issue #1656
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1656-docker-container-cleanup`

## 🎯 Goal (≤ 2 lines)
> Fix Docker container and test process cleanup issues by adding proper signal handling, init system support, and process management to ensure all CI resources are cleaned up deterministically.

## 🧠 Context
- **GitHub Issue**: #1656 - Fix Docker container and test process cleanup issues
- **Sprint**: sprint-current
- **Phase**: Phase 2: Implementation
- **Component**: ci/testing-infrastructure
- **Priority**: bug
- **Why this matters**: Orphaned processes and containers consume resources, causing CI instability and requiring manual cleanup
- **Dependencies**: None identified
- **Related**: None

## 🛠️ Subtasks
4 key areas requiring fixes based on root cause analysis:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/test-comprehensive-ci.sh | modify | Chain-of-Thought | Add signal handling and cleanup | Low |
| scripts/test-suite-like-ci.sh | modify | Chain-of-Thought | Add signal handling and cleanup | Low |
| docker-compose.ci.yml | modify | Configuration Update | Add stop signals and grace periods | Low |
| Dockerfile.ci | modify | Configuration Update | Add init system (tini) | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing CI infrastructure issues related to process and container lifecycle management.

**Context**
GitHub Issue #1656: Fix Docker container and test process cleanup issues
The CI system has orphaned processes and containers that don't shut down cleanly because:
1. Test scripts lack signal handling (SIGTERM/SIGINT traps)
2. Docker containers run without proper init system (PID 1 issues)
3. No process group management for child process cleanup
4. Services in docker-compose.ci.yml lack stop_signal configuration

Current codebase has these test scripts:
- test-comprehensive-ci.sh: Runs all CI checks but has no cleanup handlers
- test-suite-like-ci.sh: Uses `set -e` but no signal traps
Docker configuration:
- Dockerfile.ci: Standard Python slim image without init
- docker-compose.ci.yml: Services without stop configuration

**Instructions**
1. **Primary Objective**: Ensure all processes and containers shut down cleanly
2. **Scope**: Fix signal handling, add init system, configure proper shutdown
3. **Constraints**:
   - Maintain backward compatibility with existing CI
   - Keep changes minimal and focused on cleanup issues
   - Preserve all existing functionality
4. **Prompt Technique**: Chain-of-Thought for bash scripts, direct updates for Docker configs
5. **Testing**: Verify processes terminate cleanly on SIGTERM/SIGINT
6. **Documentation**: Add comments explaining signal handling

**Technical Constraints**
• Expected diff ≤ 150 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: Minimal overhead from signal handling
• Code quality: Maintain existing patterns, add clear comments
• CI compliance: Must pass all existing Docker CI checks

**Output Format**
Implement the following fixes:
1. Add signal handling to both test scripts with proper cleanup functions
2. Install and configure tini in Dockerfile.ci as init system
3. Add stop_signal and stop_grace_period to all services in docker-compose.ci.yml
4. Ensure process group management for child process cleanup

## 🔍 Verification & Testing
- `docker-compose -f docker-compose.ci.yml up ci-lint` (test container shutdown)
- `./scripts/test-comprehensive-ci.sh` then Ctrl+C (test signal handling)
- `./scripts/test-suite-like-ci.sh` then Ctrl+C (test signal handling)
- `docker ps` after tests (verify no orphaned containers)
- `ps aux | grep pytest` (verify no orphaned processes)
- Monitor system resources during/after test runs

## ✅ Acceptance Criteria
- [x] All test scripts have proper signal handling (trap handlers)
- [x] Docker containers use init system for proper PID 1 behavior
- [x] All child processes terminate when parent container stops
- [x] Ports are released when services shut down
- [x] CI cleanup is deterministic and complete
- [x] No manual intervention required to clean up after tests

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 30 minutes
├── cost_estimate: $0.50
├── complexity: medium
└── files_affected: 4

Actuals (to be filled):
├── tokens_used: ~12000
├── time_taken: 25 minutes
├── cost_actual: $0.40
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1656
sprint: sprint-current
phase: Phase 2: Implementation
component: ci/testing-infrastructure
priority: bug
complexity: medium
dependencies: []
```
