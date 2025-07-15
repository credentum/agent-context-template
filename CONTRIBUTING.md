# Contributing Guidelines

## Branch Protection and Workflow

### For Repository Owners

Please set up the following branch protection rules for the `main` branch:

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable these protections:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (at least 1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
     - Required checks: `lint` (from context-lint.yml workflow)
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators (optional but recommended)
   - ✅ Restrict who can push to matching branches (optional)

### For Contributors (including AI assistants)

**NEVER push directly to main!** Always follow this workflow:

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-description
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "type: description"
   ```

3. Push to your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create a pull request:
   ```bash
   gh pr create --title "type: description" --body "Details..."
   ```

5. Wait for CI checks to pass and get approval before merging

### Commit Message Format

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code changes that neither fix bugs nor add features
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### For AI Assistants (Claude, etc.)

When working with code:
1. Always create a new branch before making changes
2. Never use `git push origin main`
3. Always create a PR for review
4. Include clear PR descriptions with:
   - Summary of changes
   - Test plan
   - Any breaking changes

Example workflow:
```bash
# Start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b fix/mypy-errors

# Make changes
# ... edit files ...

# Commit changes
git add -A
git commit -m "fix: Address mypy type errors"

# Push to feature branch
git push -u origin fix/mypy-errors

# Create PR
gh pr create --title "fix: Address mypy type errors" --body "..."
```

## ARC-Reviewer and Auto-Triage Flow

This project uses ARC-Reviewer (Automated Review and Code-review) to provide structured code reviews and automatically create follow-up issues for suggested improvements.

### How It Works

When you create a pull request, ARC-Reviewer will:
1. Analyze your code changes
2. Provide structured feedback with blocking issues, warnings, and suggestions
3. Automatically create GitHub issues for follow-up improvements

### ISSUE: Schema for Follow-ups

ARC-Reviewer uses a structured format for creating follow-up issues:

```
ISSUE: <title> - <description> - labels=<csv> - phase=<milestone>
```

**Example:**
```
ISSUE: Fix validator coverage - Improve test coverage for validators module - labels=test,validator,coverage - phase=4.2
ISSUE: Add performance benchmarks - Create benchmark suite for vector operations - labels=performance,benchmark - phase=backlog
```

### Schema Fields

- **title**: Short descriptive title for the issue (required)
- **description**: Detailed description of the improvement (required)
- **labels**: Comma-separated list of labels (optional, defaults to `enhancement`)
  - Always includes `from-code-review` automatically
- **phase**: Project phase or milestone (optional, defaults to `backlog`)

### Auto-Generated Issues

Issues created by ARC-Reviewer include:
- Title prefixed with `[PR #<number>]` for traceability
- Link to the original PR and author
- Comprehensive issue body with context and acceptance criteria
- Appropriate labels for filtering and organization
- Milestone assignment based on the phase field

### Duplicate Prevention

The system prevents duplicate issues by checking existing issue titles before creation. If an issue with the same title already exists, it will be skipped.

### Testing the Parser

To test the ISSUE: parser logic:

```bash
./scripts/test_arc_reviewer_parser.sh
```

This script validates that the parser correctly handles the ISSUE: schema format with mocked review data.

### Infrastructure Setup

This project uses Qdrant (vector database) and Neo4j (graph database) for development and testing.

#### Quick Start

1. **Start the infrastructure:**
   ```bash
   make up
   ```
   This starts Qdrant on port 6333 and Neo4j on ports 7474/7687.

2. **Check health status:**
   ```bash
   # Option 1: Use the dedicated health check script
   ./infra/healthcheck.sh

   # Option 2: Use the Makefile target
   make health
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```
   This includes the Neo4j driver needed for health checks.

4. **Stop the infrastructure:**
   ```bash
   make down
   ```
   This stops services and removes volumes.

#### Prerequisites

- Docker and Docker Compose
- curl (for Qdrant health checks)
- Python 3.11+ with pip

#### Services Information

- **Qdrant**: Vector database at `http://localhost:6333`
  - Collections endpoint: `http://localhost:6333/collections`
  - Web UI: `http://localhost:6333/dashboard`

- **Neo4j**: Graph database at `bolt://localhost:7687`
  - Browser UI: `http://localhost:7474`
  - Authentication: Disabled for development (`NEO4J_AUTH=none`)

#### Health Check Details

The `./infra/healthcheck.sh` script verifies:
- Qdrant is responding and returns empty collections array
- Neo4j connectivity using the Python driver

Exit codes:
- `0`: All services healthy
- `1`: Qdrant failed
- `2`: Neo4j failed
- `3`: Python not available

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality. Install them:

```bash
pre-commit install
```

This will run automatically before each commit:
- Black formatting
- isort import sorting
- mypy type checking
- Custom context linting
