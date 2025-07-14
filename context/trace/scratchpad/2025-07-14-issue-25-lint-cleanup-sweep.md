# Issue #25: Lint Cleanup Sweep Before Phase 4.1

**Issue Link**: https://github.com/credentum/agent-context-template/issues/25
**Sprint**: sprint-4.1 (Infra Bring-Up prep)
**Date**: 2025-07-14

## Objective
Perform a comprehensive lint cleanup to align local development with CI enforcement, ensuring all files pass `.pre-commit-config-ci.yaml` checks.

## Current State Analysis

From previous PR #24, we identified:
- Local pre-commit was only checking `src/` files
- CI runs linting on ALL files (tests, scripts, etc.)
- This mismatch revealed ~100+ linting errors
- We have `.pre-commit-config-ci.yaml` that matches CI behavior

## Plan

### 1. Setup & Discovery (15 min)
- [x] Create new branch: `fix/issue-25-lint-cleanup`
- [ ] Run pre-commit with CI config to identify all issues
- [ ] Categorize errors by type and count

### 2. Python Linting Fixes (2-3 hours)
Fix in this order to minimize conflicts:

#### 2.1 F401 - Unused imports (~50 errors)
- Remove unused imports from all files
- Common in test files and scripts

#### 2.2 F841 - Unused variables (~15 errors)
- Either use or remove unused variables
- Check if they should be used in assertions

#### 2.3 E501 - Line too long (~20 errors)
- Break long lines at logical points
- Max line length: 100 characters

#### 2.4 F541 - F-strings without placeholders (~10 errors)
- Convert to regular strings

#### 2.5 E712 - Comparison to True/False (~10 errors)
- Change `== True` to `is True` or just use truthiness
- Change `== False` to `is False` or `not`

#### 2.6 E402 - Module level imports (~5 errors)
- Move imports to top of file

#### 2.7 Other misc errors
- F811 - Redefinition of unused names
- Type annotation issues

### 3. MyPy Type Fixes (1-2 hours)
- Fix type errors in test files
- Add type annotations where missing
- Use `# type: ignore` sparingly and with specific codes

### 4. YAML/JSON Fixes (30 min)
- Trailing whitespace
- End of file issues
- YAML syntax validation

### 5. Configuration Updates (30 min)
- [ ] Copy `.pre-commit-config-ci.yaml` to `.pre-commit-config.yaml`
- [ ] Ensure all developers use same config as CI

### 6. GitHub Action Setup (30 min)
- [ ] Create `.github/workflows/lint.yml`
- [ ] Run same pre-commit checks as local
- [ ] Fail on any regression

### 7. Commit & Sign (15 min)
- [ ] Commit with label `lint-sweep-2025-07-14`
- [ ] Sign with Sigstore if available
- [ ] Ensure no functional code changes

### 8. Testing & Verification (30 min)
- [ ] Run full test suite to ensure no breakage
- [ ] Run `./scripts/test-like-ci.sh`
- [ ] Verify all pre-commit hooks pass

## Implementation Strategy

1. **Batch similar fixes** - Fix all instances of same error type together
2. **Use automated tools** - Let Black, isort handle formatting
3. **Test frequently** - Run tests after each major batch of fixes
4. **Commit incrementally** - Separate commits for different error types

## Expected Outcomes

- All files pass linting checks
- CI and local development perfectly aligned
- No more surprise CI failures
- Foundation set for Phase 4.1 infrastructure work

## Risks & Mitigations

- **Risk**: Breaking tests with import changes
  - **Mitigation**: Run tests after each batch of fixes

- **Risk**: Merge conflicts with ongoing work
  - **Mitigation**: Complete quickly, coordinate with team

- **Risk**: Over-fixing with type ignores
  - **Mitigation**: Fix properly where possible, document ignores
