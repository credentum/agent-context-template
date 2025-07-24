# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1293-ci-migration-phase-4-optimization
# Generated from GitHub Issue #1293
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1293-ci-migration-phase-4-optimization`

## 🎯 Goal (≤ 2 lines)
> Implement CI optimization and advanced features including caching, distributed execution, incremental builds, GPU support, and analytics dashboard for Phase 4 of CI migration.

## 🧠 Context
- **GitHub Issue**: #1293 - [SPRINT-4.3] CI Migration Phase 4: Optimization & Advanced Features
- **Sprint**: sprint-4.3
- **Phase**: Phase 4.1: Infrastructure Evolution
- **Component**: ci-workflows
- **Priority**: medium
- **Why this matters**: Complete the CI migration with performance optimizations and advanced features to achieve >50% execution time reduction
- **Dependencies**: Phases 1-3 completed (#1257, #1291, #1292), caching systems, distributed computing infrastructure
- **Related**: Previous CI migration phases, performance benchmarking requirements

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/ci-cache-manager.py | create | Implementation | Content-addressable cache for dependencies | Medium |
| scripts/distributed-ci-coordinator.py | create | Implementation | Job scheduling across multiple runners | High |
| scripts/incremental-build-analyzer.py | create | Implementation | Dependency graph analysis for incremental builds | Medium |
| config/ci-optimization.yaml | create | Configuration | Central config for all optimization features | Low |
| dashboards/ci-analytics/* | create | Implementation | Performance monitoring dashboard | Medium |
| scripts/ci-hardware-detector.py | create | Implementation | GPU and specialized hardware detection | Low |
| docs/ci-optimization-guide.md | create | Documentation | User guide for optimization features | Low |
| .github/workflows/ci-unified.yml | modify | Enhancement | Add optimization features to main CI | Medium |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD optimization and distributed systems.

**Context**
GitHub Issue #1293: CI Migration Phase 4 - Optimization & Advanced Features
This is the final phase of a 4-phase CI migration project. Phases 1-3 have established local CI execution, git hooks, and full migration infrastructure. Phase 4 focuses on advanced performance optimizations.
Current codebase follows Python patterns with async support, Docker-based CI, and comprehensive testing.
Related files: Previous phase implementations in scripts/, existing CI workflows in .github/workflows/

**Instructions**
1. **Primary Objective**: Implement advanced CI optimization features to reduce execution time by >50%
2. **Scope**: Add caching, distributed execution, incremental builds, GPU support, and analytics while maintaining backward compatibility
3. **Constraints**:
   - Follow existing code patterns: Python 3.11+ with async, type hints, comprehensive testing
   - Maintain backward compatibility - all features must be opt-in
   - Keep public APIs unchanged unless specified in issue requirements
4. **Prompt Technique**: Implementation with architectural design because task involves complex system integration
5. **Testing**: Performance benchmarks, load tests, distributed execution validation
6. **Documentation**: Comprehensive guide for optimization features and migration

**Technical Constraints**
• Expected diff ≤ 2000 LoC, ≤ 15 files
• Context budget: ≤ 50k tokens
• Performance budget: >50% execution time reduction
• Code quality: Black formatting, coverage ≥ 78.0%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: feat(ci): implement advanced optimization features

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Performance benchmarks showing >50% improvement
- **Integration tests**: Distributed CI coordination, caching effectiveness
- **Load tests**: Multiple concurrent jobs, cache hit rates
- **Hardware tests**: GPU detection and job routing

## ✅ Acceptance Criteria
- [ ] Local CI caching reduces execution time by >50%
- [ ] Distributed CI across multiple machines functional
- [ ] Incremental builds working for all languages
- [ ] GPU/specialized hardware support implemented
- [ ] CI analytics dashboard deployed
- [ ] Performance benchmarks documented
- [ ] Advanced features opt-in (not breaking existing)

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 50,000 (complex system integration)
├── time_budget: 2-3 weeks (distributed systems complexity)
├── cost_estimate: $150-200 (high token usage)
├── complexity: Very High (multiple new systems)
└── files_affected: 15 (new optimization infrastructure)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1293
sprint: sprint-4.3
phase: 4.1
component: ci-workflows
priority: medium
complexity: very_high
dependencies: [1257, 1291, 1292]
```
