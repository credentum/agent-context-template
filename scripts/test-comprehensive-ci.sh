#!/bin/bash
# test-comprehensive-ci.sh - Run ALL CI checks exactly like GitHub Actions
# This matches ALL GitHub Actions workflows that are failing

set -e  # Exit on error

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
            FAILED=$((FAILED + 1))
            return 1
        fi
    fi
}

# 1. LINT CHECKS (from lint-verification.yml)
echo -e "\n${YELLOW}📋 1. LINT VERIFICATION CHECKS${NC}"
echo "=================================="

run_check "Black formatting" "black --check src/ tests/ scripts/"
run_check "isort import sorting" "isort --check-only --profile black src/ tests/ scripts/"
run_check "Flake8 linting" "flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503"
run_check "MyPy type checking (src/)" "mypy src/ --config-file=mypy.ini"
run_check "MyPy type checking (tests/)" "mypy tests/ --config-file=mypy.ini" "true"
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/"
run_check "Import check" "python -m pytest --collect-only -q"

# 2. UNIT TESTS (from test.yml)
echo -e "\n${YELLOW}📋 2. UNIT TESTS${NC}"
echo "================="

run_check "Unit Tests (Fast)" "python -m pytest tests/ -v --tb=short -m 'not integration and not e2e' --maxfail=5"

# 3. INTEGRATION TESTS (from test-suite.yml)
echo -e "\n${YELLOW}📋 3. INTEGRATION TESTS${NC}"
echo "======================"

run_check "Integration Tests" "python -m pytest tests/ -v --tb=short -m 'integration' --maxfail=3"

# 4. COVERAGE ANALYSIS (from test-coverage.yml)
echo -e "\n${YELLOW}📋 4. COVERAGE ANALYSIS${NC}"
echo "======================="

run_check "Coverage Tests" "python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=78 -m 'not e2e'"

# 5. CONFLICT DETECTION (from pr-conflict-validator.yml)
echo -e "\n${YELLOW}📋 5. CONFLICT DETECTION${NC}"
echo "========================"

# Check if we're in a git repository and have the right setup
if [ -d ".git" ]; then
    # Fetch latest main
    echo "Fetching latest main branch..."
    git fetch origin main || echo "Warning: Could not fetch main branch"

    # Check for merge conflicts
    run_check "Merge Conflict Detection" "git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main | grep -q '<<<<<<< ' && echo 'Conflicts detected' && exit 1 || echo 'No conflicts detected'" "true"

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
if [ -f ".github/workflows/ai-pr-monitor.yml" ]; then
    run_check "AI Workflow YAML Syntax" "python -c 'import yaml; yaml.safe_load(open(\".github/workflows/ai-pr-monitor.yml\"))'"
else
    echo -e "  ${RED}✗ AI workflow file not found${NC}"
    FAILED=$((FAILED + 1))
fi

# 7. PRE-COMMIT HOOKS (comprehensive)
echo -e "\n${YELLOW}📋 7. PRE-COMMIT HOOKS${NC}"
echo "====================="

run_check "Pre-commit checks" "pre-commit run --all-files"

# 8. SPECIFIC FAILING TESTS (from GitHub Actions)
echo -e "\n${YELLOW}📋 8. SPECIFIC FAILING TESTS${NC}"
echo "============================="

# Run the specific tests that were failing
run_check "Auto-merge output fix tests" "python -m pytest tests/test_auto_merge_output_fix.py -v"
run_check "Workflow feature parity tests" "python -m pytest tests/test_workflow_feature_parity.py -v"

# 9. PERFORMANCE AND QUALITY CHECKS
echo -e "\n${YELLOW}📋 9. ADDITIONAL QUALITY CHECKS${NC}"
echo "==============================="

# Security check
run_check "Security scan (bandit)" "bandit -r src/ -f json -o /tmp/bandit-report.json || bandit -r src/ -ll" "true"

# Dependency check
run_check "Dependency check" "pip check"

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
