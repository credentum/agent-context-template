Please analyze and fix the GitHub issue:
$ARGUMENTS.

Follow these steps:

# ANALYZE & PREPARE

1. Use ‘gh issue view’ to get the issue details
1. Extract sprint and phase information from issue labels/description
1. Understand the problem described in the issue
1. Ask clarifying questions if necessary
1. Understand the prior art for this issue
- Search context/trace/scratchpad/ for previous thoughts
- Search context/decisions/ for relevant ADRs
- Search PRs to see if you can find history on this issue
- Search the codebase focusing on src/ for relevant files

# CREATE TASK TEMPLATE

1. Generate a Claude Code task template based on the issue analysis:
- Save to context/trace/task-templates/issue-{number}-{title}.md
- Follow the enhanced RCICO structure with:
  - Clear goal and context from issue
  - File-level breakdown with prompt techniques
  - Budget estimates based on complexity analysis
  - Verification criteria from acceptance criteria
- Include sprint metadata and relationships

**Task Template Structure:**

```markdown
# ────────────────────────────────────────────────────────────────────────
# TASK: issue-{number}-{title}
# Generated from GitHub Issue #{number}
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-{number}-{sanitized-title}`

## 🎯 Goal (≤ 2 lines)
> {Extract clear objective from issue description}

## 🧠 Context
- **GitHub Issue**: #{number} - {title}
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
GitHub Issue #{number}: {title}
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
github_issue: {number}
sprint: {extracted}
phase: {extracted}
component: {extracted}
priority: {extracted}
complexity: {assessed}
dependencies: {identified}
```

```
# PLAN & DOCUMENT
7. Think harder about how to break the issue down into manageable tasks
8. Document your execution plan in a new scratchpad
   - Save to context/trace/scratchpad/YYYY-MM-DD-issue-{number}-{title}.md
   - Include the issue link and sprint reference
   - Reference the created task template
   - Include token budget and complexity assessment
   - Update context/sprints/current.yaml if this affects sprint goals

# EXECUTE WITH CONTEXT MANAGEMENT
9. Monitor context window usage throughout execution
   - Use `/clear` if context approaches 25k tokens
   - Reference task template for prompt technique guidance
   - Track actual vs. estimated budget in real-time

# CREATE
10. Create a new branch following the convention: fix/{issue-number}-{description} or feature/{issue-number}-{description}
11. Solve the issue in small, manageable steps according to your task template plan
12. Apply the selected prompt technique from your task template consistently
13. Commit your changes after each step using conventional commits:
    - feat(scope): description
    - fix(scope): description
    - test(scope): description
14. Update CLAUDE.md if the changes affect development workflow

# TEST
15. Run exact CI checks locally FIRST: `./scripts/run-ci-docker.sh`
    - This matches GitHub Actions exactly and prevents CI failures
    - Alternative: `make lint` (uses local Python)
16. Run pre-commit hooks: `pre-commit run --all-files`
17. Write pytest tests for new functionality in tests/
18. Ensure validators have >90% coverage if modified
19. Run the full test suite: `pytest --cov=src --cov-report=term-missing`
20. Update coverage metrics: `python scripts/update_coverage_metrics.py`
21. If working on MCP tools, test with a mock MCP client
22. Ensure all tests pass and coverage doesn't drop below 71.82%

# VERIFY
23. CI Docker checks MUST pass: `./scripts/run-ci-docker.sh`
    - Includes: Black, isort, Flake8, MyPy, context validation, import checks
    - Debug failures with: `./scripts/run-ci-docker.sh debug`
24. Check that all YAML files pass validation: `python -m src.agents.context_lint validate context/`
25. Verify any new context files have proper schema_version
26. If you modified embed_doc.py, check hash-diff functionality
27. If you touched GraphRAG, verify Neo4j queries still work

# DEPLOY & TRACK
28. Ensure your branch is up to date with main
29. Run final CI checks: `./scripts/run-ci-docker.sh`
30. Run final pre-commit and test suite
31. If pre-commit made changes: `git add -A && git commit --amend --no-edit`
32. **Update task template with actuals**: Fill in actual budget usage in the task template
33. Open a PR with:
    - Clear description linking to the issue
    - Reference to task template used
    - Test results and coverage report
    - Confirmation that Docker CI passed locally
    - Budget actuals vs. estimates
    - Any changes to context/ structure documented
    - Label with appropriate sprint tag
34. Request a review
35. Update context/trace/logs/ with completion notes and lessons learned

# IMPORTANT REMINDERS
- NEVER push directly to main
- ALWAYS run `./scripts/run-ci-docker.sh` before pushing to avoid CI failures
- ALWAYS run pre-commit before pushing
- Use `/clear` proactively to maintain context window efficiency
- Track budget actuals for future estimation improvement
- Reference task template throughout execution for consistency
- If this creates new MCP tools, update context/mcp_contracts/
- If this affects agent behavior, update relevant agent in src/agents/
- Consider if this needs a new ADR in context/decisions/

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.
```
