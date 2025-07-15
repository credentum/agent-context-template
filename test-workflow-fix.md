# Test workflow fix

This is a test change to verify that the claude-code-review.yml workflow
can now properly extract ISSUE: suggestions from Claude's comments and
create aggregated follow-up issues.

The workflow should find the ISSUE: lines from PR #83's review and create
a new aggregated issue automatically.
