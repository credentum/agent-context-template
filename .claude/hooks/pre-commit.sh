#!/bin/bash
# .claude/hooks/pre-commit.sh - Claude hook integration for pre-commit wrapper
# Source this file to use helper functions in Claude sessions

# Get the directory of this script
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Path to the claude-pre-commit wrapper
CLAUDE_PRE_COMMIT="$PROJECT_ROOT/scripts/claude-pre-commit.sh"

# Helper function to run pre-commit checks with Claude-friendly output
claude_pre_commit_check() {
    local files=("$@")

    echo "Running pre-commit checks..."

    if [[ ${#files[@]} -eq 0 ]]; then
        # Check all files
        "$CLAUDE_PRE_COMMIT" --json --all-files
    else
        # Check specific files
        "$CLAUDE_PRE_COMMIT" --json "${files[@]}"
    fi
}

# Helper function to auto-fix pre-commit issues
claude_pre_commit_fix() {
    local files=("$@")

    echo "Running pre-commit auto-fix..."

    if [[ ${#files[@]} -eq 0 ]]; then
        # Fix all files
        "$CLAUDE_PRE_COMMIT" --json --fix --all-files
    else
        # Fix specific files
        "$CLAUDE_PRE_COMMIT" --json --fix "${files[@]}"
    fi
}

# Helper function to check if files need pre-commit fixes
claude_needs_pre_commit_fix() {
    local files=("$@")

    # Run check silently and return exit code
    if [[ ${#files[@]} -eq 0 ]]; then
        "$CLAUDE_PRE_COMMIT" --json --all-files > /dev/null 2>&1
    else
        "$CLAUDE_PRE_COMMIT" --json "${files[@]}" > /dev/null 2>&1
    fi

    return $?
}

# Function to parse pre-commit results and suggest next actions
claude_pre_commit_suggest() {
    local result_json="$1"

    # Parse the JSON to extract key information
    local overall_status=$(echo "$result_json" | jq -r '.overall_status')
    local failed_checks=$(echo "$result_json" | jq -r '.summary.failed')
    local auto_fixable=$(echo "$result_json" | jq -r '.summary.auto_fixable')
    local recommendation=$(echo "$result_json" | jq -r '.recommendation')

    echo "Pre-commit Status: $overall_status"
    echo "Failed Checks: $failed_checks"
    echo "Auto-fixable: $auto_fixable"
    echo ""
    echo "Recommendation: $recommendation"

    # Provide specific commands based on status
    if [[ "$overall_status" == "FAILED" ]] && [[ $auto_fixable -gt 0 ]]; then
        echo ""
        echo "To auto-fix issues, run:"
        echo "  claude_pre_commit_fix"
    fi
}

# Function to run pre-commit before committing
claude_safe_commit() {
    local message="$1"
    shift
    local files=("$@")

    echo "Checking files before commit..."

    # Run pre-commit check
    local result=$(claude_pre_commit_check "${files[@]}")
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        echo "All checks passed! Proceeding with commit..."
        if [[ ${#files[@]} -eq 0 ]]; then
            git commit -m "$message"
        else
            git commit -m "$message" "${files[@]}"
        fi
    else
        echo "Pre-commit checks failed!"
        echo "$result" | jq .

        # Check if auto-fixable
        local auto_fixable=$(echo "$result" | jq -r '.summary.auto_fixable')
        if [[ $auto_fixable -gt 0 ]]; then
            echo ""
            echo "Would you like to auto-fix the issues? Run:"
            echo "  claude_pre_commit_fix"
            echo "Then try committing again."
        else
            echo ""
            echo "Please fix the issues manually and try again."
        fi

        return 1
    fi
}

# Function to validate files after editing
claude_validate_after_edit() {
    local files=("$@")

    echo "Validating edited files..."

    # First run the post-edit validation if available
    if [[ -f "$HOOK_DIR/post-edit.sh" ]]; then
        source "$HOOK_DIR/post-edit.sh"
        claude_validate_edits "${files[@]}"
    fi

    # Then run pre-commit checks
    echo ""
    echo "Running pre-commit checks..."
    local result=$(claude_pre_commit_check "${files[@]}")
    local exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        echo "Pre-commit issues found:"
        echo "$result" | jq -r '.recommendation'

        # Suggest auto-fix if available
        local auto_fixable=$(echo "$result" | jq -r '.summary.auto_fixable')
        if [[ $auto_fixable -gt 0 ]]; then
            echo ""
            echo "Run claude_pre_commit_fix to auto-fix $auto_fixable issue(s)"
        fi
    else
        echo "All pre-commit checks passed!"
    fi

    return $exit_code
}

# Provide usage information
claude_pre_commit_help() {
    cat << EOF
Claude Pre-commit Helper Functions:

  claude_pre_commit_check [files...]
    Run pre-commit checks on specified files (or all files if none specified)
    Returns structured JSON output for easy parsing

  claude_pre_commit_fix [files...]
    Auto-fix pre-commit issues where possible
    Shows what files were modified

  claude_needs_pre_commit_fix [files...]
    Silently check if files need pre-commit fixes
    Returns 0 if all checks pass, non-zero otherwise

  claude_pre_commit_suggest <json_result>
    Parse pre-commit results and suggest next actions

  claude_safe_commit <message> [files...]
    Run pre-commit checks before committing
    Only commits if all checks pass

  claude_validate_after_edit <files...>
    Validate files after editing (combines post-edit and pre-commit)

  claude_pre_commit_help
    Show this help message

Examples:
  # Check all files
  claude_pre_commit_check

  # Auto-fix issues in specific files
  claude_pre_commit_fix src/module.py tests/test_module.py

  # Safe commit with validation
  claude_safe_commit "feat: add new feature" src/module.py

  # Validate after editing
  claude_validate_after_edit src/module.py
EOF
}

# Export functions for use
export -f claude_pre_commit_check
export -f claude_pre_commit_fix
export -f claude_needs_pre_commit_fix
export -f claude_pre_commit_suggest
export -f claude_safe_commit
export -f claude_validate_after_edit
export -f claude_pre_commit_help

# Print available functions when sourced
echo "Claude pre-commit helper functions loaded. Run 'claude_pre_commit_help' for usage."
