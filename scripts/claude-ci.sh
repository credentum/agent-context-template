#!/usr/bin/env bash
# claude-ci.sh - Unified Claude CI Command Hub
# Provides single entry point for all CI operations with consistent interface

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default options
JSON_OUTPUT=true
VERBOSE=false
FIX_MODE=false
ALL_MODE=false
COMPREHENSIVE=false
QUICK=false

# Colors for terminal output (disabled in JSON mode)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Usage function
usage() {
    cat << EOF
Claude CI Command Hub - Unified CI operations for Claude Code

Usage: claude-ci <command> [options]

Commands:
  check <file>    Validate single file (format, lint, types)
  test           Run smart test selection
  pre-commit     Run pre-commit validation
  review         Simulate PR review locally
  all            Run complete CI pipeline
  help           Show this help message

Options:
  --fix          Enable auto-fixing where possible
  --all          Run all tests (not just relevant)
  --quick        Quick validation only
  --comprehensive Full validation suite
  --json         Output raw JSON (default)
  --pretty       Human-readable output
  --verbose      Show detailed output

Examples:
  claude-ci check src/main.py
  claude-ci test --all
  claude-ci pre-commit --fix
  claude-ci all --quick
  claude-ci review --comprehensive

Progressive Validation Modes:
  --quick        Format check, basic lint, minimal tests (seconds)
  (default)      Full lint, relevant tests, pre-commit (minutes)
  --comprehensive Everything including full tests, coverage, review (full)

EOF
    exit 0
}

# JSON output helper
json_output() {
    local command="$1"
    local status="$2"
    local target="${3:-all}"
    local duration="${4:-0s}"
    local checks="${5:-{}}"
    local errors="${6:-[]}"
    local next_action="${7:-No action needed}"

    if [ "$JSON_OUTPUT" = true ]; then
        cat << EOF
{
  "command": "$command",
  "status": "$status",
  "target": "$target",
  "duration": "$duration",
  "checks": $checks,
  "errors": $errors,
  "next_action": "$next_action"
}
EOF
    fi
}

# Pretty output helper
pretty_output() {
    local command="$1"
    local status="$2"
    local message="$3"

    if [ "$JSON_OUTPUT" = false ]; then
        case "$status" in
            "PASSED")
                echo -e "${GREEN}✅ $command: $message${NC}"
                ;;
            "FAILED")
                echo -e "${RED}❌ $command: $message${NC}"
                ;;
            "SKIPPED")
                echo -e "${YELLOW}⏭️  $command: $message${NC}"
                ;;
            *)
                echo -e "${BLUE}ℹ️  $command: $message${NC}"
                ;;
        esac
    fi
}

# Check command - validate single file
cmd_check() {
    local file="$1"
    local start_time=$(date +%s)

    if [ ! -f "$file" ]; then
        json_output "check" "FAILED" "$file" "0s" "{}" "[{\"message\": \"File not found: $file\"}]" "Verify file path"
        pretty_output "check" "FAILED" "File not found: $file"
        return 1
    fi

    # Delegate to claude-post-edit.sh
    local fix_flag=""
    if [ "$FIX_MODE" = true ]; then
        fix_flag="--fix"
    fi

    if [ -x "$SCRIPT_DIR/claude-post-edit.sh" ]; then
        local end_time=$(date +%s)
        local duration="${((end_time - start_time))}s"

        if "$SCRIPT_DIR/claude-post-edit.sh" "$file" $fix_flag > /dev/null 2>&1; then
            json_output "check" "PASSED" "$file" "$duration" "{\"format\": \"PASSED\", \"lint\": \"PASSED\"}" "[]" "File validation successful"
            pretty_output "check" "PASSED" "File validation successful: $file"
            return 0
        else
            json_output "check" "FAILED" "$file" "$duration" "{\"format\": \"FAILED\"}" "[{\"message\": \"Validation failed\", \"fix\": \"Run: claude-ci check $file --fix\"}]" "Fix issues and run again"
            pretty_output "check" "FAILED" "File validation failed: $file"
            return 1
        fi
    else
        json_output "check" "FAILED" "$file" "0s" "{}" "[{\"message\": \"claude-post-edit.sh not found\"}]" "Ensure script exists"
        pretty_output "check" "FAILED" "claude-post-edit.sh not found"
        return 1
    fi
}

