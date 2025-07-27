# Issue #1663: Support flexible branch naming patterns in Phase 4 PR validation

**Session Started**: 2025-07-27
**GitHub Issue**: #1663
**Sprint**: sprint-current
**Task Template**: context/trace/task-templates/issue-1663-support-flexible-branch-naming-patterns.md

## Token Budget & Complexity Assessment
- **Estimated tokens**: 5000
- **Complexity**: Low-Medium (method modification + configuration)
- **Files affected**: 2-3 (workflow-validator.py, config, tests)
- **Time estimate**: 30 minutes

## Step-by-Step Implementation Plan

### Phase 1: Analysis (COMPLETED)
- [x] Reviewed issue #1663 details
- [x] Located `_check_pr_created()` method in workflow-validator.py:327-339
- [x] Identified hardcoded branch patterns: only checks fix/ and feature/
- [x] Confirmed existing config loading pattern exists
- [x] Created task template

### Phase 2: Implementation Plan
1. **Modify `_check_pr_created()` method**:
   - Replace hardcoded patterns with configurable approach
   - Use `gh pr list --json headRefName` for better parsing
   - Support default patterns: fix, feature, hotfix, refactor, chore, docs, style, test
   - Add custom regex pattern support

2. **Update configuration**:
   - Add branch_patterns section to default config
   - Support both prefix list and custom regex patterns
   - Maintain backward compatibility

3. **Add tests**:
   - Test various branch naming patterns
   - Test custom regex patterns
   - Test backward compatibility

### Current Problem Analysis
```python
# Current implementation (lines 327-339)
def _check_pr_created(self) -> bool:
    """Check if PR was created."""
    result = subprocess.run(
        ["gh", "pr", "list", "--head", f"fix/{self.issue_number}-", "--limit", "10"],
        capture_output=True,
        shell=False,
        text=True,
    )
    output = result.stdout.strip()
    return f"fix/{self.issue_number}-" in output or f"feature/{self.issue_number}-" in output
```

**Problems**:
1. Only searches for fix/ prefix in `gh pr list --head`
2. Only checks fix/ and feature/ patterns in output
3. No configuration support
4. Misses valid PRs with other prefixes

### Proposed Solution
```python
def _check_pr_created(self) -> bool:
    """Check if PR was created with flexible branch pattern matching."""
    # Get configured branch prefixes or use defaults
    branch_config = self.config.get("branch_patterns", {})
    branch_prefixes = branch_config.get("prefixes", [
        "fix", "feature", "hotfix", "refactor", "chore", "docs", "style", "test"
    ])

    try:
        # Get all PRs to search through
        result = subprocess.run(
            ["gh", "pr", "list", "--json", "headRefName", "--limit", "50"],
            capture_output=True,
            shell=False,
            text=True
        )

        if result.returncode == 0:
            import json
            prs = json.loads(result.stdout)

            issue_pattern = f"{self.issue_number}-"

            # Check if any PR branch contains our issue number
            for pr in prs:
                branch_name = pr.get("headRefName", "")

                # Check standard patterns: prefix/issue_number-*
                for prefix in branch_prefixes:
                    if branch_name.startswith(f"{prefix}/{issue_pattern}"):
                        return True

                # Check custom regex if configured
                custom_pattern = branch_config.get("custom_regex")
                if custom_pattern:
                    import re
                    pattern = custom_pattern.format(issue=self.issue_number)
                    if re.match(pattern, branch_name):
                        return True

        return False
    except Exception:
        return False
```

### Configuration Addition
```python
def _get_default_config(self) -> Dict[str, Any]:
    """Get default configuration for backward compatibility."""
    return {
        "phases": {
            "validation": {
                "ci_validation": {
                    "require_ci": True,
                    "max_age_hours": 1,
                    "marker_files": [".last-ci-run"],
                    "allow_test_only": False,
                }
            }
        },
        "branch_patterns": {
            "prefixes": [
                "fix", "feature", "hotfix", "refactor",
                "chore", "docs", "style", "test"
            ],
            "custom_regex": None  # Optional custom pattern with {issue} placeholder
        }
    }
```

## Notes
- Need to ensure JSON parsing is safe
- Maintain security with subprocess calls (already using shell=False)
- Add proper error handling for JSON parsing
- Test with various branch naming scenarios
