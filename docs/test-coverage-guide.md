# Test Coverage Improvement Guide

This guide provides a systematic approach to improving test coverage across the agent-context-template project.

## Current Status & Configuration

### Coverage Configuration
All coverage thresholds are managed centrally in `.coverage-config.json`:

```json
{
  "baseline": 78.5,           // Current minimum (CI fails below this)
  "target": 85.0,             // Project goal
  "validator_target": 90.0,   // Higher standard for validators
  "last_updated": "2025-07-15"
}
```

To update thresholds:
```bash
# 1. Edit configuration
vim .coverage-config.json

# 2. Sync documentation
python scripts/update-coverage-baseline.py

# 3. Commit changes
git add .coverage-config.json CLAUDE.md && git commit -m "feat(coverage): update baseline"
```

### Current Project Coverage: 78.5%

---

## 📁 Coverage by Module

### 🔴 Critical Priority (< 50% coverage)

**Validators Module** - Target: 90%
```
src/validators/
├── kv_validators.py          33.64%  🔴 CRITICAL - Key-value validation
├── config_validator.py      34.66%  🔴 CRITICAL - Configuration schemas
└── yaml_validator.py        45.00%  🟡 HIGH     - YAML structure validation
```

### 🟡 High Priority (50-75% coverage)

**Storage Module** - Target: 85%
```
src/storage/
├── vector_db_init.py        64.29%  🟡 MEDIUM - Qdrant initialization
├── neo4j_init.py           65.79%  🟡 MEDIUM - Graph database setup
└── hash_diff_embedder.py   71.43%  🟡 MEDIUM - Document embedding cache
```

**Analytics Module** - Target: 85%
```
src/analytics/
├── context_analytics.py    58.33%  🟡 MEDIUM - Usage metrics collection
└── sum_scores_api.py       62.50%  🟡 MEDIUM - Score aggregation API
```

### 🟢 Good Coverage (75-85% coverage)

**Core Module** - Target: 85%
```
src/core/
├── base_agent.py           78.95%  🟢 GOOD - Agent base class
├── context_manager.py      81.25%  🟢 GOOD - Context lifecycle
└── error_handling.py       83.33%  🟢 GOOD - Exception management
```

**Agents Module** - Target: 85%
```
src/agents/
├── cleanup_agent.py        76.92%  🟢 GOOD - File cleanup automation
├── context_lint.py         79.17%  🟢 GOOD - YAML validation agent
└── sprint_issue_linker.py  82.35%  🟢 GOOD - GitHub integration
```

### 🟢 Excellent Coverage (> 85% coverage)

**Integrations Module** - Target: 85%
```
src/integrations/
├── github_integration.py   91.67%  🟢 EXCELLENT - GitHub API client
├── qdrant_client.py        94.12%  🟢 EXCELLENT - Vector DB client
└── mcp_server.py           96.30%  🟢 EXCELLENT - MCP protocol server
```

---

## 🎯 Implementation Phases

### Phase 1: Critical Validators (Target: 90%)

**Files to Focus On:**
- `src/validators/kv_validators.py` (33.64% → 90%)
- `src/validators/config_validator.py` (34.66% → 90%)
- `src/validators/yaml_validator.py` (45.00% → 90%)

**Key Testing Areas:**
- Input validation edge cases (null, empty, malformed)
- Schema compliance and error reporting
- Performance with large datasets
- Error handling and recovery
- Integration with downstream systems

### Phase 2: Storage Layer (Target: 85%)

**Files to Focus On:**
- `src/storage/vector_db_init.py` (64.29% → 85%)
- `src/storage/neo4j_init.py` (65.79% → 85%)
- `src/storage/hash_diff_embedder.py` (71.43% → 85%)

**Key Testing Areas:**
- Connection management and retry logic
- Authentication and authorization flows
- Data persistence and retrieval
- Concurrent access patterns
- Resource cleanup and memory management

### Phase 3: Analytics & Reporting (Target: 85%)

**Files to Focus On:**
- `src/analytics/context_analytics.py` (58.33% → 85%)
- `src/analytics/sum_scores_api.py` (62.50% → 85%)

