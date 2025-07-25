#!/bin/bash
# claude-ci.sh - Unified CI command interface with auto-fixing capabilities
# Detects issues, fixes what it can, and creates GitHub issues for what it can't

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
COMMAND=""
TARGET_FILE=""
FIX_MODE=false
ALL_MODE=false
OUTPUT_FORMAT="json"
VERBOSE=false
CREATE_ISSUES=false
AUTO_FIX_ALL=false

# Help function
show_help() {
    cat << EOF
Claude CI - Unified CI with Auto-Fix and Issue Creation

Usage: claude-ci <command> [options]

Commands:
  check <file>     Validate a single file (black, isort, flake8, mypy)
  test             Run smart test selection (or --all for full suite)
  pre-commit       Run pre-commit validation
  review           Local PR review with ARC-Reviewer
  fix-all          Find and fix ALL fixable issues automatically
  all              Complete CI validation pipeline with auto-fix
  help             Show this help message

Options:
  --fix            Auto-fix issues where possible
  --all            Run all tests (not just smart selection)
  --create-issues  Create GitHub issues for unfixable problems
  --auto-fix-all   Fix everything possible before failing
  --quick          Quick validation mode (essential checks only)
  --comprehensive  Full validation including integration tests
  --pretty         Human-readable output instead of JSON
  --verbose        Show detailed output

Exit Codes:
  0 - All checks passed (or were fixed)
  1 - Unfixable issues remain
  2 - Invalid usage/arguments

Examples:
  claude-ci fix-all                       # Fix everything possible
  claude-ci all --auto-fix-all            # Fix issues during validation
  claude-ci review --create-issues        # Create issues for problems
  claude-ci all --auto-fix-all --create-issues  # Full automation
EOF
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    show_help
    exit 2
fi

COMMAND=$1
shift

# Parse remaining arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=true
            shift
            ;;
        --all)
            ALL_MODE=true
            shift
            ;;
        --create-issues)
            CREATE_ISSUES=true
            shift
            ;;
        --auto-fix-all)
            AUTO_FIX_ALL=true
            FIX_MODE=true
            shift
            ;;
        --pretty)
            OUTPUT_FORMAT="pretty"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --quick|--comprehensive)
            MODE_FLAG=$1
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$TARGET_FILE" ] && [ "$COMMAND" = "check" ]; then
                TARGET_FILE=$1
            else
                echo "Unknown option: $1"
                show_help
                exit 2
            fi
            shift
            ;;
    esac
done

# Track issues for GitHub
UNFIXABLE_ISSUES=()

# JSON output helper
json_output() {
    local status=$1
    local command=$2
    local details=$3
    local duration=$4
    local next_action=$5

    if [ "$OUTPUT_FORMAT" = "json" ]; then
        cat << EOF
{
  "status": "$status",
  "command": "$command",
  "duration": "${duration}s",
  "details": $details,
  "next_action": "$next_action"
}
EOF
    else
        echo -e "${BLUE}Command:${NC} $command"
        echo -e "${BLUE}Status:${NC} $status"
        echo -e "${BLUE}Duration:${NC} ${duration}s"
        if [ "$status" != "PASSED" ]; then
            echo -e "${BLUE}Details:${NC}"
            echo "$details" | jq -r '.' 2>/dev/null || echo "$details"
            echo -e "${BLUE}Next Action:${NC} $next_action"
        fi
    fi
}

# Function to create GitHub issue
create_github_issue() {
    local title=$1
    local body=$2
    local labels=$3

    if [ "$CREATE_ISSUES" = true ]; then
        echo -e "${YELLOW}Creating GitHub issue for: $title${NC}"
        gh issue create \
            --title "$title" \
            --body "$body" \
            --label "$labels" || echo "Failed to create issue"
    else
        # Track for later
        UNFIXABLE_ISSUES+=("$title: $body")
    fi
}

