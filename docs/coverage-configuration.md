# Coverage Configuration Management

## Overview
This project uses a centralized coverage configuration system to manage testing thresholds across all tools and workflows.

## Configuration File: `.coverage-config.json`

```json
{
  "baseline": 78.5,           // Minimum acceptable coverage (fail CI if below)
  "target": 85.0,             // Project-wide coverage goal
  "validator_target": 90.0,   // Higher standard for critical validator modules
  "description": "Coverage thresholds for the agent-context-template project",
  "last_updated": "2025-07-15"
}
```

## What Uses This Configuration

### GitHub Actions Workflows
- **`.github/workflows/claude-code-review.yml`** - ARC-Reviewer checks
  - Loads baseline dynamically in "Load Coverage Configuration" step
  - Fails PR if coverage drops below baseline
  - Updates status messages with current threshold

### Local Development Tools
- **`scripts/test-github-ci-locally.sh`** - Local CI validation
  - Reads baseline to match GitHub Actions behavior exactly
  - Prevents "works locally but fails in CI" scenarios

### Documentation
- **`CLAUDE.md`** - Project documentation
  - Auto-updated via `scripts/update-coverage-baseline.py`
  - Keeps documentation in sync with actual CI settings

## How to Update Coverage Thresholds

### Step 1: Edit Configuration
```bash
# Edit the centralized config file
vim .coverage-config.json

# Example: Increase baseline from 78.5% to 80.0%
{
  "baseline": 80.0,  // <- Update this value
  "target": 85.0,
  "validator_target": 90.0,
  "last_updated": "2025-07-15"  // <- Update date
}
```

### Step 2: Sync Documentation
```bash
# Run the update script to sync CLAUDE.md
python scripts/update-coverage-baseline.py

# Output:
# ✅ Updated CLAUDE.md with baseline: 80.0%, target: 85.0%, validator target: 90.0%
```

### Step 3: Test Locally (Optional)
```bash
# Verify the new baseline works locally
./scripts/test-github-ci-locally.sh

# Should show: "Coverage baseline loaded: 80.0%"
```

### Step 4: Commit Changes
```bash
git add .coverage-config.json CLAUDE.md
git commit -m "feat(coverage): increase baseline from 78.5% to 80.0%

- Updated baseline to reflect improved test coverage
- All CI/CD pipelines will now enforce 80.0% minimum"
```

## Benefits of This System

### ✅ Before (Brittle)
- Coverage thresholds hardcoded in 7+ files
- Updating baselines required hunting through multiple files
- Frequent "coverage regression" false positives due to inconsistencies
- Documentation often out of sync with actual CI settings

### ✅ After (Robust)
- **Single source of truth** - `.coverage-config.json`
- **One command update** - Edit config + run sync script
- **Automatic consistency** - All tools read from same source
- **No more hunting** - Clear documentation and workflow

## Troubleshooting

### Coverage Regression Errors
If you see: `ARC-Review: Coverage regression (X% < Y%)`

1. Check current actual coverage:
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

2. Check current baseline:
   ```bash
   cat .coverage-config.json | jq '.baseline'
   ```

3. If baseline is too high, lower it to current reality:
   ```bash
   # Edit .coverage-config.json to set realistic baseline
   python scripts/update-coverage-baseline.py
   git commit -m "fix(coverage): adjust baseline to current reality"
   ```

### Local vs CI Differences
If local tests pass but CI fails on coverage:

1. Run exact CI command locally:
   ```bash
   ./scripts/test-github-ci-locally.sh
   ```

2. Check that both use same baseline:
   - Local: Reads from `.coverage-config.json`
   - CI: Loads same file in GitHub Actions

### Configuration Not Loading
If tools aren't reading the configuration:

1. Verify file exists and is valid JSON:
   ```bash
   cat .coverage-config.json | jq '.'
   ```

2. Check file permissions:
   ```bash
   ls -la .coverage-config.json
   ```

3. Verify Python can read it:
   ```bash
   python -c "import json; print(json.load(open('.coverage-config.json')))"
   ```

## File Locations

```
project-root/
├── .coverage-config.json                    # ← Main configuration
├── scripts/update-coverage-baseline.py      # ← Sync script
├── scripts/test-github-ci-locally.sh        # ← Local testing (reads config)
├── .github/workflows/claude-code-review.yml # ← CI workflow (reads config)
├── CLAUDE.md                                # ← Documentation (auto-updated)
└── docs/coverage-configuration.md           # ← This file
```

## Version History

- **2025-07-15**: Initial centralized configuration system
  - Baseline: 78.5% (migrated from hardcoded values)
  - Target: 85.0%
  - Validator target: 90.0%
