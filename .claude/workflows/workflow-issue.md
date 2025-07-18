# Fix GitHub Issue Workflow

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Usage](#usage)
4. [Parameters](#parameters)
5. [Workflow Steps](#workflow-steps)
   - [Phase 1: Analysis & Planning](#phase-1-analysis--planning)
   - [Phase 2: Implementation](#phase-2-implementation)
   - [Phase 3: Testing & Validation](#phase-3-testing--validation)
   - [Phase 4: Deployment & PR Management](#phase-4-deployment--pr-management)
   - [Phase 5: Documentation & Cleanup](#phase-5-documentation--cleanup)
6. [Error Handling](#error-handling)
7. [Security Guidelines](#security-guidelines)
8. [Success Criteria](#success-criteria)
9. [Configuration](#configuration)
10. [Integration Points](#integration-points)
11. [Usage Notes](#usage-notes)

## Overview
This workflow automates the complete GitHub issue resolution process from analysis through PR acceptance, including automated task template generation, implementation, testing, and monitoring the PR through completion.

## Prerequisites
- GitHub CLI authenticated (`gh auth status`)
- Docker available for CI testing
- Pre-commit hooks installed
- Claude Code CLI properly configured
- Appropriate repository permissions for PR creation and monitoring

## Usage
```bash
# Basic usage
claude workflow workflow-issue --issue 123

# With automation features
claude workflow workflow-issue --issue 123 --auto-template --parallel-agents

# With custom parameters
claude workflow workflow-issue --issue 123 --priority high --component api --max-wait 24h
```

## EXECUTE WORKFLOW
Please follow these steps in order. **Actually perform each action** - don't just describe what should be done.

## Parameters
- `--issue`: GitHub issue number (required)
- `--auto-template`: Enable automatic task template generation
- `--parallel-agents`: Enable multi-agent coordination
- `--priority`: Override issue priority (high/medium/low)
- `--component`: Override component classification
- `--max-wait`: Maximum time to wait for PR completion (default: 48h)
- `--check-interval`: How often to check PR status (default: 15m)

---

## Workflow Steps

### Phase 1: Analysis & Planning

#### Step 1: Issue Analysis
**EXECUTE NOW:**
1. First, extract the issue number from the command arguments
2. Run: `gh issue view [ISSUE_NUMBER]` to get issue details
3. Extract sprint and phase information from issue labels/description
4. Understand the problem described in the issue
5. Ask clarifying questions if necessary

#### Step 2: Context Gathering
**EXECUTE NOW:**
1. Search for previous thoughts: `find context/trace/scratchpad/ -name "*issue-[ISSUE_NUMBER]*" -o -name "*[ISSUE_TITLE_KEYWORDS]*"`
2. Search for relevant ADRs: `find context/decisions/ -name "*.md" | xargs grep -l "[RELEVANT_KEYWORDS]"`
3. Search for related PRs: `gh pr list --search "issue:[ISSUE_NUMBER]"`
4. Search the codebase for relevant files: `find src/ -name "*.py" | xargs grep -l "[RELEVANT_KEYWORDS]"`

#### Step 3: Task Template Generation
**EXECUTE NOW:**
1. **Create the task template file** using the issue analysis:
   - Determine sanitized title from issue
   - Create file: `context/trace/task-templates/issue-[ISSUE_NUMBER]-[sanitized-title].md`
   - Write the complete template content following the structure below
   - Fill in all placeholders with actual values from the issue analysis

**Task Template Structure:**
```markdown
# ────────────────────────────────────────────────────────────────────────
# TASK: issue-$ISSUE_NUMBER-{title}
# Generated from GitHub Issue #$ISSUE_NUMBER
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-$ISSUE_NUMBER-{sanitized-title}`

## 🎯 Goal (≤ 2 lines)
> {Extract clear objective from issue description}

## 🧠 Context
- **GitHub Issue**: #$ISSUE_NUMBER - {title}
- **Sprint**: {extract from labels/description}
- **Phase**: {extract from labels}
- **Component**: {extract from labels}
- **Priority**: {extract from labels}
- **Why this matters**: {business context from issue}
- **Dependencies**: {identified dependencies}
- **Related**: {linked PRs/issues}

## 🛠️ Subtasks
{Generate based on complexity analysis}

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| {identified files} | {modify/create/test} | {best technique} | {specific purpose} | {Low/Med/High} |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior software engineer working on {component/domain}.

**Context**
GitHub Issue #$ISSUE_NUMBER: {title}
{Paste relevant issue context}
Current codebase follows {identified patterns}.
Related files: {file list with purposes}

**Instructions**
1. **Primary Objective**: {clear goal from issue}
2. **Scope**: Address issue requirements while maintaining system integrity
3. **Constraints**:
   - Follow existing code patterns: {identified patterns}
   - Maintain backward compatibility unless breaking change approved
   - Keep public APIs unchanged unless specified in issue
4. **Prompt Technique**: {selected technique} because {justification based on task type}
5. **Testing**: Address test requirements from issue acceptance criteria
6. **Documentation**: Update as specified in issue requirements

**Technical Constraints**
• Expected diff ≤ {estimated} LoC, ≤ {estimated} files
• Context budget: ≤ {estimated based on file analysis}k tokens
• Performance budget: {based on complexity}
• Code quality: Black formatting, coverage ≥ 71.82%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation addressing issue requirements.
Use conventional commits: {type}({scope}): {description}

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: {derived from acceptance criteria}
- **Integration tests**: {if needed based on component}

## ✅ Acceptance Criteria
{Extract and reformat from GitHub issue}

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: {estimated based on file sizes}
├── time_budget: {estimated based on complexity}
├── cost_estimate: {calculated}
├── complexity: {assessed from issue scope}
└── files_affected: {count from analysis}

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: $ISSUE_NUMBER
sprint: {extracted}
phase: {extracted}
component: {extracted}
priority: {extracted}
complexity: {assessed}
dependencies: {identified}
```
```

#### Step 4: Execution Planning
**EXECUTE NOW:**
1. Break down the issue into specific, actionable tasks based on the issue requirements
2. **Create the scratchpad file**:
   - Create file: `context/trace/scratchpad/$(date +%Y-%m-%d)-issue-[ISSUE_NUMBER]-[title].md`
   - Write the execution plan including:
     - Issue link and sprint reference
     - Reference to the created task template
     - Token budget and complexity assessment
     - Step-by-step implementation plan
3. **Update sprint file if it exists**:
   - Check if `context/sprints/current.yaml` exists
   - If it does, update it to reflect this work item

#### Step 5: Context Management Setup
1. Monitor context window usage throughout execution
2. Use `/clear` if context approaches 25k tokens
3. Reference task template for prompt technique guidance
4. Track actual vs. estimated budget in real-time

### Phase 2: Implementation

#### Step 6: Branch Creation & Development
**EXECUTE NOW:**
1. **Create and switch to new branch**:
   - Determine if this is a fix or feature based on issue type
   - Run: `git checkout -b [fix|feature]/[ISSUE_NUMBER]-[description]`
2. **Implement the solution**:
   - Apply the prompt technique identified in the task template
   - Make the necessary code changes to address the issue requirements
   - Work in small, logical commits
3. **Make commits as you go**:
   - After each logical change, run: `git add [changed_files]`
   - Commit with: `git commit -m "[type]([scope]): [description]"`
   - Types: feat, fix, test, docs, refactor, style, chore
4. **Update CLAUDE.md** if the changes affect development workflow

### Phase 3: Testing & Validation

#### Step 7: Local Testing
**EXECUTE NOW:**
1. **Run CI checks locally FIRST**:
   - Execute: `./scripts/run-ci-docker.sh`
   - If this fails, debug with: `./scripts/run-ci-docker.sh debug`
   - Alternative if Docker not available: `make lint`
2. **Run pre-commit hooks**:
   - Execute: `pre-commit run --all-files`
3. **Write and run tests**:
   - Create/update tests in `tests/` directory for new functionality
   - Run: `pytest --cov=src --cov-report=term-missing`
   - Ensure coverage doesn't drop below 71.82%
4. **Update coverage metrics**:
   - Run: `python scripts/update_coverage_metrics.py`
5. **Additional testing if applicable**:
   - If working on MCP tools, test with mock MCP client
   - Run any domain-specific tests

#### Step 8: Quality Verification
**EXECUTE NOW:**
1. **Final CI verification**:
   - Run: `./scripts/run-ci-docker.sh`
   - All checks must pass: Black, isort, Flake8, MyPy, context validation, import checks
2. **Validate YAML files**:
   - Run: `python -m src.agents.context_lint validate context/`
3. **Check specific functionality**:
   - Verify any new context files have proper schema_version
   - If embed_doc.py was modified, check hash-diff functionality
   - If GraphRAG was touched, verify Neo4j queries still work

### Phase 4: Deployment & PR Management

#### Step 9: Pre-PR Preparation
**EXECUTE NOW:**
1. **Sync with main branch**:
   - Run: `git fetch origin main`
   - Run: `git rebase origin/main` (or merge if preferred)
   - Resolve any conflicts if they occur
2. **Final verification**:
   - Run: `./scripts/run-ci-docker.sh`
   - Run: `pre-commit run --all-files`
   - If pre-commit made changes: `git add -A && git commit --amend --no-edit`
3. **Update task template with actual results**:
   - Open the task template file created earlier
   - Fill in the "Actuals" section with real token usage, time taken, etc.
   - Document any lessons learned or deviations from plan

#### Step 10: PR Creation
**EXECUTE NOW:**
1. **Create the Pull Request**:
   ```bash
   gh pr create \
     --title "fix([COMPONENT]): [ISSUE_TITLE]" \
     --body "Fixes #[ISSUE_NUMBER]

   ## Changes
   - [List the specific changes made]

   ## Testing
   - [X] All CI checks pass locally
   - [X] Coverage maintained at 71.82%+
   - [X] Pre-commit hooks pass

   ## Task Template
   - Template used: context/trace/task-templates/issue-[ISSUE_NUMBER]-[title].md
   - Estimated budget: [tokens/time from template]
   - Actual usage: [actual tokens/time used]

   ## Verification
   - [X] Docker CI passed locally
   - [X] All tests pass
   - [X] Context validation successful

   ## Context Changes
   - [Document any changes to context/ structure]

   ## Sprint Impact
   - Sprint: [sprint reference if applicable]
   - Phase: [phase reference if applicable]
   - Component: [component name]
   " \
     --label "sprint-current,fix,ready-for-review" \
     --assignee @me
   ```

2. **Push the branch**: `git push origin [BRANCH_NAME]`

#### Step 11: PR Monitoring & Completion
**EXECUTE NOW:**
1. **Get PR number and enter monitoring mode**:
   ```bash
   # Get the PR number from the created PR
   PR_NUMBER=$(gh pr view --json number --jq '.number')
   echo "Created PR #$PR_NUMBER - entering monitoring mode"
   echo "You can check status manually with: gh pr view $PR_NUMBER"
   echo "Monitoring will check every 15 minutes until merged or 48 hours elapsed"
   ```

2. **Set up automated monitoring** (this will run in background):
   - Create a monitoring script that checks PR status every 15 minutes
   - Monitor CI checks, review status, and merge readiness
   - Exit when PR is merged or after 48 hours
   - Log all status changes to context/trace/logs/

3. **Manual monitoring instructions**:
   - Check PR status: `gh pr view [PR_NUMBER]`
   - Check CI status: `gh pr checks [PR_NUMBER]`
   - Check reviews: `gh pr view [PR_NUMBER] --json reviews`
   - The workflow will complete when the PR is merged by a reviewer

### Phase 5: Documentation & Cleanup

#### Step 12: Final Documentation
**EXECUTE NOW:**
1. **Update completion logs**:
   - Create/append to: `context/trace/logs/workflow-completions.log`
   - Log: "$(date): Issue #[ISSUE_NUMBER] workflow completed via PR #[PR_NUMBER]"
2. **Document lessons learned**:
   - Add any new patterns or techniques discovered to the task template
   - Note any deviations from the planned approach
3. **Update documentation if needed**:
   - If workflow changes were made, update relevant documentation
   - Update CLAUDE.md if development processes changed
4. **Archive and organize**:
   - Ensure task template and scratchpad are properly saved
   - Clean up any temporary files created during the workflow

**WORKFLOW COMPLETION**:
- Issue #[ISSUE_NUMBER] has been resolved
- PR created and submitted for review
- All documentation updated
- Monitoring in place for PR completion

---

## Error Handling

### Common Issues & Solutions

#### CI Failures
- **Problem**: Docker CI checks fail
- **Solution**: Run `./scripts/run-ci-docker.sh debug` locally first
- **Prevention**: Always run CI checks before pushing

#### Context Overflow
- **Problem**: Context window becomes too large
- **Solution**: Use `/clear` and reload essential context from task template
- **Prevention**: Monitor context usage proactively

#### PR Review Delays
- **Problem**: PR waiting too long for review
- **Solution**: Adjust `--max-wait` parameter or follow up with team
- **Prevention**: Coordinate with reviewers before starting large changes

#### Merge Conflicts
- **Problem**: Branch conflicts with main
- **Solution**:
  ```bash
  git checkout main
  git pull origin main
  git checkout fix/$ISSUE_NUMBER-{description}
  git rebase main
  # Resolve conflicts
  git push --force-with-lease
  ```

### Emergency Procedures

#### Workflow Interruption
If the workflow is interrupted:
1. Check current state: `gh pr view $PR_NUMBER`
2. Resume from appropriate phase
3. Update task template with current status
4. Continue monitoring if PR exists

#### Critical Issue Discovery
If critical issues are discovered during PR review:
1. Document the issue in task template
2. Create follow-up issue if needed
3. Update sprint plans if timeline affected
4. Coordinate with team for resolution

---

## Security Guidelines

### Bash Command Security
When using bash commands in this workflow, follow these security guidelines:

#### Variable Validation
- **Always validate user input**: Never directly use issue numbers or user-provided strings without validation
- **Use parameter expansion**: `${VAR:-default}` to provide safe defaults
- **Sanitize file paths**: Use absolute paths and validate they're within expected directories

#### Command Injection Prevention
```bash
# ❌ DANGEROUS - Direct variable interpolation
git checkout fix/$ISSUE_NUMBER-$TITLE

# ✅ SAFE - Validated and sanitized
ISSUE_NUMBER=$(echo "$ISSUE_NUMBER" | grep -E '^[0-9]+$' || echo "invalid")
SAFE_TITLE=$(echo "$TITLE" | sed 's/[^a-zA-Z0-9-]//g' | cut -c1-50)
git checkout "fix/${ISSUE_NUMBER}-${SAFE_TITLE}"
```

#### Safe Command Patterns
- **Use quoted variables**: Always quote variables in commands: `"$VARIABLE"`
- **Validate exit codes**: Check `$?` after critical commands
- **Use `--` for argument separation**: `git checkout -- "$FILE"`
- **Avoid `eval`**: Never use `eval` with user input

#### GitHub CLI Security
- **Authenticate properly**: Use `gh auth status` before operations
- **Validate PR numbers**: Ensure PR numbers are numeric
- **Use `--repo` flag**: Specify repository explicitly for safety

#### Example Safe Commands
```bash
# Safe issue number validation
if [[ "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
    gh issue view "$ISSUE_NUMBER"
else
    echo "Invalid issue number" >&2
    exit 1
fi

# Safe branch name creation
SAFE_BRANCH_NAME=$(echo "fix/${ISSUE_NUMBER}-${TITLE}" | \
    sed 's/[^a-zA-Z0-9-]/-/g' | \
    sed 's/--*/-/g' | \
    cut -c1-100)
```

### Git Security
- **Use `--force-with-lease`**: Instead of `--force` for safer push operations
- **Validate remotes**: Check `git remote -v` before push operations
- **Use SSH/HTTPS**: Avoid git:// protocol for security

### File System Security
- **Validate paths**: Ensure file paths are within expected directories
- **Use temporary files safely**: Create with proper permissions
- **Clean up**: Remove temporary files after use

---

## Success Criteria

### Workflow Completion Requirements
- [ ] All acceptance criteria from original issue met
- [ ] CI checks pass (Docker CI, tests, coverage)
- [ ] Code quality standards maintained
- [ ] PR created with comprehensive documentation
- [ ] PR successfully merged by reviewer
- [ ] Documentation updated appropriately
- [ ] Task template updated with actuals
- [ ] Sprint progress updated

### Quality Gates
- [ ] Coverage ≥ 71.82% maintained
- [ ] All Docker CI checks pass
- [ ] No regressions in existing functionality
- [ ] Code follows established patterns
- [ ] Tests cover new functionality adequately

### Automation Success Metrics
- [ ] Task template generated automatically
- [ ] Resource estimates within 20% of actuals
- [ ] Context management optimal (minimal `/clear` usage)
- [ ] PR monitoring completes successfully
- [ ] Total workflow time meets estimates

---

## Configuration

### Default Settings
```yaml
max_wait_hours: 48
check_interval_minutes: 15
auto_template_generation: true
context_budget_limit: 25000
require_ci_pass: true
require_coverage_maintained: true
```

### Customization Options
- Adjust timeout values for different issue types
- Configure notification preferences for PR status changes
- Set up custom review requirements
- Enable/disable specific automation features

---

## Integration Points

### Sprint System Integration
- Updates sprint progress automatically
- Links to sprint goals and phases
- Tracks completion metrics

### Context System Integration
- Inherits context from sprint and issue
- Maintains context history and lineage
- Optimizes context window usage

### Automation Integration
- Supports event-driven triggers
- Enables multi-agent coordination
- Provides learning data for optimization

---

## Usage Notes

### For Simple Issues
```bash
claude workflow fix-issue --issue 123
```

### For Complex Issues with Full Automation
```bash
claude workflow fix-issue --issue 456 --auto-template --parallel-agents --max-wait 72h
```

### For Urgent Issues
```bash
claude workflow fix-issue --issue 789 --priority high --check-interval 5m
```

Remember: This workflow is designed for **complete issue resolution** including PR acceptance. It will not complete until the PR is successfully merged or the timeout is reached.