# Test command - run tests
cmd_test() {
    local start_time=$(date +%s)

    if [ -x "$SCRIPT_DIR/claude-test-changed.sh" ]; then
        local test_args=""
        if [ "$ALL_MODE" = true ]; then
            test_args="--all"
        fi
        if [ "$VERBOSE" = true ]; then
            test_args="$test_args --verbose"
        fi
        if [ "$JSON_OUTPUT" = false ]; then
            test_args="$test_args --format text"
        fi

        local end_time=$(date +%s)
        local duration="${((end_time - start_time))}s"

        if "$SCRIPT_DIR/claude-test-changed.sh" $test_args; then
            json_output "test" "PASSED" "smart" "$duration" "{\"tests\": \"PASSED\"}" "[]" "All tests passed"
            pretty_output "test" "PASSED" "Tests completed successfully"
            return 0
        else
            json_output "test" "FAILED" "smart" "$duration" "{\"tests\": \"FAILED\"}" "[{\"message\": \"Some tests failed\"}]" "Review test failures"
            pretty_output "test" "FAILED" "Some tests failed"
            return 1
        fi
    else
        json_output "test" "FAILED" "smart" "0s" "{}" "[{\"message\": \"claude-test-changed.sh not found\"}]" "Ensure script exists"
        pretty_output "test" "FAILED" "claude-test-changed.sh not found"
        return 1
    fi
}

# Pre-commit command
cmd_pre_commit() {
    local start_time=$(date +%s)

    if [ -x "$SCRIPT_DIR/claude-pre-commit.sh" ]; then
        local precommit_args=""
        if [ "$FIX_MODE" = true ]; then
            precommit_args="--fix"
        fi
        if [ "$JSON_OUTPUT" = false ]; then
            precommit_args="$precommit_args --text"
        fi
        if [ "$VERBOSE" = true ]; then
            precommit_args="$precommit_args --verbose"
        fi

        local end_time=$(date +%s)
        local duration="${((end_time - start_time))}s"

        if "$SCRIPT_DIR/claude-pre-commit.sh" $precommit_args; then
            json_output "pre-commit" "PASSED" "all" "$duration" "{\"pre-commit\": \"PASSED\"}" "[]" "Pre-commit checks passed"
            pretty_output "pre-commit" "PASSED" "All pre-commit checks passed"
            return 0
        else
            json_output "pre-commit" "FAILED" "all" "$duration" "{\"pre-commit\": \"FAILED\"}" "[{\"message\": \"Pre-commit checks failed\"}]" "Fix issues and run again"
            pretty_output "pre-commit" "FAILED" "Pre-commit checks failed"
            return 1
        fi
    else
        json_output "pre-commit" "FAILED" "all" "0s" "{}" "[{\"message\": \"claude-pre-commit.sh not found\"}]" "Ensure script exists"
        pretty_output "pre-commit" "FAILED" "claude-pre-commit.sh not found"
        return 1
    fi
}

