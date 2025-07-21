#!/usr/bin/env bash
# claude-post-edit.sh - Main orchestrator for post-edit validation
# This script should be called after Claude makes edits to files
# Usage: ./claude-post-edit.sh <file1> [file2] ... [--fix]

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if any arguments provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] ... [--fix]"
    echo "  --fix: Automatically fix formatting issues where possible"
    exit 1
fi

# Check for --fix flag
FIX_MODE=""
FILES=()

for arg in "$@"; do
    if [ "$arg" = "--fix" ]; then
        FIX_MODE="--fix"
    else
        FILES+=("$arg")
    fi
done

# Validate that we have at least one file
if [ ${#FILES[@]} -eq 0 ]; then
    echo -e "${RED}Error: No files specified${NC}"
    exit 1
fi

# Log file for tracking
LOG_DIR="context/trace/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/claude-edits.log"

# Function to log
log_edit() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Summary counters
TOTAL_FILES=0
SUCCESS_FILES=0
WARNING_FILES=0
ERROR_FILES=0
TOTAL_ISSUES=0
TOTAL_FIXED=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Claude Post-Edit Format Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo

# Process each file
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}⚠ Skipping non-existent file: $file${NC}"
        continue
    fi

    ((TOTAL_FILES++)) || true

    echo -e "${YELLOW}Checking: $file${NC}"

    # Run validation script and capture output
    VALIDATION_OUTPUT=$("$SCRIPT_DIR/validate-file-format.sh" "$file" $FIX_MODE 2>&1) || true

    # Parse the structured output
    if [[ "$VALIDATION_OUTPUT" =~ CLAUDE_FORMAT_CHECK:START ]]; then
        STATUS=$(echo "$VALIDATION_OUTPUT" | grep "^status:" | cut -d' ' -f2)
        ISSUES=$(echo "$VALIDATION_OUTPUT" | grep "^issues_found:" | cut -d' ' -f2)
        FIXED=$(echo "$VALIDATION_OUTPUT" | grep "^auto_fixed:" | cut -d' ' -f2)
        REMAINING=$(echo "$VALIDATION_OUTPUT" | grep "^remaining_issues:" | cut -d' ' -f2)

        # Update totals
        TOTAL_ISSUES=$((TOTAL_ISSUES + ${ISSUES:-0}))
        TOTAL_FIXED=$((TOTAL_FIXED + ${FIXED:-0}))

        # Log the edit
        log_edit "File: $file, Status: $STATUS, Issues: $ISSUES, Fixed: $FIXED, Remaining: $REMAINING"

        # Display result with appropriate color
        case "$STATUS" in
            "success")
                echo -e "${GREEN}✓ Format check passed${NC}"
                ((SUCCESS_FILES++)) || true
                ;;
            "warning")
                echo -e "${YELLOW}⚠ Fixed $FIXED issue(s)${NC}"
                ((WARNING_FILES++)) || true
                ;;
            "error")
                echo -e "${RED}✗ Found $REMAINING issue(s) that need manual fixing${NC}"
                ((ERROR_FILES++)) || true

                # Show details if available
                if [[ "$VALIDATION_OUTPUT" =~ "details:" ]]; then
                    echo -e "${RED}  Details:${NC}"
                    echo "$VALIDATION_OUTPUT" | sed -n '/^details:/,/^CLAUDE_FORMAT_CHECK:END/p' | \
                        grep -E "^  - type:|^    message:" | sed 's/^/  /'
                fi
                ;;
        esac
    else
        echo -e "${RED}✗ Error running validation${NC}"
        ((ERROR_FILES++)) || true
    fi

    echo
done

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Files checked: ${TOTAL_FILES}"
echo -e "${GREEN}✓ Passed: ${SUCCESS_FILES}${NC}"
if [ $WARNING_FILES -gt 0 ]; then
    echo -e "${YELLOW}⚠ Fixed: ${WARNING_FILES} (${TOTAL_FIXED} issues auto-fixed)${NC}"
fi
if [ $ERROR_FILES -gt 0 ]; then
    echo -e "${RED}✗ Failed: ${ERROR_FILES}${NC}"
fi
echo -e "Total issues found: ${TOTAL_ISSUES}"

# Provide guidance based on results
echo
if [ $ERROR_FILES -gt 0 ]; then
    echo -e "${YELLOW}Action Required:${NC}"
    if [ -z "$FIX_MODE" ]; then
        echo "  • Run with --fix flag to auto-fix formatting issues"
        echo "  • Example: $0 ${FILES[*]} --fix"
    else
        echo "  • Some issues could not be auto-fixed"
        echo "  • Review the error details above and fix manually"
    fi
    exit 1
else
    if [ $WARNING_FILES -gt 0 ]; then
        echo -e "${GREEN}✓ All formatting issues were automatically fixed!${NC}"
        echo "  • Remember to stage the changes: git add ${FILES[*]}"
    else
        echo -e "${GREEN}✓ All files are properly formatted!${NC}"
    fi
    exit 0
fi
