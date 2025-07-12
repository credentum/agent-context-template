# Test Coverage Guide

## Overview

This guide documents the comprehensive test coverage framework implemented for the Agent-First Context System, targeting the following metrics:

| Coverage Metric | Target | Purpose |
|-----------------|--------|---------|
| Line coverage | ≥ 85% | Ensures all logic paths are exercised |
| Branch coverage | ≥ 70% | Catches if-else conditions and switch logic |
| Mutation score | ≥ 80% | Guarantees tests actually assert, not just execute |
| Test case traceability | 100% for critical functions | Each agent behavior maps to test scenarios |
| Reproducibility via trace | ✅ Required | Rebuilding from hash passes all audit checkpoints |

## Current Coverage Status

### Coverage Progress Bar
```
Current: 59.53% [████████████░░░░░░░░░░░░] Target: 85%
                 ^^^^^^^^^^^^^^^^^^^^^^^^
                 25.47% remaining
```

### Overall Metrics
| Metric | Current | Target | Status | Gap |
|--------|---------|--------|--------|-----|
| **Line Coverage** | 59.53% | ≥ 85% | 🔴 Below Target | 25.47% |
| **Branch Coverage** | ~45% | ≥ 70% | 🔴 Below Target | ~25% |
| **Mutation Score** | TBD | ≥ 80% | ⚠️ Not Measured | - |
| **Statements** | 3446 | - | - | - |
| **Missing** | 1206 | - | - | - |

### Module Coverage Breakdown
| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `storage/hash_diff_embedder_async.py` | 95.35% | ✅ Exceeds Target | - |
| `analytics/sum_scores_api.py` | 89.68% | ✅ Exceeds Target | - |
| `core/utils.py` | 88.89% | ✅ Exceeds Target | - |
| `storage/neo4j_init.py` | 86.49% | ✅ Exceeds Target | - |
| `agents/update_sprint.py` | 77.66% | 🟡 Near Target | Medium |
| `agents/cleanup_agent.py` | 73.78% | 🟡 Near Target | Medium |
| `core/base_component.py` | 72.48% | 🟡 Near Target | Medium |
| `agents/sprint_issue_linker.py` | 71.69% | 🟡 Near Target | Medium |
| `storage/context_kv.py` | 55.91% | 🔴 Below Target | High |
| `integrations/graphrag_integration.py` | 51.17% | 🔴 Below Target | High |
| `storage/hash_diff_embedder.py` | 49.26% | 🔴 Below Target | High |
| `storage/graph_builder.py` | 48.59% | 🔴 Below Target | High |
| `agents/context_lint.py` | 45.05% | 🔴 Below Target | High |
| `storage/vector_db_init.py` | 36.14% | 🔴 Critical | Critical |
| `analytics/context_analytics.py` | 35.62% | 🔴 Critical | Critical |
| `validators/config_validator.py` | 34.66% | 🔴 Critical | Critical |
| `validators/kv_validators.py` | 33.64% | 🔴 Critical | Critical |

### Progress Tracking
- **Initial Baseline** (July 2025): ~30% overall coverage
- **Current Status**: 59.53% overall coverage
- **Improvement**: +29.53% (98.43% increase)
- **Remaining Gap**: 25.47% to reach 85% target

### Recent Improvements
1. **hash_diff_embedder_async.py**: 0% → 95.35% ✅
2. **sum_scores_api.py**: 32.09% → 89.68% ✅
3. **neo4j_init.py**: 31.27% → 86.49% ✅

### Coverage Improvement Roadmap

#### Phase 1: Critical Modules (Current Priority)
Target: Bring critical modules from <40% to >70%
- [ ] `validators/kv_validators.py` (33.64% → 70%)
- [ ] `validators/config_validator.py` (34.66% → 70%)
- [ ] `analytics/context_analytics.py` (35.62% → 70%)
- [ ] `storage/vector_db_init.py` (36.14% → 70%)

#### Phase 2: High Priority Modules
Target: Bring modules from 45-55% to >75%
- [ ] `agents/context_lint.py` (45.05% → 75%)
- [ ] `storage/graph_builder.py` (48.59% → 75%)
- [ ] `storage/hash_diff_embedder.py` (49.26% → 75%)
- [ ] `integrations/graphrag_integration.py` (51.17% → 75%)
- [ ] `storage/context_kv.py` (55.91% → 75%)

#### Phase 3: Final Push to Target
Target: Achieve overall 85% line coverage
- [ ] Complete remaining gaps in Phase 1 & 2 modules
- [ ] Improve medium priority modules to >80%
- [ ] Add integration tests for cross-module functionality
- [ ] Implement mutation testing baseline

### Estimated Timeline
- **Phase 1**: 2-3 weeks (4 modules × 3-5 days each)
- **Phase 2**: 3-4 weeks (5 modules × 3-4 days each)
- **Phase 3**: 2 weeks (cleanup and integration)
- **Total**: 7-9 weeks to reach 85% coverage target

