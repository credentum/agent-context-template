# Execution Scratchpad: Issue #1641 - ARC Reviewer Implementation

## Date: 2025-07-25
## Issue: #1641 - Fix Local ARC Reviewer Discrepancies
## Sprint: SPRINT-5.1

### Issue Summary
- **Problem**: No local ARC reviewer exists, causing validation surprises in CI
- **Impact**: Blocks PR #1639, wastes developer time, security vulnerabilities reach PR stage
- **Root Cause**: Complete reliance on GitHub Actions for validation

### Investigation Findings
1. Pre-commit hooks only cover basic linting (black, isort, flake8, mypy)
2. No security vulnerability scanning locally (command injection, path traversal, DoS)
3. No MCP contract validation locally
4. No Python 3.12 compatibility checks locally
5. Configuration between local and CI is not synchronized

### Implementation Plan

#### Phase 1: Foundation Setup (2 hours)
```bash
# Create feature branch
git checkout -b fix/1641-local-arc-reviewer

# Create directory structure
mkdir -p scripts/validators
mkdir -p tests/arc_reviewer/fixtures
mkdir -p .claude/guides

# Create initial files
touch scripts/arc-reviewer.py
touch scripts/validators/__init__.py
touch scripts/validators/security.py
touch scripts/validators/mcp_validator.py
touch scripts/validators/python_compat.py
touch scripts/validators/config_sync.py
touch scripts/requirements.txt
chmod +x scripts/arc-reviewer.py
```

#### Phase 2: Core Implementation (8 hours)

**Step 1: Main ARC Reviewer Script**
- Create orchestrator that runs all validators
- CLI interface with options for selective validation
- Progress reporting and error aggregation
- Exit codes matching CI behavior

**Step 2: Security Validator**
- Integrate bandit for Python security scanning
- Add custom rules for:
  - Command injection detection
  - Path traversal vulnerabilities
  - DoS attack vectors
- Match GitHub security scan configuration

**Step 3: MCP Contract Validator**
- Find all MCP contract files
- Validate against schema
- Check contract consistency
- Ensure required fields present

**Step 4: Python Compatibility Checker**
- Use pyupgrade for syntax checking
- AST analysis for deprecated features
- Type annotation compatibility
- Import compatibility checks

**Step 5: Configuration Synchronizer**
- Parse CI workflow files
- Extract validation rules
- Compare with local config
- Report drift

#### Phase 3: Integration (2 hours)

**Pre-commit Hook Integration**
```yaml
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: arc-reviewer
      name: ARC Reviewer - Full Validation
      entry: python scripts/arc-reviewer.py
      language: python
      pass_filenames: false
      always_run: true
      additional_dependencies:
        - bandit>=1.7.5
        - pyupgrade>=3.15.0
        - jsonschema>=4.20.0
        - pyyaml>=6.0
```

#### Phase 4: Testing & Documentation (4 hours)

**Test Coverage Requirements**
- Unit tests for each validator
- Integration tests for full pipeline
- Comparison tests against CI output
- Performance benchmarks

**Documentation Structure**
```
.claude/guides/arc-reviewer.md
├── Overview
├── Installation
├── Usage Examples
├── Configuration
├── Troubleshooting
└── Development Guide
```

### Token Budget Management
- Estimated tokens: 15,000
- Strategy: Implement validators incrementally
- Use `/clear` between major phases
- Keep task template open for reference

### Risk Mitigation
1. **Performance Impact**
   - Implement parallel validation
   - Add caching for expensive operations
   - Provide skip flags for development

2. **Configuration Drift**
   - Daily CI job to verify sync
   - Automated PR for config updates
   - Single source of truth approach

3. **Adoption Resistance**
   - Make it fast (<30s)
   - Clear, actionable error messages
   - Gradual rollout with opt-in period

### Validation Checklist
- [ ] Security vulnerabilities detected locally match CI
- [ ] MCP contracts validated identically
- [ ] Python 3.12 issues caught
- [ ] Performance under 30 seconds
- [ ] Zero false positives
- [ ] Configuration stays synchronized
- [ ] Pre-commit integration works
- [ ] Documentation complete

### Known Challenges
1. **Bandit Configuration**: Need to match exact CI rules
2. **MCP Schema Location**: Ensure schema files are accessible
3. **Python Version Matrix**: Handle multiple Python versions
4. **Tool Versions**: Pin to match CI environment

### Success Metrics
- Developer satisfaction: >90%
- CI surprise rate: <5%
- Average validation time: <30s
- Configuration drift incidents: 0
- Security issues caught locally: 100%

### Next Steps After Implementation
1. Monitor performance metrics
2. Gather developer feedback
3. Add IDE integration
4. Create validation dashboard
5. Implement incremental validation

### Command Examples
```bash
# Full validation (default)
python scripts/arc-reviewer.py

# Security only
python scripts/arc-reviewer.py --only security

# Skip Python compatibility
python scripts/arc-reviewer.py --skip python-compat

# Verbose output
python scripts/arc-reviewer.py --verbose

# Check configuration sync
python scripts/arc-reviewer.py --check-sync

# Update configuration
python scripts/arc-reviewer.py --sync-config
```

### File Creation Order
1. Main script: `scripts/arc-reviewer.py`
2. Security validator: `scripts/validators/security.py`
3. MCP validator: `scripts/validators/mcp_validator.py`
4. Python compatibility: `scripts/validators/python_compat.py`
5. Config sync: `scripts/validators/config_sync.py`
6. Requirements: `scripts/requirements.txt`
7. Tests: `tests/arc_reviewer/test_*.py`
8. Documentation: `.claude/guides/arc-reviewer.md`

### Current Status
- [x] Investigation complete
- [x] Task template created
- [x] Execution plan documented
- [ ] Implementation started
- [ ] Testing in progress
- [ ] Documentation written
- [ ] PR created
