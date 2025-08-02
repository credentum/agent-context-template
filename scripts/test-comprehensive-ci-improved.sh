#!/bin/bash
# test-comprehensive-ci-improved.sh - Run ALL CI checks with improved process management
# This version has better cleanup and process tracking

# Parse command line arguments
NO_ARC_REVIEWER=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --no-arc-reviewer) NO_ARC_REVIEWER=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Also check environment variable for Docker compatibility
if [[ -n "$CI_EXTRA_ARGS" ]]; then
    if [[ "$CI_EXTRA_ARGS" == *"--no-arc-reviewer"* ]]; then
        NO_ARC_REVIEWER=true
    fi
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track PIDs of all spawned processes
declare -a CHILD_PIDS=()

# Signal handling for clean shutdown
cleanup() {
    echo -e "\n${YELLOW}Caught signal, cleaning up...${NC}"
    
    # Send SIGTERM to all tracked child processes
    for pid in "${CHILD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Terminating process $pid..."
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    
    # Give processes 2 seconds to terminate gracefully
    sleep 2
    
    # Force kill any remaining processes
    for pid in "${CHILD_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Force killing process $pid..."
            kill -9 "$pid" 2>/dev/null
        fi
    done
    
    # Kill all processes in our process group
    kill -TERM -- -$$ 2>/dev/null
    sleep 1
    kill -9 -- -$$ 2>/dev/null
    
    echo -e "${GREEN}Cleanup completed${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup EXIT SIGTERM SIGINT SIGHUP

# Start new process group to ensure we can kill all children
set -m

echo -e "${GREEN}🚀 Running COMPREHENSIVE CI Checks (with improved process management)${NC}"
echo "=========================================================================="
echo -e "${YELLOW}Docker Timeouts: Individual services have 12min timeout for GitHub Actions parity${NC}"
echo ""

# Statistics
TOTAL_CHECKS=0
FAILED=0

# Track the coverage baseline from coverage.yml
COVERAGE_BASELINE=78

# Improved run_check function with process tracking
run_check() {
    local name=$1
    local cmd=$2
    local allow_fail=${3:-false}
    local fix_hint=${4:-""}
    local estimated_time=${5:-"<1 min"}
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -e "\n${BLUE}▶ [$TOTAL_CHECKS] $name${NC} (Est: $estimated_time)"
    echo "  Command: $cmd"
    
    # Run command in background to get PID
    (
        # Set process group for child
        exec setsid $cmd
    ) &
    
    local cmd_pid=$!
    CHILD_PIDS+=($cmd_pid)
    
    # Wait for the command to complete
    if wait $cmd_pid; then
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

# 1. PRE-COMMIT HOOKS
echo -e "\n${YELLOW}📋 1. PRE-COMMIT HOOKS (PRIORITY)${NC}"
echo "==================================="
run_check "Pre-commit checks" "/bin/bash scripts/run-precommit-ci-safe.sh" "false" "Run 'pre-commit run --all-files' locally" "2-3 min"

# 2. INDIVIDUAL LINT CHECKS
echo -e "\n${YELLOW}📋 2. INDIVIDUAL LINT CHECKS${NC}"
echo "============================="
run_check "Black formatting" "black --check src/ tests/ scripts/" "false" "Run 'black src/ tests/ scripts/'" "<30 sec"
run_check "isort import sorting" "isort --check-only --profile black src/ tests/ scripts/" "false" "Run 'isort --profile black src/ tests/ scripts/'" "<30 sec"
run_check "Flake8 linting" "flake8 src/ tests/ scripts/" "false" "Fix lint errors manually" "<30 sec"
run_check "MyPy type checking (src/)" "mypy src/ --config-file=mypy.ini" "false" "Add type annotations or use # type: ignore" "1-2 min"
run_check "MyPy type checking (tests/)" "mypy tests/ --config-file=mypy.ini --explicit-package-bases" "true" "Type annotations in tests are optional" "<1 min"
run_check "Context YAML validation" "python -m src.agents.context_lint validate context/" "false" "Check YAML syntax and schema" "<30 sec"
run_check "Import check" "python -m pytest --collect-only -q" "false" "Fix import errors" "<30 sec"

# 3. UNIT TESTS
echo -e "\n${YELLOW}📋 3. UNIT TESTS${NC}"
echo "================"
run_check "Unit Tests (Fast)" "python -m pytest tests/ -v --tb=short -m 'not integration and not e2e' --maxfail=5" "false" "Debug failing tests" "1-2 min"

# 4. INTEGRATION TESTS
echo -e "\n${YELLOW}📋 4. INTEGRATION TESTS${NC}"
echo "======================"
run_check "Integration Tests" "python -m pytest tests/ -v --tb=short -m 'integration' --maxfail=3" "false" "Check service dependencies" "2-3 min"

# 5. COVERAGE ANALYSIS
echo -e "\n${YELLOW}📋 5. COVERAGE ANALYSIS${NC}"
echo "======================"
mkdir -p test-artifacts
run_check "Coverage Tests" "python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=xml:test-artifacts/coverage.xml --cov-report=json:test-artifacts/coverage.json --cov-fail-under=$COVERAGE_BASELINE -m 'not e2e'" "false" "Add tests for uncovered code" "2-3 min"

# 6. CONFLICT DETECTION
echo -e "\n${YELLOW}📋 6. CONFLICT DETECTION${NC}"
echo "========================"
if [ -f "tests/test_auto_merge_output_fix.py" ]; then
    run_check "Auto-merge output fix tests" "python -m pytest tests/test_auto_merge_output_fix.py -v" "false" "Fix auto-merge tests" "<1 min"
fi
if [ -f "tests/test_workflow_feature_parity.py" ]; then
    run_check "Workflow feature parity tests" "python -m pytest tests/test_workflow_feature_parity.py -v" "false" "Fix workflow tests" "<1 min"
fi

# 7. WORKFLOW VALIDATION
echo -e "\n${YELLOW}📋 7. WORKFLOW VALIDATION${NC}"
echo "========================="
run_check "GitHub workflow YAML validation" "yamllint -c .yamllint-workflows.yml .github/workflows/*.yml" "false" "Fix YAML syntax in workflows" "<30 sec"

# 8. ARC REVIEWER (if not skipped)
if [ "$NO_ARC_REVIEWER" = "false" ]; then
    echo -e "\n${YELLOW}📋 8. ARC REVIEWER (AI-ASSISTED)${NC}"
    echo "================================"
    if [ -d "test-artifacts" ]; then
        run_check "ARC Reviewer" "python -m src.agents.arc_reviewer --all-results --results-dir test-artifacts" "true" "Review ARC suggestions" "1-2 min"
    else
        echo -e "  ${YELLOW}⚠ Skipping ARC Reviewer (no test-artifacts directory)${NC}"
    fi
else
    echo -e "\n${YELLOW}📋 8. ARC REVIEWER${NC}"
    echo "=================="
    echo -e "  ${BLUE}ℹ Skipped (--no-arc-reviewer flag set)${NC}"
fi

# Final summary
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}📊 FINAL SUMMARY${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Total checks run: $TOTAL_CHECKS"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo -e "\nYour code is ready for PR! 🎉"
    exit 0
else
    echo -e "${RED}❌ $FAILED CHECKS FAILED${NC}"
    echo -e "\nPlease fix the issues above before creating a PR."
    echo -e "Tip: Use './scripts/run-ci-docker.sh quick' for faster iteration."
    exit 1
fi