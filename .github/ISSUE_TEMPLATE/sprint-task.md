---
name: Sprint Task (Claude Code Ready)
about: Create a task optimized for Claude Code execution
title: '[SPRINT-X.Y] Task Title'
labels: ['sprint-current', 'claude-ready', 'phase:?', 'component:?']
assignees: ''
---

## Task Context
**Sprint**: <!-- e.g., sprint-4-1 -->
**Phase**: <!-- e.g., Phase 2: Implementation -->
**Component**: <!-- e.g., api-middleware -->

## Scope Assessment
<!-- Check one -->
- [ ] **Scope is clear** - Requirements are well-defined, proceed with implementation
- [ ] **Scope needs investigation** - Create investigation issue first (use investigation.md template)
- [ ] **Partially clear** - Some aspects need investigation (note below)

**Investigation Notes**: <!-- If scope unclear, describe what needs investigation -->

## Acceptance Criteria
<!-- From sprint planning -->
- [ ] Specific functional requirement
- [ ] Performance requirement
- [ ] Quality gate requirement

## Claude Code Readiness Checklist
<!-- Complete before starting Claude Code -->
- [ ] **Context URLs identified** (docs, specs, related PRs)
- [ ] **File scope estimated** (< 4 files, < 400 LoC expected)
- [ ] **Dependencies mapped** (external APIs, config, other services)
- [ ] **Test strategy defined** (unit, integration, edge cases)
- [ ] **Breaking change assessment** (backward compatibility)

## Pre-Execution Context
<!-- Gather these details for Claude Code -->
**Key Files**: `src/path/to/files`, `tests/path/`
**External Dependencies**:
**Configuration**: Environment variables, feature flags
**Related Issues/PRs**: #xyz, #abc

## Implementation Notes
<!-- Technical guidance for Claude Code session -->

---

## Claude Code Execution
<!-- Fill this section when starting Claude Code -->
**Session Started**: <!-- timestamp -->
**Task Template Created**: <!-- link to generated template -->
**Token Budget**: <!-- estimated after analysis -->
**Completion Target**: <!-- time estimate -->

_This issue will be updated during Claude Code execution with progress and results._
