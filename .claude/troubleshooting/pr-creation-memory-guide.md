# PR Creation Memory Guide for Claude

## Critical First Step
**ALWAYS CHECK TOKEN VALIDITY FIRST**

```bash
# Test 1: Check if token exists and is valid
curl -s -H "Authorization: token ${PERSONAL_ACCESS_TOKEN}" https://api.github.com/user | jq -r .login
```

If this returns `null` or "Bad credentials", the token is invalid or expired.

## Common Issues & Solutions

### Issue 1: Token Shows "Bad Credentials"
**This is the most common issue**

Even if `echo ${#PERSONAL_ACCESS_TOKEN}` shows 40 characters, the token may be:
1. Expired
2. Revoked
3. Incorrectly copied (with spaces or missing characters)
4. Not having the right permissions

**Solution**:
```bash
# First, verify the token format (should start with ghp_)
echo ${PERSONAL_ACCESS_TOKEN:0:4}  # Should show "ghp_"

# If not, the token is likely corrupted or incorrectly set
```

### Issue 2: Manual PR Creation When Token Fails

When autonomous creation fails, use this approach:

1. **Prepare the files locally**:
```bash
# Create a directory for manual PR prep
mkdir -p manual-pr-prep
cd manual-pr-prep

# Create the file(s) needed
# Example: Create workflow file
mkdir -p .github/workflows
cp /path/to/source/file .github/workflows/
```

2. **Create a patch file**:
```bash
git add .
git diff --cached > pr-changes.patch
```

3. **Generate PR instructions**:
```bash
cat > pr-instructions.md << 'EOF'
# Manual PR Creation Instructions

1. Clone the repository locally
2. Create a new branch
3. Apply the patch: git apply pr-changes.patch
4. Commit and push
5. Create PR via GitHub UI
EOF
```

### Issue 3: Alternative PR Creation Methods

1. **Using gh CLI with existing auth**:
```bash
# If gh is already authenticated (check with: gh auth status)
# Fork the repo first
gh repo fork OWNER/REPO --clone=false

# Then create PR from fork
```

2. **Using REST API directly**:
```bash
# If you have a valid token, use curl directly
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/pulls \
  -d '{"title":"Title","head":"branch","base":"main","body":"Description"}'
```

## Memory Checklist for PR Creation

1. ✅ First check: `curl -s -H "Authorization: token ${PERSONAL_ACCESS_TOKEN}" https://api.github.com/user | jq -r .login`
2. ✅ If fails: Token is bad, don't waste time trying the script
3. ✅ Alternative: Prepare files and instructions for manual creation
4. ✅ Document what was attempted for user transparency

## For Persistent Issues

When tokens consistently fail:
1. The codespace secret may need to be refreshed
2. The token may need to be regenerated with correct scopes
3. Organization settings may be blocking token access

## Success Indicators

You know the token is working when:
```bash
curl -s -H "Authorization: token ${PERSONAL_ACCESS_TOKEN}" https://api.github.com/user | jq -r .login
# Returns: actual username (not null)
```

## Quick Decision Tree

```
Is token valid? (curl test)
├─ Yes → Use autonomous script
└─ No → Token is bad
    ├─ Can regenerate? → Ask user to update token
    └─ Need PR now? → Create manual instructions
```