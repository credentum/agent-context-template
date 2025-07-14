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
Current: 75.66% [███████████████░░░░░░░░] Target: 85%
                 ^^^^^^^^^^^^^^^^
                 9.34% remaining
```

### Overall Metrics
| Metric | Current | Target | Status | Gap |
|--------|---------|--------|--------|-----|
| **Line Coverage** | 75.66% | ≥ 85% | 🟡 Near Target | 9.34% |
| **Branch Coverage** | ~45% | ≥ 70% | 🔴 Below Target | ~25% |
| **Mutation Score** | TBD | ≥ 80% | ⚠️ Not Measured | - |
| **Statements** | 3572 | - | - | - |
| **Missing** | 750 | - | - | - |

### Module Coverage Breakdown
| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `validators/kv_validators.py` | 100.00% | ✅ Exceeds Target | - |
| `storage/vector_db_init.py` | 97.59% | ✅ Exceeds Target | - |
| `validators/config_validator.py` | 97.51% | ✅ Exceeds Target | - |
| `storage/graph_builder.py` | 95.63% | ✅ Exceeds Target | - |
| `storage/hash_diff_embedder_async.py` | 95.35% | ✅ Exceeds Target | - |
| `analytics/sum_scores_api.py` | 89.68% | ✅ Exceeds Target | - |
| `core/utils.py` | 88.89% | ✅ Exceeds Target | - |
| `storage/neo4j_init.py` | 86.49% | ✅ Exceeds Target | - |
| `agents/context_lint.py` | 84.68% | ✅ Near Target | - |
| `analytics/context_analytics.py` | 82.19% | 🟡 Near Target | Low |
| `agents/update_sprint.py` | 76.84% | 🟡 Near Target | Medium |
| `core/base_component.py` | 72.48% | 🟡 Near Target | Medium |
| `agents/sprint_issue_linker.py` | 71.69% | 🟡 Near Target | Medium |
| `agents/cleanup_agent.py` | 69.78% | 🟡 Below Target | Medium |
| `storage/hash_diff_embedder.py` | 95.59% | ✅ Exceeds Target | - |
| `storage/context_kv.py` | 57.51% | 🔴 Below Target | High |
| `integrations/graphrag_integration.py` | 51.17% | 🔴 Below Target | High |

### Progress Tracking
- **Initial Baseline** (July 2025): ~30% overall coverage
- **Current Status**: 75.66% overall coverage
- **Improvement**: +45.66% (152.20% increase)
- **Remaining Gap**: 9.34% to reach 85% target

### Recent Improvements

#### Phase 1 Completion (✅ COMPLETE)
Critical modules successfully improved to >70% line coverage:
1. **validators/kv_validators.py**: 33.64% → 100.00% ✅
2. **validators/config_validator.py**: 34.66% → 97.51% ✅
3. **analytics/context_analytics.py**: 35.62% → 82.19% ✅
4. **storage/vector_db_init.py**: 36.14% → 97.59% ✅
5. **hash_diff_embedder_async.py**: 0% → 95.35% ✅
6. **sum_scores_api.py**: 32.09% → 89.68% ✅
7. **neo4j_init.py**: 31.27% → 86.49% ✅

### Coverage Improvement Roadmap

#### Phase 1: Critical Modules (✅ COMPLETE)
Target: Bring critical modules from <40% to >70% line coverage, >50% branch coverage
- [x] `validators/kv_validators.py` (Line: 33.64% → 100.00%, Branch: ~25% → 100%)
- [x] `validators/config_validator.py` (Line: 34.66% → 97.51%, Branch: ~30% → 90%+)
- [x] `analytics/context_analytics.py` (Line: 35.62% → 82.19%, Branch: ~30% → 70%+)
- [x] `storage/vector_db_init.py` (Line: 36.14% → 97.59%, Branch: ~25% → 90%+)

#### Phase 2: High Priority Modules (🚧 CURRENT FOCUS)
Target: Bring modules from 45-55% to >75% line coverage, >60% branch coverage
- [x] `agents/context_lint.py` (Line: 45.05% → 84.68%, Branch: ~35% → 70%+) ✅
- [x] `storage/graph_builder.py` (Line: 48.59% → 95.63%, Branch: ~40% → 85%+) ✅
- [x] `storage/hash_diff_embedder.py` (Line: 67.28% → 95.59%, Branch: ~50% → 85%+) ✅
- [ ] `integrations/graphrag_integration.py` (Line: 51.17% → 75%, Branch: ~45% → 60%)
- [ ] `storage/context_kv.py` (Line: 55.91% → 57.51%, Branch: ~45% → 50%) 🟡 Partial Progress

#### Phase 3: Final Push to Target
Target: Achieve overall 85% line coverage and 70% branch coverage
- [ ] Complete remaining gaps in Phase 1 & 2 modules
- [ ] Improve medium priority modules to >80% line, >65% branch
- [ ] Focus on branch coverage improvements in all modules
- [ ] Add integration tests for cross-module functionality
- [ ] Implement mutation testing baseline
- [ ] Ensure all critical paths have >90% coverage

### Incremental Targets

| Milestone | Line Coverage | Branch Coverage | Timeline | Status |
|-----------|---------------|-----------------|----------|---------|
| Baseline  | 30%           | ~20%            | Start    | ✅ Done |
| Current   | 75.66%        | ~65%            | Week 2   | ✅ Done |
| Phase 1   | 70%           | 50%             | Week 1   | ✅ Complete |
| Phase 2   | 80%           | 60%             | Week 2   | 🚧 In Progress |
| Phase 3   | 85%           | 70%             | Week 4   | ⏳ Planned |

### Test Quality Standards

All new tests must include:
- Happy path scenarios
- Error conditions
- Edge cases
- Mock external dependencies
- Clear assertions

Branch coverage requirements:
- Test both if/else branches
- Test exception handling
- Test different configuration paths

Mutation testing improvements:
- Strong assertions that catch value changes
- Test boundary conditions
- Avoid trivial assertions


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

## Coverage Matrix Generation

The `scripts/generate_coverage_matrix.py` script provides detailed test-to-module mapping:

### Features
- Shows which tests cover which modules
- Generates both HTML and Markdown reports
- Configurable thresholds and limits
- Automatic validation of coverage data

### Usage
```bash
# Basic usage
python scripts/generate_coverage_matrix.py

