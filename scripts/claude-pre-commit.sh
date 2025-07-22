#!/bin/bash
# claude-pre-commit.sh - Claude-friendly wrapper for pre-commit
# Provides structured JSON output for better AI agent integration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/context/trace/logs/claude-pre-commit.log"
TEMP_OUTPUT="/tmp/pre-commit-output-$$.txt"

# Default options
FIX_MODE=false
ALL_FILES=true
FILES=()
JSON_OUTPUT=true
VERBOSE=false

# Colors for terminal output (disabled in JSON mode)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [FILES...]

Claude-friendly wrapper for pre-commit that provides structured output.

OPTIONS:
    -h, --help          Show this help message
    -f, --fix           Run auto-fix for fixable issues
    -j, --json          Output in JSON format (default)
    -t, --text          Output in human-readable text format
    -v, --verbose       Include detailed output
    --all-files         Check all files (default if no files specified)

EXAMPLES:
    $0                          # Check all files, JSON output
    $0 --fix                    # Auto-fix all fixable issues
    $0 --text src/module.py     # Check specific file, text output
    $0 --fix --verbose          # Fix with detailed output

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -f|--fix)
            FIX_MODE=true
            shift
            ;;
        -j|--json)
            JSON_OUTPUT=true
            shift
            ;;
        -t|--text)
            JSON_OUTPUT=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --all-files)
            ALL_FILES=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            ;;
        *)
            FILES+=("$1")
            ALL_FILES=false
            shift
            ;;
    esac
done

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Initialize JSON structure
init_json() {
    echo '{'
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"mode\": \"$(if $FIX_MODE; then echo "fix"; else echo "check"; fi)\","
    echo "  \"overall_status\": \"PENDING\","
    echo "  \"checks\": [],"
    echo "  \"files_modified\": [],"
    echo "  \"summary\": {},"
    echo "  \"recommendation\": \"\""
    echo '}'
}

