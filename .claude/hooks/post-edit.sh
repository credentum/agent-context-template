#!/usr/bin/env bash
# post-edit.sh - Claude hook for post-edit validation
# This can be sourced or called after Claude makes edits

# Get the directory where this script is located
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Function to validate files after Claude edits
claude_validate_edits() {
    local files=("$@")

    if [ ${#files[@]} -eq 0 ]; then
        echo "No files specified for validation"
        return 0
    fi

    # Run the validation script
    "$PROJECT_ROOT/scripts/claude-post-edit.sh" "${files[@]}"
    local exit_code=$?

    # If validation failed, suggest auto-fix
    if [ $exit_code -ne 0 ]; then
        echo
        echo "💡 Tip: To automatically fix these issues, run:"
        echo "   ./scripts/claude-post-edit.sh ${files[*]} --fix"
    fi

    return $exit_code
}

# Function to validate and auto-fix files
claude_format_edits() {
    local files=("$@")

    if [ ${#files[@]} -eq 0 ]; then
        echo "No files specified for formatting"
        return 0
    fi

    # Run the validation script with --fix
    "$PROJECT_ROOT/scripts/claude-post-edit.sh" "${files[@]}" --fix
}

# Export functions for use in other scripts
export -f claude_validate_edits
export -f claude_format_edits

# If script is executed directly (not sourced), show usage
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    echo "Claude Post-Edit Hook Functions"
    echo "==============================="
    echo
    echo "This script provides functions for validating files after Claude edits."
    echo
    echo "Usage:"
    echo "  source $0"
    echo "  claude_validate_edits file1.py file2.py  # Validate files"
    echo "  claude_format_edits file1.py file2.py    # Validate and auto-fix"
    echo
    echo "Or use the scripts directly:"
    echo "  ./scripts/claude-post-edit.sh file1.py file2.py [--fix]"
fi
