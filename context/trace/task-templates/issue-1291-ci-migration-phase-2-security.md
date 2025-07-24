# ────────────────────────────────────────────────────────────────────────
# TASK: issue-1291-ci-migration-phase-2-security
# Generated from GitHub Issue #1291
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-1291-ci-migration-phase-2-security-reliability`

## 🎯 Goal (≤ 2 lines)
> Enhance CI migration with cryptographic signing of results, retry logic for reliability,
> and proper error handling to achieve >99% success rate while maintaining <5% performance impact.

## 🧠 Context
- **GitHub Issue**: #1291 - [SPRINT-4.2] CI Migration Phase 2: Security & Reliability
- **Sprint**: sprint-4.2
- **Phase**: Phase 3: Infrastructure Evolution
- **Component**: ci-workflows
- **Priority**: high
- **Why this matters**: Phase 1 established basic local CI execution; Phase 2 adds production-grade security and reliability
- **Dependencies**: PR #1290 (Phase 1 - merged)
- **Related**: Issue #1257 (Phase 1 planning)

## 🛠️ Subtasks
Based on Phase 1 analysis and Phase 2 requirements:

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| scripts/sign-ci-results.py | create | Chain-of-Thought | GPG signing of CI results | High |
| scripts/post-ci-results.py | modify | Few-Shot | Add signing & retry logic | Medium |
| scripts/verify-ci-results.py | modify | Direct | Add signature verification | Medium |
| scripts/generate-ci-keypair.py | create | Direct | Key generation utility | Low |
| .github/workflows/ci-local-verifier.yml | modify | Template-Based | Add signature validation | Medium |
| docs/ci-security-guide.md | create | Template-Based | Security documentation | Low |
| tests/test_ci_signing.py | create | Test-Driven | Unit tests for signing | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior security engineer implementing cryptographic signing and reliability enhancements for a CI system that posts results to GitHub.

**Context**
GitHub Issue #1291: CI Migration Phase 2 - Security & Reliability
Phase 1 (PR #1290) established basic local CI execution with:
- post-ci-results.py posting JSON results to GitHub Checks API
- verify-ci-results.py validating against thresholds
- ci-local-verifier.yml workflow for verification
Current limitations: no signing, no retry logic, basic error handling
Python environment with access to GPG, GitHub API, and retry libraries

**Instructions**
1. **Primary Objective**: Add cryptographic signing to CI results and implement retry logic
2. **Scope**:
   - GPG sign complete CI result JSON before posting
   - Add retry with exponential backoff (3 attempts: 2s, 4s, 8s)
   - Verify signatures in ci-local-verifier workflow
   - Maintain backward compatibility with unsigned results
3. **Constraints**:
   - Follow existing patterns from post-ci-results.py
   - Use python-gnupg for GPG operations
   - Use tenacity library for retry logic
   - Performance impact must be <5% on CI execution
   - Private keys only on trusted CI runners
4. **Prompt Technique**: Chain-of-Thought for security implementation to ensure proper key handling
5. **Testing**: Create comprehensive tests for signing/verification edge cases
6. **Documentation**: Include key management guide and security best practices

**Technical Constraints**
• Expected diff ≤ 600 LoC, ≤ 8 files
• Context budget: ≤ 30k tokens
• Performance budget: <5% overhead on CI execution
• Code quality: Black formatting, coverage ≥ 78.0%
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation with:
- GPG signing functionality in new sign-ci-results.py
- Enhanced post-ci-results.py with signing integration and retry logic
- Updated verify-ci-results.py with signature validation
- Modified ci-local-verifier.yml workflow
- Key generation utility and security documentation
Use conventional commits: feat(ci): add cryptographic signing and retry logic

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `pytest --cov=src --cov-report=term-missing` (test suite + coverage)
- `pre-commit run --all-files` (code quality)
- **Issue-specific tests**:
  - Test GPG signing/verification with valid and invalid signatures
  - Test retry logic with simulated failures
  - Verify backward compatibility with unsigned results
  - Performance benchmarks to ensure <5% overhead
- **Integration tests**:
  - End-to-end test of posting signed results
  - Verification workflow with signed/unsigned results

## ✅ Acceptance Criteria
- [X] CI results are cryptographically signed with GPG
- [X] Verification workflow validates signatures before accepting results
- [X] Post-ci-results.py includes retry logic with exponential backoff
- [X] Error handling provides clear feedback for debugging
- [X] Success rate monitoring shows >99% reliability
- [X] Key management process is documented and secure
- [X] Performance impact is <5% on overall CI execution time

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 30000
├── time_budget: 4-6 hours
├── cost_estimate: $1.50
├── complexity: High (security + reliability)
└── files_affected: 6-8

Actuals (to be filled):
├── tokens_used: ~45000
├── time_taken: 45 minutes
├── cost_actual: $2.25
├── iterations_needed: 3
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 1291
sprint: sprint-4.2
phase: "Phase 3: Infrastructure Evolution"
component: ci-workflows
priority: high
complexity: high
dependencies: ["PR #1290"]
```
