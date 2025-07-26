# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1641-fix-arc-reviewer-discrepancies
# Generated from GitHub Issue #1641
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1641-local-arc-reviewer-validation`

## 🎯 Goal (≤ 2 lines)
> Create a local ARC reviewer implementation that catches all issues (security vulnerabilities, MCP contracts, Python 3.12 compatibility) that the GitHub CI ARC reviewer finds, eliminating validation discrepancies.

## 🧠 Context
- **GitHub Issue**: #1641 - Fix local CI pipeline ARC reviewer validation discrepancies
- **Sprint**: SPRINT-5.1
- **Phase**: Implementation
- **Component**: CI/CD, Developer Tools
- **Priority**: High (blocking PR #1639)
- **Why this matters**: Developers can't catch critical issues locally, causing CI failures and wasted time
- **Dependencies**: None - greenfield implementation
- **Related**: PR #1639 (blocked by this issue)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/arc-reviewer.py | create | Chain-of-Thought | Main validation orchestrator | High |
| scripts/validators/security.py | create | Tool Integration | Security vulnerability scanning | High |
| scripts/validators/mcp_validator.py | create | Schema Validation | MCP contract validation | Medium |
| scripts/validators/python_compat.py | create | AST Analysis | Python 3.12 compatibility | Medium |
| .pre-commit-config.yaml | modify | Configuration | Integrate ARC reviewer | High |
| .claude/guides/arc-reviewer.md | create | Documentation | User guide | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer implementing a local validation system that mirrors GitHub CI checks.

**Context**
GitHub Issue #1641: The local development environment lacks an ARC reviewer, causing developers to discover validation failures only after pushing to GitHub. The GitHub ARC reviewer catches:
- Security vulnerabilities (command injection, path traversal, DoS)
- Missing MCP contracts
- Python 3.12 compatibility issues
- Pre-commit configuration mismatches

Current state:
- Pre-commit hooks only cover basic linting (black, isort, flake8, mypy)
- No local security scanning
- No MCP contract validation
- Complete disconnect between local and CI validation

**Instructions**
1. **Primary Objective**: Create a local ARC reviewer that catches ALL issues the GitHub version would find
2. **Scope**:
   - Implement modular validation system
   - Integrate security scanning (bandit)
   - Add MCP contract validation
   - Ensure Python 3.12 compatibility checks
   - Synchronize local and CI configurations
3. **Constraints**:
   - Performance: Full validation must complete in <30 seconds
   - Zero false positives compared to CI
   - Must integrate with existing pre-commit framework
   - Configuration must stay synchronized with CI
4. **Prompt Technique**: Tool Integration + Chain-of-Thought for orchestrating multiple validation tools
5. **Testing**: Create comprehensive test suite covering all validators
6. **Documentation**: Provide clear usage guide and troubleshooting

**Technical Constraints**
• Expected diff ≤ 800 LoC, ≤ 10 files
• Context budget: ≤ 15k tokens
• Performance budget: <30s for full validation
• Code quality: Black formatting, type hints, 100% validator test coverage
• CI compliance: Must produce identical results to GitHub CI

**Output Format**
Create modular validation system with clear separation of concerns.
Use conventional commits: feat(ci): add local ARC reviewer implementation

## 🔍 Verification & Testing
- `python scripts/arc-reviewer.py` (run local validation)
- `pytest tests/arc_reviewer/ -v` (test validator modules)
- `pre-commit run --all-files` (verify integration)
- **Issue-specific tests**:
  - Inject known security vulnerabilities and verify detection
  - Create invalid MCP contracts and verify rejection
  - Add Python 3.12 incompatible code and verify warnings
- **Integration tests**: Compare local vs GitHub CI results

## ✅ Acceptance Criteria
- [ ] Local ARC reviewer detects ALL security vulnerabilities found by GitHub
- [ ] MCP contract validation works identically to CI
- [ ] Python 3.12 compatibility issues are caught locally
- [ ] Pre-commit integration works seamlessly
- [ ] Configuration synchronization prevents drift
- [ ] Documentation is clear and comprehensive
- [ ] Performance is acceptable (<30s for typical validation)

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000
├── time_budget: 16-20 hours
├── cost_estimate: $12-15
├── complexity: High (new system design)
└── files_affected: 10-12

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 1641
sprint: SPRINT-5.1
phase: Implementation
component: CI/CD
priority: high
complexity: high
dependencies: []
```
