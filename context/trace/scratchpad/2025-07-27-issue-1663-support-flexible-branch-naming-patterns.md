---
schema_version: "1.0"
---

# Execution Plan: Issue #1663 - Support Flexible Branch Naming Patterns

**Issue Link**: https://github.com/anthropics/agent-context-template/issues/1663
**Sprint Reference**: sprint-current
**Task Template**: context/trace/task-templates/issue-1663-support-flexible-branch-naming-patterns.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 12,000 (moderate complexity with security considerations)
- **Estimated time**: 3 hours (implementation + comprehensive testing)
- **Complexity**: Medium (new feature with security requirements)
- **Files affected**: 4 (workflow-validator.py, workflow-enforcement.yaml, tests, documentation)

## Step-by-Step Implementation Plan

### Phase 1: Analysis & Design (30 minutes)
- [x] Review current workflow_validator.py implementation
- [x] Analyze existing branch pattern validation in _check_pr_created() method
- [x] Identify hardcoded fix/ and feature/ patterns that need flexibility
- [x] Design configuration schema for workflow-enforcement.yaml
- [x] Plan security measures for custom regex patterns

### Phase 2: Configuration Schema Design (30 minutes)
- [ ] Add branch_patterns section to workflow-enforcement.yaml
- [ ] Define structure for prefixes and custom_regex options
- [ ] Implement backward compatibility with defaults
- [ ] Add validation rules for configuration inputs

### Phase 3: Core Implementation (90 minutes)
- [ ] Modify WorkflowValidator.__init__ to load branch pattern configuration
- [ ] Enhance _check_pr_created() method to use flexible patterns
- [ ] Add _validate_custom_regex() method for security validation
- [ ] Add _validate_branch_prefixes() method for input sanitization
- [ ] Implement safe fallback behavior for invalid configurations

### Phase 4: Security Hardening (30 minutes)
- [ ] Implement ReDoS prevention for custom regex patterns
- [ ] Add input sanitization for branch prefixes
- [ ] Validate pattern length and complexity limits
- [ ] Add try-catch blocks for regex compilation and execution
- [ ] Test security edge cases and malicious inputs

### Phase 5: Testing & Validation (60 minutes)
- [ ] Create comprehensive test suite in test_workflow_validator.py
- [ ] Test all supported branch patterns (fix/, feature/, hotfix/, refactor/, chore/, docs/, style/, test/)
- [ ] Test custom regex pattern functionality
- [ ] Test security validation and ReDoS prevention
- [ ] Test configuration loading and fallback behavior
- [ ] Test backward compatibility with existing patterns

### Phase 6: Documentation & Integration (30 minutes)
- [ ] Update configuration documentation
- [ ] Add inline code documentation for security considerations
- [ ] Run full CI pipeline to ensure compatibility
- [ ] Create trace files with schema_version header

## Current Implementation Analysis

### Existing Code Structure
```python
# Current workflow_validator.py implementation (lines ~246-255)
def _check_pr_created(self) -> bool:
    """Check if PR was created using hardcoded patterns."""
    # Current implementation only checks fix/ and feature/ patterns
    # Need to extend for flexible configuration
```

### Required Changes

#### 1. Configuration Schema (workflow-enforcement.yaml)
```yaml
# New branch_patterns section
validation:
  branch_patterns:
    # List of allowed prefixes
    prefixes:
      - "fix"
      - "feature" 
      - "hotfix"
      - "refactor"
      - "chore"
      - "docs"
      - "style"
      - "test"
    
    # Optional custom regex pattern
    custom_regex: "^(fix|feature|hotfix)\/\\d+-.+"
    
    # Security settings
    max_pattern_length: 1000
    allow_custom_regex: true
```

