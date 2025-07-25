# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1377-test-load-monitoring
# Generated from GitHub Issue #1377
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1377-test-load-monitoring-throttling`

## 🎯 Goal (≤ 2 lines)
> Implement system load monitoring and automatic test throttling for CI pipeline to prevent server overload during test execution.

## 🧠 Context
- **GitHub Issue**: #1377 - Implement Test Load Monitoring and Throttling for CI Pipeline
- **Sprint**: sprint-4.1
- **Phase**: Phase 2: Implementation
- **Component**: ci-cd
- **Priority**: high (server stability critical)
- **Why this matters**: Server became unresponsive with load 25+ due to unthrottled pytest processes
- **Dependencies**: Issue #1303 (CI pipeline fixes), PR #1376 (local CI improvements)
- **Related**: CI optimization Phase 4 (#1293)

## 🛠️ Subtasks
Based on issue requirements and server stability needs:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/load-monitor.sh | create | Sequential Steps | Check system load/resources | Low |
| scripts/safe-test-runner.sh | create | Problem-Solution | Wrap pytest with monitoring | Medium |
| scripts/claude-ci.sh | modify | Targeted Patch | Add load checks to test command | Medium |
| scripts/claude-test-changed.sh | modify | Targeted Patch | Use safe runner for pytest | Low |
| scripts/run-ci-docker.sh | modify | Targeted Patch | Add container resource limits | Low |
| tests/test_load_monitoring.py | create | TDD | Test load monitoring logic | Low |
| CLAUDE.md | modify | Documentation | Document load management | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer implementing resource protection for CI systems.

**Context**
GitHub Issue #1377: Implement Test Load Monitoring and Throttling
- Server reached load 25+ and became unresponsive during CI test runs
- Multiple pytest processes run without resource limits
- Timeout kills parent but orphans child processes
- Need automatic throttling based on system load

Current environment:
- Scripts use bash with standard Unix tools (uptime, ps, kill, nice)
- pytest supports -n flag for worker control
- CI runs via claude-ci.sh orchestrator

**Instructions**
1. **Primary Objective**: Prevent server overload during CI test runs
2. **Scope**:
   - Monitor load before/during tests
   - Throttle pytest workers dynamically
   - Clean up orphaned processes
   - Integrate seamlessly with existing CI
3. **Constraints**:
   - Backward compatible (opt-out via env vars)
   - Default max load: 8
   - Maintain test coverage
   - Work in Docker and bare metal
4. **Prompt Technique**: Sequential implementation with clear integration points
5. **Testing**: Unit tests for monitoring, integration tests for throttling
6. **Documentation**: Update CLAUDE.md with load management section

**Technical Constraints**
• Expected diff ≤ 300 LoC, ≤ 6 files
• Context budget: ≤ 20k tokens
• Performance budget: <1s overhead for load checks
• Code quality: shellcheck compliance, pytest coverage
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation with:
- Load monitoring script with configurable thresholds
- Safe test runner with dynamic worker allocation
- Integration patches for existing scripts
- Tests and documentation updates
Use conventional commits: fix(ci): implement test load monitoring and throttling

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `shellcheck scripts/*.sh` (bash script quality)
- `pytest tests/test_load_monitoring.py -v` (unit tests)
- **Load testing**: Simulate high load and verify throttling
- **Process cleanup**: Verify no orphaned processes after timeout
- **Integration**: Run full CI with monitoring enabled

## ✅ Acceptance Criteria
From issue #1377:
- [X] Monitor system load before and during test execution
- [X] Implement automatic test throttling when load exceeds threshold
- [X] Add process cleanup for timed-out test runs
- [X] Integrate with existing claude-ci.sh and test runners
- [X] Maintain full test coverage while preventing server overload
- [X] Add configurable load thresholds (default: max load 8)
- [X] Document load management in CLAUDE.md

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 20000
├── time_budget: 1-2 hours
├── cost_estimate: $0.30-0.60
├── complexity: medium
└── files_affected: 6

Actuals (completed):
├── tokens_used: ~18000 (within budget)
├── time_taken: ~90 minutes
├── cost_actual: ~$0.27
├── iterations_needed: 3 (initial + 2 fix rounds)
└── context_clears: 0 (stayed within limits)
```

## 🏷️ Metadata
```yaml
github_issue: 1377
sprint: sprint-4.1
phase: "Phase 2: Implementation"
component: ci-cd
priority: high
complexity: medium
dependencies: [1303, 1376]
```
