# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1257-migrate-ci-pipeline-local-execution
# Generated from GitHub Issue #1257
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1257-migrate-ci-pipeline-local-execution`

## 🎯 Goal (≤ 2 lines)
> Transform GitHub Actions from CI executor to CI verifier by implementing local CI execution
> with secure result posting and GitHub verification workflows.

## 🧠 Context
- **GitHub Issue**: #1257 - [SPRINT-4.2] Migrate CI Pipeline to Local Execution with GitHub Verification
- **Sprint**: sprint-4.2
- **Phase**: Phase 3: Infrastructure Evolution (phase:4.1)
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: Improve developer experience with faster CI feedback, reduce GitHub Actions costs, enable better debugging
- **Dependencies**:
  - Related to #1063 (Local CI alignment)
  - Builds on #1061 (claude-ci command hub)
  - Affects #1256 (Pre-commit issues would be fixed locally)
- **Related**: #1243 (Workflow consolidation affects architecture)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `.github/workflows/ci-local-verifier.yml` | create | Tree-of-Thought | New workflow to verify posted results | High |
| `scripts/post-ci-results.py` | create | Chain-of-Thought | Script to post CI results to GitHub | High |
| `scripts/verify-ci-results.py` | create | Chain-of-Thought | Script to verify result authenticity | High |
| `.github/workflows/ci-unified.yml` | modify | Careful Edit | Convert from executor to verifier | High |
| `scripts/claude-ci.sh` | modify | Few-Shot | Add result posting capability | Medium |
| `docs/ci-migration-guide.md` | create | Template | Document new CI workflow | Medium |
| `.github/workflows/*.yml` | modify | Batch Edit | Update all CI workflows | High |
| `scripts/sign-ci-results.py` | create | Chain-of-Thought | Implement result signing | High |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer specializing in CI/CD pipeline architecture and GitHub Actions workflows, with expertise in security and distributed systems.

**Context**
GitHub Issue #1257: [SPRINT-4.2] Migrate CI Pipeline to Local Execution with GitHub Verification

The current CI system runs entirely on GitHub Actions, causing:
- Slow feedback loops (waiting for runners)
- High costs (GitHub Actions minutes)
- Difficult debugging (can't reproduce locally)
- Limited control over CI environment

We need to transform this into a local-first CI system where:
1. CI runs locally on developer machines or dedicated infrastructure
2. Results are securely posted to GitHub
3. GitHub workflows only verify results meet quality thresholds
4. Security prevents tampering with CI results

Current codebase has:
- `scripts/claude-ci.sh` - Unified CI command interface
- `.github/workflows/ci-unified.yml` - Main CI workflow
- `scripts/post-review-comment.py` - Existing PR comment formatter
- Related files from issues #1061 and #1063

**Instructions**
1. **Primary Objective**: Implement a proof-of-concept for local CI execution with GitHub verification
2. **Scope**:
   - Phase 1 only: Basic local runner, result posting, simple verification
   - Do not implement full security/signing in this phase
   - Focus on coverage check as the pilot use case
3. **Constraints**:
   - Maintain backward compatibility during transition
   - Use existing `claude-ci.sh` infrastructure
   - Follow secure coding practices for API interactions
   - Design for future security enhancements
4. **Prompt Technique**: Tree-of-Thought for architectural decisions, Chain-of-Thought for implementation details
5. **Testing**: Create test workflows that verify both success and failure cases
6. **Documentation**: Clear migration guide for developers

**Technical Constraints**
• Expected diff ≤ 500 LoC for Phase 1 PoC
• Context budget: ≤ 20k tokens
• Performance: Local CI should be faster than GitHub Actions
• Code quality: Python scripts with type hints, bash scripts with error handling
• CI compliance: All new scripts must pass existing CI checks

**Output Format**
1. Create `ci-local-verifier.yml` workflow
2. Create `post-ci-results.py` with GitHub API integration
3. Update `claude-ci.sh` to support `--post-results` flag
4. Create basic `verify-ci-results.py` for threshold checking
5. Document the PoC in a migration guide

Use conventional commits:
- feat(ci): add local CI result verification workflow
- feat(scripts): add CI result posting capability
- docs(ci): add local CI migration guide

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Ensure new scripts pass CI)
- `pytest tests/test_post_ci_results.py` (Unit tests for new scripts)
- Manual test: Run `claude-ci all --post-results` locally
- Manual test: Verify GitHub workflow reads posted results
- Manual test: Test failure cases (bad results, auth failures)
- **Issue-specific tests**:
  - Verify posted results appear in PR
  - Test threshold validation (coverage < 85% should fail)
  - Test result format compatibility
- **Integration tests**: End-to-end test of local execution → posting → verification

## ✅ Acceptance Criteria
- [ ] Local CI execution produces standardized, verifiable results
- [ ] Results can be posted to GitHub PRs as check statuses
- [ ] GitHub workflows verify posted results meet quality thresholds
- [ ] Security mechanism prevents tampering with CI results (basic auth for PoC)
- [ ] Developer experience is improved (faster feedback, easier debugging)
- [ ] Migration path allows gradual transition without disruption
- [ ] Documentation clearly explains new CI workflow
- [ ] Existing PR checks continue working during transition

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 20000 (architectural complexity)
├── time_budget: 16 hours (2 days for PoC)
├── cost_estimate: $2.00 (assuming Claude 3 pricing)
├── complexity: high (new architecture pattern)
└── files_affected: 8-10

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1257
sprint: sprint-4.2
phase: phase-4.1
component: ci-workflows
priority: high
complexity: high
dependencies: [1063, 1061]
investigation_required: true
investigation_areas:
  - Security model for result verification
  - GitHub API authentication approach
  - Result storage mechanism
  - Migration strategy details
```
