# Enhanced Fix GitHub Issue Workflow

## Critical Missing Steps in Original Workflow

### 1. Pre-Implementation Validation (MISSING)
**When**: After Phase 1 Planning, before Phase 2 Implementation
**What**: Validate the approach will work
```bash
# Test schema changes won't break validation
python -m src.agents.context_lint validate context/ --dry-run

# Check if any files depend on the schemas
grep -r "schemas/" . --include="*.py" --include="*.yaml"
```

### 2. CI Validation Before Commit (CRITICAL - MISSING)
**When**: After Phase 2 Implementation, before ANY commits
**What**: Run CI to catch issues early
```bash
# Run pre-commit hooks BEFORE committing
pre-commit run --all-files

# If hooks modify files, stage those changes
git add -A

# Run Docker CI
./scripts/run-ci-docker.sh

# Only commit if CI passes
```

### 3. Branch Validation Script (MISSING)
**When**: Before Phase 4 PR Creation
**What**: Use the provided validation script
```bash
# This script handles rebasing, conflicts, and push
./scripts/validate-branch-for-pr.sh
```

### 4. Agent Delegation Verification (MISSING)
**When**: Throughout workflow
**What**: Ensure proper agent delegation

## Corrected Phase Execution Order

### Phase 0: Investigation (If Needed)
- **Agent**: issue-investigator
- **Validation**: Confirm scope is clear before proceeding

### Phase 1: Planning
- **Agent**: task-planner
- **Output**: issue_[NUMBER]_tasks.md
- **Validation**: Review task plan completeness

### Phase 2: Implementation
- **Agent**: main Claude (or appropriate specialist)
- **Critical Steps**:
  1. Create feature branch
  2. Implement changes
  3. **Run pre-commit hooks** (MISSING IN ORIGINAL)
  4. **Fix any hook issues** (MISSING IN ORIGINAL)
  5. **Run CI validation** (MISSING IN ORIGINAL)
  6. Only commit after validation passes

### Phase 3: Testing & Validation
- **Agent**: test-runner
- **Critical Steps**:
  1. Run Docker CI: `./scripts/run-ci-docker.sh`
  2. Run all tests
  3. Verify coverage maintained
  4. **Document all test results**

### Phase 4: PR Creation
- **Agent**: pr-manager
- **Critical Steps**:
  1. **Run branch validation script** (MISSING IN ORIGINAL)
  2. Ensure all changes committed
  3. Push branch
  4. Create PR with proper description
  5. Apply labels

### Phase 5: Monitoring
- **Agent**: pr-manager
- **Track**: CI status, reviews, merge

## Common Failures and Solutions

### 1. Pre-commit Hook Failures
**Issue**: Files modified by hooks after commit attempt
**Solution**:
```bash
# Stage hook changes
git add -A
# Re-run hooks to ensure clean
pre-commit run --all-files
# Then commit
```

### 2. Schema Validation Failures
**Issue**: Yamale expects multi-document format
**Solution**: Use schema adapter pattern or maintain Yamale format

### 3. CI Pipeline Failures
**Issue**: Docker CI not run before PR
**Solution**: Always run `./scripts/run-ci-docker.sh` before creating PR

## Workflow Automation Script

```bash
#!/bin/bash
# Automated workflow with proper validation

# Phase 2: After implementation
echo "Running pre-commit hooks..."
pre-commit run --all-files || {
    echo "Pre-commit hooks failed, fixing..."
    git add -A
    pre-commit run --all-files
}

# Phase 3: Validation
echo "Running Docker CI..."
./scripts/run-ci-docker.sh || {
    echo "CI failed! Fix issues before proceeding"
    exit 1
}

# Phase 4: Pre-PR validation
echo "Validating branch..."
./scripts/validate-branch-for-pr.sh || {
    echo "Branch validation failed!"
    exit 1
}

# Only then create PR
echo "Creating PR..."
gh pr create ...
```

## Key Learnings

1. **Never skip CI validation** - Run before committing
2. **Use provided scripts** - They handle edge cases
3. **Delegate properly** - Each agent has specific expertise
4. **Validate at each step** - Don't assume success
5. **Handle hook modifications** - Stage changes from hooks

## Updated Workflow Command

```bash
# Enhanced workflow with validation
/workflow-issue 123 --validate-each-phase --use-ci-scripts
```
