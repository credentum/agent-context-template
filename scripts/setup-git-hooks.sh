#!/bin/bash

# Setup git hooks for the project
# This script installs the pre-push hook and other git hooks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up git hooks...${NC}"

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get the git hooks directory
hooks_dir="$(git rev-parse --git-dir)/hooks"

# Make sure the hooks directory exists
mkdir -p "$hooks_dir"

# Install pre-push hook
echo -e "${YELLOW}📦 Installing pre-push hook...${NC}"
if [ -f ".githooks/pre-push" ]; then
    cp ".githooks/pre-push" "$hooks_dir/pre-push"
    chmod +x "$hooks_dir/pre-push"
    echo -e "${GREEN}✅ Pre-push hook installed${NC}"
else
    echo -e "${RED}❌ Pre-push hook source not found${NC}"
    exit 1
fi

# Make scripts executable
echo -e "${YELLOW}🔧 Making scripts executable...${NC}"
chmod +x scripts/check-branch-sync.sh
chmod +x scripts/pre-push-ci-check.sh
chmod +x scripts/setup-git-hooks.sh

if [ -f "scripts/run-ci-docker.sh" ]; then
    chmod +x scripts/run-ci-docker.sh
fi

echo -e "${GREEN}✅ Git hooks setup complete!${NC}"
echo -e "${GREEN}📋 Installed hooks:${NC}"
echo -e "${GREEN}  • pre-push: Runs CI checks and branch sync validation${NC}"
echo -e "${YELLOW}💡 Hook behavior:${NC}"
echo -e "${YELLOW}  • Runs automatically before 'git push'${NC}"
echo -e "${YELLOW}  • Skipped for main branch${NC}"
echo -e "${YELLOW}  • Can be bypassed with 'git push --no-verify'${NC}"
echo -e "${YELLOW}  • Emergency bypass: 'EMERGENCY_PUSH=1 git push'${NC}"
echo -e "${YELLOW}  • Skip entirely: 'SKIP_HOOKS=1 git push'${NC}"