## Configuration

### Coverage Configuration

The project uses both `.coveragerc` and `pyproject.toml` for coverage configuration:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
parallel = true

[tool.coverage.report]
precision = 2
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "@abstractmethod"
]
```

### Mutation Testing Configuration

Mutation testing is configured in `pyproject.toml`:

```toml
[tool.mutmut]
paths_to_mutate = "src/"
runner = "python -m pytest -x -q"
tests_dir = "tests/"
```

## Running Coverage Analysis

### 1. Basic Coverage Report

```bash
# Run tests with coverage
python -m pytest --cov=src --cov-branch --cov-report=term-missing

# Generate HTML report
python -m pytest --cov=src --cov-branch --cov-report=html
```

### 2. Comprehensive Coverage Script

```bash
# Run full coverage analysis with threshold checks
./scripts/run_coverage.sh
```

This script:
- Runs tests with branch coverage
- Generates multiple report formats (HTML, XML, JSON)
- Checks against coverage thresholds
- Provides detailed feedback on missing coverage

### 3. Mutation Testing

```bash
# Run mutation testing on critical modules
./scripts/run_mutation_testing.sh

# Run on specific module
mutmut run --paths-to-mutate="src/agents/cleanup_agent.py"
```

### 4. Coverage Summary

```bash
# Generate comprehensive coverage summary
python scripts/coverage_summary.py
```

## Test Organization

### Critical Function Tests

Tests for critical functions are organized in dedicated coverage modules:

- `tests/test_cleanup_agent_coverage.py` - CleanupAgent comprehensive tests
- `tests/test_update_sprint_coverage.py` - SprintUpdater comprehensive tests
- `tests/test_sprint_issue_linker_coverage.py` - SprintIssueLinker tests
- `tests/test_context_kv_coverage.py` - Redis storage layer tests

### Test Traceability Matrix

The traceability matrix (`tests/test_traceability_matrix.py`) maps:
- Critical functions to test cases
- Test cases to requirements
- Ensures 100% coverage of critical paths

Example:
```python
CRITICAL_FUNCTIONS = {
    "src.agents.cleanup_agent.CleanupAgent._is_expired": {
        "description": "Determines if documents/sprints should be archived",
        "test_cases": [
            "test_cleanup_agent_coverage.py::test_is_expired_document",
            "test_cleanup_agent_coverage.py::test_is_expired_sprint"
        ],
        "requirements": ["REQ-CLEANUP-001", "REQ-CLEANUP-002"]
    }
}
```

### Reproducibility Tests

The reproducibility tests (`tests/test_reproducibility.py`) ensure:
- Document hashes are deterministic
- System state can be snapshot and restored
- Audit checkpoints can be validated
- Changes can be tracked via hash chains

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/test-coverage.yml` workflow:
1. Runs tests with coverage on every PR
2. Checks coverage thresholds
3. Runs sample mutation testing
4. Uploads coverage reports
5. Comments on PRs with coverage changes

### Pre-commit Hooks

Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: test-coverage
      name: Check test coverage
      entry: python -m pytest --cov=src --cov-fail-under=85
      language: system
      pass_filenames: false
      always_run: true
```

## Best Practices

### 1. Writing Testable Code

- Keep functions small and focused
- Minimize side effects
- Use dependency injection
- Avoid global state

### 2. Test Structure

```python
class TestComponent:
    """Tests for Component"""

    def test_normal_operation(self):
        """Test happy path"""
        pass

    def test_edge_cases(self):
        """Test boundary conditions"""
        pass

    def test_error_handling(self):
        """Test failure scenarios"""
        pass
```

### 3. Coverage Improvements

When coverage is below target:

1. Run with `--cov-report=term-missing` to see uncovered lines
2. Focus on:
   - Error handling paths
   - Edge cases
   - Branch conditions
   - Loop variations

### 4. Mutation Testing

To improve mutation score:
- Ensure tests have assertions
- Test return values
- Verify side effects
- Check boundary conditions

## Monitoring Coverage

### Local Development

```bash
# Quick coverage check
pytest --cov=src --cov-report=term

# Detailed HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### CI Reports

- Coverage reports are uploaded as artifacts
- Codecov integration provides trends
- PR comments show coverage changes

## Troubleshooting

### Common Issues

1. **Low Branch Coverage**
   - Add tests for all if/else branches
   - Test loop conditions (0, 1, many)
   - Cover exception handlers

2. **Surviving Mutations**
   - Add more specific assertions
   - Test edge cases
   - Verify state changes

3. **Flaky Tests**
   - Mock external dependencies
   - Use fixed timestamps
   - Control randomness with seeds

### Debug Commands

```bash
# Show specific file coverage
coverage report -m src/agents/cleanup_agent.py

# Run single test with coverage
pytest tests/test_cleanup_agent.py::test_specific -cov=src.agents.cleanup_agent

# Show mutation testing details
mutmut show 47  # Show mutation #47
```
