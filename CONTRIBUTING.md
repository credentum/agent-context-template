# Contributing Guidelines

## Branch Protection and Workflow

### For Repository Owners

Please set up the following branch protection rules for the `main` branch:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable these protections:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (at least 1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
     - Required checks: `lint` (from context-lint.yml workflow)
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators (optional but recommended)
   - ✅ Restrict who can push to matching branches (optional)

### For Contributors (including AI assistants)

**NEVER push directly to main!** Always follow this workflow:

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-description
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "type: description"
   ```

3. Push to your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create a pull request:
   ```bash
   gh pr create --title "type: description" --body "Details..."
   ```

5. Wait for CI checks to pass and get approval before merging

### Commit Message Format

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code changes that neither fix bugs nor add features
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### For AI Assistants (Claude, etc.)

When working with code:
1. Always create a new branch before making changes
2. Never use `git push origin main`
3. Always create a PR for review
4. Include clear PR descriptions with:
   - Summary of changes
   - Test plan
   - Any breaking changes

Example workflow:
```bash
# Start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b fix/mypy-errors

# Make changes
# ... edit files ...

# Commit changes
git add -A
git commit -m "fix: Address mypy type errors"

# Push to feature branch
git push -u origin fix/mypy-errors

# Create PR
gh pr create --title "fix: Address mypy type errors" --body "..."
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality. Install them:

```bash
pre-commit install
```

This will run automatically before each commit:
- Black formatting
- isort import sorting
- mypy type checking
- Custom context linting
