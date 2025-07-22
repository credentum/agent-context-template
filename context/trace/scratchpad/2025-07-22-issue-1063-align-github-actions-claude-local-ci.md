# Execution Plan: Issue #1063 - Align GitHub Actions with Claude Local CI

## Issue Reference
- **GitHub Issue**: [#1063](https://github.com/droter/agent-context-template/issues/1063)
- **Sprint Reference**: Not assigned to current Sprint 5
- **Task Template**: `context/trace/task-templates/issue-1063-align-github-actions-claude-local-ci.md`

## Analysis Summary
The issue requests consolidation of 20+ GitHub Actions workflows to use the same claude-ci.sh scripts that Claude uses locally. This will eliminate duplicate CI logic and ensure consistent results between local and GitHub runs.

**Current State**:
- ci-optimized.yml has 802 lines of embedded CI logic
- Multiple workflows (test.yml, test-suite.yml, lint-verification.yml) with overlapping functionality
- Different commands/output formats between local and GitHub CI
- Existing claude-ci.sh script provides unified interface locally

**Desired State**:
- Workflows call claude-ci.sh instead of embedding logic
- Identical behavior between local `claude-ci all` and GitHub Actions
- Simplified YAML files with script delegation
- Single source of truth for CI logic

## Token Budget & Complexity
- **Estimated tokens**: 8,000 (moderate YAML refactoring)
- **Estimated time**: 2-3 hours
- **Complexity**: Medium - workflow consolidation + script enhancement
- **Files affected**: 8-10 workflow files + claude-ci.sh + documentation

## Implementation Strategy

### Phase 1: Enhance claude-ci.sh for GitHub Actions
1. **Add --github-output flag** to claude-ci.sh:
   - Output GitHub Actions step outputs (::set-output name=key::value)
   - Maintain JSON format but add Actions-specific output
   - Support integration with GitHub's workflow syntax

2. **Add --format github flag** for workflow compatibility:
   - Ensure proper exit codes for workflow steps
   - Add step summaries for GitHub Actions UI
   - Format errors for GitHub's annotations

### Phase 2: Create Unified Workflows  
1. **ci-unified.yml** (new):
   - Replace ci-optimized.yml complex logic
   - Simple delegation to `./scripts/claude-ci.sh all`
   - Maintain same triggers and permissions

2. **pr-review-unified.yml** (new):
   - Use `./scripts/claude-ci.sh review` 
   - Parse JSON output and post as PR comment
   - Replace complex review logic

### Phase 3: Workflow Migration Strategy
1. **Parallel execution** during transition:
   - Keep existing workflows with .legacy suffix
   - Run new unified workflows alongside
   - Compare results to ensure identical behavior

2. **Gradual migration**:
   - Phase 1: Create unified alongside existing
   - Phase 2: Verify identical results  
   - Phase 3: Switch to unified as primary
   - Phase 4: Archive legacy workflows

### Phase 4: Consolidation  
**Target workflow reduction**:
- ci-optimized.yml (802 lines) → ci-unified.yml (~50 lines)  
- test.yml (82 lines) → (merged into unified)
- test-suite.yml (200+ lines) → (merged into unified)
- lint-verification.yml (102 lines) → (merged into unified)

**Expected benefits**:
- 90% reduction in workflow complexity
- Single source of truth for CI logic
- Identical local/GitHub behavior
- Easier debugging and maintenance

## Success Criteria Validation
- [ ] claude-ci.sh supports --github-output flag
- [ ] New ci-unified.yml delegates to claude-ci scripts  
- [ ] Identical results between local and GitHub runs
- [ ] Legacy workflows archived after successful migration
- [ ] Documentation updated with new architecture
- [ ] All existing CI checks continue to pass

## Implementation Notes
- Focus on maintaining all existing functionality while simplifying implementation
- Preserve caching, parallel execution, and conditional job execution
- Ensure security permissions remain appropriate
- Create migration guide for other projects using this pattern

## Risk Assessment
- **Medium risk**: Workflow changes could break CI if not tested properly
- **Mitigation**: Parallel execution during transition period
- **Main risk**: GitHub Actions output format compatibility
- **Mitigation**: Thorough testing of --github-output flag integration