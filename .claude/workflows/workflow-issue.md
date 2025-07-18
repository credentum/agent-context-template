# Fix GitHub Issue Workflow

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
claude workflow fix-issue --issue 123

# With automation features
claude workflow fix-issue --issue 123 --auto-template --parallel-agents

# With custom parameters
claude workflow fix-issue --issue 123 --priority high --component api --max-wait 24h
```

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
1. Use `gh issue view $ISSUE_NUMBER` to get issue details
2. Extract sprint and phase information from issue labels/description
3. Understand the problem described in the issue
4. Ask clarifying questions if necessary

#### Step 2: Context Gathering
1. Search `context/trace/scratchpad/` for previous thoughts
2. Search `context/decisions/` for relevant ADRs
3. Search PRs to find history on this issue: `gh pr list --search "issue:$ISSUE_NUMBER"`
4. Search the codebase focusing on `src/` for relevant files

#### Step 3: Task Template Generation
1. **Generate Claude Code task template** based on issue analysis:
   - Save to `context/trace/task-templates/issue-$ISSUE_NUMBER-{sanitized-title}.md`
   - Follow enhanced RCICO structure with:
     - Clear goal and context from issue
     - File-level breakdown with prompt techniques
     - Budget estimates based on complexity analysis
     - Verification criteria from acceptance criteria
   - Include sprint metadata and relationships

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
1. Break down issue into manageable tasks based on task template
2. Document execution plan in scratchpad:
   - Save to `context/trace/scratchpad/$(date +%Y-%m-%d)-issue-$ISSUE_NUMBER-{title}.md`
   - Include issue link and sprint reference
   - Reference the created task template
   - Include token budget and complexity assessment
3. Update `context/sprints/current.yaml` if this affects sprint goals

#### Step 5: Context Management Setup
1. Monitor context window usage throughout execution
2. Use `/clear` if context approaches 25k tokens
3. Reference task template for prompt technique guidance
4. Track actual vs. estimated budget in real-time

### Phase 2: Implementation

#### Step 6: Branch Creation & Development
1. Create branch: `git checkout -b fix/$ISSUE_NUMBER-{description}` or `feature/$ISSUE_NUMBER-{description}`
2. Apply selected prompt technique from task template consistently
3. Solve issue in small, manageable steps according to task template plan
4. Commit changes after each step using conventional commits:
   - `feat(scope): description`
   - `fix(scope): description`
   - `test(scope): description`
5. Update `CLAUDE.md` if changes affect development workflow

### Phase 3: Testing & Validation

#### Step 7: Local Testing
1. **Run CI checks locally FIRST**: `./scripts/run-ci-docker.sh`
   - This matches GitHub Actions exactly and prevents CI failures
   - Alternative: `make lint` (uses local Python)
2. Run pre-commit hooks: `pre-commit run --all-files`
3. Write pytest tests for new functionality in `tests/`
4. Ensure validators have >90% coverage if modified
5. Run full test suite: `pytest --cov=src --cov-report=term-missing`
6. Update coverage metrics: `python scripts/update_coverage_metrics.py`
7. If working on MCP tools, test with a mock MCP client
8. Ensure all tests pass and coverage doesn't drop below 71.82%

#### Step 8: Quality Verification
1. **CI Docker checks MUST pass**: `./scripts/run-ci-docker.sh`
   - Includes: Black, isort, Flake8, MyPy, context validation, import checks
   - Debug failures with: `./scripts/run-ci-docker.sh debug`
2. Check YAML files pass validation: `python -m src.agents.context_lint validate context/`
3. Verify any new context files have proper schema_version
4. If you modified embed_doc.py, check hash-diff functionality
5. If you touched GraphRAG, verify Neo4j queries still work

### Phase 4: Deployment & PR Management

#### Step 9: Pre-PR Preparation
1. Ensure branch is up to date with main: `git pull origin main`
2. Run final CI checks: `./scripts/run-ci-docker.sh`
3. Run final pre-commit and test suite
4. If pre-commit made changes: `git add -A && git commit --amend --no-edit`
5. **Update task template with actuals**: Fill in actual budget usage in task template

#### Step 10: PR Creation
1. **Create PR with comprehensive information**:
   ```bash
   gh pr create --title "fix($COMPONENT): $ISSUE_TITLE" \
     --body "Fixes #$ISSUE_NUMBER

   ## Changes
   - [List key changes made]
   
   ## Testing
   - [X] All CI checks pass locally
   - [X] Coverage maintained at 71.82%+
   - [X] Pre-commit hooks pass
   
   ## Task Template
   - Template used: context/trace/task-templates/issue-$ISSUE_NUMBER-{title}.md
   - Estimated budget: {tokens/time}
   - Actual usage: {tokens/time}
   
   ## Verification
   - [X] Docker CI passed locally
   - [X] All tests pass
   - [X] Context validation successful
   
   ## Context Changes
   - [Document any changes to context/ structure]
   
   ## Sprint Impact
   - Sprint: {sprint reference}
   - Phase: {phase reference}
   - Component: {component}
   " \
     --label "sprint-current,fix,component-$COMPONENT" \
     --assignee @me
   ```

2. **Add appropriate labels**:
   - Sprint labels from issue
   - Component labels
   - Priority labels
   - `ready-for-review` when complete

#### Step 11: PR Monitoring & Completion
1. **Get PR number and enter monitoring mode**:
   ```bash
   PR_NUMBER=$(gh pr view --json number --jq '.number')
   echo "Created PR #$PR_NUMBER - entering monitoring mode"
   ```

2. **Monitor PR status until completion**:
   ```bash
   MAX_WAIT_HOURS=${MAX_WAIT:-48}
   CHECK_INTERVAL_MINUTES=${CHECK_INTERVAL:-15}
   START_TIME=$(date +%s)
   
   while true; do
     # Check current PR status
     PR_STATUS=$(gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup --jq '{state: .state, mergeable: .mergeable, checks: .statusCheckRollup}')
     
     echo "$(date): Checking PR #$PR_NUMBER status..."
     echo "Status: $PR_STATUS"
     
     # Parse the status
     STATE=$(echo "$PR_STATUS" | jq -r '.state')
     MERGEABLE=$(echo "$PR_STATUS" | jq -r '.mergeable')
     CHECKS=$(echo "$PR_STATUS" | jq -r '.checks')
     
     # Check if PR is merged or closed
     if [[ "$STATE" == "MERGED" ]]; then
       echo "✅ SUCCESS: PR #$PR_NUMBER has been merged!"
       break
     elif [[ "$STATE" == "CLOSED" ]]; then
       echo "❌ FAILURE: PR #$PR_NUMBER was closed without merging"
       exit 1
     fi
     
     # Check if all conditions are met for merge
     if [[ "$MERGEABLE" == "MERGEABLE" ]]; then
       # Check if all status checks pass
       FAILING_CHECKS=$(echo "$CHECKS" | jq -r '.[] | select(.conclusion != "SUCCESS" and .conclusion != "SKIPPED" and .conclusion != null) | .name')
       
       if [[ -z "$FAILING_CHECKS" ]]; then
         echo "✅ All checks passing and PR is mergeable"
         
         # Check if there are any requested changes or pending reviews
         REVIEWS=$(gh pr view $PR_NUMBER --json reviews --jq '.reviews[] | select(.state == "CHANGES_REQUESTED" or .state == "PENDING")')
         
         if [[ -z "$REVIEWS" ]]; then
           echo "✅ No blocking reviews - PR is ready for merge"
           echo "⏳ Waiting for maintainer to merge..."
         else
           echo "⏳ Waiting for review completion..."
           echo "$REVIEWS" | jq -r '"Review from " + .author.login + ": " + .state'
         fi
       else
         echo "❌ Some checks are still failing:"
         echo "$FAILING_CHECKS"
       fi
     else
       echo "⏳ PR not yet mergeable: $MERGEABLE"
     fi
     
     # Check timeout
     CURRENT_TIME=$(date +%s)
     ELAPSED_HOURS=$(( (CURRENT_TIME - START_TIME) / 3600 ))
     
     if [[ $ELAPSED_HOURS -ge $MAX_WAIT_HOURS ]]; then
       echo "⏰ TIMEOUT: Waited $MAX_WAIT_HOURS hours for PR completion"
       echo "PR #$PR_NUMBER status: $STATE"
       echo "Final status: $PR_STATUS"
       exit 1
     fi
     
     # Wait before next check
     echo "⏳ Waiting $CHECK_INTERVAL_MINUTES minutes before next check..."
     echo "   Elapsed: ${ELAPSED_HOURS}h / ${MAX_WAIT_HOURS}h max"
     sleep ${CHECK_INTERVAL_MINUTES}m
   done
   ```

3. **Post-completion actions**:
   ```bash
   # Update completion logs
   echo "$(date): PR #$PR_NUMBER completed successfully" >> context/trace/logs/pr-completions.log
   
   # Update task template with final actuals
   echo "## Final Results" >> context/trace/task-templates/issue-$ISSUE_NUMBER-{title}.md
   echo "- PR #$PR_NUMBER merged successfully" >> context/trace/task-templates/issue-$ISSUE_NUMBER-{title}.md
   echo "- Total time: ${ELAPSED_HOURS} hours" >> context/trace/task-templates/issue-$ISSUE_NUMBER-{title}.md
   echo "- Workflow completed: $(date)" >> context/trace/task-templates/issue-$ISSUE_NUMBER-{title}.md
   
   # Update sprint progress if applicable
   if [[ -f context/sprints/current.yaml ]]; then
     echo "Updating sprint progress for issue #$ISSUE_NUMBER"
     # Add logic to update sprint completion status
   fi
   
   echo "🎉 Workflow completed successfully!"
   echo "Issue #$ISSUE_NUMBER resolved via PR #$PR_NUMBER"
   ```

### Phase 5: Documentation & Cleanup

#### Step 12: Final Documentation
1. Update `context/trace/logs/` with completion notes and lessons learned
2. Document any new patterns or techniques discovered
3. Update relevant documentation if workflow changes were made
4. Archive task template and scratchpad notes

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
