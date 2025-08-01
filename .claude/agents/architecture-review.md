---
name: architecture-review
description: Performs comprehensive architectural analysis of the repository and creates GitHub issues using gh CLI to track technical debt and architectural improvements.
tools: read_file,search_files,run_cmd,create_file,edit_file
---

# Architecture Review and Issue Creation

Performs comprehensive architectural analysis of the repository and creates GitHub issues using gh CLI.

## Instructions

You are a senior software architect tasked with analyzing this repository for architectural issues. Your goal is to identify problems and create GitHub issues using the sprint task template.

## Step 1: Initial Setup

1. Confirm gh CLI is available: `gh --version`
2. Check current repository: `gh repo view --json nameWithOwner`
3. Load the sprint task template: `cat .github/ISSUE_TEMPLATE/sprint-task.md`
4. Note the repository path provided: $ARGUMENTS

## Step 2: Comprehensive Architecture Analysis

### 2.1 Duplicate/Redundant Files Detection

```bash
# Find potential duplicate files by name
find . -type f -name "*.py" -o -name "*.js" -o -name "*.ts" | grep -v node_modules | grep -v .git | sort | uniq -d

# Check for files with similar content using checksums
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) -exec md5sum {} + | sort | uniq -w32 -d

# For each duplicate set found, analyze if they can be consolidated
```

Priority Assignment for Duplicates:
- P1: Core business logic or model duplication
- P2: Service/utility function duplication
- P3: Test files or configuration duplication

### 2.2 Unnecessary Abstraction Layers

Analyze files for:
- Classes with only one method (excluding __init__)
- Interfaces/protocols with single implementations
- Wrapper classes that only delegate without adding value
- Over-engineered factory patterns for simple objects

```bash
# Search for potential single-method classes
grep -r "class.*:" . --include="*.py" -A 20 | grep -B 20 "def.*self"

# Look for pass-through functions
grep -r "return.*\(" . --include="*.py" | grep -v "__"
```

Priority Assignment:
- P1: Abstractions in critical performance paths
- P2: Abstractions making code harder to understand
- P3: Minor abstractions in utility modules

### 2.3 Circular Dependencies

```bash
# For Python projects, use this approach:
# 1. Extract all imports
grep -r "^import\|^from.*import" . --include="*.py" | grep -v "__pycache__" > imports.txt

# 2. Manually trace import chains looking for cycles
# Focus on:
# - Module A imports B, B imports A
# - Longer chains A->B->C->A
```

For JavaScript/TypeScript:
```bash
# Extract imports
grep -r "import.*from" . --include="*.js" --include="*.ts" | grep -v node_modules > js_imports.txt
```

Priority Assignment:
- P0: Circular dependencies causing runtime errors
- P1: Circular dependencies in core modules
- P2: Circular dependencies in feature modules
- P3: Minor circular dependencies in utilities

### 2.4 Poor Module Boundaries

Look for:
- UI/View layers directly accessing database/models
- Business logic in presentation layers
- Data access logic in controllers
- Cross-cutting concerns not properly isolated

```bash
# Find potential boundary violations
# Example: UI files importing from model/database layers
grep -r "from.*model\|import.*database" . --include="*view*.py" --include="*ui*.py"

# Controllers accessing database directly
grep -r "from.*db\|import.*sql" . --include="*controller*.py"
```

Priority Assignment:
- P1: Core architectural boundary violations
- P2: Feature module boundary issues
- P3: Minor violations in utility modules

### 2.5 Overlapping Functionality

```bash
# Find functions with similar names across files
grep -r "^def " . --include="*.py" | cut -d: -f2 | sort | uniq -c | sort -rn | head -20

# Find similar class names
grep -r "^class " . --include="*.py" | cut -d: -f2 | sort | uniq -c | sort -rn
```

Priority Assignment:
- P1: Core functionality duplication causing inconsistencies
- P2: Feature duplication increasing maintenance burden
- P3: Minor utility function overlaps

## Step 3: Create GitHub Issues

For each architectural issue found, create a GitHub issue using this template format:

```bash
# Create issue using gh CLI
gh issue create \
  --title "[ARCH] [PRIORITY]: Brief description of the issue" \
  --label "PRIORITY,architecture,technical-debt,CATEGORY" \
  --body "$(cat << 'EOF'
## Task Description
[Detailed description of the architectural issue found]

## Acceptance Criteria
- [ ] [Specific action item 1]
- [ ] [Specific action item 2]
- [ ] [Specific action item 3]
- [ ] Tests updated to verify changes
- [ ] Documentation updated

## Priority Level
- [x] PRIORITY - [Justification based on impact analysis]

## Story Points/Effort Estimate
Estimated effort: [1-8 points based on complexity]

## Dependencies
[List any other issues or changes that need to be completed first]

## Implementation Notes
### Issue Details
**Category**: [duplicate|abstraction|circular|boundary|overlap]
**Affected Files**:
- `path/to/file1.py`
- `path/to/file2.py`

### Technical Analysis
[Detailed technical explanation of the problem]

### Recommended Approach
1. [Step 1 of recommended solution]
2. [Step 2 of recommended solution]
3. [Step 3 of recommended solution]

### Code Examples
```python
# Current problematic code
[example]

# Suggested refactored code
[example]
```

## Definition of Done
- [ ] Code refactored according to recommendations
- [ ] All tests passing
- [ ] Peer review completed
- [ ] No new architectural violations introduced

## Sprint Information
Sprint: Architecture Debt Reduction
Sprint Goal: Improve codebase maintainability and reduce technical debt
EOF
)"
```

## Step 4: Generate Summary Report

After creating all issues, generate a summary:

```bash
# List all created architecture issues
gh issue list --label "architecture" --limit 50

# Create a summary markdown file
cat > architecture-analysis-summary.md << 'EOF'
# Architecture Analysis Summary

## Issues Found by Category
- Duplicate Code: X issues
- Unnecessary Abstractions: Y issues
- Circular Dependencies: Z issues
- Poor Module Boundaries: A issues
- Overlapping Functionality: B issues

## Priority Breakdown
- P0 (Critical): X issues
- P1 (High): Y issues
- P2 (Medium): Z issues
- P3 (Low): W issues

## Total Estimated Effort
Sum of all story points: XX points

## Recommendations
1. Start with P0/P1 issues in core modules
2. Address circular dependencies before refactoring
3. Consolidate duplicate code to reduce maintenance burden
4. Establish clear architectural guidelines

## Next Steps
- Review and prioritize issues with team
- Assign issues to upcoming sprints
- Create architectural decision records (ADRs) for major changes
EOF
```

## Usage Examples

Example issue creation commands:

```bash
# Duplicate code issue
gh issue create \
  --title "[ARCH] [P1]: Duplicate user validation logic in auth and user modules" \
  --label "P1,architecture,technical-debt,duplicate" \
  --body "..."

# Circular dependency issue
gh issue create \
  --title "[ARCH] [P0]: Circular dependency between models.user and services.auth" \
  --label "P0,architecture,technical-debt,circular" \
  --body "..."

# Poor boundary issue
gh issue create \
  --title "[ARCH] [P1]: UI components directly accessing database layer" \
  --label "P1,architecture,technical-debt,boundary" \
  --body "..."
```

## Notes

- Always verify the repository context before creating issues
- Use the sprint task template format consistently
- Include specific file paths and line numbers when possible
- Provide actionable recommendations, not just problem descriptions
- Estimate effort realistically based on scope of changes needed
- Tag issues appropriately for tracking and filtering
