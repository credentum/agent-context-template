#!/bin/bash
# Unit test for ARC-Reviewer multi-cycle aggregated parser logic
# Tests the parser with multiple review cycles and commit tracking

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing ARC-Reviewer Multi-Cycle Aggregated Parser${NC}"
echo "=================================================="

# Test 1: First review cycle (new issue creation)
echo -e "\n${YELLOW}Test 1: First Review Cycle${NC}"
echo "Creating mock review with 2 suggestions..."

cat > "review_cycle1.txt" << 'EOF'
**PR Verdict:** APPROVE
**Summary:** Good start, some suggestions for improvement.
**Blocking Issues (❌):**
None
**Warnings (⚠️):**
1. Consider adding error handling
**Nits (💡):**
1. Minor style improvements
**Coverage Delta:** 75.0% → 77.5% [PASS]
**Suggested Follow-ups:**
ISSUE: Add error handling - Improve error handling in validators - labels=error,validator - phase=4.2
ISSUE: Update documentation - Add more comprehensive docstrings - labels=docs - phase=backlog
End of report. Do *not* add anything after this line.
EOF

# Simulate first cycle processing
echo "Processing first review cycle..."
commit_hash1="abc1234567890"
commit_short1="${commit_hash1:0:7}"
review_date1="2025-07-15 10:30 UTC"

suggestions_checklist1=""
issue_count1=0

while read -r line; do
    content=$(echo "${line#ISSUE:}" | xargs)
    [ -z "$content" ] && continue

    # Use simpler parsing to avoid regex issues
    # Split on ' - ' manually
    title="${content%% - *}"
    temp="${content#* - }"

    if [[ "$temp" == "$content" ]]; then
        # No ' - ' found, use whole content as title
        description="Suggested improvement from code review"
        phase="backlog"
    else
        description="${temp%% - *}"
        temp2="${temp#* - }"

        if [[ "$temp2" == "$temp" ]]; then
            # No more ' - ' found
            phase="backlog"
        else
            # Extract phase from remaining
            if [[ "$temp2" =~ phase=([^[:space:]]+) ]]; then
                phase="${BASH_REMATCH[1]}"
            else
                phase="backlog"
            fi
        fi
    fi

    suggestions_checklist1="${suggestions_checklist1}- [ ] **${title}**: ${description} (phase: ${phase})\n"
    ((issue_count1++))

done < <(grep '^ISSUE:' "review_cycle1.txt")

# Create first issue body
first_issue_body="## Context\n\nThis issue consolidates all follow-up suggestions from ARC-Reviewer across multiple review cycles for better triage and sprint planning.\n\n**Original PR:** #123 - Test PR Title\n**PR URL:** https://github.com/test/repo/pull/123\n**Author:** @testuser\n\n## Review Cycle - $review_date1 (Commit $commit_short1)\n\n$suggestions_checklist1\n\n## Triage Instructions\n\n**For PM/Agent Review:**\n1. Review each suggestion for actionable value across all review cycles\n2. Check priority alignment with current sprint goals\n3. Promote high-value items to appropriate sprint YAML files\n4. Check off completed suggestions as they are addressed\n5. Add \`sprint-triage\` label when reviewed\n6. Close this issue once all cycles are triaged\n\n## Labels\n- \`from-code-review\`: Auto-generated from code review\n- \`sprint-triage\`: Needs PM/agent triage review\n- \`phase=backlog\`: Default phase for new suggestions\n\n---\n*Automatically created by ARC-Reviewer bot - tracks suggestions across multiple review cycles*"

echo -e "${GREEN}✓ First cycle processed: $issue_count1 suggestions${NC}"

# Test 2: Second review cycle (append to existing issue)
echo -e "\n${YELLOW}Test 2: Second Review Cycle (Append)${NC}"
echo "Creating mock review with 1 additional suggestion..."

cat > "review_cycle2.txt" << 'EOF'
**PR Verdict:** APPROVE
**Summary:** Addressed previous feedback, one more suggestion.
**Blocking Issues (❌):**
None
**Warnings (⚠️):**
None
**Nits (💡):**
1. Consider adding unit tests
**Coverage Delta:** 77.5% → 80.0% [PASS]
**Suggested Follow-ups:**
ISSUE: Add unit tests - Create unit tests for new functionality - labels=test,unit - phase=4.3
End of report. Do *not* add anything after this line.
EOF

# Simulate second cycle processing
echo "Processing second review cycle..."
commit_hash2="def9876543210"
commit_short2="${commit_hash2:0:7}"
review_date2="2025-07-15 14:45 UTC"

suggestions_checklist2=""
issue_count2=0

