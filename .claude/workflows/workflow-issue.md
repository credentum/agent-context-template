# Fix GitHub Issue Workflow

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Usage](#usage)
4. [Parameters](#parameters)
5. [Workflow Steps](#workflow-steps)
   - [Phase 0: Investigation (If Needed)](#phase-0-investigation-if-needed)
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

# With hybrid mode (specialist sub-agents)
claude workflow workflow-issue --issue 123 --hybrid
```

## EXECUTE WORKFLOW
Please follow these steps in order. **Actually perform each action** - don't just describe what should be done.

## 🛡️ WORKFLOW ENFORCEMENT INTEGRATION
**CRITICAL: This workflow now includes automatic enforcement validation at each phase!**

### Enforcement Overview
- Each phase now starts with `enforce_workflow_phase()` to validate prerequisites
- Each phase ends with `complete_workflow_phase()` to validate outputs
- State is persisted across all agent executions in `.workflow-state-{issue_number}.json`
- Failed validations prevent progression to next phase
- Resume capability available from any failed phase

### Resume from Failed Phase
If workflow was interrupted or validation failed:
```python
# Check current workflow state
from workflow_validator import WorkflowValidator
validator = WorkflowValidator(issue_number)
print(f"Current phase: {validator.state['current_phase']}")
print(f"Completed phases: {[p['phase'] for p in validator.state['phases_completed'] if p['status'] == 'completed']}")

# Resume from last successful phase or retry failed phase
# The enforcement system will automatically detect where to resume
```

### Agent Integration Points
- **Phase 0**: issue-investigator agent with validation hooks
- **Phase 1**: task-planner agent with validation hooks
- **Phase 2**: main-claude with validation hooks
- **Phase 3**: test-runner agent with validation hooks
- **Phase 4**: pr-manager agent with validation hooks
- **Phase 5**: pr-manager agent with validation hooks

### Error Handling Strategy
1. **Validation Failure**: Fix prerequisites and retry phase
2. **Agent Failure**: Resume from last checkpoint
3. **State Corruption**: Restore from state file
4. **Process Interruption**: Resume from workflow state

## 🔄 HYBRID MODE WITH SPECIALIST SUB-AGENTS
**NEW: Enhanced workflow execution with specialist consultants!**

### Hybrid Mode Overview
The hybrid mode enhances the standard WorkflowExecutor with specialist sub-agents that provide expert analysis without handling persistence:

```bash
# Enable hybrid mode with --hybrid flag
claude workflow workflow-issue --issue 123 --hybrid
```

### Specialist Integration Points
- **Phase 0 (Investigation)**: `issue-investigator` for complex root cause analysis
- **Phase 1 (Planning)**: `general-purpose` for codebase research and pattern analysis
- **Phase 3 (Validation)**: `test-runner` + `security-analyzer` in parallel
- **All Phases**: Graceful fallback if specialists fail

### Benefits of Hybrid Mode
1. **Enhanced Analysis**: Specialists provide deeper insights for complex issues
2. **Parallel Processing**: Multiple specialists can run simultaneously (e.g., validation)
3. **Maintained Persistence**: All state management remains in WorkflowExecutor
4. **Backward Compatible**: Falls back to basic mode if specialists unavailable
5. **Configurable**: Customize when specialists are used via `.claude/config/specialist-agents.yaml`

### When to Use Hybrid Mode
- **Complex Issues**: Issues marked as "high complexity" or "investigation needed"
- **Large Codebases**: When >10 files affected or cross-module changes
- **Enhanced Validation**: For critical changes requiring thorough testing
- **Performance Testing**: When parallel specialist analysis can speed up workflow

### Specialist Configuration
Configure specialist behavior in `.claude/config/specialist-agents.yaml`:
```yaml
specialist_agents:
  investigation:
    threshold: complex  # When to use: always, never, complex, large_codebase
    agents:
      - type: issue-investigator
        timeout: 300  # 5 minutes
```

### Hybrid Mode Example
```bash
# For a complex architectural issue
claude workflow workflow-issue --issue 789 --hybrid --priority high

# Output will show specialist consultations:
🔍 Executing investigation phase (hybrid mode)...
  🤖 Consulting issue-investigator specialist...
  ✅ Specialist provided additional insights
```

## 📋 DOCUMENTATION STRATEGY
**CRITICAL: All documentation must be committed BEFORE or DURING the PR, not after!**

| Phase | Documentation Action | Timing | Purpose |
|-------|---------------------|---------|----------|
| Phase 1 | Create task template & scratchpad | Before implementation | Planning & context |
| Phase 1 | Initial commit of docs | Before code changes | Ensure docs in PR |
| Phase 4 | Update with actual results | Before PR creation | Accurate tracking |
| Phase 4 | Add completion logs | Before PR creation | Include in PR |
| Phase 5 | Verify documentation | After PR creation | Ensure completeness |

**This prevents the common mistake of creating documentation after pushing the PR, which leaves it only in local branch.**

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

### Phase 0: Investigation (If Needed)

**When to Use This Phase:**
- Issue describes symptoms but root cause is unclear
- Initial implementation attempts reveal unexpected complexity
- Multiple potential solutions exist with different trade-offs
- The problem spans multiple components or systems
- You discover the issue is significantly larger than described

#### Step 0.0: Workflow Enforcement Setup
**EXECUTE NOW:**
```python
# Initialize workflow enforcement for this issue
from workflow_validator import enforce_workflow_phase, complete_workflow_phase

# Enforce Phase 0 prerequisites before starting
validator = enforce_workflow_phase(issue_number, 0, "issue-investigator")
```

#### Step 0.1: Assess Investigation Need
**EXECUTE NOW:**
1. Review the issue description for clarity of scope
2. Check if issue uses investigation template or has "needs-scope" label
3. Look for phrases like "sometimes", "occasionally", "might be related to"
4. Consider if you can confidently estimate the implementation effort

**Decision Point:**
- If scope is clear → Skip to Phase 1 (but complete Phase 0 enforcement first)
- If scope is unclear → Continue with investigation

#### Step 0.2: Create Investigation Issue (If Not Exists)
**EXECUTE NOW:**
```bash
# If the current issue isn't already an investigation issue
gh issue create \
  --title "[INVESTIGATION] Original issue title" \
  --body "$(cat <<EOF
## Related To
Original issue: #[ISSUE_NUMBER]

## Symptoms Observed
[Copy relevant symptoms from original issue]

## Investigation Plan
- [ ] [Specific investigation steps based on symptoms]

## Time Budget
Maximum investigation time: 4 hours
EOF
)" \
  --label "investigation,needs-scope"
```

#### Step 0.3: Time-boxed Investigation
**EXECUTE NOW:**
1. Set investigation timer (recommended: 2-4 hours max)
2. Follow investigation plan systematically
3. Document findings in real-time in the investigation issue
4. Test theories with minimal code changes
5. Identify distinct sub-problems as you discover them

#### Step 0.4: Document Findings and Decompose
**EXECUTE NOW:**
1. Update investigation issue with:
   - Root cause analysis
   - Identified sub-problems
   - Recommended decomposition strategy
   - Effort estimates for each component

2. Create decomposed implementation issues:
```bash
# For each identified sub-problem
gh issue create \
  --title "[Component] Specific sub-problem" \
  --body "Part of investigation #[INVESTIGATION_NUMBER]

## Context
[Relevant findings from investigation]

## Specific Scope
[Clear boundaries of this sub-issue]

## Dependencies
- Depends on: #[OTHER_ISSUE] (if applicable)
- Blocks: #[OTHER_ISSUE] (if applicable)
" \
  --label "component:[relevant],decomposed"
```

#### Step 0.5: Close Investigation with Summary
**EXECUTE NOW:**
1. Update investigation issue with final summary
2. Link all created sub-issues
3. Close investigation issue with resolution comment
4. Proceed to Phase 1 with first implementation issue

**Example from Issue #1029:**
```markdown
Investigation revealed 3 interconnected problems:
1. Git syntax error (created #1043) - Must fix first
2. Authentication scope issue (created #1044) - Depends on #1043
3. Phantom check creation (created #1045) - Cleanup after #1044

Proceeding with #1043 as first implementation.
```

#### Step 0.6: Complete Phase 0 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 0 with investigation outputs
phase_0_outputs = {
    "investigation_completed": True,
    "root_cause_identified": True,
    "decomposed_issues": [], # List of any sub-issues created
    "scope_clarity": "clear" or "decomposed",
    "next_phase": 1
}

try:
    complete_workflow_phase(validator, 0, phase_0_outputs)
    print("✅ Phase 0 (Investigation) completed successfully")
except ValueError as e:
    print(f"❌ Phase 0 validation failed: {e}")
    print("Fix validation errors before proceeding to Phase 1")
    # Handle failure: review requirements and retry
```

**Error Handling:**
- If validation fails, review Phase 0 outputs and ensure all investigation artifacts are created
- Check that investigation findings are properly documented
- Ensure state persistence is working correctly
- Use resume capability if process was interrupted

### Phase 1: Analysis & Planning

#### Step 1.0: Enforce Phase 1 Prerequisites
**EXECUTE NOW:**
```python
# Enforce Phase 1 prerequisites before starting planning
try:
    validator = enforce_workflow_phase(issue_number, 1, "task-planner")
    print("✅ Phase 1 prerequisites validated, proceeding with planning")
except ValueError as e:
    print(f"❌ Cannot start Phase 1: {e}")
    print("Complete required previous phases before proceeding")
    # Resume from last completed phase or handle missing prerequisites
    return
```

#### Step 1.1: Issue Analysis
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

#### Step 4: Execution Planning & Initial Documentation Commit
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
4. **CRITICAL: Commit documentation files before implementation**:
   ```bash
   git add context/trace/task-templates/issue-[ISSUE_NUMBER]-*.md
   git add context/trace/scratchpad/$(date +%Y-%m-%d)-issue-[ISSUE_NUMBER]-*.md
   git commit -m "docs(trace): add task template and execution plan for issue #[ISSUE_NUMBER]"
   ```
   - This ensures documentation is included in the eventual PR
   - Prevents the issue of documentation being created after PR push

#### Step 1.5: Context Management Setup
1. Monitor context window usage throughout execution
2. Use `/clear` if context approaches 25k tokens
3. Reference task template for prompt technique guidance
4. Track actual vs. estimated budget in real-time

#### Step 1.6: Complete Phase 1 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 1 with planning outputs
phase_1_outputs = {
    "task_template_created": True,
    "task_template_path": f"context/trace/task-templates/issue-{issue_number}-*.md",
    "scratchpad_created": True,
    "scratchpad_path": f"context/trace/scratchpad/*-issue-{issue_number}-*.md",
    "documentation_committed": True,
    "execution_plan_complete": True,
    "context_budget_estimated": True,
    "next_phase": 2
}

try:
    complete_workflow_phase(validator, 1, phase_1_outputs)
    print("✅ Phase 1 (Analysis & Planning) completed successfully")
except ValueError as e:
    print(f"❌ Phase 1 validation failed: {e}")
    print("Fix validation errors before proceeding to Phase 2")
    # Handle failure: ensure all documentation is created and committed
    # Check that task template and scratchpad files exist
    # Verify git commits were made
```

**Error Handling:**
- If validation fails, ensure task template and scratchpad files are created
- Verify documentation was committed to git
- Check that all required planning artifacts exist
- Use state persistence to resume from validation failure point

### Phase 2: Implementation

#### Step 2.0: Enforce Phase 2 Prerequisites
**EXECUTE NOW:**
```python
# Enforce Phase 2 prerequisites before starting implementation
try:
    validator = enforce_workflow_phase(issue_number, 2, "main-claude")
    print("✅ Phase 2 prerequisites validated, proceeding with implementation")
except ValueError as e:
    print(f"❌ Cannot start Phase 2: {e}")
    print("Complete Phase 1 (Planning) and ensure all task templates are created")
    # Resume from Phase 1 or handle missing prerequisites
    return
```

#### Step 2.1: Branch Creation & Development
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

#### Step 2.2: Complete Phase 2 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 2 with implementation outputs
phase_2_outputs = {
    "branch_created": True,
    "implementation_complete": True,
    "commits_made": True,
    "branch_name": f"fix/{issue_number}-*" or f"feature/{issue_number}-*",
    "code_changes_applied": True,
    "task_template_followed": True,
    "next_phase": 3
}

try:
    complete_workflow_phase(validator, 2, phase_2_outputs)
    print("✅ Phase 2 (Implementation) completed successfully")
except ValueError as e:
    print(f"❌ Phase 2 validation failed: {e}")
    print("Fix validation errors before proceeding to Phase 3")
    # Handle failure: ensure commits exist and pre-commit passes
    # Check that implementation matches task template requirements
```

**Error Handling:**
- If validation fails, ensure git commits were made on feature branch
- Verify pre-commit hooks pass
- Check that implementation follows task template guidance
- Use state persistence to track implementation progress

### Phase 3: Testing & Validation

#### Step 3.0: Enforce Phase 3 Prerequisites
**EXECUTE NOW:**
```python
# Enforce Phase 3 prerequisites before starting testing
try:
    validator = enforce_workflow_phase(issue_number, 3, "test-runner")
    print("✅ Phase 3 prerequisites validated, proceeding with testing")
except ValueError as e:
    print(f"❌ Cannot start Phase 3: {e}")
    print("Complete Phase 2 (Implementation) and ensure commits exist")
    # Resume from Phase 2 or handle missing prerequisites
    return
```

#### Step 3.1: Local Testing
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

#### Step 3.2: Quality Verification
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

#### Step 3.3: Complete Phase 3 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 3 with testing outputs
phase_3_outputs = {
    "tests_run": True,
    "ci_passed": True,
    "pre_commit_passed": True,
    "coverage_maintained": True,
    "coverage_percentage": "≥71.82%",
    "quality_checks_passed": True,
    "tests_created": True,
    "ci_artifacts_created": True,
    "next_phase": 4
}

try:
    complete_workflow_phase(validator, 3, phase_3_outputs)
    print("✅ Phase 3 (Testing & Validation) completed successfully")
except ValueError as e:
    print(f"❌ Phase 3 validation failed: {e}")
    print("Fix validation errors before proceeding to Phase 4")
    # Handle failure: ensure all tests pass and CI artifacts exist
    # Check that coverage targets are met
    # Verify CI execution markers exist
```

**Error Handling:**
- If validation fails, ensure all tests were executed successfully
- Verify CI was run locally and passed
- Check that test coverage meets requirements
- Ensure CI artifacts and execution markers are created

### Phase 4: Deployment & PR Management

#### Step 4.0: Enforce Phase 4 Prerequisites
**EXECUTE NOW:**
```python
# Enforce Phase 4 prerequisites before starting PR creation
try:
    validator = enforce_workflow_phase(issue_number, 4, "pr-manager")
    print("✅ Phase 4 prerequisites validated, proceeding with PR creation")
except ValueError as e:
    print(f"❌ Cannot start Phase 4: {e}")
    print("Complete Phase 3 (Testing) and ensure CI passes")
    # Resume from Phase 3 or handle missing prerequisites
    return
```

#### Step 4.1: Pre-PR Preparation
**EXECUTE NOW:**

**🚀 Quick Method (Recommended)**:
```bash
# Use the automated validation script
./scripts/validate-branch-for-pr.sh
```

**📋 Manual Method (for understanding the process)**:

1. **Branch Status Validation**:
   - Verify current branch is not main
   - Check for uncommitted changes
   - Prompt user for confirmation if issues found

2. **Sync with main branch and detect conflicts**:
   - Fetch latest changes from origin/main
   - Calculate commits behind main
   - Show recent commits on main if behind
   - Check for potential merge conflicts using `git merge-tree`
   - Perform interactive rebase with conflict detection
   - Handle rebase failures with clear instructions

3. **Validate branch state**:
   - Ensure branch exists on origin (required for PR)
   - Push branch if not already pushed
   - Push any new local commits to origin

4. **Final verification**:
   - Run CI checks to ensure everything works after rebase
   - Run pre-commit hooks and handle any changes
   - Force push with lease if pre-commit made changes

5. **Update task template with actual results and create completion logs**:
   - Open the task template file created earlier
   - Fill in the "Actuals" section with real token usage, time taken, etc.
   - Document any lessons learned or deviations from plan
   - **Create completion log entry**:
     ```bash
     # Create logs directory if it doesn't exist
     mkdir -p context/trace/logs

     # Add completion log entry
     echo "$(date): Issue #[ISSUE_NUMBER] workflow completed - creating PR" >> context/trace/logs/workflow-completions.log
     ```
   - **CRITICAL: Commit all documentation before creating PR**:
     ```bash
     git add context/trace/task-templates/issue-[ISSUE_NUMBER]-*.md
     git add context/trace/logs/workflow-completions.log
     git commit -m "docs(trace): update task template with actuals and add completion log for issue #[ISSUE_NUMBER]"
     ```

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

2. **Push the branch with all documentation**: `git push origin [BRANCH_NAME]`
   - This ensures all documentation files are included in the PR
   - No need for follow-up documentation pushes

#### Step 4.2: Complete Phase 4 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 4 with PR creation outputs
phase_4_outputs = {
    "pr_created": True,
    "branch_pushed": True,
    "documentation_included": True,
    "pr_template_used": True,
    "labels_applied": True,
    "assignee_set": True,
    "task_template_updated": True,
    "completion_log_created": True,
    "next_phase": 5
}

try:
    complete_workflow_phase(validator, 4, phase_4_outputs)
    print("✅ Phase 4 (Deployment & PR Management) completed successfully")
except ValueError as e:
    print(f"❌ Phase 4 validation failed: {e}")
    print("Fix validation errors before proceeding to Phase 5")
    # Handle failure: ensure PR was created successfully
    # Check that all documentation is included in PR
    # Verify branch was pushed to remote
```

**Error Handling:**
- If validation fails, ensure PR was created successfully
- Verify all documentation files are included in the PR
- Check that branch exists on remote and is accessible
- Ensure PR template was used and all fields completed

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

#### Step 5.0: Enforce Phase 5 Prerequisites
**EXECUTE NOW:**
```python
# Enforce Phase 5 prerequisites before starting monitoring
try:
    validator = enforce_workflow_phase(issue_number, 5, "pr-manager")
    print("✅ Phase 5 prerequisites validated, proceeding with monitoring")
except ValueError as e:
    print(f"❌ Cannot start Phase 5: {e}")
    print("Complete Phase 4 (PR Creation) and ensure PR exists")
    # Resume from Phase 4 or handle missing prerequisites
    return
```

#### Step 5.1: Documentation Verification & Cleanup
**EXECUTE NOW:**
1. **Verify all documentation is included in PR**:
   ```bash
   # Check that all documentation files are in the PR
   gh pr view [PR_NUMBER] --json files --jq '.files[].path' | grep -E "(task-templates|logs|scratchpad)"

   # Expected files:
   # - context/trace/task-templates/issue-[ISSUE_NUMBER]-*.md
   # - context/trace/scratchpad/*-issue-[ISSUE_NUMBER]-*.md
   # - context/trace/logs/workflow-completions.log
   ```

2. **If any documentation is missing** (this should not happen with updated workflow):
   ```bash
   # Add missing files and push to PR
   git add context/trace/
   git commit -m "docs(trace): add missing documentation for issue #[ISSUE_NUMBER]"
   git push origin [BRANCH_NAME]
   ```

3. **Update PR status in completion log** (optional):
   ```bash
   # Update log with PR number if desired
   echo "$(date): PR #[PR_NUMBER] created for issue #[ISSUE_NUMBER]" >> context/trace/logs/pr-status.log
   # Note: This is optional since main completion log was already created in Phase 4
   ```

4. **Clean up and organize**:
   - Archive any temporary files created during the workflow
   - Ensure workspace is clean for next task
   - Document any process improvements discovered

#### Step 5.2: Complete Phase 5 Enforcement
**EXECUTE NOW:**
```python
# Complete Phase 5 with final workflow outputs
phase_5_outputs = {
    "documentation_verified": True,
    "pr_monitoring_active": True,
    "workspace_cleaned": True,
    "process_improvements_documented": True,
    "workflow_completed": True,
    "pr_status_tracked": True,
    "issue_resolution_complete": True
}

try:
    complete_workflow_phase(validator, 5, phase_5_outputs)
    print("✅ Phase 5 (Documentation & Cleanup) completed successfully")
    print("🎉 Complete workflow enforcement cycle finished!")
except ValueError as e:
    print(f"❌ Phase 5 validation failed: {e}")
    print("Fix validation errors to complete workflow")
    # Handle failure: ensure all documentation is verified
    # Check that PR monitoring is properly set up
    # Verify cleanup was performed correctly
```

**Error Handling:**
- If validation fails, verify all documentation is included in PR
- Ensure PR monitoring is properly configured
- Check that workspace cleanup was completed
- Verify process improvements are documented

**WORKFLOW COMPLETION**:
- Issue #[ISSUE_NUMBER] has been resolved
- PR created and submitted for review
- **All documentation committed and included in PR**
- Task template, scratchpad, and completion logs are part of the PR
- Monitoring in place for PR completion
- **Workflow enforcement active throughout all phases**

**✅ DOCUMENTATION INTEGRITY CHECK:**
- Task template: ✅ Created in Phase 1, committed before implementation
- Execution scratchpad: ✅ Created in Phase 1, committed before implementation
- Actual results: ✅ Updated in Phase 4, committed before PR creation
- Completion logs: ✅ Created in Phase 4, committed before PR creation
- All files: ✅ Included in PR from the start, will be merged with code changes

---

## Error Handling

### Common Issues & Solutions

#### Workflow Enforcement Failures
- **Problem**: Phase validation fails due to missing prerequisites
- **Solution**:
  ```python
  # Check what's missing
  validator = WorkflowValidator(issue_number)
  can_proceed, errors = validator.validate_phase_prerequisites(phase)
  print("Missing prerequisites:", errors)

  # Fix each error and retry
  validator = enforce_workflow_phase(issue_number, phase, agent_type)
  ```
- **Prevention**: Follow each phase step completely before proceeding

#### State Persistence Issues
- **Problem**: Workflow state is corrupted or missing
- **Solution**:
  ```python
  # Reset state if corrupted
  import os
  os.remove(f".workflow-state-{issue_number}.json")

  # Restart from beginning or manually create state
  validator = WorkflowValidator(issue_number)
  ```
- **Prevention**: Don't manually edit state files

#### Resume from Interruption
- **Problem**: Workflow was interrupted mid-phase
- **Solution**:
  ```python
  # Check current state
  validator = WorkflowValidator(issue_number)
  current_phase = validator.state['current_phase']

  # Resume from current phase
  validator = enforce_workflow_phase(issue_number, current_phase, agent_type)
  ```
- **Prevention**: Use state persistence consistently

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
  # Use the validation script which handles conflicts automatically
  ./scripts/validate-branch-for-pr.sh

  # Or manual resolution:
  git fetch origin main
  git rebase origin/main
  # Resolve conflicts in editor
  git add <resolved_files>
  git rebase --continue
  git push --force-with-lease origin <branch_name>
  ```

#### Branch Out of Date
- **Problem**: Branch is behind main when creating PR
- **Solution**:
  ```bash
  # Run validation script before PR creation
  ./scripts/validate-branch-for-pr.sh
  ```
- **Prevention**: Always run branch validation before creating PRs

#### Documentation Not in PR
- **Problem**: Documentation files created after pushing PR, only exist locally
- **Root Cause**: Documentation created in Phase 5 instead of Phase 4
- **Solution**:
  ```bash
  # Add missing documentation to existing PR
  git add context/trace/task-templates/issue-[ISSUE_NUMBER]-*.md
  git add context/trace/scratchpad/$(date +%Y-%m-%d)-issue-[ISSUE_NUMBER]-*.md
  git add context/trace/logs/workflow-completions.log
  git commit -m "docs(trace): add missing documentation for issue #[ISSUE_NUMBER]"
  git push origin [BRANCH_NAME]

  # Verify it's now in the PR
  gh pr view [PR_NUMBER] --json files --jq '.files[].path' | grep -E "(task-templates|logs|scratchpad)"
  ```
- **Prevention**: Follow Documentation Strategy table - commit docs in Phase 1, update and create completion logs in Phase 4 BEFORE creating PR, verify in Phase 5

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
- [ ] **Workflow enforcement active through all phases**
- [ ] **State persistence maintained across agent executions**
- [ ] **Phase prerequisites validated before each phase**
- [ ] **Phase outputs validated after each phase**
- [ ] CI checks pass (Docker CI, tests, coverage)
- [ ] Code quality standards maintained
- [ ] PR created with comprehensive documentation
- [ ] PR successfully merged by reviewer
- [ ] Documentation updated appropriately
- [ ] Task template updated with actuals
- [ ] Sprint progress updated
- [ ] **Workflow state file properly managed**

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
# Standard workflow settings
max_wait_hours: 48
check_interval_minutes: 15
auto_template_generation: true
context_budget_limit: 25000
require_ci_pass: true
require_coverage_maintained: true

# Workflow enforcement settings
workflow_enforcement_enabled: true
state_persistence_enabled: true
phase_validation_strict: true
resume_capability_enabled: true
validation_error_handling: "strict"  # or "lenient"
state_file_location: ".workflow-state-{issue_number}.json"
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
claude workflow workflow-issue --issue 123
```

### For Complex Issues with Full Automation
```bash
claude workflow workflow-issue --issue 456 --auto-template --parallel-agents --max-wait 72h
```

### For Urgent Issues
```bash
claude workflow workflow-issue --issue 789 --priority high --check-interval 5m
```

### For Complex Issues with Hybrid Mode
```bash
# Use hybrid mode for enhanced analysis with specialist sub-agents
claude workflow workflow-issue --issue 456 --hybrid

# Combine with other flags for maximum effectiveness
claude workflow workflow-issue --issue 789 --hybrid --priority high --type feature
```

### Resume Interrupted Workflow
```bash
# Resume from last successful phase
claude workflow workflow-issue --issue 123 --resume

# Resume from specific phase (bypass enforcement for debugging)
claude workflow workflow-issue --issue 123 --resume-from-phase 3 --skip-validation
```

### Enforcement Debugging
```bash
# Check workflow state
python .claude/workflows/workflow-validator.py 123 1

# Validate specific phase manually
python -c "
from workflow_validator import WorkflowValidator
validator = WorkflowValidator(123)
can_proceed, errors = validator.validate_phase_prerequisites(2)
print('Can proceed:', can_proceed)
print('Errors:', errors)
"
```

Remember: This workflow is designed for **complete issue resolution** including PR acceptance with **full enforcement validation**. It will not complete until the PR is successfully merged or the timeout is reached. Each phase is now validated before and after execution to ensure compliance and enable resume capability.
