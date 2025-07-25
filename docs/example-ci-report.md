# Example Claude CI Report

This is what successful and failed CI reports look like, showing the detailed output format.

## ✅ Successful CI Report

---

### Claude CI Report - SUCCESS

**Branch**: `feature/add-context-analyzer`
**Date**: 2025-07-25 14:45:00
**Duration**: 2m 34s
**Status**: ✅ **All Checks Passed**

#### 📋 Summary

All CI checks completed successfully. The code is ready for PR submission.

#### 🔍 Detailed Results

##### Code Quality
- ✅ **Formatting (black)**: Clean - 104 files checked
- ✅ **Import sorting (isort)**: Properly ordered
- ✅ **Linting (flake8)**: No issues found
- ✅ **Type checking (mypy)**: Success - no issues in 104 source files

##### Security
- ✅ **Secret scan**: No hardcoded credentials detected
- ✅ **Dependency check**: All dependencies secure
- ✅ **Pre-commit hooks**: All 16 hooks passed

##### Testing
- ✅ **Unit tests**: 1,051 passed, 0 failed, 4 skipped
- ✅ **Test duration**: 40 seconds
- ✅ **Smart selection**: Not used (full suite run)

##### Coverage Report
```
Overall Coverage: 79.84% (baseline: 78.0%) ✅

Module Coverage:
├── src/agents/         81.20%  ✅
├── src/core/          78.95%  ✅
├── src/storage/       82.35%  ✅
├── src/validators/   100.00%  ✅ Excellent!
└── src/analytics/     75.50%  ⚠️  Below target

Top Coverage Improvements:
- src/validators/config_validator.py: 34.66% → 100.00% (+65.34%)
- src/validators/kv_validators.py: 33.64% → 100.00% (+66.36%)
```

##### Context Validation
- ✅ **YAML schemas**: All valid
- ✅ **MCP contracts**: Consistent
- ✅ **Graph relationships**: No broken references

##### ARC Reviewer Verdict
```yaml
verdict: APPROVE
summary: All checks passed - ready for merge
issues:
  blocking: []
  warnings: []
  nits: []
```

#### 🎯 Next Steps

1. Push to remote: `git push -u origin feature/add-context-analyzer`
2. Create PR with closing keywords for related issues
3. Request review from team members

#### 📊 Performance Metrics

- Linting: 7s
- Type checking: 3s
- Tests: 40s
- Coverage analysis: 5s
- ARC review: 7s
- **Total: 62s**

---

## ❌ Failed CI Report

---

### Claude CI Report - FAILED

**Branch**: `feature/experimental-optimizer`
**Date**: 2025-07-25 15:30:00
**Duration**: 1m 45s
**Status**: ❌ **Checks Failed**

#### 📋 Summary

CI validation failed with 3 blocking issues that must be resolved before PR submission.

#### 🔍 Detailed Results

##### Code Quality
- ✅ **Formatting (black)**: Clean
- ❌ **Import sorting (isort)**: **3 files need fixing**
  ```
  src/optimizers/gradient_optimizer.py
  src/optimizers/batch_processor.py
  tests/test_optimizers.py
  ```
- ⚠️ **Linting (flake8)**: **2 warnings**
  ```
  src/optimizers/gradient_optimizer.py:45:80: E501 line too long (92 > 88 characters)
  src/optimizers/batch_processor.py:78: F841 local variable 'result' is assigned but never used
  ```
- ❌ **Type checking (mypy)**: **4 errors**
  ```
  src/optimizers/gradient_optimizer.py:23: error: Missing return statement [return]
  src/optimizers/gradient_optimizer.py:67: error: Argument 1 has incompatible type "float"; expected "int" [arg-type]
  tests/test_optimizers.py:12: error: Cannot find implementation or library stub for module named "missing_module" [import-not-found]
  tests/test_optimizers.py:45: error: "None" has no attribute "process" [attr-defined]
  ```

##### Security
- ❌ **Secret scan**: **CRITICAL - Hardcoded credential found**
  ```
  src/optimizers/config.py:12: Potential hardcoded secret: api_key
  Fix guidance: Use environment variables or secrets management
  ```
- ✅ **Dependency check**: All dependencies secure
- ❌ **Pre-commit hooks**: **4 hooks failed**

