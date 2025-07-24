# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1297-integrate-arc-reviewer
# Generated from GitHub Issue #1297
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1297-integrate-arc-reviewer-local-ci`

## 🎯 Goal (≤ 2 lines)
> Integrate ARC-Reviewer into claude-ci.sh to enable local execution of the same coverage and quality checks that run in GitHub CI, preventing push failures.

## 🧠 Context
- **GitHub Issue**: #1297 - [SPRINT-4.3] Integrate ARC-Reviewer into local CI workflow
- **Sprint**: sprint-4.3
- **Phase**: Phase 4.1: Enhancement
- **Component**: ci
- **Priority**: enhancement
- **Why this matters**: Developers currently push PRs that fail GitHub CI with coverage/quality issues
- **Dependencies**: ARC-Reviewer already exists at src/agents/arc_reviewer.py
- **Related**: PR #1296 (discovered issue during review), Issue #1292 (CI Migration Phase 3)

## 🛠️ Subtasks
Based on issue requirements and existing implementation:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/claude-ci.sh | modify | Chain-of-Thought | Add ARC-Reviewer integration | Medium |
| .git-hooks/pre-push | modify | Direct | Optional ARC in comprehensive mode | Low |
| scripts/quick-pre-push.sh | review | Direct | Ensure quick mode skips ARC | Low |
| scripts/claude-ci.sh | test | Few-shot | Validate JSON output format | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer integrating a code review tool into the CI pipeline.

**Context**
GitHub Issue #1297: Integrate ARC-Reviewer into local CI workflow
- ARC-Reviewer (src/agents/arc_reviewer.py) performs coverage validation and code quality checks
- claude-ci.sh is the unified CI command hub with JSON output
- Need to match GitHub CI behavior locally to prevent push failures
- Must respect --quick vs --comprehensive modes
Related files:
- scripts/claude-ci.sh: Main CI script with commands for check, test, pre-commit, review, all
- src/agents/arc_reviewer.py: Standalone Python module with review_pr() and format_yaml_output()
- .coverage-config.json: Coverage thresholds (baseline: 78.0%)

**Instructions**
1. **Primary Objective**: Add ARC-Reviewer execution to claude-ci.sh
2. **Scope**: Integrate ARC output into existing JSON format
3. **Constraints**:
   - Follow existing JSON output patterns in claude-ci.sh
   - Maintain backward compatibility - ARC is additive only
   - Quick mode should skip ARC-Reviewer (too slow)
   - Comprehensive mode must include full ARC review
   - Parse YAML output from ARC-Reviewer into structured JSON
4. **Prompt Technique**: Chain-of-Thought for complex integration logic
5. **Testing**: Ensure coverage drops are detected before push
6. **Documentation**: Update help text to mention ARC-Reviewer

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 4 files
• Context budget: ≤ 15k tokens
• Performance budget: ARC adds ~30s to comprehensive mode
• Code quality: shellcheck compliance, JSON validity
• CI compliance: Must match GitHub CI ARC-Reviewer behavior

**Output Format**
Return complete implementation with ARC-Reviewer integration.
Use conventional commits: feat(ci): integrate ARC-Reviewer into local workflow

## 🔍 Verification & Testing
- `./scripts/claude-ci.sh review` (should now include ARC checks)
- `./scripts/claude-ci.sh all --comprehensive` (must run ARC)
- `./scripts/claude-ci.sh all --quick` (should skip ARC)
- **Issue-specific tests**:
  - Simulate coverage drop below 78% and verify detection
  - Run against PR with known ARC issues
- **Integration tests**: Verify JSON output includes ARC results

## ✅ Acceptance Criteria
- [ ] claude-ci.sh runs ARC-Reviewer in review mode
- [ ] Pre-push hook optionally runs ARC-Reviewer for comprehensive validation
- [ ] Coverage regression detected locally before GitHub CI
- [ ] Code quality issues caught by ARC-Reviewer shown in structured output
- [ ] Quick mode skips ARC-Reviewer, comprehensive mode includes it

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15k (4 files to read/modify)
├── time_budget: 45 minutes
├── cost_estimate: $0.25
├── complexity: Medium (integration task)
└── files_affected: 3-4

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1297
sprint: sprint-4.3
phase: 4.1
component: ci
priority: enhancement
complexity: medium
dependencies: ["arc_reviewer.py", "claude-ci.sh"]
```
