# Issue #1662 - CI Validation Flexibility Enhancement

**Issue Link**: https://github.com/anthropics/agent-context-template/issues/1662
**Sprint**: sprint-current
**Task Template**: context/trace/task-templates/issue-1662-ci-validation-flexibility.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 8,000
- **Complexity**: Low (well-defined enhancement)
- **Files Affected**: 3 (workflow-validator.py, workflow-enforcement.yaml, tests)
- **Time Estimate**: 2 hours

## Implementation Plan

### Step 1: Analyze Current Implementation
- [x] Read workflow-validator.py to understand current CI validation
- [x] Review workflow-enforcement.yaml structure for configuration patterns
- [x] Identify the restrictive _check_ci_status() method at lines 246-255

### Step 2: Design Configuration Schema
- [ ] Add ci_validation section to workflow-enforcement.yaml
- [ ] Define flexible marker files, time limits, and environment awareness
- [ ] Ensure backward compatibility

### Step 3: Implement Enhanced CI Validation
- [ ] Modify _check_ci_status() method to use configuration
- [ ] Support multiple CI marker files beyond .last-ci-run
- [ ] Make time restrictions configurable (0 = no limit)
- [ ] Add environment-aware validation (Docker vs non-Docker)

### Step 4: Update Configuration Loading
- [ ] Add configuration loading to WorkflowValidator.__init__
- [ ] Implement safe defaults for backward compatibility
- [ ] Add validation for configuration schema

### Step 5: Create Tests
- [ ] Unit tests for various CI scenarios
- [ ] Test configuration loading and defaults
- [ ] Test backward compatibility
- [ ] Test edge cases (missing files, old markers, etc.)

### Step 6: Integration Testing
- [ ] Run existing workflow tests
- [ ] Test with and without Docker CI
- [ ] Test resume scenarios

## Key Changes Required

### 1. workflow-validator.py
```python
# Lines 246-255: Current restrictive implementation
def _check_ci_status(self) -> bool:
    """Check if CI has passed."""
    # Current: hardcoded .last-ci-run with 1-hour limit

# New: Flexible implementation with configuration
def _check_ci_status(self) -> bool:
    """Check if CI has passed with configurable validation."""
    # Support multiple markers, configurable time limits, environment awareness
```

### 2. workflow-enforcement.yaml
```yaml
# Add new section:
validation:
  ci_validation:
    require_ci: true
    max_age_hours: 0  # 0 = no time limit
    marker_files:
      - .last-ci-run
      - ci-output.log
      - .pytest_cache/v/cache/lastfailed
      - coverage.xml
    allow_test_only: false  # Allow validation with tests but no CI
```

### 3. Configuration Loading
- Add YAML loading to WorkflowValidator
- Implement safe defaults
- Validate configuration schema

## Risk Assessment
- **Backward Compatibility**: Low risk - adding configuration with defaults
- **Security**: Low risk - using existing secure patterns for file checking
- **Performance**: Minimal impact - same validation logic, just more flexible

## Success Metrics
- All existing workflows continue to work
- New configuration options allow flexible CI validation
- Tests cover edge cases and configuration scenarios
- Documentation explains new configuration options
