#!/bin/bash
# compare-environments.sh - Compare local Docker CI environment with GitHub CI
# This script generates a detailed comparison report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Environment Comparison Report"
echo "================================="
echo "This script compares local Docker CI environment with GitHub CI expectations"
echo

# Function to check if we're running in Docker
is_docker() {
    if [ -f /.dockerenv ]; then
        return 0
    else
        return 1
    fi
}

# Function to display environment details
show_environment() {
    local env_name=$1
    echo -e "\n${BLUE}📋 $env_name Environment Details:${NC}"
    echo "----------------------------------------"

    echo "🐍 Python Environment:"
    echo "  Version: $(python --version)"
    echo "  Executable: $(python -c 'import sys; print(sys.executable)')"
    echo "  Site packages: $(python -c 'import site; print(site.getsitepackages())')"
    echo "  pip version: $(pip --version)"

    echo
    echo "🛠️  Required Tools:"
    for tool in black isort flake8 mypy pytest coverage; do
        if which $tool > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ $tool: $(which $tool)${NC}"
        else
            echo -e "  ${RED}✗ $tool: NOT FOUND${NC}"
        fi
    done

    echo
    echo "📁 Working Directory:"
    echo "  Current: $(pwd)"
    echo "  Contents: $(ls -la | wc -l) items"

    echo
    echo "🌐 Environment Variables:"
    echo "  PYTHONPATH: $PYTHONPATH"
    echo "  CI: $CI"
    echo "  PYTHONUNBUFFERED: $PYTHONUNBUFFERED"
    echo "  CACHE_VERSION: $CACHE_VERSION"
    echo "  PYTHON_VERSION: $PYTHON_VERSION"

    echo
    echo "💾 System Resources:"
    echo "  Memory: $(free -h | head -2 | tail -1)"
    echo "  Disk: $(df -h . | tail -1)"

    echo
    echo "📦 Python Packages (key ones):"
    pip list | grep -E "(black|isort|flake8|mypy|pytest|coverage)" | while read package; do
        echo "  $package"
    done
}

# Function to run a test command and report results
test_command() {
    local name=$1
    local cmd=$2
    echo -e "\n${YELLOW}🧪 Testing: $name${NC}"
    echo "   Command: $cmd"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ SUCCESS${NC}"
        return 0
    else
        echo -e "   ${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to generate recommendations
generate_recommendations() {
    echo -e "\n${BLUE}💡 Recommendations:${NC}"
    echo "===================="

    # Check if we're in Docker
    if is_docker; then
        echo -e "${GREEN}✓ Running in Docker environment${NC}"
        echo "  - This matches the isolated environment approach"
    else
        echo -e "${YELLOW}⚠ Running in host environment${NC}"
        echo "  - Consider using Docker for consistency"
    fi

    # Check tool availability
    missing_tools=()
    for tool in black isort flake8 mypy pytest coverage; do
        if ! which $tool > /dev/null 2>&1; then
            missing_tools+=($tool)
        fi
    done

    if [ ${#missing_tools[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ All required tools are available${NC}"
    else
        echo -e "${RED}⚠ Missing tools: ${missing_tools[*]}${NC}"
        echo "  - Run: pip install ${missing_tools[*]}"
    fi

    # Check environment variables
    if [ "$CI" = "true" ]; then
        echo -e "${GREEN}✓ CI environment variable set correctly${NC}"
    else
        echo -e "${YELLOW}⚠ CI environment variable not set${NC}"
        echo "  - Set: export CI=true"
    fi

    if [ -n "$PYTHONPATH" ]; then
        echo -e "${GREEN}✓ PYTHONPATH is set${NC}"
    else
        echo -e "${YELLOW}⚠ PYTHONPATH not set${NC}"
        echo "  - Set: export PYTHONPATH=/app (or current directory)"
    fi
}

# Main execution
main() {
    # Determine environment type
    if is_docker; then
        ENV_TYPE="Docker CI"
    else
        ENV_TYPE="Host"
    fi

    # Show environment details
    show_environment "$ENV_TYPE"

    # Run test commands
    echo -e "\n${BLUE}🧪 Command Tests:${NC}"
    echo "=================="

    PASSED=0
    TOTAL=0

    # Test each critical command
    commands=(
        "Python import test:python -c 'import sys; print(sys.version)'"
        "Black check:black --check --diff src/ tests/ scripts/ || true"
        "Isort check:isort --check-only --profile black src/ tests/ scripts/ || true"
        "Flake8 check:flake8 src/ tests/ scripts/ --max-line-length=100 --extend-ignore=E203,W503 || true"
        "MyPy check:mypy src/ --config-file=mypy.ini || true"
        "Pytest collect:python -m pytest --collect-only -q || true"
        "Context lint:python -m src.agents.context_lint validate context/ || true"
    )

    for cmd_desc in "${commands[@]}"; do
        IFS=':' read -r name cmd <<< "$cmd_desc"
        TOTAL=$((TOTAL + 1))
        if test_command "$name" "$cmd"; then
            PASSED=$((PASSED + 1))
        fi
    done

    # Generate recommendations
    generate_recommendations

    # Summary
    echo -e "\n${BLUE}📊 Summary:${NC}"
    echo "==========="
    echo "Environment: $ENV_TYPE"
    echo "Tests passed: $PASSED/$TOTAL"

    if [ $PASSED -eq $TOTAL ]; then
        echo -e "${GREEN}✅ Environment looks ready for CI!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Environment needs attention${NC}"
        exit 1
    fi
}

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo ""
    echo "This script compares the current environment with GitHub CI expectations."
    echo "It can run both in Docker and host environments."
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            set -x
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Run main function
main
