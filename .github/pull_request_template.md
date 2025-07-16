---
# 🤖 Machine-Readable Metadata (required for automation)
pr_metadata:
  type: "feature"  # feature|fix|docs|refactor|test|chore
  closes_issues: []  # [123, 456] - list of issue numbers this PR closes
  priority: "medium"  # high|medium|low
  breaking_change: false  # true|false
  affects_components: []  # workflow|automation|core|storage|agents|analytics|validators|docs|infra|ci
  test_coverage:
    added: false  # true if tests were added
    percentage: 0  # current test coverage percentage
    requirements_met: false  # true if coverage requirements are met
  risk_assessment: "low"  # low|medium|high
  review_requirements:
    security_review: false  # true if security review needed
    architecture_review: false  # true if architecture review needed
  automation_flags:
    auto_merge: false  # true to enable auto-merge when conditions are met
    skip_ci: false  # true for docs-only changes
    update_docs: false  # true to automatically update documentation
---

# Pull Request Description

## Summary
Brief description of changes and why they are needed.

## What Changed
- List the specific changes made
- Include any new features, fixes, or improvements
- Mention any files or components affected

## Related Issues
<!-- This section is now handled by the metadata above, but you can add context here -->
This PR addresses the requirements in the linked issues by implementing [describe approach].

## Type of Change
<!-- This is now specified in metadata, but you can elaborate here -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Maintenance (refactoring, dependencies, etc.)

## Testing
- [ ] Tests pass locally with `./scripts/run-ci-docker.sh`
- [ ] Added tests for new functionality
- [ ] Coverage requirements met (≥85% for new code, ≥78% overall)
- [ ] Manual testing completed for UI/UX changes

### Test Results
```
# Paste test coverage output here
Coverage: 85.2% (target: 78%+)
Tests: 45 passed, 0 failed
```

## Risk Assessment
<!-- This is now specified in metadata, but provide details here -->
**Risk Level**: [Low/Medium/High]

**Potential Issues**:
- List any potential risks or side effects
- Include mitigation strategies
- Mention any rollback procedures

## Review Requirements
<!-- Specify if special reviews are needed -->
- [ ] Code review (always required)
- [ ] Architecture review (for significant design changes)
- [ ] Security review (for security-related changes)
- [ ] Performance review (for performance-critical changes)

## Deployment Notes
- Any special deployment considerations
- Database migrations required: Yes/No
- Configuration changes needed: Yes/No
- Feature flags involved: Yes/No

## Checklist
- [ ] Code follows the style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional commit format
- [ ] PR title is clear and descriptive
- [ ] Machine-readable metadata is complete and accurate

## Additional Notes
<!-- Any additional information, breaking changes, migration notes, etc. -->

---

<!--
🔧 Format Documentation:

The YAML frontmatter above provides machine-readable metadata for automation workflows.
This enables reliable parsing and automation while maintaining human readability.

Key benefits:
- Eliminates shell parsing errors in CI workflows
- Enables advanced automation based on PR characteristics
- Provides structured data for reporting and analytics
- Maintains backward compatibility

For more information, see: docs/pr-format-guide.md
-->
