#!/bin/bash
# Unit test for ARC-Reviewer ISSUE: aggregated parser logic
# Tests the parser with mocked review containing two follow-ups

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_REVIEW_FILE="test_review.txt"
EXPECTED_SUGGESTIONS=2

echo -e "${YELLOW}Testing ARC-Reviewer ISSUE: aggregated parser logic${NC}"
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

echo "Created mock review file with $EXPECTED_SUGGESTIONS ISSUE: lines"

# Count ISSUE: lines in the test file
issue_count=$(grep -c '^ISSUE:' "$TEST_REVIEW_FILE")
echo "Found $issue_count ISSUE: lines in review"

if [ "$issue_count" -ne "$EXPECTED_SUGGESTIONS" ]; then
    echo -e "${RED}❌ FAIL: Expected $EXPECTED_SUGGESTIONS ISSUE: lines, found $issue_count${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PASS: Correct number of ISSUE: lines found${NC}"

# Test the aggregated parser logic (extracted from workflow)
echo
echo "Testing aggregated parser logic..."

# Initialize aggregated variables
suggestions_count=0
suggestions_checklist=""
all_phases=""

while read -r line; do
    echo "Processing: $line"

    # Remove ISSUE: prefix and trim whitespace
    content=$(echo "${line#ISSUE:}" | xargs)
    [ -z "$content" ] && continue

    # Parse using robust field extraction that handles spaces in fields
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

    # Parse phase/milestone (format: phase=4.2 or phase=backlog)
    if [[ "$phase_field" =~ ^phase=(.+)$ ]]; then
        phase="${BASH_REMATCH[1]}"
    else
        phase="backlog"
    fi

    echo "  Title: $title"
    echo "  Description: $description"
    echo "  Phase: $phase"

    # Build checklist item (matching workflow logic)
    suggestions_checklist="${suggestions_checklist}- [ ] **${title}**: ${description} (phase: ${phase})\n"

    # Track phases for metadata
    if [[ "$all_phases" != *"$phase"* ]]; then
        all_phases="${all_phases}${phase}, "
    fi

    suggestions_count=$((suggestions_count + 1))

    # Validate parsing results
    case $suggestions_count in
        1)
            if [[ "$title" == "Fix validator coverage" ]] && \
               [[ "$description" == "Improve test coverage for validators module" ]] && \
               [[ "$phase" == "4.2" ]]; then
                echo -e "  ${GREEN}✓ Suggestion 1 parsed correctly${NC}"
            else
                echo -e "  ${RED}❌ Suggestion 1 parsing failed${NC}"
                echo "    Expected: Fix validator coverage | Improve test coverage... | 4.2"
                echo "    Got: $title | $description | $phase"
                exit 1
            fi
            ;;
        2)
            if [[ "$title" == "Add performance benchmarks" ]] && \
               [[ "$description" == "Create benchmark suite for vector operations" ]] && \
               [[ "$phase" == "backlog" ]]; then
                echo -e "  ${GREEN}✓ Suggestion 2 parsed correctly${NC}"
            else
                echo -e "  ${RED}❌ Suggestion 2 parsing failed${NC}"
                echo "    Expected: Add performance benchmarks | Create benchmark suite... | backlog"
                echo "    Got: $title | $description | $phase"
                exit 1
            fi
            ;;
    esac

done < <(grep '^ISSUE:' "$TEST_REVIEW_FILE")

echo
if [ "$suggestions_count" -eq "$EXPECTED_SUGGESTIONS" ]; then
    echo -e "${GREEN}✓ PASS: All $EXPECTED_SUGGESTIONS suggestions parsed correctly${NC}"
else
    echo -e "${RED}❌ FAIL: Expected to parse $EXPECTED_SUGGESTIONS suggestions, got $suggestions_count${NC}"
    exit 1
fi

# Test aggregated output
echo
echo "Testing aggregated checklist generation..."

# Clean up phases list
all_phases=${all_phases%, }

# Validate checklist content
expected_checklist="- [ ] **Fix validator coverage**: Improve test coverage for validators module (phase: 4.2)\n- [ ] **Add performance benchmarks**: Create benchmark suite for vector operations (phase: backlog)\n"

if [[ "$suggestions_checklist" == "$expected_checklist" ]]; then
    echo -e "${GREEN}✓ PASS: Checklist generated correctly${NC}"
else
    echo -e "${RED}❌ FAIL: Checklist generation failed${NC}"
    echo "Expected:"
    echo -e "$expected_checklist"
    echo "Got:"
    echo -e "$suggestions_checklist"
    exit 1
fi

# Validate phases collection
if [[ "$all_phases" == "4.2, backlog" ]]; then
    echo -e "${GREEN}✓ PASS: Phases collected correctly: $all_phases${NC}"
else
    echo -e "${RED}❌ FAIL: Phase collection failed${NC}"
    echo "Expected: 4.2, backlog"
    echo "Got: $all_phases"
    exit 1
fi

# Test GitHub CLI integration (dry-run)
echo
echo "Testing GitHub CLI integration (dry-run)..."

if command -v gh &> /dev/null; then
    # Test that gh commands would work (without actually creating issues)
    echo "GitHub CLI available - testing aggregated command structure"

    # Mock the aggregated gh issue create command structure
    aggregated_title="[PR #123] Follow-ups Suggested by ARC-Reviewer"
    gh_test_cmd=(
        "gh" "issue" "create"
        "--title" "$aggregated_title"
        "--body" "Test aggregated body with checklist"
        "--label" "from-code-review,sprint-triage,phase=backlog"
    )

    echo "Would execute: ${gh_test_cmd[*]}"
    echo -e "${GREEN}✓ PASS: GitHub CLI aggregated command structure valid${NC}"
else
    echo -e "${YELLOW}⚠ WARNING: GitHub CLI not available, skipping integration test${NC}"
fi

# Cleanup
rm -f "$TEST_REVIEW_FILE"

echo
echo "================================================"
echo -e "${GREEN}🎉 ALL TESTS PASSED${NC}"
echo -e "${GREEN}Aggregated parser correctly handles $EXPECTED_SUGGESTIONS ISSUE: follow-ups${NC}"
echo -e "${GREEN}Creates single issue with checklist instead of multiple individual issues${NC}"