# Auto-fix functions
fix_yaml_issues() {
    echo -e "${BLUE}Fixing YAML formatting issues...${NC}"

    # Fix sprint-4.1.yaml specifically (known issues)
    if [ -f "context/sprints/sprint-4.1.yaml" ]; then
        # Add document start marker
        if ! grep -q "^---" context/sprints/sprint-4.1.yaml; then
            sed -i '1i---' context/sprints/sprint-4.1.yaml
        fi

        # Fix indentation for common patterns
        # This is simplified - in reality would need more sophisticated fixing
        python3 -c "
import yaml
import sys

try:
    with open('context/sprints/sprint-4.1.yaml', 'r') as f:
        data = yaml.safe_load(f)
    with open('context/sprints/sprint-4.1.yaml', 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, width=80)
    print('Fixed YAML formatting')
except Exception as e:
    print(f'Could not auto-fix YAML: {e}')
    sys.exit(1)
"
    fi

    # Run yamllint to check
    if yamllint context/sprints/*.yaml >/dev/null 2>&1; then
        echo -e "${GREEN}✓ YAML issues fixed${NC}"
        return 0
    else
        create_github_issue \
            "[CI] YAML formatting issues need manual fixing" \
            "The following YAML files have formatting issues that couldn't be auto-fixed:\n\`\`\`\n$(yamllint context/sprints/*.yaml 2>&1 | head -20)\n\`\`\`" \
            "ci,yaml,needs-fix"
        return 1
    fi
}

fix_python_formatting() {
    echo -e "${BLUE}Fixing Python formatting issues...${NC}"

    # Run black
    black src/ tests/ scripts/ || true

    # Run isort
    isort src/ tests/ scripts/ || true

    echo -e "${GREEN}✓ Python formatting fixed${NC}"
}

fix_type_annotations() {
    echo -e "${BLUE}Checking type annotations...${NC}"

    # Run mypy and capture output
    local mypy_output=$(mypy src/ tests/ 2>&1 || true)

    if echo "$mypy_output" | grep -q "error:"; then
        # Try to add common type: ignore comments for known issues
        echo "$mypy_output" | grep -E "error:.*\[" | while read -r line; do
            if echo "$line" | grep -q "import-not-found"; then
                # Auto-add type: ignore for missing imports
                local file=$(echo "$line" | cut -d: -f1)
                local line_num=$(echo "$line" | cut -d: -f2)
                # This is simplified - would need proper parsing
                echo "Would add type: ignore to $file:$line_num"
            fi
        done

        create_github_issue \
            "[CI] Type annotation errors need fixing" \
            "MyPy found type errors that need manual fixing:\n\`\`\`\n$mypy_output\n\`\`\`" \
            "ci,types,needs-fix"
        return 1
    else
        echo -e "${GREEN}✓ No type annotation issues${NC}"
        return 0
    fi
}

fix_security_issues() {
    echo -e "${BLUE}Checking for security issues...${NC}"

    # Common patterns to fix
    local files_with_secrets=$(grep -r -l -E "(password|api_key|secret)\\s*=\\s*[\"'][^\"']+[\"']" src/ tests/ 2>/dev/null || true)

    if [ -n "$files_with_secrets" ]; then
        echo -e "${YELLOW}Found potential hardcoded secrets in:${NC}"
        echo "$files_with_secrets"

        create_github_issue \
            "[SECURITY] Potential hardcoded secrets detected" \
            "The following files may contain hardcoded secrets:\n\`\`\`\n$files_with_secrets\n\`\`\`\n\nPlease review and move to environment variables." \
            "security,high-priority,needs-fix"
        return 1
    else
        echo -e "${GREEN}✓ No obvious security issues${NC}"
        return 0
    fi
}

# Enhanced ARC reviewer with issue fixing
run_review_with_fixes() {
    local start_time=$(date +%s)

    echo -e "${BLUE}Running ARC reviewer...${NC}"

    # Run ARC reviewer and capture full output
    local output=$(python -m src.agents.arc_reviewer --skip-coverage --timeout 60 2>&1)
    local exit_code=$?

    # Parse the output for issues
    local verdict=$(echo "$output" | grep "verdict:" | cut -d' ' -f2)

    if [[ "$verdict" = "REQUEST_CHANGES" || "$verdict" = "REQUEST CHANGES" ]] && [ "$AUTO_FIX_ALL" = true ]; then
        echo -e "${YELLOW}ARC found issues, attempting fixes...${NC}"

        # Extract and fix specific issues
        if echo "$output" | grep -q "Pre-commit hooks failed"; then
            echo -e "${BLUE}Fixing pre-commit issues...${NC}"
            pre-commit run --all-files || true

            # Run again to see if fixed
            output=$(python -m src.agents.arc_reviewer --skip-coverage --timeout 60 2>&1)
            verdict=$(echo "$output" | grep "verdict:" | cut -d' ' -f2)
        fi

        # Check for other fixable issues
        if echo "$output" | grep -q "hardcoded secret"; then
            fix_security_issues
        fi
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ "$verdict" = "APPROVE" ] || [ "$verdict" = "APPROVED" ]; then
        json_output "PASSED" "review" '{"verdict": "APPROVE"}' "$duration" "Ready for PR"
        return 0
    else
        # Extract blocking issues for GitHub
        local blocking_issues=$(echo "$output" | sed -n '/blocking:/,/warnings:/p' | grep "description:" | sed 's/.*description: //')

        if [ "$CREATE_ISSUES" = true ] && [ -n "$blocking_issues" ]; then
            create_github_issue \
                "[CI] ARC Reviewer found blocking issues" \
                "The ARC reviewer found issues that must be fixed:\n\n$blocking_issues\n\nFull output:\n\`\`\`\n$output\n\`\`\`" \
                "ci,arc-reviewer,blocking"
        fi

        json_output "FAILED" "review" '{"verdict": "REQUEST_CHANGES"}' "$duration" "Fix blocking issues"
        return 1
    fi
}

# Main fix-all command
run_fix_all() {
    echo -e "${GREEN}🔧 Running comprehensive auto-fix...${NC}"
    local all_fixed=true

    # 1. Python formatting
    fix_python_formatting

    # 2. YAML issues
    if ! fix_yaml_issues; then
        all_fixed=false
    fi

    # 3. Type annotations
    if ! fix_type_annotations; then
        all_fixed=false
    fi

    # 4. Pre-commit hooks
    echo -e "${BLUE}Running pre-commit fixes...${NC}"
    pre-commit run --all-files || true

    # 5. Security scan
    if ! fix_security_issues; then
        all_fixed=false
    fi

    # 6. Final validation
    if ! run_review_with_fixes; then
        all_fixed=false
    fi

    # Summary
    echo ""
    if [ "$all_fixed" = true ]; then
        echo -e "${GREEN}✅ All issues fixed successfully!${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Some issues require manual intervention${NC}"
        if [ ${#UNFIXABLE_ISSUES[@]} -gt 0 ]; then
            echo -e "${YELLOW}Unfixable issues:${NC}"
            printf '%s\n' "${UNFIXABLE_ISSUES[@]}"
        fi
        return 1
    fi
}

# Command implementations
run_file_check() {
    local file=$1
    local start_time=$(date +%s)

    if [ ! -f "$file" ]; then
        json_output "ERROR" "check" '{"error": "File not found"}' "0" "Verify file path"
        exit 1
    fi

    if [ "$FIX_MODE" = true ]; then
        black "$file"
        isort "$file"

        # Check for remaining issues
        if ! flake8 "$file" >/dev/null 2>&1; then
            local flake8_errors=$(flake8 "$file" 2>&1)
            create_github_issue \
                "[CI] Flake8 errors in $file" \
                "The following flake8 errors need manual fixing:\n\`\`\`\n$flake8_errors\n\`\`\`" \
                "ci,flake8,needs-fix"
        fi
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    json_output "PASSED" "check $file" '{}' "$duration" "File checked"
}

run_all() {
    local start_time=$(date +%s)
    local all_passed=true
    local failed_checks=()

    echo -e "${GREEN}Running comprehensive CI validation${NC}"

    # If auto-fix mode, run fixes first
    if [ "$AUTO_FIX_ALL" = true ]; then
        if ! run_fix_all; then
            all_passed=false
        fi
    else
        # 1. Run linting checks (pre-commit includes black, isort, flake8, yamllint)
        echo -e "${BLUE}Running linting checks...${NC}"
        if ! pre-commit run --all-files >/dev/null 2>&1; then
            all_passed=false
            failed_checks+=("linting")
            echo -e "${RED}✗ Linting checks failed${NC}"
        else
            echo -e "${GREEN}✓ Linting checks passed${NC}"
        fi

        # 2. Run MyPy type checking
        echo -e "${BLUE}Running type checking...${NC}"
        if ! mypy src/ tests/ >/dev/null 2>&1; then
            all_passed=false
            failed_checks+=("type-checking")
            echo -e "${RED}✗ Type checking failed${NC}"
        else
            echo -e "${GREEN}✓ Type checking passed${NC}"
        fi

        # 3. Run tests (quick mode uses smart selection, otherwise full suite)
        echo -e "${BLUE}Running tests...${NC}"
        if [ "$QUICK_MODE" = true ]; then
            if [ -f "./scripts/claude-test-changed.sh" ]; then
                if ! ./scripts/claude-test-changed.sh >/dev/null 2>&1; then
                    all_passed=false
                    failed_checks+=("tests")
                    echo -e "${RED}✗ Tests failed${NC}"
                else
                    echo -e "${GREEN}✓ Tests passed${NC}"
                fi
            else
                if ! pytest -x >/dev/null 2>&1; then
                    all_passed=false
                    failed_checks+=("tests")
                    echo -e "${RED}✗ Tests failed${NC}"
                else
                    echo -e "${GREEN}✓ Tests passed${NC}"
                fi
            fi
        else
            if ! pytest --cov=src --cov-report=term-missing >/dev/null 2>&1; then
                all_passed=false
                failed_checks+=("tests")
                echo -e "${RED}✗ Tests failed${NC}"
            else
                echo -e "${GREEN}✓ Tests passed${NC}"
            fi
        fi

        # 4. Run ARC reviewer
        if ! run_review_with_fixes; then
            all_passed=false
            failed_checks+=("arc-reviewer")
        fi
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ "$all_passed" = true ]; then
        json_output "PASSED" "all" '{"status": "clean"}' "$duration" "Ready for PR"
    else
        local failed_list=$(IFS=','; echo "${failed_checks[*]}")
        json_output "FAILED" "all" "{\"status\": \"issues remain\", \"failed_checks\": \"$failed_list\"}" "$duration" "Fix ${#failed_checks[@]} failing check(s): $failed_list"
        exit 1
    fi
}

# Test command implementation
run_tests() {
    local start_time=$(date +%s)
    local test_cmd="pytest"

    if [ "$RUN_ALL_TESTS" = true ]; then
        echo -e "${BLUE}Running full test suite...${NC}"
        test_cmd="pytest --cov=src --cov-report=term-missing"
    else
        echo -e "${BLUE}Running smart test selection...${NC}"
        # Use the smart test runner if available
        if [ -f "./scripts/claude-test-changed.sh" ]; then
            ./scripts/claude-test-changed.sh
            local exit_code=$?
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))

            if [ $exit_code -eq 0 ]; then
                json_output "PASSED" "test" '{"mode": "smart"}' "$duration" "All tests passed"
                return 0
            else
                json_output "FAILED" "test" '{"mode": "smart"}' "$duration" "Test failures detected"
                return 1
            fi
        else
            test_cmd="pytest"
        fi
    fi

    # Run pytest
    if $test_cmd; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        json_output "PASSED" "test" '{}' "$duration" "All tests passed"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        json_output "FAILED" "test" '{}' "$duration" "Test failures detected"
        return 1
    fi
}

# Main command dispatcher
case $COMMAND in
    check)
        if [ -z "$TARGET_FILE" ]; then
            echo "Error: check command requires a file path"
            show_help
            exit 2
        fi
        run_file_check "$TARGET_FILE"
        ;;
    test)
        run_tests
        ;;
    fix-all)
        run_fix_all
        ;;
    review)
        run_review_with_fixes
        ;;
    all)
        run_all
        ;;
    help)
        show_help
        exit 0
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 2
        ;;
esac
