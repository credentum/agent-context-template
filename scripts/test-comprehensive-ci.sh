#!/bin/bash
# test-comprehensive-ci.sh - Run ALL CI checks exactly like GitHub Actions
# This matches ALL GitHub Actions workflows that are failing

# Note: We intentionally do NOT use 'set -e' here
# This ensures ALL checks run even if some fail, allowing us to see all errors at once

# Signal handling for clean shutdown
cleanup() {
    echo -e "\n${YELLOW}Caught signal, cleaning up...${NC}"
    # Kill all child processes in this process group
    jobs -p | xargs -r kill 2>/dev/null
    # Wait briefly for processes to exit gracefully
    sleep 1
    # Force kill any remaining processes
    jobs -p | xargs -r kill -9 2>/dev/null
    wait
    echo -e "${GREEN}Cleanup completed${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup EXIT SIGTERM SIGINT

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Running COMPREHENSIVE CI Checks (exactly like GitHub Actions)${NC}"
echo "=========================================================================="
echo "This runs ALL the checks that are failing in GitHub Actions"
echo

# Track failures
FAILED=0
TOTAL_CHECKS=0

# Function to run a command and check status
run_check() {
    local name=$1
    local cmd=$2
    local allow_fail=${3:-false}
    local fix_hint=${4:-""}  # Optional fix suggestion

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}▶ $name${NC}"
    echo "  Command: $cmd"

    if eval "$cmd"; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        return 0
    else
        if [ "$allow_fail" = "true" ]; then
            echo -e "  ${YELLOW}⚠ FAILED (allowed)${NC}"
            return 0
        else
            echo -e "  ${RED}✗ FAILED${NC}"
            if [ -n "$fix_hint" ]; then
                echo -e "  ${YELLOW}Fix: $fix_hint${NC}"
            fi
            FAILED=$((FAILED + 1))
            return 1
        fi
    fi
}

# 1. LINT CHECKS (from lint-verification.yml)
echo -e "\n${YELLOW}📋 1. LINT VERIFICATION CHECKS${NC}"
echo "=================================="

run_check "Black formatting" "black --check src/ tests/ scripts/" "false" "Run 'black src/ tests/ scripts/' to fix formatting"
run_check "isort import sorting" "isort --check-only --profile black src/ tests/ scripts/" "false" "Run 'isort --profile black src/ tests/ scripts/' to fix imports"
run_check "Flake8 linting" "flake8 src/ tests/ scripts/" "false" "Check specific error codes and fix manually or use 'autopep8'"
run_check "MyPy type checking (src/)" "mypy src/ --config-file=mypy.ini" "false" "Add type annotations or use '# type: ignore' comments where needed"
run_check "MyPy type checking (tests/)" "mypy tests/ --config-file=mypy.ini" "true" "Type annotations in tests are optional"
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/" "false" "Check YAML syntax and schema compliance in context/ files"
run_check "Import check" "python -m pytest --collect-only -q" "false" "Fix import errors or missing dependencies"

# 2. UNIT TESTS (from test.yml)
echo -e "\n${YELLOW}📋 2. UNIT TESTS${NC}"
echo "================="

run_check "Unit Tests (Fast)" "python -m pytest tests/ -v --tb=short -m 'not integration and not e2e' --maxfail=5" "false" "Debug failing tests and update test code"

# 3. INTEGRATION TESTS (from test-suite.yml)
echo -e "\n${YELLOW}📋 3. INTEGRATION TESTS${NC}"
echo "======================"

run_check "Integration Tests" "python -m pytest tests/ -v --tb=short -m 'integration' --maxfail=3" "false" "Check service dependencies and integration test setup"

# 4. COVERAGE ANALYSIS (from test-coverage.yml)
echo -e "\n${YELLOW}📋 4. COVERAGE ANALYSIS${NC}"
echo "======================="

# Read coverage threshold from centralized configuration
if [ -f ".coverage-config.json" ]; then
    COVERAGE_BASELINE=$(python -c "import json; print(int(json.load(open('.coverage-config.json'))['baseline']))" 2>/dev/null || echo "78")
else
    COVERAGE_BASELINE=78
fi

run_check "Coverage Tests" "python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=$COVERAGE_BASELINE -m 'not e2e'" "false" "Add tests for uncovered code or adjust coverage threshold"

# 5. CONFLICT DETECTION (from pr-conflict-validator.yml)
echo -e "\n${YELLOW}📋 5. CONFLICT DETECTION${NC}"
echo "========================"