# Parse hook output based on hook type
parse_hook_output() {
    local hook_name="$1"
    local exit_code="$2"
    local output="$3"
    local status="PASSED"
    local files_failed=()
    local issues=()
    local auto_fixable=false
    local fix_command=""

    if [[ $exit_code -ne 0 ]]; then
        status="FAILED"

        case "$hook_name" in
            "black")
                auto_fixable=true
                fix_command="black"
                # Parse files that would be reformatted
                while IFS= read -r line; do
                    if [[ $line =~ ^would\ reformat\ (.+)$ ]]; then
                        files_failed+=("${BASH_REMATCH[1]}")
                    fi
                done <<< "$output"
                ;;

            "isort")
                auto_fixable=true
                fix_command="isort"
                # Parse files with incorrect imports
                while IFS= read -r line; do
                    if [[ $line =~ ^ERROR:\ (.+)\ Imports\ are\ incorrectly\ sorted ]]; then
                        files_failed+=("${BASH_REMATCH[1]}")
                    fi
                done <<< "$output"
                ;;

            "flake8")
                auto_fixable=false
                # Parse flake8 errors: file:line:col: code message
                while IFS= read -r line; do
                    if [[ $line =~ ^(.+):([0-9]+):([0-9]+):\ ([A-Z][0-9]+)\ (.+)$ ]]; then
                        local file="${BASH_REMATCH[1]}"
                        local line_num="${BASH_REMATCH[2]}"
                        local col="${BASH_REMATCH[3]}"
                        local code="${BASH_REMATCH[4]}"
                        local message="${BASH_REMATCH[5]}"

                        # Provide fix guidance based on error code
                        local fix_guidance=""
                        case "$code" in
                            E501) fix_guidance="Break line at logical point or use parentheses for implicit continuation" ;;
                            W291) fix_guidance="Remove trailing whitespace" ;;
                            E302) fix_guidance="Add blank line before function/class definition" ;;
                            F401) fix_guidance="Remove unused import" ;;
                            *) fix_guidance="Refer to flake8 documentation for $code" ;;
                        esac

                        issues+=("{\"file\": \"$file\", \"line\": $line_num, \"column\": $col, \"code\": \"$code\", \"message\": \"$message\", \"fix_guidance\": \"$fix_guidance\"}")
                    fi
                done <<< "$output"
                ;;

            "mypy")
                auto_fixable=false
                # Parse mypy errors: file:line: error: message
                while IFS= read -r line; do
                    if [[ $line =~ ^(.+):([0-9]+):\ error:\ (.+)$ ]]; then
                        local file="${BASH_REMATCH[1]}"
                        local line_num="${BASH_REMATCH[2]}"
                        local message="${BASH_REMATCH[3]}"
                        issues+=("{\"file\": \"$file\", \"line\": $line_num, \"type\": \"error\", \"message\": \"$message\"}")
                    fi
                done <<< "$output"
                ;;

            "trailing-whitespace"|"end-of-file-fixer"|"mixed-line-ending")
                auto_fixable=true
                # These hooks just list files they would fix
                while IFS= read -r line; do
                    if [[ $line =~ ^Fixing\ (.+)$ ]] || [[ $line =~ ^(.+)$ && ! $line =~ ^(Trim|Fix|Pass|Fail) ]]; then
                        local file="${BASH_REMATCH[1]}"
                        [[ -n "$file" && -f "$file" ]] && files_failed+=("$file")
                    fi
                done <<< "$output"
                ;;
        esac
    fi

    # Build JSON for this check
    echo -n "{\"hook\": \"$hook_name\", \"status\": \"$status\""

    if [[ ${#files_failed[@]} -gt 0 ]]; then
        echo -n ", \"files_failed\": ["
        local first=true
        for file in "${files_failed[@]}"; do
            if ! $first; then echo -n ", "; fi
            echo -n "\"$file\""
            first=false
        done
        echo -n "]"
    fi

    if [[ ${#issues[@]} -gt 0 ]]; then
        echo -n ", \"issues\": ["
        local first=true
        for issue in "${issues[@]}"; do
            if ! $first; then echo -n ", "; fi
            echo -n "$issue"
            first=false
        done
        echo -n "]"
    fi

    echo -n ", \"auto_fixable\": $auto_fixable"

    if [[ -n "$fix_command" ]]; then
        echo -n ", \"fix_command\": \"$fix_command\""
    fi

    echo -n "}"
}

# Run pre-commit and capture output
run_pre_commit() {
    local args=()

    if $ALL_FILES; then
        args+=("--all-files")
    else
        args+=("--files" "${FILES[@]}")
    fi

    # Run pre-commit and capture output
    local exit_code=0
    if $VERBOSE; then
        pre-commit run "${args[@]}" 2>&1 | tee "$TEMP_OUTPUT" || exit_code=$?
    else
        pre-commit run "${args[@]}" &> "$TEMP_OUTPUT" || exit_code=$?
    fi

    return $exit_code
}

# Extract individual hook results from pre-commit output
extract_hook_results() {
    local output_file="$1"
    local current_hook=""
    local hook_output=""
    local hook_status=0
    local results=()

    while IFS= read -r line; do
        # Detect hook header lines
        if [[ $line =~ ^([a-z0-9-]+)\.+\.(Passed|Failed|Skipped)$ ]]; then
            # Process previous hook if any
            if [[ -n "$current_hook" ]]; then
                local json_result=$(parse_hook_output "$current_hook" "$hook_status" "$hook_output")
                results+=("$json_result")
            fi

            # Start new hook
            current_hook="${BASH_REMATCH[1]}"
            hook_status=$(if [[ "${BASH_REMATCH[2]}" == "Failed" ]]; then echo 1; else echo 0; fi)
            hook_output=""
        elif [[ -n "$current_hook" ]]; then
            hook_output+="$line"$'\n'
        fi
    done < "$output_file"

    # Process last hook
    if [[ -n "$current_hook" ]]; then
        local json_result=$(parse_hook_output "$current_hook" "$hook_status" "$hook_output")
        results+=("$json_result")
    fi

    # Output results
    local first=true
    for result in "${results[@]}"; do
        if ! $first; then echo -n ", "; fi
        echo -n "$result"
        first=false
    done
}

# Get list of modified files after auto-fix
get_modified_files() {
    git diff --name-only 2>/dev/null || true
}

# Main execution
main() {
    local start_time=$(date +%s)

    # Check if pre-commit is installed
    if ! command -v pre-commit &> /dev/null; then
        if $JSON_OUTPUT; then
            cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "overall_status": "ERROR",
  "error": "pre-commit is not installed",
  "recommendation": "Install pre-commit with: pip install pre-commit"
}
EOF
        else
            echo -e "${RED}Error: pre-commit is not installed${NC}" >&2
            echo "Install with: pip install pre-commit" >&2
        fi
        exit 1
    fi

    # Store initial modified files for comparison
    local initial_modified_files=()
    if $FIX_MODE; then
        mapfile -t initial_modified_files < <(get_modified_files)
    fi

    # Run pre-commit
    local overall_exit_code=0
    run_pre_commit || overall_exit_code=$?

    # Parse results
    local checks_json=$(extract_hook_results "$TEMP_OUTPUT")

    # Get modified files if in fix mode
    local files_modified_json="[]"
    if $FIX_MODE; then
        local current_modified_files=()
        mapfile -t current_modified_files < <(get_modified_files)

        # Find newly modified files
        local newly_modified=()
        for file in "${current_modified_files[@]}"; do
            local found=false
            for initial_file in "${initial_modified_files[@]}"; do
                if [[ "$file" == "$initial_file" ]]; then
                    found=true
                    break
                fi
            done
            if ! $found; then
                newly_modified+=("$file")
            fi
        done

        if [[ ${#newly_modified[@]} -gt 0 ]]; then
            files_modified_json="["
            local first=true
            for file in "${newly_modified[@]}"; do
                if ! $first; then files_modified_json+=", "; fi
                files_modified_json+="{\"path\": \"$file\", \"changes\": \"Auto-formatted by pre-commit\"}"
                first=false
            done
            files_modified_json+="]"
        fi
    fi

    # Calculate summary
    local total_checks=$(echo "$checks_json" | grep -o '"hook"' | wc -l)
    local passed_checks=$(echo "$checks_json" | grep -o '"status": "PASSED"' | wc -l)
    local failed_checks=$((total_checks - passed_checks))
    local auto_fixable=$(echo "$checks_json" | grep -o '"auto_fixable": true' | wc -l)

    # Determine overall status
    local overall_status="PASSED"
    if [[ $overall_exit_code -ne 0 ]]; then
        overall_status="FAILED"
    fi

    # Generate recommendation
    local recommendation=""
    if [[ $overall_status == "FAILED" ]]; then
        if [[ $auto_fixable -gt 0 ]] && ! $FIX_MODE; then
            recommendation="Run with --fix to automatically fix $auto_fixable issue(s), then manually fix remaining issues"
        elif $FIX_MODE && [[ $failed_checks -gt 0 ]]; then
            recommendation="Some issues remain after auto-fix. Review and manually fix remaining issues"
        else
            recommendation="Review and fix the reported issues manually"
        fi
    else
        recommendation="All checks passed. Code is ready to commit"
    fi

    # Log the run
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | Mode: $(if $FIX_MODE; then echo "fix"; else echo "check"; fi) | Status: $overall_status | Duration: ${duration}s | Checks: $total_checks | Failed: $failed_checks" >> "$LOG_FILE"

    # Output results
    if $JSON_OUTPUT; then
        cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "mode": "$(if $FIX_MODE; then echo "fix"; else echo "check"; fi)",
  "overall_status": "$overall_status",
  "checks": [$checks_json],
  "files_modified": $files_modified_json,
  "summary": {
    "total_checks": $total_checks,
    "passed": $passed_checks,
    "failed": $failed_checks,
    "auto_fixable": $auto_fixable,
    "duration_seconds": $duration
  },
  "recommendation": "$recommendation"
}
EOF
    else
        # Text output
        echo -e "\n${GREEN}Pre-commit Check Results${NC}"
        echo "========================"
        echo "Mode: $(if $FIX_MODE; then echo "Fix"; else echo "Check"; fi)"
        echo "Overall Status: $(if [[ $overall_status == "PASSED" ]]; then echo -e "${GREEN}PASSED${NC}"; else echo -e "${RED}FAILED${NC}"; fi)"
        echo "Total Checks: $total_checks"
        echo "Passed: $passed_checks"
        echo "Failed: $failed_checks"
        echo "Auto-fixable: $auto_fixable"
        echo "Duration: ${duration}s"
        echo
        echo "Recommendation: $recommendation"

        if [[ $FIX_MODE ]] && [[ "$files_modified_json" != "[]" ]]; then
            echo -e "\n${YELLOW}Files Modified:${NC}"
            if command -v jq &> /dev/null; then
                echo "$files_modified_json" | jq -r '.[] | "  - \(.path)"'
            else
                # Fallback without jq - basic parsing
                echo "$files_modified_json" | grep -o '"path": "[^"]*"' | cut -d'"' -f4 | sed 's/^/  - /'
            fi
        fi
    fi

    # Clean up
    rm -f "$TEMP_OUTPUT"

    # Exit with appropriate code
    exit $overall_exit_code
}

# Run main function
main "$@"
