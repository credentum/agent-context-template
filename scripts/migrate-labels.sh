#!/bin/bash
# GitHub Label Migration Script
# Standardizes labels across all issues and PRs
# Usage: ./migrate-labels.sh [--dry-run] [--verbose]

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
DRY_RUN=true  # Default to dry-run for safety
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --execute)
            DRY_RUN=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--dry-run|--execute] [--verbose]"
            exit 1
            ;;
    esac
done

# Print current mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}Running in DRY-RUN mode. No changes will be made.${NC}"
    echo -e "${YELLOW}Use --execute to apply changes.${NC}"
else
    echo -e "${RED}Running in EXECUTE mode. Changes WILL be made!${NC}"
    read -p "Are you sure you want to continue? (yes/no) " -n 3 -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo

# Define label mappings
declare -A label_map=(
    # Standardize phase labels
    ["phase-1"]="phase:1"
    ["phase-2"]="phase:2"
    ["phase-3"]="phase:3"
    ["phase-4"]="phase:4"
    ["phase-5"]="phase:5"

    # Component standardization
    ["testing"]="component:testing"
    ["test"]="component:testing"
    ["tests"]="component:testing"
    ["infrastructure"]="component:infra"
    ["ci"]="component:ci"
    ["ci/cd"]="component:ci"
    ["security"]="component:security"
    ["docs"]="component:docs"

    # Priority standardization
    ["urgent"]="priority:high"
    ["critical"]="priority:critical"
    ["p0"]="priority:critical"
    ["p1"]="priority:high"
    ["p2"]="priority:medium"
    ["p3"]="priority:low"

    # Sprint standardization
    ["current-sprint"]="sprint-current"
    ["sprint:current"]="sprint-current"
    ["next-sprint"]="sprint:next"

    # Type standardization
    ["feature"]="enhancement"
    ["feat"]="enhancement"
    ["bugfix"]="bug"
    ["fix"]="bug"
)

# Function to check if label exists
label_exists() {
    local label=$1
    gh label list --json name | jq -r '.[].name' | grep -q "^${label}$"
}

# Function to migrate labels for a single item
migrate_item_labels() {
    local item_type=$1  # "issue" or "pr"
    local item_number=$2
    local changes_made=false

    # Get current labels
    if [ "$item_type" = "issue" ]; then
        current_labels=$(gh issue view "$item_number" --json labels --jq '.labels[].name' 2>/dev/null || echo "")
    else
        current_labels=$(gh pr view "$item_number" --json labels --jq '.labels[].name' 2>/dev/null || echo "")
    fi

    if [ -z "$current_labels" ]; then
        return
    fi

    # Check each label
    while IFS= read -r label; do
        if [ -n "${label_map[$label]:-}" ]; then
            new_label="${label_map[$label]}"

            if [ "$VERBOSE" = true ]; then
                echo -e "  ${YELLOW}$label${NC} → ${GREEN}$new_label${NC}"
            fi

            if [ "$DRY_RUN" = false ]; then
                # Remove old label
                gh "$item_type" edit "$item_number" --remove-label "$label" 2>/dev/null || true
                # Add new label if it exists
                if label_exists "$new_label"; then
                    gh "$item_type" edit "$item_number" --add-label "$new_label" 2>/dev/null || true
                else
                    echo -e "  ${RED}Warning: Label '$new_label' does not exist${NC}"
                fi
            fi

            changes_made=true
        fi
    done <<< "$current_labels"

    if [ "$changes_made" = true ] && [ "$VERBOSE" = false ]; then
        echo -n "."
    fi
}

# Main migration logic
echo -e "${BLUE}Starting label migration...${NC}"
echo

# Count items to process
echo "Counting items to process..."
issue_count=$(gh issue list --state all --limit 1000 --json number | jq 'length')
pr_count=$(gh pr list --state all --limit 1000 --json number | jq 'length')
total_count=$((issue_count + pr_count))

echo "Found $issue_count issues and $pr_count PRs to check ($total_count total)"
echo

# Process issues
echo -e "${BLUE}Processing issues...${NC}"
issue_numbers=$(gh issue list --state all --limit 1000 --json number --jq '.[].number')
processed=0

while IFS= read -r issue_num; do
    if [ "$VERBOSE" = true ]; then
        echo "Issue #$issue_num:"
    fi

    migrate_item_labels "issue" "$issue_num"

    processed=$((processed + 1))
    if [ $((processed % 10)) -eq 0 ] && [ "$VERBOSE" = false ]; then
        echo -n " ($processed/$issue_count)"
    fi
done <<< "$issue_numbers"

if [ "$VERBOSE" = false ]; then
    echo " Done!"
fi

# Process PRs
echo -e "${BLUE}Processing pull requests...${NC}"
pr_numbers=$(gh pr list --state all --limit 1000 --json number --jq '.[].number')
processed=0

while IFS= read -r pr_num; do
    if [ "$VERBOSE" = true ]; then
        echo "PR #$pr_num:"
    fi

    migrate_item_labels "pr" "$pr_num"

    processed=$((processed + 1))
    if [ $((processed % 10)) -eq 0 ] && [ "$VERBOSE" = false ]; then
        echo -n " ($processed/$pr_count)"
    fi
done <<< "$pr_numbers"

if [ "$VERBOSE" = false ]; then
    echo " Done!"
fi

echo
echo -e "${GREEN}Migration complete!${NC}"

if [ "$DRY_RUN" = true ]; then
    echo
    echo -e "${YELLOW}This was a dry run. To apply changes, run:${NC}"
    echo "  $0 --execute"
fi

# Summary of label mappings
echo
echo -e "${BLUE}Label mappings used:${NC}"
for old_label in "${!label_map[@]}"; do
    echo "  $old_label → ${label_map[$old_label]}"
done | sort