#### 2. Enhanced WorkflowValidator Class
```python
class WorkflowValidator:
    def __init__(self, config_path: str = None):
        # Load branch pattern configuration
        self.branch_config = self._load_branch_patterns()
    
    def _load_branch_patterns(self) -> dict:
        """Load and validate branch pattern configuration."""
        # Load from workflow-enforcement.yaml with safe defaults
    
    def _validate_custom_regex(self, pattern: str) -> bool:
        """Validate custom regex pattern for security."""
        # Prevent ReDoS attacks and validate format
    
    def _validate_branch_prefixes(self, prefixes: list) -> list:
        """Sanitize and validate branch prefixes."""
        # Remove dangerous characters and validate length
    
    def _check_pr_created(self) -> bool:
        """Check PR creation with flexible branch patterns."""
        # Use configuration-driven pattern matching
```

## Security Considerations

### 1. ReDoS Prevention
- Validate regex pattern complexity
- Limit pattern length (max 1000 characters)
- Detect dangerous patterns (nested quantifiers, excessive backtracking)
- Test compilation before use

### 2. Input Sanitization
- Sanitize branch prefixes (alphanumeric, underscore, hyphen only)
- Validate prefix length (1-50 characters)
- Type checking for all inputs
- Safe defaults when validation fails

### 3. Configuration Validation
- JSON/YAML parsing error handling
- Type validation for configuration values
- Graceful fallback to original behavior
- Logging of validation issues

## Risk Assessment & Mitigation

### High Priority Risks
1. **ReDoS Attack Risk**: Custom regex patterns could cause catastrophic backtracking
   - *Mitigation*: Comprehensive regex validation and testing before use
   
2. **Backward Compatibility**: Changes could break existing workflows
   - *Mitigation*: Maintain fix/ and feature/ as defaults, extensive testing

3. **Configuration Errors**: Invalid YAML could crash validator
   - *Mitigation*: Robust error handling and safe fallback behavior

### Medium Priority Risks
1. **Performance Impact**: Complex regex patterns could slow validation
   - *Mitigation*: Pattern complexity limits and caching

2. **Security Bypass**: Malicious patterns could bypass validation
   - *Mitigation*: Input sanitization and allowlist-based validation

## Testing Strategy

### Unit Tests
- Test each branch pattern type individually
- Test custom regex pattern functionality
- Test security validation methods
- Test configuration loading and error handling
- Test backward compatibility scenarios

### Integration Tests
- Test full workflow with various branch patterns
- Test with real GitHub API responses
- Test configuration file loading from filesystem
- Test fallback behavior under error conditions

### Security Tests
- Test ReDoS prevention with malicious patterns
- Test input sanitization effectiveness
- Test edge cases and boundary conditions
- Test error handling with invalid inputs

## Success Metrics

### Functional Requirements
- [ ] All existing fix/ and feature/ patterns continue to work
- [ ] New branch patterns (hotfix/, refactor/, chore/, docs/, style/, test/) are supported
- [ ] Custom regex patterns work for complex naming schemes
- [ ] Configuration loads properly from workflow-enforcement.yaml
- [ ] Graceful fallback when configuration is invalid or missing

### Security Requirements
- [ ] Custom regex patterns are validated for ReDoS risks
- [ ] Branch prefixes are properly sanitized
- [ ] No security vulnerabilities introduced
- [ ] Error handling prevents crashes and information leakage

### Quality Requirements
- [ ] Test coverage ≥ 90% for new functionality
- [ ] All CI checks pass (linting, type checking, security scans)
- [ ] Documentation is complete and accurate
- [ ] Performance impact is minimal (<5ms additional validation time)

## Implementation Status

### Completed Tasks
- [x] Issue analysis and requirements gathering
- [x] Architecture design and security planning
- [x] Task template creation with schema_version
- [x] Scratchpad creation with schema_version

### Next Steps
1. Implement configuration loading in WorkflowValidator
2. Add security validation methods
3. Enhance _check_pr_created() method
4. Create comprehensive test suite
5. Validate security measures and performance
6. Complete integration testing and documentation

## Notes & Observations

- The existing workflow validator is tightly coupled to fix/ and feature/ patterns
- Security is a primary concern due to custom regex support
- Backward compatibility is critical for existing workflows
- Configuration-driven approach provides maximum flexibility
- Comprehensive testing is essential due to security implications