# Review command - local PR review simulation
cmd_review() {
    local start_time=$(date +%s)

    # Use run-ci-docker.sh for comprehensive review
    if [ -x "$SCRIPT_DIR/run-ci-docker.sh" ]; then
        local end_time=$(date +%s)
        local duration="${((end_time - start_time))}s"

        if "$SCRIPT_DIR/run-ci-docker.sh" > /dev/null 2>&1; then
            json_output "review" "PASSED" "all" "$duration" "{\"docker-ci\": \"PASSED\", \"coverage\": \"PASSED\"}" "[]" "PR review simulation passed"
            pretty_output "review" "PASSED" "PR review simulation completed successfully"
            return 0
        else
            json_output "review" "FAILED" "all" "$duration" "{\"docker-ci\": \"FAILED\"}" "[{\"message\": \"Docker CI checks failed\"}]" "Fix CI issues before PR"
            pretty_output "review" "FAILED" "Docker CI checks failed"
            return 1
        fi
    else
        json_output "review" "FAILED" "all" "0s" "{}" "[{\"message\": \"run-ci-docker.sh not found\"}]" "Ensure script exists"
        pretty_output "review" "FAILED" "run-ci-docker.sh not found"
        return 1
    fi
}

# All command - complete CI pipeline
cmd_all() {
    local start_time=$(date +%s)
    local overall_status="PASSED"
    local checks="{}"
    local errors="[]"

    pretty_output "all" "INFO" "Running complete CI pipeline..."

    # Progressive validation based on mode
    if [ "$QUICK" = true ]; then
        pretty_output "all" "INFO" "Quick mode: format check + basic lint"
        # Quick format check on changed files
        if ! cmd_pre_commit; then
            overall_status="FAILED"
        fi
    elif [ "$COMPREHENSIVE" = true ]; then
        pretty_output "all" "INFO" "Comprehensive mode: full validation suite"
        # Run everything
        if ! cmd_pre_commit; then overall_status="FAILED"; fi
        if ! cmd_test; then overall_status="FAILED"; fi
        if ! cmd_review; then overall_status="FAILED"; fi
    else
        pretty_output "all" "INFO" "Standard mode: lint + relevant tests + pre-commit"
        # Standard pipeline
        if ! cmd_pre_commit; then overall_status="FAILED"; fi
        if ! cmd_test; then overall_status="FAILED"; fi
    fi

    local end_time=$(date +%s)
    local duration="${((end_time - start_time))}s"

    if [ "$overall_status" = "PASSED" ]; then
        json_output "all" "PASSED" "pipeline" "$duration" "$checks" "$errors" "CI pipeline completed successfully"
        pretty_output "all" "PASSED" "Complete CI pipeline finished successfully"
        return 0
    else
        json_output "all" "FAILED" "pipeline" "$duration" "$checks" "[{\"message\": \"One or more pipeline stages failed\"}]" "Review failures and fix issues"
        pretty_output "all" "FAILED" "CI pipeline failed - review individual stage results"
        return 1
    fi
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    usage
fi

COMMAND=""
TARGET_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        help|--help|-h)
            usage
            ;;
        check|test|pre-commit|review|all)
            COMMAND="$1"
            shift
            ;;
        --fix)
            FIX_MODE=true
            shift
            ;;
        --all)
            ALL_MODE=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --comprehensive)
            COMPREHENSIVE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --pretty)
            JSON_OUTPUT=false
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            ;;
        *)
            if [ "$COMMAND" = "check" ] && [ -z "$TARGET_FILE" ]; then
                TARGET_FILE="$1"
            else
                echo "Unexpected argument: $1" >&2
                usage
            fi
            shift
            ;;
    esac
done

# Validate command
if [ -z "$COMMAND" ]; then
    echo "Error: No command specified" >&2
    usage
fi

# Execute command
case "$COMMAND" in
    check)
        if [ -z "$TARGET_FILE" ]; then
            echo "Error: check command requires a file argument" >&2
            json_output "check" "FAILED" "" "0s" "{}" "[{\"message\": \"No file specified\"}]" "Specify file to check"
            exit 1
        fi
        cmd_check "$TARGET_FILE"
        ;;
    test)
        cmd_test
        ;;
    pre-commit)
        cmd_pre_commit
        ;;
    review)
        cmd_review
        ;;
    all)
        cmd_all
        ;;
    *)
        echo "Error: Unknown command: $COMMAND" >&2
        usage
        ;;
esac
