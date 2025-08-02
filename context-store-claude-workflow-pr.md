# Pull Request: Add Claude Code Review Workflow to context-store

## PR Title
feat: Add Claude code review workflow for automated PR reviews

## PR Description
```markdown
## Description

This PR adds the Claude code review workflow from agent-context-template to enable automated PR reviews.

## Features
- 🤖 Automated code review on all PRs using Claude (ARC-Reviewer)
- 📊 Test coverage checks with configurable baselines
- 🔍 Code quality validation (pre-commit, linting, type checking)
- 🏷️ Automated issue generation for follow-up tasks
- ✅ GitHub status checks for blocking issues

## Setup Required
After merging, you'll need to:
1. Add the `CLAUDE_CODE_OAUTH_TOKEN` secret to the repository settings
2. Create a `.coverage-config.json` file if you want custom coverage thresholds (defaults to 78%)

## Testing
The workflow will automatically run on this PR once the token is configured.

Related to Sprint 5 implementation - improves development workflow for the context-store repository.
```

## Instructions to Create the PR

1. **Clone the context-store repository**:
   ```bash
   git clone https://github.com/credentum/context-store.git
   cd context-store
   ```

2. **Create a new branch**:
   ```bash
   git checkout -b feat/claude-code-review-workflow
   ```

3. **Create the workflow directory**:
   ```bash
   mkdir -p .github/workflows
   ```

4. **Create the workflow file** at `.github/workflows/claude-code-review.yml`:
   Copy the contents from the next section into this file.

5. **Commit the changes**:
   ```bash
   git add .github/workflows/claude-code-review.yml
   git commit -m "feat: Add Claude code review workflow for automated PR reviews

   - Adds ARC-Reviewer workflow from agent-context-template
   - Provides automated code review on all PRs
   - Checks test coverage, code quality, and MCP compatibility
   - Generates follow-up issues for improvements
   - Requires CLAUDE_CODE_OAUTH_TOKEN secret to be configured"
   ```

6. **Push the branch**:
   ```bash
   git push origin feat/claude-code-review-workflow
   ```

7. **Create the PR**:
   ```bash
   gh pr create --repo credentum/context-store \
     --title "feat: Add Claude code review workflow for automated PR reviews" \
     --body "$(cat pr-description.md)"
   ```

   Or create it via the GitHub web interface.

## Workflow File Content

The workflow file is located at: `/workspaces/agent-context-template/context-store-repo/.github/workflows/claude-code-review.yml`

This file is a complete adaptation of the agent-context-template Claude workflow, modified for the context-store repository.

Key changes made for context-store:
- Updated review prompt to mention "context-store" instead of "agent-context-template"
- Made coverage configuration flexible with fallback defaults
- Adapted allowed tools for context-store structure
- Kept all functionality for automated reviews and issue generation