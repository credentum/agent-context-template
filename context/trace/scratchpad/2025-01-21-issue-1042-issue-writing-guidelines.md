# Issue #1042 Implementation Plan
**Date**: 2025-01-21
**Issue**: #1042 - [SPRINT-5.2] Create issue writing guidelines and investigation templates
**Sprint**: sprint-5-2
**Task Template**: context/trace/task-templates/issue-1042-issue-writing-guidelines.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 10,000 (documentation heavy)
- **Estimated time**: 2-3 hours
- **Complexity**: Medium (mostly documentation, one code file update)
- **Files to create/modify**: 5-6

## Implementation Plan

### 1. Create Issue Writing Guide (docs/issue-writing-guide.md)
- **Structure**:
  - Introduction: The problem with underestimating scope
  - Case study: Issue #1029 (1-line fix → 1300+ lines)
  - Problem-first approach (symptoms vs solutions)
  - Investigation patterns
  - Sub-issue decomposition
  - Templates and examples
- **Key principles**:
  - Describe what you observe, not what you think the fix is
  - Include reproduction steps and environment details
  - Use investigation issues for unclear scope
  - Document discovered complexities

### 2. Create Investigation Template (.github/ISSUE_TEMPLATE/investigation.md)
- **Purpose**: For problems with unclear scope
- **Sections**:
  - Observed symptoms
  - Initial hypothesis
  - Investigation findings
  - Discovered sub-problems
  - Recommended decomposition
- **Metadata**: Labels for "investigation", "needs-scope"

### 3. Update Sprint Task Template (.github/ISSUE_TEMPLATE/sprint-task.md)
- Add "Investigation Phase" section
- Include scope discovery checklist
- Reference investigation template for unclear tasks

### 4. Enhance workflow-issue.md
- Add "Phase 0: Investigation" for unclear scope
- Document when to use investigation issues
- Add examples from issue #1029
- Include scope discovery protocols

### 5. Update sprint_issue_linker.py
- Add `--template` parameter for issue creation
- Support template selection based on task type
- Maintain backward compatibility
- Add documentation for template usage

### 6. Document Findings
- Create summary of implementation
- Document any additional patterns discovered
- Update task template with actuals

## Order of Implementation
1. Create issue writing guide (establish principles)
2. Create investigation template (concrete example)
3. Update existing templates (integrate new patterns)
4. Enhance workflow documentation (process integration)
5. Update sprint_issue_linker.py (automation support)
6. Final documentation and testing

## Context Management
- Monitor token usage throughout
- Use /clear if approaching 25k tokens
- Keep focus on documentation quality over quantity

## Success Metrics
- Clear, actionable documentation
- Templates that encourage thorough investigation
- Seamless integration with existing workflows
- Examples that illustrate key principles
- Code changes that maintain compatibility
