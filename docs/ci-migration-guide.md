# CI Migration Guide: Local Execution with GitHub Verification

## Overview

This guide explains the new CI architecture where CI runs locally and posts results to GitHub for verification, rather than running entirely on GitHub Actions.

## Phase 1: Proof of Concept

The initial implementation provides basic functionality for running CI locally and posting results to GitHub.

### Architecture

```
Developer Machine          GitHub                    PR Status
┌─────────────────┐       ┌──────────────────┐     ┌─────────────┐
│ claude-ci.sh    │──────>│ post-ci-results  │────>│ Check Run   │
│ (local execution)│       │ (via API)        │     │ or Comment  │
└─────────────────┘       └──────────────────┘     └─────────────┘
                                   │
                                   v
                          ┌──────────────────┐     ┌─────────────┐
                          │ ci-local-verifier│────>│ PR Status   │
                          │ (workflow)       │     │ ✓ Verified  │
                          └──────────────────┘     └─────────────┘
```

### Quick Start

1. **Run CI locally with result saving:**
   ```bash
   ./scripts/claude-ci.sh all --output ci-results.json
   ```

2. **Post results to GitHub (automatic PR detection):**
   ```bash
   ./scripts/claude-ci.sh all --output ci-results.json --post-results
   ```

3. **Post results to specific PR:**
   ```bash
   ./scripts/post-ci-results.py ci-results.json --pr 123
   ```

### How It Works

#### Local Execution
- `claude-ci.sh` runs all CI checks locally
- Results are formatted as standardized JSON
- Execution is much faster than GitHub Actions (2 min vs 5-10 min)

#### Result Posting
- `post-ci-results.py` posts results using GitHub API
- Creates a Check Run with detailed results
- Falls back to PR comment if needed
- Includes pass/fail status and detailed metrics

#### GitHub Verification
- `ci-local-verifier.yml` workflow runs on PRs
- Fetches posted results from Check Runs or PR comments
- Verifies results meet quality thresholds
- Updates PR status to reflect verification

### Result Format

```json
{
  "version": "1.0",
  "timestamp": "2025-07-23T10:30:00Z",
  "commit_sha": "abc123...",
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

### Verification Rules

The verifier checks:
- Coverage meets threshold (≥ 85%)
- All tests pass (0 failures)
- Linting passes (no errors)
- Type checking passes (if present)

### Benefits

1. **Speed**: Get CI results in 2 minutes instead of waiting for GitHub runners
2. **Cost**: Reduce GitHub Actions minutes usage
3. **Debugging**: Easier to reproduce and debug CI failures locally
4. **Control**: Full control over CI environment and caching

### Limitations (Phase 1)

- Basic authentication only (uses GITHUB_TOKEN)
- No result signing/attestation yet
- Manual trigger required (not automatic on push)
- Limited to coverage, tests, and linting checks

## Usage Examples

### Basic CI Run
```bash
# Run standard CI and post results
./scripts/claude-ci.sh all --output results.json --post-results
```

### Quick Validation
```bash
# Quick mode with posting
./scripts/claude-ci.sh all --quick --output results.json --post-results
```

### Comprehensive Check
```bash
# Full validation suite
./scripts/claude-ci.sh all --comprehensive --output results.json --post-results
```

### Manual Result Posting
```bash
# If you already have results
./scripts/post-ci-results.py existing-results.json --pr 456
```

### Verify Results Locally
```bash
# Check if results would pass verification
./scripts/verify-ci-results.py ci-results.json
```

## Troubleshooting

### Results Not Appearing
1. Check GitHub token permissions: `gh auth status`
2. Verify PR exists: `gh pr view`
3. Check for API errors in post-ci-results.py output

### Verification Failing
1. Run verifier locally: `./scripts/verify-ci-results.py results.json`
2. Check coverage threshold in `.coverage-config.json`
3. Ensure all tests are passing locally

### Authentication Issues
- Set GITHUB_TOKEN environment variable
- Or ensure `gh` CLI is authenticated: `gh auth login`

## Future Phases

### Phase 2: Security & Reliability
- Result signing with GPG/JWT
- Secure result storage
- Retry logic and error handling
- Monitoring and alerting

### Phase 3: Full Migration
- Convert all CI checks
- Automatic posting on git push
- Local caching strategies
- Performance optimizations

### Phase 4: Advanced Features
- Distributed CI across multiple machines
- Custom hardware support (GPUs)
- Advanced caching and incremental builds
- CI result analytics

## Migration Checklist

- [ ] Install required tools: `gh`, `jq`, Python 3.11+
- [ ] Authenticate GitHub CLI: `gh auth login`
- [ ] Test local CI execution: `./scripts/claude-ci.sh all`
- [ ] Test result posting: `--post-results` flag
- [ ] Verify PR status updates correctly
- [ ] Document team-specific workflows
- [ ] Plan gradual rollout strategy
