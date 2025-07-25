# Git Workflow Rules

## 🚨 CRITICAL: Never Push to Main

**NEVER push directly to main branch!** Always follow this workflow:

### Standard Git Workflow

1. **Start from updated main:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b fix/description
   # or
   git checkout -b feature/description
   # or
   git checkout -b chore/description
   ```

3. **Make changes and commit:**
   ```bash
   git add -A
   git commit -m "type: description"
   ```

4. **Push to feature branch:**
   ```bash
   git push -u origin fix/description
   ```

5. **Create PR:**
   ```bash
   gh pr create --title "type: description" --body "..."
   ```

### Branch Naming Conventions
- `feat/*` - New features
- `fix/*` - Bug fixes
- `chore/*` - Maintenance tasks
- `docs/*` - Documentation only
- `refactor/*` - Code refactoring

### Important Rules
- NEVER use `git push origin main`
- ALWAYS create a PR for code review
- Include test results in PR descriptions
- Wait for CI checks to pass before merging
- Prefer squash-merge for cleaner history

### Commit Message Format
Follow Conventional Commits:
```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
