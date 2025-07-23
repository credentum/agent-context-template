# Scratchpad: Issue #1257 - Migrate CI Pipeline to Local Execution

**Date**: 2025-07-23
**Issue**: [#1257](https://github.com/agent-context-template/issues/1257)
**Sprint**: sprint-4.2
**Task Template**: `context/trace/task-templates/issue-1257-migrate-ci-pipeline-local-execution.md`

## Token Budget & Complexity Assessment
- **Estimated Tokens**: 20,000 (high architectural complexity)
- **Complexity**: High - New architecture pattern requiring investigation
- **Risk**: Medium-High - Changes core CI infrastructure

## Investigation Findings
From the issue description, several areas need investigation:
1. Security model for trusting locally-generated CI results
2. Best approach for posting results back to GitHub PRs
3. Verification mechanism design (how GitHub validates results)
4. Migration strategy from current GitHub Actions to local execution

## Phase 1 Implementation Plan (Proof of Concept)

### Step 1: Create Basic Result Schema
- Define JSON schema for CI results
- Include: timestamp, commit SHA, checks performed, results, coverage data
- Keep simple for PoC, extensible for future phases

### Step 2: Create Local Result Poster Script
- `scripts/post-ci-results.py`:
  - Parse claude-ci.sh output
  - Format as standardized JSON
  - Post to GitHub using Checks API or Status API
  - Basic authentication using GITHUB_TOKEN

### Step 3: Create GitHub Verification Workflow
- `.github/workflows/ci-local-verifier.yml`:
  - Triggered by repository_dispatch or check_suite events
  - Fetch posted results
  - Verify coverage threshold (≥ 85%)
  - Update PR status

### Step 4: Enhance claude-ci.sh
- Add `--post-results` flag
- Capture output in machine-readable format
- Call post-ci-results.py if flag is set
- Maintain backward compatibility

### Step 5: Create Basic Verification Script
- `scripts/verify-ci-results.py`:
  - Parse posted results
  - Check thresholds (coverage, test pass rate)
  - Return pass/fail status

### Step 6: Documentation
- Create migration guide explaining:
  - How to run CI locally
  - How results are posted
  - How verification works
  - Security considerations for future phases

## Technical Decisions for PoC

### Result Storage
- **Phase 1**: Store as PR comment artifacts or Check Run annotations
- **Future**: Consider S3, GitHub Artifacts, or dedicated storage

### Authentication
- **Phase 1**: Use GITHUB_TOKEN from environment
- **Future**: Implement signing/attestation

### Result Format
```json
{
  "version": "1.0",
  "timestamp": "ISO-8601",
  "commit_sha": "abc123",
  "branch": "feature/xyz",
  "runner": "local",
  "checks": {
    "coverage": {
      "passed": true,
      "percentage": 87.5,
      "threshold": 85.0
    },
    "tests": {
      "passed": true,
      "total": 150,
      "failed": 0,
      "skipped": 5
    },
    "linting": {
      "passed": true,
      "issues": []
    }
  }
}
```

### API Choice
- Use GitHub Checks API for detailed results
- Fall back to Status API for simpler cases
- Both support external posting

## Implementation Order
1. Create post-ci-results.py with basic functionality
2. Create ci-local-verifier.yml workflow
3. Update claude-ci.sh to support result posting
4. Create verify-ci-results.py
5. Test end-to-end flow
6. Document the process

## Success Metrics
- Local CI runs in < 2 minutes (vs 5-10 on GitHub)
- Results posted successfully to PR
- Verification workflow correctly validates results
- Existing CI continues to work during transition

## Risk Mitigation
- Keep changes backward compatible
- Test thoroughly in separate PR first
- Provide clear rollback instructions
- Monitor for security issues

## Next Steps
1. Implement Phase 1 PoC following the plan above
2. Test with a sample PR
3. Gather feedback from team
4. Plan Phase 2 (security hardening) based on learnings