**Key Testing Areas:**
- Metric calculation accuracy
- API endpoint validation
- Data aggregation and reporting
- Performance under load
- Export and formatting functionality

---

## 🔧 Testing Implementation Strategy

### 1. Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch
from src.validators.example_validator import ExampleValidator

class TestExampleValidator:
    """Test suite for validators.example_validator"""

    def setup_method(self):
        """Setup test fixtures"""
        self.validator = ExampleValidator()

    def test_valid_input_happy_path(self):
        """Test normal operation with valid inputs"""
        pass

    def test_invalid_input_edge_cases(self):
        """Test boundary conditions and malformed inputs"""
        pass

    def test_error_handling_scenarios(self):
        """Test exception handling and error reporting"""
        pass

    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test async functionality if applicable"""
        pass
```

### 2. Coverage Analysis Commands

```bash
# Generate detailed coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Focus on specific module
pytest tests/test_validators.py --cov=src.validators --cov-report=term-missing

# Test with centralized baseline check
./scripts/test-github-ci-locally.sh

# Update coverage metrics
python scripts/update_coverage_metrics.py
```

### 3. Essential Test Categories

**For All Modules:**
- ✅ Happy path scenarios
- ✅ Edge cases and boundary conditions
- ✅ Error handling and exceptions
- ✅ Input validation
- ✅ Resource cleanup
- ✅ Async operations (where applicable)

**For Validators Specifically:**
- ✅ Schema compliance testing
- ✅ Malformed input handling
- ✅ Performance with large datasets
- ✅ Unicode and special character support
- ✅ Nested structure validation

**For Storage Modules:**
- ✅ Connection lifecycle management
- ✅ Transaction handling
- ✅ Concurrent access patterns
- ✅ Data integrity verification
- ✅ Backup and recovery scenarios

---

## 📊 Progress Tracking

### Phase Milestones

```
Phase 1: Validators (Week 1-2)
├── kv_validators.py          33.64% → 90%     [+56.36%]
├── config_validator.py      34.66% → 90%     [+55.34%]
└── yaml_validator.py        45.00% → 90%     [+45.00%]

Phase 2: Storage (Week 3-4)
├── vector_db_init.py        64.29% → 85%     [+20.71%]
├── neo4j_init.py           65.79% → 85%     [+19.21%]
└── hash_diff_embedder.py   71.43% → 85%     [+13.57%]

Phase 3: Analytics (Week 5-6)
├── context_analytics.py    58.33% → 85%     [+26.67%]
└── sum_scores_api.py       62.50% → 85%     [+22.50%]
```

### Success Criteria
- [ ] Overall project coverage ≥ 85%
- [ ] No module below 75% coverage
- [ ] Validator modules ≥ 90% coverage
- [ ] All new code has ≥ 90% coverage
- [ ] Coverage baseline consistently met in CI

---

## 🛠️ Development Workflow

### Before Starting Work
```bash
# Check current coverage
pytest --cov=src --cov-report=term-missing

# Run local CI validation
./scripts/test-github-ci-locally.sh
```

### During Development
```bash
# Test specific module while developing
pytest tests/test_validators.py -v --cov=src.validators

# Watch mode for continuous testing
pytest-watch tests/test_validators.py --cov=src.validators
```

### Before Committing
```bash
# Required pre-commit checks
pre-commit run --all-files

# Verify coverage hasn't dropped
pytest --cov=src --cov-report=term-missing

# Update coverage metrics if needed
python scripts/update_coverage_metrics.py
```

---

## 📚 Resources

### Project-Specific Documentation
- [Coverage Configuration Guide](./coverage-configuration.md)
- [Context System Architecture](../context/README.md)
- [Validator Implementation Patterns](../src/validators/)
- [Testing Patterns and Examples](../tests/)

### Testing Tools & References
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Guide](https://coverage.readthedocs.io/)
- [Python Mock Library](https://docs.python.org/3/library/unittest.mock.html)
- [Async Testing Patterns](https://pytest-asyncio.readthedocs.io/)
