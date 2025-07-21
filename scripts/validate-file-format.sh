#!/usr/bin/env bash
# validate-file-format.sh - Validate and optionally fix formatting for a single file
# Usage: ./validate-file-format.sh <file_path> [--fix]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if file path is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <file_path> [--fix]"
    exit 1
fi

FILE_PATH="$1"
FIX_MODE=false

# Check for --fix flag
if [ "${2:-}" = "--fix" ]; then
    FIX_MODE=true
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "CLAUDE_FORMAT_CHECK:START"
    echo "status: error"
    echo "file: $FILE_PATH"
    echo "error: File not found"
    echo "CLAUDE_FORMAT_CHECK:END"
    exit 1
fi

# Initialize counters
ISSUES_FOUND=0
AUTO_FIXED=0
REMAINING_ISSUES=0
DETAILS=""

# Function to add issue detail
add_detail() {
    local type="$1"
    local message="$2"
    DETAILS="${DETAILS}  - type: ${type}\n    message: ${message}\n"
}

# Get file extension
EXTENSION="${FILE_PATH##*.}"
FILENAME=$(basename "$FILE_PATH")

# Start structured output
echo "CLAUDE_FORMAT_CHECK:START"

# Show fix mode message if enabled
if $FIX_MODE; then
    echo "Fixing $FILE_PATH"
fi

# Python file handling
if [[ "$EXTENSION" == "py" ]]; then
    # Check if in virtual environment or use project Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    # Black formatting check
    if command -v black >/dev/null 2>&1; then
        if $FIX_MODE; then
            if ! black --line-length 100 --quiet "$FILE_PATH" 2>/dev/null; then
                ((AUTO_FIXED++)) || true
                add_detail "black" "Reformatted with Black"
            fi
        else
            if ! black --line-length 100 --check --quiet "$FILE_PATH" 2>/dev/null; then
                ((ISSUES_FOUND++)) || true
                ((REMAINING_ISSUES++)) || true
                add_detail "black" "File needs Black formatting"
            fi
        fi
    fi

    # isort import sorting check
    if command -v isort >/dev/null 2>&1; then
        if $FIX_MODE; then
            if ! isort --profile black --line-length 100 --check-only "$FILE_PATH" 2>/dev/null; then
                isort --profile black --line-length 100 "$FILE_PATH" 2>/dev/null
                ((AUTO_FIXED++)) || true
                add_detail "isort" "Import order fixed with isort"
            fi
        else
            if ! isort --profile black --line-length 100 --check-only "$FILE_PATH" 2>/dev/null; then
                ((ISSUES_FOUND++)) || true
                ((REMAINING_ISSUES++)) || true
                add_detail "isort" "Import order needs fixing"
            fi
        fi
    fi

    # Flake8 linting check
    if command -v flake8 >/dev/null 2>&1; then
        FLAKE8_OUTPUT=$(flake8 --max-line-length=100 --extend-ignore=E203,W503 "$FILE_PATH" 2>&1 || true)
        if [ -n "$FLAKE8_OUTPUT" ]; then
            ((ISSUES_FOUND++)) || true
            ((REMAINING_ISSUES++)) || true
            # Extract first error for detail
            FIRST_ERROR=$(echo "$FLAKE8_OUTPUT" | head -n1)
            add_detail "flake8" "Linting issues: $FIRST_ERROR"
        fi
    fi

    # Type checking with mypy (informational only)
    if command -v mypy >/dev/null 2>&1; then
        MYPY_OUTPUT=$(mypy --ignore-missing-imports --no-error-summary "$FILE_PATH" 2>&1 || true)
        if [ -n "$MYPY_OUTPUT" ] && [[ ! "$MYPY_OUTPUT" =~ "Success: no issues found" ]]; then
            # Don't count as blocking issue, just informational
            add_detail "mypy" "Type hints could be improved (non-blocking)"
        fi
    fi

# YAML file handling
elif [[ "$EXTENSION" == "yaml" ]] || [[ "$EXTENSION" == "yml" ]]; then
    if command -v yamllint >/dev/null 2>&1; then
        YAMLLINT_OUTPUT=$(yamllint -c .yamllint "$FILE_PATH" 2>&1 || true)
        if [ -n "$YAMLLINT_OUTPUT" ]; then
            ((ISSUES_FOUND++)) || true
            ((REMAINING_ISSUES++)) || true
            FIRST_ERROR=$(echo "$YAMLLINT_OUTPUT" | head -n1)
            add_detail "yamllint" "YAML formatting issues: $FIRST_ERROR"
        fi
    fi

# Shell script handling
elif [[ "$EXTENSION" == "sh" ]] || [[ "$FILENAME" == "Makefile" ]]; then
    if command -v shellcheck >/dev/null 2>&1 && [[ "$EXTENSION" == "sh" ]]; then
        SHELLCHECK_OUTPUT=$(shellcheck "$FILE_PATH" 2>&1 || true)
        if [ -n "$SHELLCHECK_OUTPUT" ]; then
            ((ISSUES_FOUND++)) || true
            ((REMAINING_ISSUES++)) || true
            add_detail "shellcheck" "Shell script issues found"
        fi
    fi
fi

# Determine status
if [ $REMAINING_ISSUES -eq 0 ]; then
    STATUS="success"
elif [ $AUTO_FIXED -gt 0 ]; then
    STATUS="warning"
else
    STATUS="error"
fi

# Output structured format
echo "status: $STATUS"
echo "file: $FILE_PATH"
echo "issues_found: $ISSUES_FOUND"
echo "auto_fixed: $AUTO_FIXED"
echo "remaining_issues: $REMAINING_ISSUES"
if [ -n "$DETAILS" ]; then
    echo "details:"
    echo -e "$DETAILS" | sed 's/^$//'
fi
echo "CLAUDE_FORMAT_CHECK:END"

# Exit with appropriate code
if [ $REMAINING_ISSUES -gt 0 ]; then
    exit 1
else
    exit 0
fi
