#!/bin/bash
# validate-branch-for-pr.sh - Comprehensive branch validation before PR creation
#
# This script ensures:
# 1. Branch is not main
# 2. Branch is up-to-date with origin/main
# 3. No merge conflicts will occur
# 4. Branch is properly pushed to origin
# 5. CI checks pass after any rebase

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Main validation function
validate_branch_for_pr() {
    log_info "Starting branch validation for PR creation..."

    # 1. Branch Status Validation
    log_info "Step 1: Validating branch status..."

    CURRENT_BRANCH=$(git branch --show-current)
    log_info "Current branch: $CURRENT_BRANCH"

    # Ensure we're not on main
    if [ "$CURRENT_BRANCH" = "main" ]; then
        log_error "Cannot create PR from main branch"
        exit 1
    fi

    # Check for uncommitted changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        log_warning "Uncommitted changes detected:"
        git status --porcelain
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Aborting due to uncommitted changes"
            exit 1
        fi
    fi

    log_success "Branch status validation passed"

    # 2. Sync with main branch and detect conflicts
    log_info "Step 2: Syncing with main branch..."

    # Fetch latest changes
    log_info "Fetching latest changes from origin..."
    git fetch origin main

    # Check if main has moved ahead
    BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    if [ "$BEHIND" -gt 0 ]; then
        log_warning "Branch is $BEHIND commits behind origin/main"
        echo
        log_info "Recent commits on main:"
        git log --oneline HEAD..origin/main --max-count=5
        echo

        # Check for potential conflicts before rebasing
        log_info "Checking for potential merge conflicts..."
        MERGE_BASE=$(git merge-base HEAD origin/main)
        CONFLICTS=$(git merge-tree $MERGE_BASE HEAD origin/main 2>/dev/null || echo "")

        if [ -n "$CONFLICTS" ] && echo "$CONFLICTS" | grep -q "<<<<<<< "; then
            log_warning "POTENTIAL CONFLICTS DETECTED:"
            echo "$CONFLICTS" | head -20
            echo "..."
            echo
            read -p "Continue with rebase? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_error "Aborting PR creation. Please resolve conflicts manually."
                exit 1
            fi
        fi

        # Perform rebase
        log_info "Rebasing onto origin/main..."
        if ! git rebase origin/main; then
            log_error "REBASE FAILED - Conflicts detected"
            echo
            echo "Please resolve conflicts manually:"
            echo "1. Fix conflicts in the listed files"
            echo "2. Run: git add <resolved_files>"
            echo "3. Run: git rebase --continue"
            echo "4. Re-run this script when rebase is complete"
            exit 1
        fi

        log_success "Successfully rebased onto origin/main"
    else
        log_success "Branch is up-to-date with origin/main"
    fi

    # Verify clean rebase
    AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
    log_info "Branch status: $AHEAD commits ahead of main"

    # 3. Validate branch state
    log_info "Step 3: Validating branch push status..."

    # Ensure branch is pushed to origin (required for PR)
    REMOTE_BRANCH=$(git ls-remote --heads origin $CURRENT_BRANCH 2>/dev/null || echo "")
    if [ -z "$REMOTE_BRANCH" ]; then
        log_info "Pushing branch to origin for the first time..."
        git push -u origin $CURRENT_BRANCH
    else
        # Check if local is ahead of remote
        LOCAL_AHEAD=$(git rev-list --count origin/$CURRENT_BRANCH..HEAD 2>/dev/null || echo "0")
        if [ "$LOCAL_AHEAD" -gt 0 ]; then
            log_info "Pushing $LOCAL_AHEAD new commits to origin..."
            git push origin $CURRENT_BRANCH
        else
            log_success "Branch is up-to-date with remote"
        fi
    fi

    # 4. Final verification
    log_info "Step 4: Running final verification..."

    # Run CI checks to ensure everything still works after rebase
    log_info "Running final CI verification after rebase..."
    if command -v ./scripts/run-ci-docker.sh &> /dev/null; then
        if ! ./scripts/run-ci-docker.sh black; then
            log_error "CI checks failed after rebase - please fix issues"
            exit 1
        fi
    else
        log_warning "CI script not found, skipping CI verification"
    fi

    # Run pre-commit hooks if available
    if command -v pre-commit &> /dev/null; then
        log_info "Running pre-commit hooks..."
        if ! pre-commit run --all-files; then
            log_info "Pre-commit made changes, committing..."
            git add -A
            if git diff --cached --quiet; then
                log_info "No changes to commit after pre-commit"
            else
                git commit --amend --no-edit
                git push origin $CURRENT_BRANCH --force-with-lease
                log_success "Pushed pre-commit changes"
            fi
        fi
    else
        log_warning "pre-commit not installed, skipping hook validation"
    fi

    # Success!
    echo
    log_success "🎉 Branch validation completed successfully!"
    log_success "Branch '$CURRENT_BRANCH' is ready for PR creation"
    echo
    log_info "Next steps:"
    echo "1. Create PR with: gh pr create --title '...' --body '...'"
    echo "2. Or use the GitHub web interface"
    echo
}

# Script execution
main() {
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi

    # Check if GitHub CLI is available
    if ! command -v gh &> /dev/null; then
        log_warning "GitHub CLI (gh) not found - PR creation will need to be done manually"
    fi

    # Run validation
    validate_branch_for_pr
}

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Validates current branch for PR creation by ensuring:"
    echo "• Branch is not main"
    echo "• Branch is up-to-date with origin/main"
    echo "• No merge conflicts will occur"
    echo "• Branch is properly pushed to origin"
    echo "• CI checks pass after any rebase"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0            # Validate current branch"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
