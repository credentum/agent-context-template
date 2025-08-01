#!/bin/bash
# run-precommit-with-overlay.sh - Run pre-commit hooks with writable overlay
# This script creates a writable copy of files that pre-commit needs to modify
# to work around read-only filesystem issues in Docker CI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up writable overlay for pre-commit hooks${NC}"

# Create temporary directory for writable overlay
OVERLAY_DIR="/tmp/precommit-overlay-$$"
mkdir -p "$OVERLAY_DIR"

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}Cleaning up overlay directory...${NC}"
    rm -rf "$OVERLAY_DIR"
}
trap cleanup EXIT

# Copy necessary files to overlay
echo "Copying files to writable overlay..."

# Copy source directories
for dir in src tests scripts; do
    if [ -d "$dir" ]; then
        echo "  - Copying $dir/"
        cp -r "$dir" "$OVERLAY_DIR/"
    fi
done

# Copy individual files that pre-commit might need to modify
for file in .github/workflows/*.yml context/**/*.yaml context/**/*.yml; do
    if [ -e "$file" ]; then
        # Create directory structure
        dir=$(dirname "$file")
        mkdir -p "$OVERLAY_DIR/$dir"
        echo "  - Copying $file"
        cp "$file" "$OVERLAY_DIR/$file"
    fi
done

# Copy configuration files (read-only is fine for these)
for config in .pre-commit-config.yaml pyproject.toml .flake8 mypy.ini .yamllint-workflows.yml .yamllint-schemas.yml; do
    if [ -f "$config" ]; then
        echo "  - Linking $config"
        ln -s "$(pwd)/$config" "$OVERLAY_DIR/$config"
    fi
done

# Create .git directory structure for pre-commit
mkdir -p "$OVERLAY_DIR/.git"
if [ -d ".git" ]; then
    # Copy essential git files for pre-commit to work
    cp -r .git/config "$OVERLAY_DIR/.git/config" 2>/dev/null || true
    cp -r .git/HEAD "$OVERLAY_DIR/.git/HEAD" 2>/dev/null || true
    cp -r .git/refs "$OVERLAY_DIR/.git/refs" 2>/dev/null || true
    cp -r .git/objects "$OVERLAY_DIR/.git/objects" 2>/dev/null || true

    # Create a minimal gitconfig if needed
    if [ ! -f "$OVERLAY_DIR/.git/config" ]; then
        echo "[core]" > "$OVERLAY_DIR/.git/config"
        echo "    repositoryformatversion = 0" >> "$OVERLAY_DIR/.git/config"
        echo "    filemode = true" >> "$OVERLAY_DIR/.git/config"
    fi
else
    # If no git directory, create a minimal one
    cd "$OVERLAY_DIR"
    git init --quiet
    cd - >/dev/null
fi

echo -e "${GREEN}✓ Overlay setup complete${NC}"

# Change to overlay directory
cd "$OVERLAY_DIR"

# Run pre-commit with proper error handling
echo -e "\n${BLUE}Running pre-commit hooks...${NC}"

# Initialize pre-commit in the overlay directory
pre-commit install --install-hooks >/dev/null 2>&1 || true

# Run pre-commit and capture the exit code
set +e
pre-commit run --all-files
PRECOMMIT_EXIT_CODE=$?
set -e

# Show results
if [ $PRECOMMIT_EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✅ All pre-commit checks passed!${NC}"
else
    echo -e "\n${RED}❌ Pre-commit checks failed${NC}"
    echo -e "${YELLOW}Note: Files were checked in the overlay directory${NC}"
    echo -e "${YELLOW}Any fixes would need to be applied to the original files${NC}"
fi

# Return to original directory
cd - >/dev/null

# Exit with the same code as pre-commit
exit $PRECOMMIT_EXIT_CODE