##### Testing
- ❌ **Unit tests**: **1,043 passed, 8 failed, 4 skipped**

  **Failed Tests**:
  ```
  FAILED tests/test_optimizers.py::TestGradientOptimizer::test_convergence
    AssertionError: Expected convergence in 100 iterations, got 150

  FAILED tests/test_optimizers.py::TestBatchProcessor::test_memory_limit
    MemoryError: Exceeded memory limit during batch processing

  FAILED tests/test_integration.py::test_optimizer_integration
    ConnectionError: Could not connect to optimization service

  ... 5 more failures
  ```

##### Coverage Report
```
Overall Coverage: 76.23% (baseline: 78.0%) ❌ BELOW BASELINE

Module Coverage:
├── src/agents/         81.20%  ✅
├── src/core/          78.95%  ✅
├── src/storage/       82.35%  ✅
├── src/validators/   100.00%  ✅
├── src/optimizers/    42.50%  ❌ Needs improvement
└── src/analytics/     75.50%  ⚠️

Uncovered Lines in New Code:
- src/optimizers/gradient_optimizer.py: Lines 45-67, 89-95
- src/optimizers/batch_processor.py: Lines 23-45, 78-90
```

##### ARC Reviewer Verdict
```yaml
verdict: REQUEST_CHANGES
summary: Found 5 blocking, 2 warning, 0 nit issues
issues:
  blocking:
    - description: "Coverage 76.23% below baseline 78.0%"
      file: overall
      category: test_coverage
      fix_guidance: "Add tests to achieve 78.0% coverage"

    - description: "Potential hardcoded secret: api_key"
      file: src/optimizers/config.py
      line: 12
      category: security
      fix_guidance: "Use environment variables or secrets management"

    - description: "Missing return statement"
      file: src/optimizers/gradient_optimizer.py
      line: 23
      category: type_safety
      fix_guidance: "Add return statement with appropriate type"

    - description: "Pre-commit hooks failed"
      file: multiple
      category: code_quality
      fix_guidance: "Run 'pre-commit run --all-files' locally"

    - description: "8 test failures detected"
      file: tests/
      category: test_failures
      fix_guidance: "Fix failing tests before PR submission"

  warnings:
    - description: "Import order violations in 3 files"
      category: code_style
      fix_guidance: "Run 'isort src/ tests/' to fix"

    - description: "Line length violations"
      category: code_style
      fix_guidance: "Break long lines or use parentheses"
```

#### 🔧 Auto-Fix Available

The following issues can be automatically fixed:

```bash
# Fix all auto-fixable issues
./scripts/claude-ci.sh fix-all

# This will fix:
# - Import sorting (3 files)
# - Some formatting issues
# - Trailing whitespace
```

#### ❌ Manual Fixes Required

The following issues require manual intervention:

1. **Type Errors**: Add missing return statement and fix type mismatches
2. **Test Failures**: Debug and fix the 8 failing tests
3. **Security Issue**: Move hardcoded API key to environment variable
4. **Coverage**: Add tests for uncovered code in optimizers module

#### 📝 Suggested Fix Order

1. Run auto-fix first: `./scripts/claude-ci.sh fix-all`
2. Fix the security issue (highest priority)
3. Fix type errors in gradient_optimizer.py
4. Fix failing tests one by one
5. Add tests to improve coverage above 78%
6. Re-run CI: `./scripts/claude-ci.sh all`

#### 🚫 Blocked Actions

- ❌ Cannot create PR until issues are resolved
- ❌ GitHub Actions will fail if pushed
- ❌ Auto-merge not possible

#### 📊 Fix Time Estimate

Based on the issues found:
- Auto-fixable issues: ~2 minutes
- Manual fixes: ~30-45 minutes
- Total estimated fix time: ~45 minutes

---

## 📈 CI Trend Report

### Weekly CI Performance

```
Week of July 21-25, 2025

Success Rate: 87.3% (48/55 runs)
Average Duration: 2m 15s
Most Common Failures:
1. Type checking errors (28%)
2. Test failures (23%)
3. Coverage drops (19%)
4. Linting issues (15%)
5. Security scans (15%)

Improvement from last week: +5.2%
```

---

*Generated by Claude CI Pipeline v2.0*
