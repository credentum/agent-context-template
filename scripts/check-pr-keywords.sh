#!/bin/bash

# Check PR Keywords Script
# Helps developers validate their PR has proper closing keywords before pushing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Checking PR for issue closing keywords...${NC}"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get current branch
current_branch=$(git branch --show-current)

if [ "$current_branch" = "main" ]; then
    echo -e "${YELLOW}⚠️  You're on the main branch. Create a feature branch first.${NC}"
    exit 1
fi

# Check if PR template exists
template_file=".github/pull_request_template.md"
if [ -f "$template_file" ]; then
    echo -e "${GREEN}✅ PR template found${NC}"
else
    echo -e "${YELLOW}⚠️  No PR template found${NC}"
fi

# Get recent commits for keyword checking
echo -e "\n${BLUE}📝 Checking recent commits for closing keywords...${NC}"

# Get commits since main branch
commits=$(git log --oneline main..HEAD --format="%s" 2>/dev/null || git log --oneline -5 --format="%s")

# Keywords to search for
keywords_regex="(closes?|close|closed|closing|fixes?|fix|fixed|fixing|resolves?|resolve|resolved|resolving|implements?|implement|implemented|implementing|addresses?|address|addressed|addressing|completes?|complete|completed|completing)\s+#[0-9]+"

# Check commits
found_keywords=false
while IFS= read -r commit_msg; do
    if echo "$commit_msg" | grep -iE "$keywords_regex" > /dev/null; then
        echo -e "${GREEN}✅ Found closing keywords in commit: $commit_msg${NC}"
        found_keywords=true
    fi
done <<< "$commits"

# Check if there are any staged changes that might contain keywords
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  No staged changes found${NC}"
else
    echo -e "${GREEN}✅ Staged changes detected${NC}"
fi

# Show example usage
echo -e "\n${BLUE}💡 Closing Keywords Examples:${NC}"
echo "  - closes #123"
echo "  - fixes #456"
echo "  - resolves #789"
echo "  - implements #101"
echo "  - addresses #202"
echo "  - completes #303"

# Check if gh CLI is available
if command -v gh > /dev/null 2>&1; then
    echo -e "\n${BLUE}🔧 GitHub CLI detected. You can create a PR with:${NC}"
    echo "  gh pr create --title \"feat: your feature description\" --body \"Closes #123\""

    # Check for existing PR
    existing_pr=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "")
    if [ -n "$existing_pr" ]; then
        echo -e "${GREEN}✅ PR #$existing_pr already exists for this branch${NC}"

        # Check PR body for keywords
        pr_body=$(gh pr view --json body --jq '.body' 2>/dev/null || echo "")
        if echo "$pr_body" | grep -iE "$keywords_regex" > /dev/null; then
            echo -e "${GREEN}✅ PR body contains closing keywords${NC}"
        else
            echo -e "${YELLOW}⚠️  PR body doesn't contain closing keywords${NC}"
            echo -e "${BLUE}💡 Update your PR description to include closing keywords${NC}"
        fi
    fi
else
    echo -e "\n${YELLOW}⚠️  GitHub CLI not found. Install with: brew install gh${NC}"
fi

# Summary
echo -e "\n${BLUE}📋 Summary:${NC}"
if [ "$found_keywords" = true ]; then
    echo -e "${GREEN}✅ Closing keywords found in commits${NC}"
else
    echo -e "${YELLOW}⚠️  No closing keywords found in commits${NC}"
    echo -e "${BLUE}💡 Add closing keywords to your PR description or commit messages${NC}"
fi

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo "1. Ensure your PR description contains closing keywords"
echo "2. Run tests: make lint && pytest"
echo "3. Create/update PR: gh pr create or gh pr edit"
echo "4. Verify validation checks pass"

echo -e "\n${GREEN}✅ PR keyword check complete${NC}"
