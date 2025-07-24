# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1334-fix-phase-4-ci-optimization-runtime-failures
# Generated from GitHub Issue #1334
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1334-phase-4-ci-optimization-runtime-failures`

## 🎯 Goal (≤ 2 lines)
> Fix runtime failures in Phase 4 CI optimization scripts (hardware detector, incremental build analyzer) and enhance local ARC reviewer to catch runtime errors during development.

## 🧠 Context
- **GitHub Issue**: #1334 - [SPRINT-4.3] Fix Phase 4 CI Optimization Script Runtime Failures
- **Sprint**: sprint-4.3
- **Phase**: Phase 4.2: Bug Fixes & Stabilization
- **Component**: ci-workflows
- **Priority**: CRITICAL (blocking PR #1301 and Phase 4 completion)
- **Why this matters**: CI optimization scripts are failing at runtime in GitHub Actions but pass local static analysis
- **Dependencies**: argparse, subprocess, dataclasses for script fixes
- **Related**: PR #1301 (merged), issues #1293, #1303

## 🛠️ Subtasks
Based on the four critical runtime failures identified:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/ci_hardware_detector.py | modify | Chain-of-Thought | Fix command line parsing to require subcommand | High |
| scripts/incremental_build_analyzer.py | modify | Few-Shot | Fix set/list conversion in dataclasses | High |
| src/agents/arc_reviewer.py | modify | Chain-of-Thought | Add runtime validation capability | High |
| tests/test_bidirectional_sync.py | modify | Direct Fix | Fix sync test assertion failure | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer fixing critical CI pipeline runtime failures in Python scripts.

**Context**
GitHub Issue #1334: Phase 4 CI optimization scripts are failing at runtime in GitHub Actions:
1. Hardware detector: `error: unrecognized arguments: --output` - missing required subcommand
2. Incremental build analyzer: `AttributeError: 'list' object has no attribute 'add'` - set/list conversion issue
3. Local ARC reviewer: Only does static analysis, missing runtime validation
4. Bidirectional sync test: `AssertionError: Sync should not try to create issue #116 again`

Current codebase uses argparse for CLI, dataclasses for data structures, subprocess for git operations.
Related files: scripts/ci_hardware_detector.py, scripts/incremental_build_analyzer.py, src/agents/arc_reviewer.py, tests/test_bidirectional_sync.py

**Instructions**
1. **Primary Objective**: Fix all four runtime failures to unblock CI pipeline
2. **Scope**:
   - Hardware detector: Ensure all call sites use correct subcommand syntax
   - Build analyzer: Separate JSON serialization from runtime data structures
   - ARC reviewer: Add runtime testing capability to catch errors locally
   - Sync test: Fix logic or update test expectations
3. **Constraints**:
   - Maintain backward compatibility
   - Follow existing argparse patterns for CLI
   - Keep dataclass structures but fix serialization
   - Ensure fixes work in both local and GitHub Actions environments
4. **Prompt Technique**: Chain-of-Thought for complex logic, Few-Shot for pattern fixes
5. **Testing**: Each fix must include runtime validation
6. **Documentation**: Update help text and docstrings where changed

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 4 files
• Context budget: ≤ 20k tokens
• Performance budget: Scripts must complete in < 30 seconds
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation fixing all four runtime issues.
Use conventional commits: fix(ci): fix Phase 4 CI optimization runtime failures

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - `python scripts/ci_hardware_detector.py detect --output /tmp/test.json` (verify subcommand works)
  - `python scripts/incremental_build_analyzer.py analyze --git-diff HEAD~1` (verify no set/list errors)
  - `python -m src.agents.arc_reviewer --runtime-test` (verify runtime validation)
  - `pytest tests/test_bidirectional_sync.py -v` (verify sync test passes)
- **Integration tests**: Full CI pipeline execution

## ✅ Acceptance Criteria
- [ ] Hardware detector script executes without command line parsing errors
- [ ] Incremental build analyzer completes scan without crashing
- [ ] Local ARC reviewer enhanced to catch runtime failures during development
- [ ] All Phase 4 optimization scripts pass end-to-end runtime testing
- [ ] CI pipeline executes successfully with optimization features enabled
- [ ] Bidirectional sync test failure resolved (blocking unrelated feature)

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 20000
├── time_budget: 4-6 hours
├── cost_estimate: $2.50
├── complexity: HIGH (4 interconnected failures)
└── files_affected: 4

Actuals (to be filled):
├── tokens_used: ~18000
├── time_taken: 1 hour 15 minutes
├── cost_actual: $2.25
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1334
sprint: sprint-4.3
phase: Phase 4.2
component: ci-workflows
priority: CRITICAL
complexity: HIGH
dependencies: [argparse, subprocess, dataclasses]
```