# With custom options
python scripts/generate_coverage_matrix.py \
    --max-tests-shown 10 \
    --high-threshold 90 \
    --output-dir reports \
    --debug

# Run via pre-commit hook
pre-commit run generate-coverage-matrix --hook-stage manual
```

### Command Line Options
- `--max-tests-shown`: Maximum tests to display in HTML (default: 5)
- `--max-test-names`: Maximum test names in Markdown (default: 3)
- `--high-threshold`: High coverage threshold (default: 85%)
- `--medium-threshold`: Medium coverage threshold (default: 70%)
- `--timeout`: Test execution timeout in seconds (default: 120)
- `--output-dir`: Directory for HTML output (default: current)
- `--docs-dir`: Directory for Markdown output (default: docs)
- `--debug`: Enable debug logging

### Output Files
- `coverage-matrix.html`: Interactive HTML report
- `docs/coverage-matrix.md`: Markdown report for documentation

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

## Automation Scripts

### Coverage Metrics Update
```bash
# Update coverage metrics and badges
python scripts/update_coverage_metrics.py
```
This script:
- Runs pytest with coverage
- Updates coverage-summary.json
- Updates README.md badges
- Shows current metrics

### Coverage Report Generation
```bash
# Generate coverage reports with graphs
python scripts/generate_coverage_report.py
```
This script:
- Generates coverage trend graphs
- Creates module distribution charts
- Updates documentation with visualizations

### JSON Validation
```bash
# Validate coverage-summary.json
python scripts/validate_coverage_json.py
```
This script:
- Validates against schemas/coverage-summary.schema.json
- Ensures consistent data structure
- Catches format errors early

### Automated Workflow
```bash
# Complete coverage update workflow
python scripts/update_coverage_metrics.py && \
python scripts/validate_coverage_json.py && \
python scripts/generate_coverage_report.py
```

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