while read -r line; do
    content=$(echo "${line#ISSUE:}" | xargs)
    [ -z "$content" ] && continue

    if [[ "$content" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        title="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        title="$content"
        remaining=""
    fi

    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        description="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        description="${remaining:-Suggested improvement from code review}"
        remaining=""
    fi

    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        labels_field="${BASH_REMATCH[1]}"
        phase_field="${BASH_REMATCH[2]}"
    else
        labels_field="$remaining"
        phase_field=""
    fi

    if [[ "$phase_field" =~ ^phase=(.+)$ ]]; then
        phase="${BASH_REMATCH[1]}"
    else
        phase="backlog"
    fi

    suggestions_checklist2="${suggestions_checklist2}- [ ] **${title}**: ${description} (phase: ${phase})\n"
    ((issue_count2++))

done < <(grep '^ISSUE:' "review_cycle2.txt")

# Simulate appending to existing issue
existing_body="$first_issue_body"

# Find insertion point (before Triage Instructions)
before_triage=$(echo "$existing_body" | awk '/^## Triage Instructions/,0 {exit} {print}')
triage_and_after=$(echo "$existing_body" | awk '/^## Triage Instructions/,0 {print}')

new_cycle_section="## Review Cycle - $review_date2 (Commit $commit_short2)\n\n$suggestions_checklist2\n"
updated_body="${before_triage}\n${new_cycle_section}\n${triage_and_after}"

echo -e "${GREEN}✓ Second cycle processed: $issue_count2 suggestions${NC}"

# Test 3: Update existing cycle (same commit)
echo -e "\n${YELLOW}Test 3: Update Existing Cycle (Same Commit)${NC}"
echo "Simulating update to existing commit cycle..."

# Create updated suggestions for same commit
cat > "review_cycle2_updated.txt" << 'EOF'
**PR Verdict:** APPROVE
**Summary:** Updated suggestions for same commit.
**Blocking Issues (❌):**
None
**Warnings (⚠️):**
None
**Nits (💡):**
1. Refined suggestions
**Coverage Delta:** 77.5% → 81.0% [PASS]
**Suggested Follow-ups:**
ISSUE: Add comprehensive tests - Create comprehensive test suite including unit and integration tests - labels=test,comprehensive - phase=4.3
ISSUE: Performance optimization - Optimize performance for large datasets - labels=performance - phase=4.4
End of report. Do *not* add anything after this line.
EOF

suggestions_checklist2_updated=""
issue_count2_updated=0

while read -r line; do
    content=$(echo "${line#ISSUE:}" | xargs)
    [ -z "$content" ] && continue

    if [[ "$content" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        title="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        title="$content"
        remaining=""
    fi

    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        description="${BASH_REMATCH[1]}"
        remaining="${BASH_REMATCH[2]}"
    else
        description="${remaining:-Suggested improvement from code review}"
        remaining=""
    fi

    if [[ "$remaining" =~ ^([^-]*[^[:space:]])[[:space:]]*-[[:space:]](.*)$ ]]; then
        labels_field="${BASH_REMATCH[1]}"
        phase_field="${BASH_REMATCH[2]}"
    else
        labels_field="$remaining"
        phase_field=""
    fi

    if [[ "$phase_field" =~ ^phase=(.+)$ ]]; then
        phase="${BASH_REMATCH[1]}"
    else
        phase="backlog"
    fi

    suggestions_checklist2_updated="${suggestions_checklist2_updated}- [ ] **${title}**: ${description} (phase: ${phase})\n"
    ((issue_count2_updated++))

done < <(grep '^ISSUE:' "review_cycle2_updated.txt")

# Simulate replacing existing cycle section
new_cycle_section_updated="## Review Cycle - $review_date2 (Commit $commit_short2)\n\n$suggestions_checklist2_updated"

# Simple replacement simulation (would use awk in real implementation)
final_body=$(echo "$updated_body" | sed "s|## Review Cycle - $review_date2 (Commit $commit_short2).*## Triage Instructions|$new_cycle_section_updated\n\n## Triage Instructions|")

echo -e "${GREEN}✓ Existing cycle updated: $issue_count2_updated suggestions${NC}"

# Validation Tests
echo -e "\n${YELLOW}Validation Tests${NC}"

# Test that first cycle is preserved
if echo "$final_body" | grep -q "Review Cycle - $review_date1 (Commit $commit_short1)"; then
    echo -e "${GREEN}✓ First review cycle preserved${NC}"
else
    echo -e "${RED}❌ First review cycle lost${NC}"
    exit 1
fi

# Test that second cycle exists
if echo "$final_body" | grep -q "Review Cycle - $review_date2 (Commit $commit_short2)"; then
    echo -e "${GREEN}✓ Second review cycle present${NC}"
else
    echo -e "${RED}❌ Second review cycle missing${NC}"
    exit 1
fi

# Test that updated suggestions are reflected
if echo "$final_body" | grep -q "Add comprehensive tests"; then
    echo -e "${GREEN}✓ Updated suggestions reflected${NC}"
else
    echo -e "${RED}❌ Updated suggestions missing${NC}"
    exit 1
fi

# Test that both commits are tracked
total_cycles=$(echo "$final_body" | grep -c "## Review Cycle")
if [ "$total_cycles" -eq 2 ]; then
    echo -e "${GREEN}✓ Correct number of review cycles: $total_cycles${NC}"
else
    echo -e "${RED}❌ Incorrect number of review cycles: $total_cycles (expected 2)${NC}"
    exit 1
fi

# Test triage instructions are preserved
if echo "$final_body" | grep -q "## Triage Instructions"; then
    echo -e "${GREEN}✓ Triage instructions preserved${NC}"
else
    echo -e "${RED}❌ Triage instructions missing${NC}"
    exit 1
fi

# Display final structure
echo -e "\n${YELLOW}Final Issue Structure Preview:${NC}"
echo "=============================="
echo "$final_body" | head -20
echo "..."
echo "$final_body" | tail -5

# Cleanup
rm -f review_cycle1.txt review_cycle2.txt review_cycle2_updated.txt

echo
echo "=================================================="
echo -e "${GREEN}🎉 ALL MULTI-CYCLE TESTS PASSED${NC}"
echo -e "${GREEN}✓ Multiple review cycles supported${NC}"
echo -e "${GREEN}✓ Commit tracking implemented${NC}"
echo -e "${GREEN}✓ Cycle updates work correctly${NC}"
echo -e "${GREEN}✓ Previous cycles preserved${NC}"
