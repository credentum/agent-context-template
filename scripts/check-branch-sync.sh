#!/bin/bash

# Branch sync validation script
# Checks if current branch is up-to-date with main and has no conflicts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Checking branch sync status...${NC}"

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Don't check sync for main branch
if [ "$current_branch" = "main" ]; then
    echo -e "${GREEN}✅ On main branch, no sync check needed${NC}"
    exit 0
fi

# Fetch latest from origin
echo -e "${YELLOW}📡 Fetching latest from origin...${NC}"
git fetch origin main

# Check if we're behind main
behind_count=$(git rev-list --count HEAD..origin/main)
ahead_count=$(git rev-list --count origin/main..HEAD)

echo -e "${GREEN}📊 Branch status:${NC}"
echo -e "  Current branch: $current_branch"
echo -e "  Behind main: $behind_count commit(s)"
echo -e "  Ahead of main: $ahead_count commit(s)"

# Check for merge conflicts
echo -e "${YELLOW}🔍 Checking for potential merge conflicts...${NC}"

# Try to merge main into current branch (dry run)
if git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main | grep -q "^changed in both"; then
    echo -e "${RED}❌ MERGE CONFLICTS DETECTED${NC}"
    echo -e "${RED}Your branch has conflicts with main. Please resolve them first:${NC}"
    echo -e "${YELLOW}  1. git checkout main${NC}"
    echo -e "${YELLOW}  2. git pull origin main${NC}"
    echo -e "${YELLOW}  3. git checkout $current_branch${NC}"
    echo -e "${YELLOW}  4. git merge main${NC}"
    echo -e "${YELLOW}  5. Resolve conflicts and commit${NC}"
    exit 1
fi

# Check if branch is behind main
if [ "$behind_count" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Branch is $behind_count commit(s) behind main${NC}"
    echo -e "${YELLOW}Consider syncing with main:${NC}"
    echo -e "${YELLOW}  git checkout main && git pull origin main && git checkout $current_branch && git merge main${NC}"

    # For now, we'll allow this but warn
    echo -e "${YELLOW}⚠️  Continuing with sync warning...${NC}"
fi

# Check if branch is up-to-date
if [ "$behind_count" -eq 0 ] && [ "$ahead_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Branch is up-to-date with main${NC}"
elif [ "$behind_count" -eq 0 ] && [ "$ahead_count" -eq 0 ]; then
    echo -e "${GREEN}✅ Branch is identical to main${NC}"
fi

echo -e "${GREEN}✅ Branch sync check completed${NC}"
