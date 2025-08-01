---
name: Autonomous PR Creation Issue
about: Report issues with autonomous PR creation
title: "[PR-AUTO] "
labels: bug, pr-automation
assignees: ''

---

## Issue Description
Brief description of the PR creation issue

## Error Details
```
Paste the exact error message here
```

## Environment
- **Repository**: (e.g., credentum/context-store)
- **Command Used**: (e.g., `./scripts/create-autonomous-pr.sh --repo ...`)
- **Codespace**: Yes/No
- **Token Type**: PERSONAL_ACCESS_TOKEN/GITHUB_TOKEN

## Troubleshooting Attempted
- [ ] Ran `unset GITHUB_TOKEN`
- [ ] Verified `PERSONAL_ACCESS_TOKEN` is set
- [ ] Tested authentication: `curl -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user`
- [ ] Checked token scopes (repo, workflow, read:org)
- [ ] Reviewed `.claude/troubleshooting/autonomous-pr-creation.md`

## Additional Context
Any other context about the problem

## Quick Diagnostic
Please run and paste the output:
```bash
echo "Token present: $(if [[ -n "$PERSONAL_ACCESS_TOKEN" ]]; then echo "YES (${PERSONAL_ACCESS_TOKEN:0:4}...)"; else echo "NO"; fi)"
echo "GITHUB_TOKEN override: $(if [[ -n "$GITHUB_TOKEN" ]]; then echo "YES (${GITHUB_TOKEN:0:4}...)"; else echo "NO"; fi)"
curl -s -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user | jq -r '.login // .message'
```