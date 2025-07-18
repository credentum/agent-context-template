# ────────────────────────────────────────────────────────────────────────
# TASK: issue-760-fix-arc-reviewer-blocking-issues
# Generated from GitHub Issue #760
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-760-arc-reviewer-blocking-issues`

## 🎯 Goal (≤ 2 lines)
> Fix ARC-Reviewer blocking issues from PR #681 that prevent proper PR processing and auto-merge functionality by addressing validation, security, and documentation issues.

## 🧠 Context
- **GitHub Issue**: #760 - Fix ARC-Reviewer Blocking Issues from PR #681
- **Sprint**: Sprint 41
- **Phase**: Phase 10 (Cleanup & Fixes)
- **Component**: CI
- **Priority**: High
- **Why this matters**: These blocking issues prevent proper PR validation workflow and auto-merge functionality, affecting development velocity
- **Dependencies**: Understanding of PR validation workflows, GitHub Actions, PR template processing, security best practices
- **Related**: PR #681 (merged), Issue #173 (AI-monitored PR process), Issue #753 (workflow feedback loop fix)

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| .github/workflows/pr-issue-validation.yml | modify | Direct/Analytical | Fix PR validation to detect issue references and exemption checkboxes | Medium |
| .github/workflows/ai-pr-monitor.yml | modify | Direct/Analytical | Resolve branch conflict detection and auto-resolution | High |
| .github/PULL_REQUEST_TEMPLATE.md | create/modify | Direct/Analytical | Implement proper PR template metadata validation | Low |
| .claude/workflows/workflow-issue.md | modify | Direct/Analytical | Add security guidelines for workflow bash commands | Low |
| Various YAML files | modify | Direct/Analytical | Ensure YAML examples include proper schema_version fields | Low |
| Large documentation files | modify | Direct/Analytical | Add table of contents to large documentation files | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on CI/CD automation and PR validation workflows.

**Context**
GitHub Issue #760: Fix ARC-Reviewer Blocking Issues from PR #681
ARC-Reviewer has identified blocking issues in PR #681 that prevent proper PR processing and auto-merge functionality. These issues include:
1. PR validation not properly detecting issue references and exemption checkboxes
2. Branch conflict detection and auto-resolution mechanisms failing
3. PR template metadata validation incomplete
4. Security concerns with bash command examples in workflow documentation
5. YAML examples lacking proper schema_version fields
6. Large documentation files needing table of contents

Current codebase follows GitHub Actions workflows with automated PR processing and AI-monitored PR processes.
Related files: .github/workflows/pr-issue-validation.yml, .github/workflows/ai-pr-monitor.yml, PR templates, workflow documentation

**Instructions**
1. **Primary Objective**: Fix all ARC-Reviewer blocking issues to restore proper PR validation and auto-merge functionality
2. **Scope**: Address validation, security, and documentation issues while maintaining existing automation capabilities
3. **Constraints**:
   - Follow existing GitHub Actions patterns and YAML structure
   - Maintain backward compatibility with existing PR workflows
   - Keep PR template user-friendly while adding required metadata validation
4. **Prompt Technique**: Direct/Analytical approach because this involves specific technical fixes to existing systems
5. **Testing**: Validate fixes with sample PR and ensure all ARC-Reviewer concerns are addressed
6. **Documentation**: Update security guidelines and add table of contents where needed

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 8 files
• Context budget: ≤ 15k tokens
• Performance budget: No performance impact expected
• Code quality: Follow YAML best practices, maintain workflow standards
• CI compliance: All workflow changes must pass validation

**Output Format**
Return complete implementation addressing all ARC-Reviewer blocking issues.
Use conventional commits: fix(ci): resolve ARC-Reviewer blocking issues

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**: Create test PR to validate all fixes work correctly
- **Workflow validation**: Ensure all GitHub Actions workflows pass validation

## ✅ Acceptance Criteria
- [ ] Fix PR validation to properly detect issue references and exemption checkboxes
- [ ] Resolve branch conflict detection and auto-resolution mechanisms
- [ ] Implement proper PR template metadata validation
- [ ] Add security guidelines for workflow bash commands
- [ ] Ensure YAML examples include proper schema_version fields
- [ ] Add table of contents to large documentation files
- [ ] Test the fixes with a sample PR

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 15000 (based on workflow file analysis and documentation review)
├── time_budget: 2-3 hours (multiple file modifications with testing)
├── cost_estimate: $7-10 (token usage for analysis and implementation)
├── complexity: Medium (involves multiple workflow files and validation logic)
└── files_affected: 6-8 (workflows, templates, documentation)

Actuals (to be filled):
├── tokens_used: ___
├── time_taken: ___
├── cost_actual: $___
├── iterations_needed: ___
└── context_clears: ___
```

## 🏷️ Metadata
```yaml
github_issue: 760
sprint: Sprint 41
phase: Phase 10 (Cleanup & Fixes)
component: CI
priority: High
complexity: Medium
dependencies: ["PR validation workflows", "GitHub Actions", "PR template processing", "Security best practices"]
```
