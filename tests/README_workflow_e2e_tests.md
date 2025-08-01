# Workflow Pipeline End-to-End Tests

## Overview

This test suite verifies that the complete workflow pipeline (from issue to PR) works correctly and catches bugs like #1706 where only documentation was created instead of actual code.

## Test Structure

### Main Test File
- `tests/test_workflow_pipeline_e2e.py` - Contains all end-to-end test scenarios

### Test Utilities
- `src/utils/workflow_test_utils.py` - Helper functions for workflow testing

### Test Fixtures
- `tests/fixtures/workflow_test_issues/` - Mock issue templates for testing:
  - `simple_function_addition.json` - Tests adding a function to existing module
  - `new_module_creation.json` - Tests creating new modules with functions
  - `bug_fix_scenario.json` - Tests fixing bugs in existing code

## Running the Tests

### Run All E2E Tests
```bash
pytest tests/test_workflow_pipeline_e2e.py -v
```

### Run Specific Test
```bash
pytest tests/test_workflow_pipeline_e2e.py::TestWorkflowPipelineE2E::test_simple_function_addition -v
```

### Run with Coverage
```bash
pytest tests/test_workflow_pipeline_e2e.py --cov=scripts.workflow_executor --cov-report=term-missing
```

## Test Scenarios

1. **Simple Function Addition** - Verifies that new functions are added correctly to existing modules
2. **New Module Creation** - Tests creation of entirely new modules with multiple functions
3. **Code Modification** - Ensures existing code can be modified correctly
4. **Bug Fix** - Tests that bugs are fixed with proper error handling
5. **Documentation-Only Prevention** - Catches the #1706 bug where only docs were created

## Debugging Failed Tests

### 1. Check Temporary Repository
Tests create temporary git repositories. To debug:
```python
# Add breakpoint in test
import pdb; pdb.set_trace()
# Inspect repo_path to see generated files
```

### 2. Enable Verbose Output
```bash
pytest tests/test_workflow_pipeline_e2e.py -v -s
```

### 3. Check Git Operations
Tests verify git commits. To debug git issues:
```bash
# In test, print git log
os.system(f"cd {repo_path} && git log --oneline")
```

### 4. Verify Mocked Calls
Tests mock GitHub API and subprocess calls. Check mock assertions:
```python
mock_run.assert_called_with(...)
```

## Common Issues and Solutions

### Issue: Tests Fail Due to Missing Git Config
**Solution**: Ensure git is configured in test environment
```bash
git config --global user.email "test@example.com"
git config --global user.name "Test User"
```

### Issue: Import Errors
**Solution**: Run from repository root with proper PYTHONPATH
```bash
PYTHONPATH=/workspaces/agent-context-template pytest tests/test_workflow_pipeline_e2e.py
```

### Issue: Temporary Files Not Cleaned Up
**Solution**: Tests should clean up automatically, but if not:
```bash
# Clean up /tmp manually
rm -rf /tmp/tmp*
```

## Adding New Test Scenarios

1. Create new test method in `TestWorkflowPipelineE2E`
2. Add fixture template in `tests/fixtures/workflow_test_issues/`
3. Implement simulation method (e.g., `_simulate_new_scenario`)
4. Add appropriate assertions

Example:
```python
def test_new_scenario(self, temp_repo):
    """Test description."""
    issue_data = {...}
    # Test implementation
    assert expected_behavior
```

## Integration with CI

These tests should run as part of the CI pipeline to catch workflow bugs before they reach production:

```yaml
# In .github/workflows/ci.yml
- name: Run Workflow E2E Tests
  run: |
    pytest tests/test_workflow_pipeline_e2e.py --cov=scripts.workflow_executor
```

## Performance Considerations

- Tests use temporary directories and mock external calls for speed
- Each test is independent and can run in parallel
- Total test suite should complete in under 5 minutes

## Future Enhancements

1. Add more complex scenarios (multi-file changes, refactoring)
2. Test error recovery and rollback scenarios
3. Add performance benchmarks for workflow execution
4. Test concurrent workflow executions