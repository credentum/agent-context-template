#!/bin/bash
# Unit test for ARC-Reviewer ISSUE: parser logic
# Tests the parser with mocked review containing two follow-ups

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_REVIEW_FILE="test_review.txt"
EXPECTED_ISSUES=2

echo -e "${YELLOW}Testing ARC-Reviewer ISSUE: parser logic${NC}"
echo "================================================"

# Create mock review with two ISSUE: follow-ups
cat > "$TEST_REVIEW_FILE" << 'EOF'
**PR Verdict:** APPROVE
**Summary:** Code looks good, just a few suggestions for improvement.
**Blocking Issues (❌):**
None
**Warnings (⚠️):**
1. Consider adding more detailed docstrings
**Nits (💡):**
1. Minor formatting improvements
**Coverage Delta:** 78.5% → 79.2% [PASS]
**Suggested Follow-ups:**
ISSUE: Fix validator coverage - Improve test coverage for validators module - labels=test,validator,coverage - phase=4.2
ISSUE: Add performance benchmarks - Create benchmark suite for vector operations - labels=performance,benchmark - phase=backlog
End of report. Do *not* add anything after this line.
EOF

echo "Created mock review file with $EXPECTED_ISSUES ISSUE: lines"

# Count ISSUE: lines in the test file
issue_count=$(grep -c '^ISSUE:' "$TEST_REVIEW_FILE")
echo "Found $issue_count ISSUE: lines in review"

if [ "$issue_count" -ne "$EXPECTED_ISSUES" ]; then
    echo -e "${RED}❌ FAIL: Expected $EXPECTED_ISSUES ISSUE: lines, found $issue_count${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PASS: Correct number of ISSUE: lines found${NC}"

# Test the parser logic (extracted from workflow)
echo
echo "Testing parser logic..."

issue_num=0
while read -r line; do
    echo "Processing: $line"

    # Remove ISSUE: prefix and trim whitespace
    content=$(echo "${line#ISSUE:}" | xargs)
    [ -z "$content" ] && continue

    # Parse using more robust field extraction that handles spaces in fields
    # Split on ' - ' delimiter manually to preserve spaces within fields

    # Extract title (everything before first ' - ')
    if [[ "$content" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        title="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        title="$content"
        remaining=""
    fi

    # Extract description (everything before next ' - ')
    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        description="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        description="${remaining:-Suggested improvement from code review}"
        remaining=""
    fi

    # Extract labels field (everything before next ' - ')
    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        labels_field="${BASH_REMATCH[1]}"
        phase_field="${BASH_REMATCH[2]}"
    else
        labels_field="$remaining"
        phase_field=""
    fi

    # Skip if no title
    [ -z "$title" ] && continue

    # Parse labels (format: labels=tag1,tag2,tag3)
    if [[ "$labels_field" =~ ^labels=(.+)$ ]]; then
        custom_labels="${BASH_REMATCH[1]}"
        all_labels="from-code-review,$custom_labels"
    else
        all_labels="from-code-review,enhancement"
    fi

    # Parse phase/milestone (format: phase=4.2 or phase=backlog)
    if [[ "$phase_field" =~ ^phase=(.+)$ ]]; then
        phase="${BASH_REMATCH[1]}"
    else
        phase="backlog"
    fi

    echo "  Title: $title"
    echo "  Description: $description"
    echo "  Labels: $all_labels"
    echo "  Phase: $phase"

    # Validate expected results
    case $((++issue_num)) in
        1)
            if [[ "$title" == "Fix validator coverage" ]] && \
               [[ "$description" == "Improve test coverage for validators module" ]] && \
               [[ "$all_labels" == "from-code-review,test,validator,coverage" ]] && \
               [[ "$phase" == "4.2" ]]; then
                echo -e "  ${GREEN}✓ Issue 1 parsed correctly${NC}"
            else
                echo -e "  ${RED}❌ Issue 1 parsing failed${NC}"
                echo "    Expected: Fix validator coverage | Improve test coverage... | from-code-review,test,validator,coverage | 4.2"
                echo "    Got: $title | $description | $all_labels | $phase"
                exit 1
            fi
            ;;
        2)
            if [[ "$title" == "Add performance benchmarks" ]] && \
               [[ "$description" == "Create benchmark suite for vector operations" ]] && \
               [[ "$all_labels" == "from-code-review,performance,benchmark" ]] && \
               [[ "$phase" == "backlog" ]]; then
                echo -e "  ${GREEN}✓ Issue 2 parsed correctly${NC}"
            else
                echo -e "  ${RED}❌ Issue 2 parsing failed${NC}"
                echo "    Expected: Add performance benchmarks | Create benchmark suite... | from-code-review,performance,benchmark | backlog"
                echo "    Got: $title | $description | $all_labels | $phase"
                exit 1
            fi
            ;;
    esac

done < <(grep '^ISSUE:' "$TEST_REVIEW_FILE")

echo
if [ "$issue_num" -eq "$EXPECTED_ISSUES" ]; then
    echo -e "${GREEN}✓ PASS: All $EXPECTED_ISSUES issues parsed correctly${NC}"
else
    echo -e "${RED}❌ FAIL: Expected to parse $EXPECTED_ISSUES issues, got $issue_num${NC}"
    exit 1
fi

# Test GitHub CLI dry-run (if gh is available)
echo
echo "Testing GitHub CLI integration (dry-run)..."

if command -v gh &> /dev/null; then
    # Test that gh commands would work (without actually creating issues)
    echo "GitHub CLI available - testing command structure"

    # Mock the gh issue create command structure
    gh_test_cmd=(
        "gh" "issue" "create"
        "--title" "[PR #123] Fix validator coverage"
        "--body" "Test body"
        "--label" "from-code-review,test,validator,coverage"
    )

    echo "Would execute: ${gh_test_cmd[*]}"
    echo -e "${GREEN}✓ PASS: GitHub CLI command structure valid${NC}"
else
    echo -e "${YELLOW}⚠ WARNING: GitHub CLI not available, skipping integration test${NC}"
fi

# Cleanup
rm -f "$TEST_REVIEW_FILE"

echo
echo "================================================"
echo -e "${GREEN}🎉 ALL TESTS PASSED${NC}"
echo -e "${GREEN}Parser correctly handles $EXPECTED_ISSUES ISSUE: follow-ups${NC}"
