# Autonomous PR Creation Troubleshooting Guide

This guide documents the issues we discovered and their permanent solutions for creating pull requests autonomously from codespaces.

## 🎯 Quick Fix Commands

```bash
# 1. Fix authentication
unset GITHUB_TOKEN

# 2. Create PR using our script
./scripts/create-autonomous-pr.sh --repo credentum/context-store --title "feat: New feature" --body "Description"

# 3. Or use the helper alias
fix-pr-auth
create-pr --repo credentum/context-store --title "feat: New feature" --body "Description"
```

## 🔍 Root Causes We Discovered

### Issue 1: Authentication Override
**Problem**: `GITHUB_TOKEN` environment variable (codespace token) overrides personal access token
**Symptoms**: 
- `gh pr create` fails with "Resource not accessible by integration"
- API calls return "Bad credentials" despite valid token

**Solution**:
```bash
unset GITHUB_TOKEN  # Clear the environment variable
# Then use PERSONAL_ACCESS_TOKEN from codespace secrets
```

### Issue 2: Branch History Mismatch
**Problem**: Branch created with unrelated history (no common ancestor with main)
**Symptoms**: 
- Error: "branch has no history in common with main"

**Solution**:
```bash
git fetch origin main
git checkout origin/main
git checkout -b feature/new-branch
# Then make changes and commit
```

### Issue 3: GraphQL vs REST API
**Problem**: GitHub CLI GraphQL endpoint treats requests as "integration"
**Symptoms**: 
- "Resource not accessible by integration" error
- Works for git operations but not PR creation

**Solution**: Use REST API directly:
```bash
curl -X POST \
  -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/pulls \
  -d '{"title":"Title","head":"branch","base":"main","body":"Description"}'
```

## 🔧 Token Setup (One-Time)

### 1. Generate Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. **Required Scopes**:
   - ✅ `repo` (Full control of repositories)
   - ✅ `workflow` (Update GitHub Actions workflows)
   - ✅ `read:org` (Read organization membership)
   - ✅ `write:discussion` (Write team discussions)
4. Set expiration: 90 days or no expiration
5. Copy the token (starts with `ghp_`)

### 2. Add to Codespace Secrets
1. Go to: https://github.com/credentum/agent-context-template/settings/codespaces
2. Click "New repository secret"
3. Name: `PERSONAL_ACCESS_TOKEN`
4. Value: Your generated token
5. Save

### 3. Restart Codespace
After adding the secret, restart your codespace for it to take effect.

## 🚀 Automated Solutions

### Script: `scripts/create-autonomous-pr.sh`
Handles all the issues automatically:
- Fixes authentication
- Creates proper branch from main
- Uses REST API for PR creation
- Provides detailed error messages

### Codespace Configuration
`.devcontainer/postCreateCommand.sh` sets up:
- Helpful aliases
- Environment warnings
- Usage instructions

### Helper Commands
```bash
fix-pr-auth          # Clear GITHUB_TOKEN override
create-pr            # Alias for our script
autonomous-pr-help   # Show usage instructions
```

## 🧪 Testing Your Setup

1. **Test Authentication**:
```bash
curl -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user
```
Should return your GitHub username, not "Bad credentials"

2. **Test Repository Access**:
```bash
curl -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/repos/credentum/context-store
```
Should return repository information

3. **Create Test PR**:
```bash
./scripts/create-autonomous-pr.sh --repo credentum/context-store --title "test: PR creation" --body "Testing autonomous PR creation"
```

## 🚨 Common Errors & Solutions

### "Bad credentials"
- **Cause**: Invalid or expired token
- **Fix**: Generate new token and update `PERSONAL_ACCESS_TOKEN` secret

### "Resource not accessible by integration"
- **Cause**: Using GITHUB_TOKEN environment variable
- **Fix**: `unset GITHUB_TOKEN`

### "Branch has no history in common with main"
- **Cause**: Branch created from wrong base
- **Fix**: Use our script which creates branch from `origin/main`

### "Token scopes missing"
- **Cause**: Token lacks required permissions
- **Fix**: Regenerate token with `repo`, `workflow`, `read:org` scopes

## 📝 Historical Context

**Date**: August 1, 2025
**Issue**: PR creation worked 2 hours earlier but then failed
**Root Cause**: Multiple layered authentication and branch issues
**Resolution**: Ultra-deep investigation revealed all root causes
**Lesson**: GitHub CLI and API have different authentication behaviors in codespaces

## 🔄 Maintenance

### When Tokens Expire
1. Generate new token with same scopes
2. Update `PERSONAL_ACCESS_TOKEN` secret
3. Restart codespace
4. Test with our script

### When Adding New Repositories
Make sure the token has access to the target repository:
- Public repos: No additional setup needed
- Private repos: Token user must have write access
- Organization repos: May need organization approval for token

## ✅ Success Criteria

You know it's working when:
1. ✅ `curl -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user` returns your username
2. ✅ Our script creates PRs without errors
3. ✅ PR appears immediately on GitHub
4. ✅ No "Resource not accessible by integration" errors

This setup ensures autonomous PR creation works reliably every time!