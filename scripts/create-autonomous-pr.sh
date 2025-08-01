#!/bin/bash
# Autonomous PR Creation Script
# Fixes all the issues we discovered and creates PRs reliably

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Usage function
usage() {
    echo "Usage: $0 --repo OWNER/REPO --title 'PR Title' --body 'PR Body' [--branch BRANCH_NAME]"
    echo ""
    echo "Example:"
    echo "  $0 --repo credentum/context-store --title 'feat: Add new schemas' --body 'Comprehensive schema collection'"
    echo ""
    echo "Options:"
    echo "  --repo      Target repository (required)"
    echo "  --title     PR title (required)"
    echo "  --body      PR description (required)"
    echo "  --branch    Branch name (optional, auto-generated if not provided)"
    echo "  --base      Base branch (optional, defaults to main)"
    echo "  --help      Show this help message"
    exit 1
}

# Parse command line arguments
REPO=""
TITLE=""
BODY=""
BRANCH=""
BASE="main"

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --title)
            TITLE="$2"
            shift 2
            ;;
        --body)
            BODY="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --base)
            BASE="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REPO" || -z "$TITLE" || -z "$BODY" ]]; then
    print_error "Missing required arguments"
    usage
fi

# Generate branch name if not provided
if [[ -z "$BRANCH" ]]; then
    TIMESTAMP=$(date +%s)
    BRANCH="feature/auto-pr-${TIMESTAMP}"
fi

print_status "Starting autonomous PR creation..."
echo "Repository: $REPO"
echo "Title: $TITLE"
echo "Branch: $BRANCH"
echo "Base: $BASE"
echo ""

# Step 1: Fix authentication issues
print_status "Step 1: Configuring authentication..."

# Unset GITHUB_TOKEN to avoid override issues
if [[ -n "$GITHUB_TOKEN" ]]; then
    print_warning "GITHUB_TOKEN environment variable detected - unsetting to use personal token"
    unset GITHUB_TOKEN
fi

# Check if we have PERSONAL_ACCESS_TOKEN
if [[ -z "$PERSONAL_ACCESS_TOKEN" ]]; then
    print_error "PERSONAL_ACCESS_TOKEN not found. Please set it as a codespace secret."
    echo ""
    echo "To fix:"
    echo "1. Go to: https://github.com/$(echo "$REPO" | cut -d'/' -f1)/$(basename "$(pwd)")/settings/codespaces"
    echo "2. Add secret: PERSONAL_ACCESS_TOKEN"
    echo "3. Generate token at: https://github.com/settings/tokens"
    echo "4. Required scopes: repo, workflow, read:org"
    exit 1
fi

# Test authentication
print_status "Testing authentication..."
AUTH_TEST=$(curl -s -H "Authorization: token $PERSONAL_ACCESS_TOKEN" https://api.github.com/user | jq -r '.login // "error"')

if [[ "$AUTH_TEST" == "error" ]]; then
    print_error "Authentication failed. Token may be invalid or expired."
    echo ""
    echo "To fix:"
    echo "1. Generate new token at: https://github.com/settings/tokens"
    echo "2. Required scopes: repo, workflow, read:org, write:discussion"
    echo "3. Update codespace secret: PERSONAL_ACCESS_TOKEN"
    exit 1
fi

print_success "Authenticated as: $AUTH_TEST"

# Step 2: Setup proper git branch
print_status "Step 2: Setting up git branch..."

# Fetch latest from remote
git fetch origin "$BASE" || {
    print_error "Failed to fetch $BASE branch from origin"
    exit 1
}

# Create branch from the base branch
git checkout "origin/$BASE" || {
    print_error "Failed to checkout origin/$BASE"
    exit 1
}

git checkout -b "$BRANCH" || {
    print_error "Failed to create branch $BRANCH"
    exit 1
}

print_success "Created branch: $BRANCH"

# Step 3: Check if there are changes to commit
print_status "Step 3: Checking for changes..."

if git diff --quiet && git diff --staged --quiet; then
    print_warning "No changes detected. Make sure you have made changes before running this script."
    echo ""
    echo "To fix:"
    echo "1. Make your changes"
    echo "2. Add files: git add ."
    echo "3. Run this script again"
    exit 1
fi

# Step 4: Commit changes if any are staged
if ! git diff --staged --quiet; then
    print_status "Step 4: Committing staged changes..."
    git commit -m "$TITLE

$BODY

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" || {
        print_error "Failed to commit changes"
        exit 1
    }
    print_success "Changes committed"
fi

# Step 5: Push branch
print_status "Step 5: Pushing branch to remote..."

git push -u origin "$BRANCH" || {
    print_error "Failed to push branch to remote"
    exit 1
}

print_success "Branch pushed successfully"

# Step 6: Create PR using REST API
print_status "Step 6: Creating pull request..."

# Escape JSON strings
TITLE_ESCAPED=$(echo "$TITLE" | sed 's/"/\\"/g')
BODY_ESCAPED=$(echo "$BODY" | sed 's/"/\\"/g')

# Create PR via REST API
PR_RESPONSE=$(curl -s -X POST \
    -H "Authorization: token $PERSONAL_ACCESS_TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$REPO/pulls" \
    -d "{
        \"title\": \"$TITLE_ESCAPED\",
        \"head\": \"$BRANCH\",
        \"base\": \"$BASE\",
        \"body\": \"$BODY_ESCAPED\"
    }")

# Check if PR was created successfully
PR_URL=$(echo "$PR_RESPONSE" | jq -r '.html_url // empty')
PR_NUMBER=$(echo "$PR_RESPONSE" | jq -r '.number // empty')
ERROR_MESSAGE=$(echo "$PR_RESPONSE" | jq -r '.message // empty')

if [[ -n "$PR_URL" && -n "$PR_NUMBER" ]]; then
    print_success "PR created successfully!"
    echo ""
    echo "🔗 PR #$PR_NUMBER: $PR_URL"
    echo ""
    echo "✅ Autonomous PR creation completed!"
else
    print_error "Failed to create PR"
    echo "Error: $ERROR_MESSAGE"
    echo ""
    echo "Response: $PR_RESPONSE"
    exit 1
fi