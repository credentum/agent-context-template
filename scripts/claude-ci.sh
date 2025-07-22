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
GITHUB_OUTPUT=false

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
  --github-output Enable GitHub Actions output format
  --verbose      Show detailed output

Examples:
  claude-ci check src/main.py
  claude-ci test --all
  claude-ci pre-commit --fix
  claude-ci all --quick --github-output
  claude-ci review --comprehensive

Progressive Validation Modes:
  --quick        Format check, basic lint, minimal tests (seconds)
  (default)      Full lint, relevant tests, pre-commit (minutes)
  --comprehensive Everything including full tests, coverage, review (full)

EOF
    exit 0
}

# GitHub Actions output helper
github_actions_output() {
    local status="$1"
    local command="$2"
    local target="${3:-all}"
    local checks="${4:-{}}"
    local errors="${5:-[]}"
    
    if [ "$GITHUB_OUTPUT" = true ]; then
        # Set GitHub Actions step outputs
        if [ -n "${GITHUB_OUTPUT_FILE:-}" ]; then
            echo "status=${status}" >> "${GITHUB_OUTPUT_FILE}"
            echo "command=${command}" >> "${GITHUB_OUTPUT_FILE}"
            echo "target=${target}" >> "${GITHUB_OUTPUT_FILE}"
        elif [ -n "${GITHUB_OUTPUT:-}" ] && [ "$GITHUB_OUTPUT" != "true" ]; then
            echo "status=${status}" >> "${GITHUB_OUTPUT}"
            echo "command=${command}" >> "${GITHUB_OUTPUT}"
            echo "target=${target}" >> "${GITHUB_OUTPUT}"
        else
            # Use modern GitHub Actions output format (only if GITHUB_OUTPUT is set)
            if [ -n "${GITHUB_OUTPUT:-}" ]; then
                echo "status=${status}" >> "${GITHUB_OUTPUT}"
                echo "command=${command}" >> "${GITHUB_OUTPUT}"
                echo "target=${target}" >> "${GITHUB_OUTPUT}"
            fi
        fi
        
        # Set summary for GitHub Actions UI
        if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
            case "$status" in
                "PASSED")
                    echo "✅ **${command}** completed successfully" >> "$GITHUB_STEP_SUMMARY"
                    ;;
                "FAILED")
                    echo "❌ **${command}** failed" >> "$GITHUB_STEP_SUMMARY"
                    if [ "$errors" != "[]" ]; then
                        echo "" >> "$GITHUB_STEP_SUMMARY"
                        echo "**Errors:**" >> "$GITHUB_STEP_SUMMARY"
                        echo "\`\`\`" >> "$GITHUB_STEP_SUMMARY"
                        echo "$errors" | jq -r '.[] | "- " + (.message // .error // .)' 2>/dev/null || echo "- Check logs for details" >> "$GITHUB_STEP_SUMMARY"
                        echo "\`\`\`" >> "$GITHUB_STEP_SUMMARY"
                    fi
                    ;;
            esac
        fi
        
        # Add annotations for errors (visible in PR checks)
        if [ "$status" = "FAILED" ] && [ "$errors" != "[]" ]; then
            echo "$errors" | jq -r '.[] | select(.file and .line) | "::error file=\(.file),line=\(.line)::\(.message // .error // "Check failed")"' 2>/dev/null || true
        fi
    fi
}

# JSON output helper - robust JSON generation using jq
json_output() {
    local command="$1"
    local status="$2"
    local target="${3:-all}"
    local duration="${4:-0s}"
    local checks="${5:-{}}"
    local errors="${6:-[]}"
    local next_action="${7:-No action needed}"

    # Validate JSON inputs and ensure proper formatting
    if ! echo "$checks" | jq empty 2>/dev/null; then
        checks="{}"
    fi
    if ! echo "$errors" | jq empty 2>/dev/null; then
        errors="[]"
    fi

    # Add GitHub Actions output if enabled
    github_actions_output "$status" "$command" "$target" "$checks" "$errors"

    if [ "$JSON_OUTPUT" = true ]; then
        # Use jq to ensure proper JSON formatting
        jq -n \
            --arg command "$command" \
            --arg status "$status" \
            --arg target "$target" \
            --arg duration "$duration" \
            --argjson checks "$checks" \
            --argjson errors "$errors" \
            --arg next_action "$next_action" \
            '{
                "command": $command,
                "status": $status,
                "target": $target,
                "duration": $duration,
                "checks": $checks,
                "errors": $errors,
                "next_action": $next_action
            }'
    fi
}

# Dependency check helper
check_script_dependency() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"

    if [ ! -f "$script_path" ]; then
        return 1
    fi

    if [ ! -x "$script_path" ]; then
        return 2  # Exists but not executable
    fi

    return 0
}

