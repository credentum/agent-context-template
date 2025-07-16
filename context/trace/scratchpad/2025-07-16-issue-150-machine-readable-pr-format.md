# Issue 150: Machine-Readable PR Description Format

**Issue Link**: https://github.com/credentum/agent-context-template/issues/150
**Sprint**: sprint-4.1, Phase 6
**Priority**: High
**Created**: 2025-07-16

## Problem Analysis

Current PR descriptions use free-form markdown which causes:
- Shell parsing errors in CI workflows (sprint-update.yml, auto-close-issues.yml)
- Complex regex parsing that breaks with special characters
- Unreliable automation due to text parsing fragility
- Maintenance overhead from parsing edge cases

### Current Parsing Issues Found

1. **sprint-update.yml** (lines 88-96):
   ```bash
   pr_body=$(gh pr view "$pr_number" --json body --jq '.body // ""')
   combined_text="$pr_body $pr_title"
   issue_nums=$(echo "$combined_text" | \
     grep -ioE "(closes?|fixes?|resolves?|implements?)\s+#[0-9]+" | \
     grep -oE "#[0-9]+" | sed 's/#//')
   ```

2. **Auto-close workflows** parse free-form text for issue references
3. **Auto-merge workflow** accesses `pr.body` directly without structure

## Proposed Solution

### Hybrid Format Design

Create a YAML frontmatter + markdown format that maintains human readability while providing machine-parseable metadata:

```yaml
---
# Machine-readable metadata
pr_metadata:
  type: "feature" | "fix" | "docs" | "refactor" | "test" | "chore"
  closes_issues: [123, 456]  # List of issue numbers
  priority: "high" | "medium" | "low"
  breaking_change: true | false
  affects_components: ["workflow", "automation", "core"]
  test_coverage:
    added: true | false
    percentage: 85.5
    requirements_met: true | false
  risk_assessment: "low" | "medium" | "high"
  review_requirements:
    security_review: true | false
    architecture_review: true | false
---

# Human-readable description follows...
## Summary
Brief description of changes

## What Changed
- List of changes

## Testing
- How this was tested

## Additional Notes
Any other relevant information
```

### Implementation Plan

#### Phase 1: Template and Validation
1. Create new PR template with hybrid format
2. Add validation workflow for YAML frontmatter
3. Ensure backward compatibility with existing PRs

#### Phase 2: Workflow Updates
1. Update auto-merge workflow to parse YAML metadata
2. Update sprint-update workflow to use structured data
3. Update auto-close-issues workflow

#### Phase 3: Documentation and Testing
1. Update CLAUDE.md with new format guidance
2. Create examples and documentation
3. Test with real PRs

## Technical Implementation

### Schema Definition

```yaml
# .github/pr-template-schema.yaml
type: object
properties:
  pr_metadata:
    type: object
    required: ["type", "closes_issues", "breaking_change"]
    properties:
      type:
        enum: ["feature", "fix", "docs", "refactor", "test", "chore"]
      closes_issues:
        type: array
        items:
          type: integer
      priority:
        enum: ["high", "medium", "low"]
        default: "medium"
      breaking_change:
        type: boolean
        default: false
      affects_components:
        type: array
        items:
          type: string
      test_coverage:
        type: object
        properties:
          added:
            type: boolean
          percentage:
            type: number
          requirements_met:
            type: boolean
      risk_assessment:
        enum: ["low", "medium", "high"]
        default: "low"
      review_requirements:
        type: object
        properties:
          security_review:
            type: boolean
            default: false
          architecture_review:
            type: boolean
            default: false
```

### Parsing Logic

For workflows, create a helper function:

```bash
# Extract YAML frontmatter and parse with yq
extract_pr_metadata() {
  local pr_body="$1"
  echo "$pr_body" | awk '/^---$/{flag=1;next}/^---$/{flag=0}flag' | yq eval
}

# Usage in workflows:
closes_issues=$(extract_pr_metadata "$pr_body" | yq eval '.pr_metadata.closes_issues[]')
pr_type=$(extract_pr_metadata "$pr_body" | yq eval '.pr_metadata.type')
```

### Backward Compatibility

- Keep existing regex parsing as fallback
- Gradual migration - new PRs use new format
- Old PRs continue to work with legacy parsing

## Benefits

1. **Reliability**: Structured data eliminates parsing errors
2. **Extensibility**: Easy to add new metadata fields
3. **Automation**: Enables advanced workflow logic
4. **Human-friendly**: Maintains readability
5. **Type Safety**: Schema validation prevents malformed data

## Risks and Mitigation

- **Risk**: Users might not follow new format
  - **Mitigation**: Validation workflow + clear template
- **Risk**: Complexity increases
  - **Mitigation**: Gradual rollout + documentation
- **Risk**: Breaking existing workflows
  - **Mitigation**: Backward compatibility + testing

## Success Metrics

- [ ] Zero shell parsing errors in workflows
- [ ] 100% of new PRs use structured format
- [ ] Workflows parse metadata reliably
- [ ] Developer experience improves (clearer template)
- [ ] Automation reliability increases

## Implementation Steps

1. ✅ Analysis and planning (this document)
2. 🔄 Create new PR template with hybrid format
3. ⏳ Add validation workflow
4. ⏳ Update workflows to parse structured data
5. ⏳ Test and validate
6. ⏳ Documentation and rollout

---
**Next Actions**: Create new PR template and validation workflow
