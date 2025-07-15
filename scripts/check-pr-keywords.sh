#!/bin/bash
# Pre-commit hook to check for issue closing keywords in commit messages
# This helps ensure PRs will auto-close related issues

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Checking commit messages for issue references...${NC}"

# Get the commit message
if [ -n "$1" ]; then
    commit_msg="$1"
else
    commit_msg=$(git log -1 --pretty=%B)
fi

# Check if commit message contains issue closing keywords
if echo "$commit_msg" | grep -iqE "(closes?|fixes?|resolves?|implements?)\s+#[0-9]+"; then
    echo -e "${GREEN}✓ Found issue closing keywords in commit message${NC}"
    exit 0
fi

# Check if this is a feature/fix branch that might relate to an issue
branch_name=$(git branch --show-current 2>/dev/null || echo "unknown")
if echo "$branch_name" | grep -qE "(feature/|fix/|issue-)[0-9]+"; then
    issue_num=$(echo "$branch_name" | grep -oE "[0-9]+" | head -1)
    if [ -n "$issue_num" ]; then
        echo -e "${YELLOW}⚠️  Branch suggests this relates to issue #$issue_num${NC}"
        echo -e "${YELLOW}   Consider adding 'Closes #$issue_num' to your PR description${NC}"
        echo -e "${YELLOW}   This will auto-close the issue when the PR is merged${NC}"
    fi
fi

echo -e "${YELLOW}💡 Reminder: If this PR fixes an issue, add closing keywords to the PR description:${NC}"
echo -e "${YELLOW}   - Closes #123${NC}"
echo -e "${YELLOW}   - Fixes #123${NC}"
echo -e "${YELLOW}   - Resolves #123${NC}"
echo -e "${YELLOW}   - Implements #123${NC}"
echo ""
echo -e "${YELLOW}📋 The PR template will help you remember to add these keywords!${NC}"
echo -e "${YELLOW}🤖 Our GitHub Actions will automatically close referenced issues when the PR is merged.${NC}"

exit 0  # Don't block commits, just remind