# Get dependency error message
get_dependency_error() {
    local script_name="$1"
    local check_result="$2"

    case $check_result in
        1)
            echo "Script $script_name not found in $SCRIPT_DIR"
            ;;
        2)
            echo "Script $script_name exists but is not executable. Run: chmod +x $SCRIPT_DIR/$script_name"
            ;;
        *)
            echo "Unknown dependency error for $script_name"
            ;;
    esac
}
# File path validation helper
validate_file_path() {
    local file="$1"

    # Check for empty path
    if [ -z "$file" ]; then
        return 1
    fi

    # Convert to absolute path and validate it's within project
    local abs_path
    abs_path=$(realpath "$file" 2>/dev/null) || return 1
    local project_path
    project_path=$(realpath "$PROJECT_ROOT" 2>/dev/null) || return 1

    # Ensure path is within project boundaries
    case "$abs_path" in
        "$project_path"*)
            # Path is within project - additional security checks
            # Reject paths with suspicious patterns
            case "$file" in
                */../*|../*|*/..*)
                    return 1 ;;
                */proc/*|*/sys/*|*/dev/*)
                    return 1 ;;
                *)
                    return 0 ;;
            esac
            ;;
        *)
            # Path is outside project
            return 1 ;;
    esac
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

    # Validate file path for security
    if ! validate_file_path "$file"; then
        json_output "check" "FAILED" "$file" "0s" "{}" "[{\"message\": \"Invalid file path: $file\", \"details\": \"Path must be within project directory and not contain directory traversal patterns\"}]" "Use a valid file path within the project"
        pretty_output "check" "FAILED" "Invalid file path: $file"
        return 1
    fi

    if [ ! -f "$file" ]; then
        json_output "check" "FAILED" "$file" "0s" "{}" "[{\"message\": \"File not found: $file\"}]" "Verify file path"
        pretty_output "check" "FAILED" "File not found: $file"
        return 1
    fi

    # Dependencies already validated at startup

    # Delegate to claude-post-edit.sh
    local fix_flag=""
    if [ "$FIX_MODE" = true ]; then
        fix_flag="--fix"
    fi

    local end_time=$(date +%s)
    local duration="$((end_time - start_time))s"

    if "$SCRIPT_DIR/claude-post-edit.sh" "$file" $fix_flag > /dev/null 2>&1; then
        json_output "check" "PASSED" "$file" "$duration" "{\"format\": \"PASSED\", \"lint\": \"PASSED\"}" "[]" "File validation successful"
        pretty_output "check" "PASSED" "File validation successful: $file"
        return 0
    else
        json_output "check" "FAILED" "$file" "$duration" "{\"format\": \"FAILED\"}" "[{\"message\": \"Validation failed\", \"fix\": \"Run: claude-ci check $file --fix\"}]" "Fix issues and run again"
        pretty_output "check" "FAILED" "File validation failed: $file"
        return 1
    fi
}

# Test command - run tests
cmd_test() {
    local start_time=$(date +%s)

    # Dependencies already validated at startup
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
    local duration="$((end_time - start_time))s"

    if "$SCRIPT_DIR/claude-test-changed.sh" $test_args; then
        json_output "test" "PASSED" "smart" "$duration" "{\"tests\": \"PASSED\"}" "[]" "All tests passed"
        pretty_output "test" "PASSED" "Tests completed successfully"
        return 0
    else
        json_output "test" "FAILED" "smart" "$duration" "{\"tests\": \"FAILED\"}" "[{\"message\": \"Some tests failed\"}]" "Review test failures"
        pretty_output "test" "FAILED" "Some tests failed"
        return 1
    fi
}

# Pre-commit command
cmd_pre_commit() {
    local start_time=$(date +%s)

    # Dependencies already validated at startup
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
    local duration="$((end_time - start_time))s"

    if "$SCRIPT_DIR/claude-pre-commit.sh" $precommit_args; then
        json_output "pre-commit" "PASSED" "all" "$duration" "{\"pre-commit\": \"PASSED\"}" "[]" "Pre-commit checks passed"
        pretty_output "pre-commit" "PASSED" "All pre-commit checks passed"
        return 0
    else
        json_output "pre-commit" "FAILED" "all" "$duration" "{\"pre-commit\": \"FAILED\"}" "[{\"message\": \"Pre-commit checks failed\"}]" "Fix issues and run again"
        pretty_output "pre-commit" "FAILED" "Pre-commit checks failed"
        return 1
    fi
}

# Review command - local PR review simulation
cmd_review() {
    local start_time=$(date +%s)

    # Dependencies already validated at startup
    # Use comprehensive checks instead of Docker in CI environment
    local overall_status="PASSED"
    local checks_json="{"
    local errors_json="["
    local first_check=true
    local first_error=true
    
    # Don't output pretty messages in JSON mode to avoid contaminating JSON output
    if [ "$JSON_OUTPUT" = false ]; then
        pretty_output "review" "INFO" "Running comprehensive PR review simulation..."
    fi
    
    # Run pre-commit checks
    if cmd_pre_commit > /dev/null 2>&1; then
        if [ "$first_check" = true ]; then
            checks_json="${checks_json}\"pre-commit\": \"PASSED\""
            first_check=false
        else
            checks_json="${checks_json}, \"pre-commit\": \"PASSED\""
        fi
    else
        overall_status="FAILED"
        if [ "$first_check" = true ]; then
            checks_json="${checks_json}\"pre-commit\": \"FAILED\""
            first_check=false
        else
            checks_json="${checks_json}, \"pre-commit\": \"FAILED\""
        fi
        if [ "$first_error" = true ]; then
            errors_json="${errors_json}{\"stage\": \"pre-commit\", \"message\": \"Pre-commit checks failed\"}"
            first_error=false
        else
            errors_json="${errors_json}, {\"stage\": \"pre-commit\", \"message\": \"Pre-commit checks failed\"}"
        fi
    fi
    
    # Run test suite
    if cmd_test > /dev/null 2>&1; then
        if [ "$first_check" = true ]; then
            checks_json="${checks_json}\"tests\": \"PASSED\""
            first_check=false
        else
            checks_json="${checks_json}, \"tests\": \"PASSED\""
        fi
    else
        overall_status="FAILED"
        if [ "$first_check" = true ]; then
            checks_json="${checks_json}\"tests\": \"FAILED\""
            first_check=false
        else
            checks_json="${checks_json}, \"tests\": \"FAILED\""
        fi
        if [ "$first_error" = true ]; then
            errors_json="${errors_json}{\"stage\": \"tests\", \"message\": \"Test suite failed\"}"
            first_error=false
        else
            errors_json="${errors_json}, {\"stage\": \"tests\", \"message\": \"Test suite failed\"}"
        fi
    fi
    
    checks_json="${checks_json}}"
    errors_json="${errors_json}]"

    local end_time=$(date +%s)
    local duration="$((end_time - start_time))s"
    local next_action="PR review simulation completed successfully"
    
    if [ "$overall_status" = "FAILED" ]; then
        next_action="Fix failed checks before PR submission"
    fi

    json_output "review" "$overall_status" "all" "$duration" "$checks_json" "$errors_json" "$next_action"

    if [ "$overall_status" = "PASSED" ]; then
        pretty_output "review" "PASSED" "PR review simulation completed successfully"
        return 0
    else
        pretty_output "review" "FAILED" "PR review found issues that need fixing"
        return 1
    fi
}

# All command - complete CI pipeline with detailed error aggregation
cmd_all() {
    local start_time=$(date +%s)
    local overall_status="PASSED"
    local checks_json="{"
    local errors_json="["
    local stages_run=""
    local first_check=true
    local first_error=true
    local temp_files=()

    # Cleanup trap for temporary files
    cleanup_temp_files() {
        for temp_file in "${temp_files[@]}"; do
            if [ -f "$temp_file" ]; then
                rm -f "$temp_file"
            fi
        done
    }
    trap cleanup_temp_files EXIT

    # Don't output pretty messages in JSON mode to avoid contaminating JSON output
    if [ "$JSON_OUTPUT" = false ]; then
        pretty_output "all" "INFO" "Running complete CI pipeline..."
    fi

    # Helper function to capture command output and status
    run_stage() {
        local stage_name="$1"
        local stage_func="$2"
        local temp_output
        local stage_result

        # Don't output pretty messages in JSON mode to avoid contaminating JSON output
        if [ "$JSON_OUTPUT" = false ]; then
            pretty_output "all" "INFO" "Running stage: $stage_name"
        fi
        stages_run="$stages_run $stage_name"

        # Capture output from stage with secure temp file
        temp_output=$(mktemp -t "claude-ci-${stage_name}-XXXXXX")
        temp_files+=("$temp_output")
        set +e  # Allow failures temporarily
        $stage_func >"$temp_output" 2>&1
        stage_result=$?
        set -e

        # Parse stage output if it's JSON
        if [ -s "$temp_output" ] && head -1 "$temp_output" | grep -q "^{"; then
            local stage_output
            stage_output=$(cat "$temp_output")

            # Extract checks and errors from stage output
            if echo "$stage_output" | jq empty 2>/dev/null; then
                local stage_checks stage_errors
                stage_checks=$(echo "$stage_output" | jq -c '.checks // {}')
                stage_errors=$(echo "$stage_output" | jq -c '.errors // []')

                # Add to aggregated checks
                if [ "$first_check" = true ]; then
                    checks_json="$checks_json\"$stage_name\": $stage_checks"
                    first_check=false
                else
                    checks_json="$checks_json, \"$stage_name\": $stage_checks"
                fi

                # Add to aggregated errors
                if [ "$stage_errors" != "[]" ]; then
                    if [ "$first_error" = true ]; then
                        errors_json="$errors_json{\"stage\": \"$stage_name\", \"details\": $stage_errors}"
                        first_error=false
                    else
                        errors_json="$errors_json, {\"stage\": \"$stage_name\", \"details\": $stage_errors}"
                    fi
                fi
            fi
        fi

        rm -f "$temp_output"

        if [ $stage_result -ne 0 ]; then
            overall_status="FAILED"
            if [ "$first_error" = true ]; then
                errors_json="$errors_json{\"stage\": \"$stage_name\", \"message\": \"Stage failed with exit code $stage_result\"}"
                first_error=false
            else
                errors_json="$errors_json, {\"stage\": \"$stage_name\", \"message\": \"Stage failed with exit code $stage_result\"}"
            fi
        fi

        return $stage_result
    }

    # Progressive validation based on mode
    if [ "$QUICK" = true ]; then
        if [ "$JSON_OUTPUT" = false ]; then
            pretty_output "all" "INFO" "Quick mode: format check + basic lint"
        fi
        run_stage "pre-commit" "cmd_pre_commit" || true
    elif [ "$COMPREHENSIVE" = true ]; then
        if [ "$JSON_OUTPUT" = false ]; then
            pretty_output "all" "INFO" "Comprehensive mode: full validation suite"
        fi
        run_stage "pre-commit" "cmd_pre_commit" || true
        run_stage "test" "cmd_test" || true
        run_stage "review" "cmd_review" || true
    else
        if [ "$JSON_OUTPUT" = false ]; then
            pretty_output "all" "INFO" "Standard mode: lint + relevant tests + pre-commit"
        fi
        run_stage "pre-commit" "cmd_pre_commit" || true
        run_stage "test" "cmd_test" || true
    fi

    # Close JSON objects
    checks_json="$checks_json}"
    errors_json="$errors_json]"

    local end_time=$(date +%s)
    local duration="$((end_time - start_time))s"
    local next_action="CI pipeline completed successfully"

    if [ "$overall_status" = "FAILED" ]; then
        next_action="Review failed stages:$stages_run. Check individual stage outputs for details."
    fi

    json_output "all" "$overall_status" "pipeline" "$duration" "$checks_json" "$errors_json" "$next_action"

    if [ "$overall_status" = "PASSED" ]; then
        pretty_output "all" "PASSED" "Complete CI pipeline finished successfully"
        return 0
    else
        pretty_output "all" "FAILED" "CI pipeline failed - stages run:$stages_run"
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
        --github-output)
            GITHUB_OUTPUT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            if [ "$COMMAND" = "check" ] && [ -z "$TARGET_FILE" ]; then
                TARGET_FILE="$1"
            elif [ -z "$COMMAND" ]; then
                # This is likely an invalid command
                echo "Unknown command: $1" >&2
                exit 1
            else
                echo "Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate command
if [ -z "$COMMAND" ]; then
    echo "Error: No command specified" >&2
    exit 1
fi

# Early dependency validation for better user experience
validate_dependencies() {
    local dependencies=()

    case "$COMMAND" in
        check)
            dependencies+=("claude-post-edit.sh")
            ;;
        test)
            dependencies+=("claude-test-changed.sh")
            ;;
        pre-commit)
            dependencies+=("claude-pre-commit.sh")
            ;;
        review)
            # Review uses pre-commit and test commands, no Docker required
            dependencies+=("claude-pre-commit.sh" "claude-test-changed.sh")
            ;;
        all)
            # All command needs multiple dependencies, Docker optional for review
            dependencies+=("claude-post-edit.sh" "claude-test-changed.sh" "claude-pre-commit.sh")
            ;;
    esac

    # Check all required dependencies upfront
    for script_name in "${dependencies[@]}"; do
        if ! check_script_dependency "$script_name"; then
            local check_result=$?
            local error_msg
            error_msg=$(get_dependency_error "$script_name" $check_result)
            json_output "$COMMAND" "FAILED" "" "0s" "{}" "[{\"message\": \"$error_msg\", \"dependency\": \"$script_name\"}]" "Install missing dependency script"
            pretty_output "$COMMAND" "FAILED" "$error_msg"
            exit 1
        fi
    done
}

# Run dependency validation early
validate_dependencies

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
        echo "Unknown command: $COMMAND" >&2
        exit 1
        ;;
esac
