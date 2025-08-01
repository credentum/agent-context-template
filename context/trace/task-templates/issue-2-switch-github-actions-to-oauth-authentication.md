# ────────────────────────────────────────────────────────────────────────
# TASK: issue-2-switch-github-actions-to-oauth-authentication
# Generated from GitHub Issue #2
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-2-switch-github-actions-to-oauth-authentication`

## 🎯 Goal (≤ 2 lines)
> Switch GitHub Actions to OAuth authentication

## 🧠 Context
- **GitHub Issue**: #2 - Switch GitHub Actions to OAuth authentication
- **Labels**: None
- **Component**: workflow-automation
- **Why this matters**: Resolves reported issue

## 🛠️ Subtasks
| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| TBD | TBD | TBD | TBD | TBD |

## 📝 Issue Description
## Summary
- Switched Claude GitHub Actions workflows from API key authentication to OAuth
- Updated both `claude.yml` and `claude-code-review.yml` to use `use_oauth: true`
- Removes the need to store `ANTHROPIC_API_KEY` in repository secrets

## Test plan
- [ ] Verify that Claude bot responds to @claude mentions in issues/PRs after merge
- [ ] Confirm automated PR reviews work without API key configuration
- [ ] Check that OAuth flow completes successfully in GitHub Actions logs

🤖 Generated with [Claude Code](https://claude.ai/code)

## 🔍 Verification & Testing
- Run CI checks locally
- Test the specific functionality
- Verify issue is resolved

## ✅ Acceptance Criteria
- Issue requirements are met
- Tests pass
- No regressions introduced
