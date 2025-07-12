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