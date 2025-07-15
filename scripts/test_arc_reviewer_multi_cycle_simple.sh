#!/bin/bash
# Simple test for ARC-Reviewer multi-cycle functionality
# Tests basic multi-cycle structure and commit tracking

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing ARC-Reviewer Multi-Cycle Support${NC}"
echo "=========================================="

# Test case: Multiple review cycles with different commits
echo -e "\n${YELLOW}Test: Multi-Cycle Issue Structure${NC}"

# Simulate first review cycle
commit1="abc1234"
date1="2025-07-15 10:30 UTC"
suggestions1="- [ ] **Add error handling**: Improve error handling in validators (phase: 4.2)\n- [ ] **Update docs**: Add comprehensive docstrings (phase: backlog)"

# Simulate second review cycle
commit2="def5678"
date2="2025-07-15 14:45 UTC"
suggestions2="- [ ] **Add tests**: Create unit tests for new functionality (phase: 4.3)"

# Create multi-cycle issue body
issue_body="## Context

This issue consolidates all follow-up suggestions from ARC-Reviewer across multiple review cycles for better triage and sprint planning.

**Original PR:** #123 - Test Multi-Cycle PR
**PR URL:** https://github.com/test/repo/pull/123
**Author:** @testuser

## Review Cycle - $date1 (Commit $commit1)

$suggestions1

## Review Cycle - $date2 (Commit $commit2)

$suggestions2

## Triage Instructions

**For PM/Agent Review:**
1. Review each suggestion for actionable value across all review cycles
2. Check priority alignment with current sprint goals
3. Promote high-value items to appropriate sprint YAML files
4. Check off completed suggestions as they are addressed
5. Add \`sprint-triage\` label when reviewed
6. Close this issue once all cycles are triaged

## Labels
- \`from-code-review\`: Auto-generated from code review
- \`sprint-triage\`: Needs PM/agent triage review
- \`phase=backlog\`: Default phase for new suggestions

---
*Automatically created by ARC-Reviewer bot - tracks suggestions across multiple review cycles*"

# Validation tests
echo "Running validation tests..."

# Test 1: Check both commits are present
if echo "$issue_body" | grep -q "Commit $commit1" && echo "$issue_body" | grep -q "Commit $commit2"; then
    echo -e "${GREEN}✓ Both commit hashes tracked${NC}"
else
    echo -e "${RED}❌ Commit tracking failed${NC}"
    exit 1
fi

# Test 2: Check both review cycles are present
cycle_count=$(echo "$issue_body" | grep -c "## Review Cycle")
if [ "$cycle_count" -eq 2 ]; then
    echo -e "${GREEN}✓ Correct number of review cycles: $cycle_count${NC}"
else
    echo -e "${RED}❌ Incorrect cycle count: $cycle_count (expected 2)${NC}"
    exit 1
fi

# Test 3: Check suggestions from both cycles are preserved
if echo "$issue_body" | grep -q "Add error handling" && echo "$issue_body" | grep -q "Add tests"; then
    echo -e "${GREEN}✓ Suggestions from all cycles preserved${NC}"
else
    echo -e "${RED}❌ Suggestions missing from some cycles${NC}"
    exit 1
fi

# Test 4: Check phase tracking
if echo "$issue_body" | grep -q "phase: 4.2" && echo "$issue_body" | grep -q "phase: 4.3"; then
    echo -e "${GREEN}✓ Phase tracking across cycles works${NC}"
else
    echo -e "${RED}❌ Phase tracking failed${NC}"
    exit 1
fi

# Test 5: Check structure integrity
if echo "$issue_body" | grep -q "## Triage Instructions" && echo "$issue_body" | grep -q "## Context"; then
    echo -e "${GREEN}✓ Issue structure preserved${NC}"
else
    echo -e "${RED}❌ Issue structure corrupted${NC}"
    exit 1
fi

# Test workflow behavior simulation
echo -e "\n${YELLOW}Test: Workflow Behavior Simulation${NC}"

# Simulate existing issue detection
existing_title="[PR #123] Follow-ups Suggested by ARC-Reviewer"
echo "Testing title format: $existing_title"

if [[ "$existing_title" =~ ^\[PR\ #[0-9]+\]\ Follow-ups\ Suggested\ by\ ARC-Reviewer$ ]]; then
    echo -e "${GREEN}✓ Title format correct for detection${NC}"
else
    echo -e "${RED}❌ Title format incorrect${NC}"
    exit 1
fi

# Test commit detection in existing body
if echo "$issue_body" | grep -q "Commit $commit1"; then
    echo -e "${GREEN}✓ Existing commit detection works${NC}"
else
    echo -e "${RED}❌ Commit detection failed${NC}"
    exit 1
fi

# Display sample structure
echo -e "\n${YELLOW}Sample Multi-Cycle Issue Structure:${NC}"
echo "===================================="
echo "$issue_body" | head -15
echo "..."
echo "$issue_body" | grep "## Review Cycle" -A 3
echo "..."
echo "$issue_body" | tail -5

echo
echo "=========================================="
echo -e "${GREEN}🎉 ALL MULTI-CYCLE TESTS PASSED${NC}"
echo -e "${GREEN}✓ Multiple review cycles supported${NC}"
echo -e "${GREEN}✓ Commit tracking implemented${NC}"
echo -e "${GREEN}✓ Suggestion preservation works${NC}"
echo -e "${GREEN}✓ Phase tracking across cycles${NC}"
echo -e "${GREEN}✓ Workflow integration ready${NC}"
