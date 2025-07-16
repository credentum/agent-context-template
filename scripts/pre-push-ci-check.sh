#!/bin/bash

# Pre-push CI validation script
# Runs the same checks as GitHub Actions locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Running pre-push CI validation...${NC}"

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo -e "${GREEN}🌿 Current branch: $current_branch${NC}"

# Don't run CI checks for main branch
if [ "$current_branch" = "main" ]; then
    echo -e "${GREEN}✅ On main branch, skipping CI checks${NC}"
    exit 0
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker to run CI checks.${NC}"
    exit 1
fi

# Run Docker CI checks
echo -e "${YELLOW}🔍 Running Docker CI checks (this may take a few minutes)...${NC}"
if ./scripts/run-ci-docker.sh; then
    echo -e "${GREEN}✅ All CI checks passed!${NC}"
else
    echo -e "${RED}❌ CI checks failed!${NC}"
    echo -e "${RED}Please fix the issues above before pushing.${NC}"
    echo -e "${YELLOW}💡 Common fixes:${NC}"
    echo -e "${YELLOW}  • Run 'black src/ tests/ scripts/' to fix formatting${NC}"
    echo -e "${YELLOW}  • Run 'isort src/ tests/ scripts/' to fix imports${NC}"
    echo -e "${YELLOW}  • Check flake8 errors and fix manually${NC}"
    echo -e "${YELLOW}  • Run 'mypy src/' to check type annotations${NC}"
    echo -e "${YELLOW}  • Validate YAML files with yamllint${NC}"
    exit 1
fi

# Check if there are uncommitted changes after CI fixes
if ! git diff --quiet; then
    echo -e "${YELLOW}⚠️  Uncommitted changes detected after CI checks${NC}"
    echo -e "${YELLOW}Please commit any changes made by linters/formatters:${NC}"
    echo -e "${YELLOW}  git add -A && git commit --amend --no-edit${NC}"
    exit 1
fi

# Run branch sync check
echo -e "${YELLOW}🔍 Checking branch sync status...${NC}"
if ./scripts/check-branch-sync.sh; then
    echo -e "${GREEN}✅ Branch sync check passed!${NC}"
else
    echo -e "${RED}❌ Branch sync check failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 All pre-push checks passed! Safe to push.${NC}"
