# Test Suite Documentation

This directory contains comprehensive tests for the Agent Context Template system, including unit tests, integration tests, mutation tests, and end-to-end tests.

## Test Structure

```
tests/
├── test_hash_diff_embedder.py      # Unit tests for document embedding
├── test_agent_state_machines.py    # Unit tests for agent state transitions
├── test_metadata_validation.py     # Unit tests for metadata validation
├── test_integration_embedding_flow.py  # Integration tests for embedding → Qdrant
├── test_integration_agent_flow.py      # Integration tests for agent execution
├── test_integration_ci_workflow.py     # Integration tests for CI/CD workflows
├── test_e2e_project_lifecycle.py       # End-to-end project lifecycle tests
├── test_sigstore_verification.py       # Sigstore signature verification tests
├── mutation_testing_setup.py           # Mutation testing configuration
└── README.md                          # This file
```

## Running Tests

### Run All Tests
```bash
python run_all_tests.py
```

### Run Specific Test Suites
```bash
# Unit tests only
python run_all_tests.py --suite unit

# Integration tests only
python run_all_tests.py --suite integration

# End-to-end tests only
python run_all_tests.py --suite e2e

# Mutation tests only
python run_all_tests.py --suite mutation
```

### Run with Coverage
```bash
# Run all tests with coverage
pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=xml

# View coverage report
coverage report
```

### Run Individual Test Files
```bash
# Run specific test file
pytest tests/test_hash_diff_embedder.py -v

# Run with specific markers
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests
```

## Test Types

### 1. Unit Tests
- **Purpose**: Test individual components in isolation
- **Coverage**:
  - File transforms and YAML parsing
  - Agent state machines
  - Metadata validation
  - Configuration validation
  - Key-value validators

### 2. Integration Tests
- **Purpose**: Test component interactions
- **Coverage**:
  - Document → Embedding → Qdrant flow
  - Agent run → Reflection → Trace commit
  - PR → CI → Sprint update flow

### 3. Mutation Tests
- **Purpose**: Test the quality of tests by introducing code mutations
- **Targets**:
  - Core agents (cleanup, sprint update, context lint)
  - Critical validators
  - Summarization logic
- **Tool**: mutmut

### 4. End-to-End Tests
- **Purpose**: Test complete system workflows
- **Coverage**:
  - Full project lifecycle
  - Trace replay functionality
  - Document integrity
  - Sigstore signature verification

## Test Configuration

### pytest.ini
Contains pytest configuration including:
- Test discovery patterns
- Coverage settings
- Test markers
- Warning filters

### setup.cfg
Contains mutation testing configuration for mutmut

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<specific_behavior>`

### Example Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestMyComponent:
    def setup_method(self):
        """Set up test fixtures"""
        self.component = MyComponent()

    def test_normal_behavior(self):
        """Test expected behavior"""
        result = self.component.process("input")
        assert result == "expected_output"

    @pytest.mark.slow
    def test_performance(self):
        """Test performance requirements"""
        # Performance test implementation
```

### Using Test Markers
```python
@pytest.mark.integration
def test_database_connection():
    """Integration test requiring database"""
    pass

@pytest.mark.e2e
def test_full_workflow():
    """End-to-end test of complete workflow"""
    pass
```

## Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r requirements-dev.txt
    python run_all_tests.py --fail-fast
```

## Test Reports

After running tests, reports are generated:
- `test_report.yaml` - Detailed test results in YAML format
- `test_report.json` - Test results in JSON format for CI integration
- `coverage.xml` - XML coverage report for CI integration
- `mutation_test_report.yaml` - Mutation testing results

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-timeout pytest-asyncio mutmut
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes the project root
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Timeout errors**: Increase timeout in pytest.ini or use `--timeout=600`

3. **Coverage not showing**: Ensure source files are in the `src/` directory

4. **Mutation tests slow**: Run on specific files:
   ```bash
   mutmut run --paths-to-mutate src/agents/cleanup_agent.py
   ```

## Best Practices

1. **Keep tests focused**: Each test should verify one specific behavior
2. **Use meaningful assertions**: Include clear assertion messages
3. **Mock external dependencies**: Use mocks for databases, APIs, file systems
4. **Test edge cases**: Include tests for error conditions and boundaries
5. **Maintain test coverage**: Aim for >80% coverage on critical components
