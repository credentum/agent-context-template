# Issue #60: Close-the-Loop for ARC-Reviewer Suggested Follow-ups

**Issue Link**: https://github.com/credentum/agent-context-template/issues/60
**Sprint**: sprint-4.1
**Phase**: 4.1 (CI component)
**Priority**: High

## Problem Statement

Currently, ARC-Reviewer's "Suggested Follow-ups" are human-readable bullet points that never enter the backlog. We need to standardize them into a machine-parseable `ISSUE:` schema and update the GitHub workflow to auto-file tickets.

## Current State Analysis

### Existing Implementation (.github/workflows/claude-code-review.yml)
- Lines 254-282: Basic follow-up handling using AWK
- Lines 108-111: Prompt specifies bullet point format `• <optional backlog items>`
- Creates GitHub issues with basic metadata but no structured parsing

### Current Format:
```
**Suggested Follow-ups:**
• <optional backlog items>
```

### Target Format:
```
**Suggested Follow-ups:**
ISSUE: <title> - <desc> - labels=<csv> - phase=<milestone>
```

## Implementation Tasks

### 1. Update Prompt Format
- **File**: `.github/workflows/claude-code-review.yml` (lines 108-111)
- **Change**: Replace bullet point format with ISSUE: schema
- **Estimate**: 15 minutes

### 2. Replace Parser Logic
- **File**: `.github/workflows/claude-code-review.yml` (lines 254-282)
- **Change**: Replace AWK-based bullet extraction with robust ISSUE: line parsing
- **Requirements**:
  - Split on ' - ' delimiter
  - Extract title, description, labels, phase
  - Default phase to 'backlog' when absent
  - Prevent duplicate issue creation
- **Estimate**: 45 minutes

### 3. Enhanced Issue Creation
- **Requirements**:
  - Title prefixed by `[PR #<num>]`
  - Labels from `labels=` field plus `from-code-review`
  - Milestone/project column matching `phase=` field
- **Estimate**: 30 minutes

### 4. Unit Tests
- **File**: Create test script in scripts/
- **Requirements**:
  - Mock review comment with two follow-ups
  - Verify CI job creates exactly two issues
  - Use `gh api` dry-run mode
- **Estimate**: 60 minutes

### 5. Documentation
- **File**: `CONTRIBUTING.md`
- **Content**: Explain ISSUE: schema and auto-triage flow
- **Estimate**: 30 minutes

### 6. Integration Testing
- **Test**: Complete workflow with sample PR
- **Estimate**: 30 minutes

## Implementation Details

### New ISSUE Schema Format
```
ISSUE: Fix validator coverage - Improve test coverage for validators module - labels=test,validator,coverage - phase=4.2
```

### Parser Logic (Bash)
```bash
# Extract ISSUE: lines from review
grep '^ISSUE:' review.txt | while read -r line; do
  # Remove ISSUE: prefix
  content=${line#ISSUE: }

  # Split on ' - ' delimiter
  IFS=' - ' read -ra PARTS <<< "$content"
  title="${PARTS[0]}"
  description="${PARTS[1]}"

  # Extract metadata from remaining parts
  labels_part="${PARTS[2]}"  # labels=test,coverage
  phase_part="${PARTS[3]}"   # phase=4.2

  # Parse labels and phase
  labels=$(echo "$labels_part" | sed 's/labels=//')
  phase=$(echo "$phase_part" | sed 's/phase=//')

  # Default phase if missing
  phase=${phase:-backlog}

  # Create issue with enhanced metadata
done
```

## Success Criteria
- [ ] Prompt format updated to use ISSUE: schema
- [ ] Parser handles ISSUE: lines correctly
- [ ] Issues created with proper metadata (title prefix, labels, phase)
- [ ] Unit test passes with mocked review containing two follow-ups
- [ ] Documentation updated in CONTRIBUTING.md
- [ ] No duplicate issues created
- [ ] CI workflow validates successfully

## Dependencies
- GitHub CLI (already available in runner)
- No blocking tasks

## Notes
- This replaces the current AWK-based approach with a more structured format
- Maintains backward compatibility during transition
- Enables automatic triage and project management
