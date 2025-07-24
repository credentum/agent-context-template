# Execution Plan: Issue #1297 - Integrate ARC-Reviewer into Local CI

**Issue Link**: https://github.com/[org]/agent-context-template/issues/1297
**Sprint Reference**: sprint-4.3, Phase 4.1: Enhancement
**Task Template**: context/trace/task-templates/issue-1297-integrate-arc-reviewer.md

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 15k (reading 4 files, modifying 3)
- **Complexity**: Medium - Integration task with JSON parsing
- **Time Estimate**: 45 minutes

## Step-by-Step Implementation Plan

### 1. Understand Current State
- [x] claude-ci.sh already has review command but doesn't run ARC-Reviewer
- [x] ARC-Reviewer exists and works standalone (src/agents/arc_reviewer.py)
- [x] Need to parse YAML output from ARC into JSON format
- [x] Must respect --quick vs --comprehensive modes

### 2. Integration Points
- **cmd_review()**: Add ARC-Reviewer execution here
- **cmd_all()**: Include ARC in comprehensive mode only
- **JSON output**: Parse ARC's YAML into existing JSON structure

### 3. Implementation Steps

#### Step 3.1: Add ARC-Reviewer to cmd_review()
- Add Python execution of arc_reviewer.py
- Capture YAML output
- Parse YAML to extract:
  - Coverage status and percentage
  - Code quality issues
  - Security findings
  - Context integrity checks
- Convert to JSON format matching existing structure

#### Step 3.2: Update cmd_all() for Comprehensive Mode
- Add ARC stage when COMPREHENSIVE=true
- Skip ARC in quick mode (too slow)
- Include ARC results in aggregated output

#### Step 3.3: Handle Error Cases
- Missing Python/dependencies
- ARC-Reviewer failures
- YAML parsing errors
- Coverage below baseline (78%)

#### Step 3.4: Update Help Documentation
- Document ARC-Reviewer in review command
- Explain quick vs comprehensive behavior

### 4. Testing Strategy
- Test review command with ARC
- Test comprehensive mode includes ARC
- Test quick mode skips ARC
- Simulate coverage regression scenario
- Verify JSON output structure

### 5. Expected Changes Summary
```
scripts/claude-ci.sh:
- cmd_review(): +50 lines for ARC integration
- cmd_all(): +10 lines for comprehensive mode
- Helper function for YAML->JSON: +30 lines
- Updated help text: +5 lines

Total: ~95 lines added, well within 200 LoC budget
```

### 6. Risk Mitigation
- Backward compatibility: ARC is optional/additive
- Performance: Only in review/comprehensive modes
- Dependencies: Graceful fallback if Python unavailable

## Progress Tracking
- [ ] Step 1: Modify cmd_review() to run ARC
- [ ] Step 2: Parse YAML output to JSON
- [ ] Step 3: Update comprehensive mode
- [ ] Step 4: Test all scenarios
- [ ] Step 5: Update documentation

## Notes
- Issue discovered during PR #1296 when local CI missed coverage issues
- This completes the local CI migration story
- ARC-Reviewer already tested and working (from issue #1130)
