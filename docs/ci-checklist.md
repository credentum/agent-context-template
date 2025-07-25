# Claude CI Checklist

Before creating any PR, ensure all items are checked. This checklist is designed to prevent CI failures and ensure code quality.

## 🔍 Pre-Flight Checklist

### Git Status
- [ ] Currently on feature branch (not main)
  ```bash
  git branch --show-current  # Should NOT show "main"
  ```
- [ ] All changes committed locally
  ```bash
  git status  # Should show "nothing to commit, working tree clean"
  ```
- [ ] Branch is up to date with main
  ```bash
  git fetch origin main
  git merge origin/main  # or rebase
  ```
- [ ] No merge conflicts

## 📝 Code Quality Checklist

### Formatting
- [ ] Python code formatted with Black
  ```bash
  ./scripts/claude-ci.sh check src/ --fix
  ```
- [ ] Imports sorted with isort
  ```bash
  ./scripts/claude-ci.sh check src/ --fix
  ```
- [ ] YAML files properly formatted
  ```bash
  yamllint context/ -f parsable
  ```

### Linting
- [ ] No Flake8 errors
  ```bash
  flake8 src/ tests/
  ```
- [ ] No commented-out code (except for documentation)
- [ ] No debug print statements
- [ ] No TODO comments without issue numbers

### Type Safety
- [ ] All functions have type hints
- [ ] MyPy passes without errors
  ```bash
  mypy src/
  ```
- [ ] No `type: ignore` without justification comment

## 🧪 Testing Checklist

### Test Coverage
- [ ] All new code has tests
- [ ] Tests pass locally
  ```bash
  ./scripts/claude-ci.sh test
  ```
- [ ] Coverage above 78.0% (current baseline)
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```
- [ ] No skipped tests without justification

### Test Quality
- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases
- [ ] Integration tests updated if needed
- [ ] No hardcoded test data that could break

## 🔒 Security Checklist

### Secrets Management
- [ ] No hardcoded passwords
- [ ] No API keys in code
- [ ] No tokens or credentials
- [ ] Environment variables used for secrets
- [ ] No sensitive data in logs

### Dependencies
- [ ] No new vulnerable dependencies
- [ ] Dependencies pinned to specific versions
- [ ] requirements.txt updated if needed

## 📚 Documentation Checklist

### Code Documentation
- [ ] All public functions have docstrings
- [ ] Complex logic has inline comments
- [ ] README updated if needed
- [ ] API changes documented

### Project Documentation
- [ ] CLAUDE.md updated if adding new commands
- [ ] Context files updated if design changes
- [ ] Sprint documents reflect completed work
- [ ] Architecture decisions documented

## 🔄 CI Pipeline Checklist

### Pre-Push Validation
- [ ] Run full CI locally
  ```bash
  ./scripts/claude-ci.sh all
  ```
- [ ] All checks pass
- [ ] No warnings that could become errors

### Quick Validation Commands
```bash
# Quick check (30 seconds)
./scripts/claude-ci.sh all --quick

# Fix all issues automatically
./scripts/claude-ci.sh fix-all

# Comprehensive check before PR
./scripts/claude-ci.sh all --comprehensive
```

## 📊 Final Review Checklist

### Code Review Preparation
- [ ] Self-review all changes
- [ ] Remove any experimental code
- [ ] Ensure consistent code style
- [ ] Check for obvious bugs

### PR Readiness
- [ ] Descriptive commit messages following convention
  ```
  type(scope): description

  Examples:
  feat(storage): add vector similarity search
  fix(validators): handle empty input gracefully
  docs(ci): update testing guide
  ```
- [ ] PR title describes the change
- [ ] PR body includes:
  - [ ] What changed and why
  - [ ] How to test
  - [ ] Screenshots if UI changes
  - [ ] Related issue numbers with closing keywords

### Issue Closing Keywords
Ensure PR description includes one of these to auto-close issues:
- `Closes #123`
- `Fixes #123`
- `Resolves #123`
- `Implements #123`

## 🚀 Quick Commands Reference

```bash
# After making changes
./scripts/claude-ci.sh check <file> --fix

# Before committing
./scripts/claude-ci.sh pre-commit --fix

# Run tests
./scripts/claude-ci.sh test

# Before creating PR
./scripts/claude-ci.sh all --auto-fix-all

# If something fails
./scripts/claude-ci.sh fix-all
```

## ⚡ Emergency Fixes

If CI fails after push:

1. **Don't panic** - Check the specific failure
2. **Run locally** - `./scripts/claude-ci.sh all --verbose`
3. **Auto-fix** - `./scripts/claude-ci.sh fix-all`
4. **Manual fix** - Address issues that can't be auto-fixed
5. **Verify** - Run CI again before pushing

## 📈 Performance Tips

- Use `--quick` mode during development
- Run `--comprehensive` only before PR
- Cache is your friend - don't clean unless necessary
- Smart tests save time - trust the selection

## 🎯 Success Criteria

Your PR is ready when:
- ✅ All checklist items completed
- ✅ `claude-ci all` returns "PASSED"
- ✅ Coverage meets or exceeds baseline
- ✅ No security issues flagged
- ✅ ARC Reviewer verdict: APPROVE
- ✅ You've self-reviewed the changes

---

*Remember: A few minutes of local validation saves hours of CI debugging!*
