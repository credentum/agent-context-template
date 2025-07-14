Please analyze and fix the GitHub issue:
$ARGUMENTS.

Follow these steps:

# PLAN
1. Use 'gh issue view' to get the issue details
2. Understand the problem described in the issue
3. Ask clarifying questions if necessary
4. Understand the prior art for this issue
   - Search context/trace/scratchpad/ for previous thoughts
   - Search context/decisions/ for relevant ADRs
   - Search PRs to see if you can find history on this issue
   - Search the codebase focusing on src/ for relevant files
5. Think harder about how to break the issue down into a series of small, manageable tasks
6. Document your plan in a new scratchpad
   - Save to context/trace/scratchpad/YYYY-MM-DD-issue-{number}-{title}.md
   - Include the issue link and sprint reference
   - Update context/sprints/current.yaml if this affects sprint goals

# CREATE
- Create a new branch following the convention: fix/{issue-number}-{description} or feature/{issue-number}-{description}
- Solve the issue in small, manageable steps according to your plan
- Commit your changes after each step using conventional commits:
  - feat(scope): description
  - fix(scope): description
  - test(scope): description
- Update CLAUDE.md if the changes affect development workflow

# TEST
- Run exact CI checks locally FIRST: `./scripts/run-ci-docker.sh`
  - This matches GitHub Actions exactly and prevents CI failures
  - Alternative: `make lint` (uses local Python)
- Run pre-commit hooks: `pre-commit run --all-files`
- Write pytest tests for new functionality in tests/
- Ensure validators have >90% coverage if modified
- Run the full test suite: `pytest --cov=src --cov-report=term-missing`
- Update coverage metrics: `python scripts/update_coverage_metrics.py`
- If working on MCP tools, test with a mock MCP client
- Ensure all tests pass and coverage doesn't drop below 71.82%

# VERIFY
- CI Docker checks MUST pass: `./scripts/run-ci-docker.sh`
  - Includes: Black, isort, Flake8, MyPy, context validation, import checks
  - Debug failures with: `./scripts/run-ci-docker.sh debug`
- Check that all YAML files pass validation: `python -m src.agents.context_lint validate context/`
- Verify any new context files have proper schema_version
- If you modified embed_doc.py, check hash-diff functionality
- If you touched GraphRAG, verify Neo4j queries still work

# DEPLOY
- Ensure your branch is up to date with main
- Run final CI checks: `./scripts/run-ci-docker.sh`
- Run final pre-commit and test suite
- If pre-commit made changes: `git add -A && git commit --amend --no-edit`
- Open a PR with:
  - Clear description linking to the issue
  - Test results and coverage report
  - Confirmation that Docker CI passed locally
  - Any changes to context/ structure documented
  - Label with appropriate sprint tag
- Request a review
- Update context/trace/logs/ with completion notes

# IMPORTANT REMINDERS
- NEVER push directly to main
- ALWAYS run `./scripts/run-ci-docker.sh` before pushing to avoid CI failures
- ALWAYS run pre-commit before pushing
- If this creates new MCP tools, update context/mcp_contracts/
- If this affects agent behavior, update relevant agent in src/agents/
- Consider if this needs a new ADR in context/decisions/

Remember to use the GitHub CLI (`gh`) for all GitHub-related tasks.