# Check if we're in a git repository and have the right setup
if [ -d ".git" ]; then
    # Fetch latest main
    echo "Fetching latest main branch..."
    git fetch origin main || echo "Warning: Could not fetch main branch"

    # Check for merge conflicts (secure version)
    # Get merge base safely
    MERGE_BASE=$(git merge-base HEAD origin/main 2>/dev/null || true)

    if [ -n "$MERGE_BASE" ]; then
        # Perform merge tree check safely
        MERGE_OUTPUT=$(git merge-tree "$MERGE_BASE" HEAD origin/main 2>/dev/null || true)
        if echo "$MERGE_OUTPUT" | grep -q '<<<<<<< '; then
            echo -e "  ${RED}✗ Merge Conflict Detection: Conflicts detected${NC}"
            echo "  Fix: Merge or rebase with origin/main to resolve conflicts"
            FAILED=$((FAILED + 1))
        else
            echo -e "  ${GREEN}✓ Merge Conflict Detection: No conflicts detected${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ Could not determine merge base${NC}"
    fi

    # Check if branch is up to date
    BEHIND_COUNT=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    if [ "$BEHIND_COUNT" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠ Branch is $BEHIND_COUNT commits behind main${NC}"
    else
        echo -e "  ${GREEN}✓ Branch is up to date with main${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Not in git repository, skipping conflict detection${NC}"
fi

# 6. WORKFLOW VALIDATION (from ai-pr-monitor.yml validation)
echo -e "\n${YELLOW}📋 6. WORKFLOW VALIDATION${NC}"
echo "=========================="

# Check if our new AI workflow file exists and is valid
WORKFLOW_FILE=".github/workflows/ai-pr-monitor.yml"
if [ -f "$WORKFLOW_FILE" ]; then
    # Secure Python execution with proper error handling
    YAML_CHECK_CMD="python -c 'import sys, yaml; \ntry: \n    with open(sys.argv[1], \"r\") as f: \n        yaml.safe_load(f); \n    print(\"YAML syntax valid\"); \n    sys.exit(0) \nexcept Exception as e: \n    print(f\"YAML syntax error: {e}\"); \n    sys.exit(1)' '$WORKFLOW_FILE'"

    run_check "AI Workflow YAML Syntax" "$YAML_CHECK_CMD"
else
    echo -e "  ${RED}✗ AI workflow file not found${NC}"
    echo "  Fix: Ensure .github/workflows/ai-pr-monitor.yml exists"
    FAILED=$((FAILED + 1))
fi

# 7. PRE-COMMIT HOOKS (comprehensive)
echo -e "\n${YELLOW}📋 7. PRE-COMMIT HOOKS${NC}"
echo "====================="

run_check "Pre-commit checks" "pre-commit run --all-files" "false" "Run 'pre-commit run --all-files' locally and fix issues"

# 8. SPECIFIC FAILING TESTS (from GitHub Actions)
echo -e "\n${YELLOW}📋 8. SPECIFIC FAILING TESTS${NC}"
echo "============================="

# Run the specific tests that were failing (with file existence check)
if [ -f "tests/test_auto_merge_output_fix.py" ]; then
    run_check "Auto-merge output fix tests" "python -m pytest tests/test_auto_merge_output_fix.py -v" "false" "Fix failing auto-merge output tests"
else
    echo -e "  ${YELLOW}⚠ Skipping auto-merge output fix tests (file not found)${NC}"
fi

if [ -f "tests/test_workflow_feature_parity.py" ]; then
    run_check "Workflow feature parity tests" "python -m pytest tests/test_workflow_feature_parity.py -v" "false" "Fix failing workflow feature parity tests"
else
    echo -e "  ${YELLOW}⚠ Skipping workflow feature parity tests (file not found)${NC}"
fi

# 9. PERFORMANCE AND QUALITY CHECKS
echo -e "\n${YELLOW}📋 9. ADDITIONAL QUALITY CHECKS${NC}"
echo "==============================="

# Security check
run_check "Security scan (bandit)" "bandit -r src/ -f json -o /tmp/bandit-report.json || bandit -r src/ -ll" "true" "Review security findings and fix high-severity issues"

# Dependency check
run_check "Dependency check" "pip check" "false" "Fix dependency conflicts with 'pip install -r requirements.txt'"

# 10. SUMMARY
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}COMPREHENSIVE CI CHECK SUMMARY${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL $TOTAL_CHECKS CHECKS PASSED!${NC}"
    echo -e "${GREEN}Your code is ready for GitHub Actions CI${NC}"
    echo
    echo "✅ Lint checks: PASSED"
    echo "✅ Unit tests: PASSED"
    echo "✅ Integration tests: PASSED"
    echo "✅ Coverage analysis: PASSED"
    echo "✅ Conflict detection: PASSED"
    echo "✅ Workflow validation: PASSED"
    echo "✅ Pre-commit hooks: PASSED"
    echo "✅ Specific failing tests: PASSED"
    echo
    echo "🚀 Safe to push to GitHub!"
    exit 0
else
    echo -e "${RED}❌ $FAILED out of $TOTAL_CHECKS checks failed${NC}"
    echo
    echo "Failing areas:"
    echo "- Check the specific error messages above"
    echo "- Run individual checks to debug issues"
    echo "- Fix issues and re-run this script"
    echo
    echo "Quick fixes:"
    echo "  - Format code: black src/ tests/ scripts/"
    echo "  - Fix imports: isort src/ tests/ scripts/"
    echo "  - Install missing deps: pip install -r requirements.txt"
    echo "  - Update git: git fetch origin main"
    echo
    exit 1
fi
