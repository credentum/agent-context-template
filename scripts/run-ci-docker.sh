#!/bin/bash
# run-ci-docker.sh - Easy wrapper for Docker CI testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  all       Run all CI lint checks (default)"
    echo "  black     Run Black formatting check only"
    echo "  isort     Run isort import sorting check only"
    echo "  flake8    Run Flake8 linting only"
    echo "  mypy      Run MyPy type checking only"
    echo "  context   Run context YAML validation only"
    echo "  imports   Run import checking only"
    echo "  debug     Start interactive debug shell"
    echo "  build     Build/rebuild the CI Docker image"
    echo "  clean     Stop and remove containers"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all checks"
    echo "  $0 black        # Run only Black check"
    echo "  $0 build        # Rebuild image after requirements change"
    echo "  $0 debug        # Interactive shell for debugging"
}

# Default command
COMMAND=${1:-all}

# Function to run a service
run_service() {
    local service=$1
    local description=$2

    echo -e "${BLUE}▶ Running $description...${NC}"
    docker-compose -f docker-compose.ci.yml run --rm $service
}

# Main logic
case $COMMAND in
    all)
        echo -e "${GREEN}🚀 Running all CI lint checks in Docker${NC}"
        echo -e "${YELLOW}This replicates GitHub Actions environment exactly${NC}"
        echo ""
        run_service ci-lint "all CI checks"
        ;;
    black)
        run_service ci-black "Black formatting check"
        ;;
    isort)
        run_service ci-isort "isort import sorting check"
        ;;
    flake8)
        run_service ci-flake8 "Flake8 linting"
        ;;
    mypy)
        run_service ci-mypy "MyPy type checking"
        ;;
    context)
        run_service ci-context-lint "context YAML validation"
        ;;
    imports)
        run_service ci-import-check "import checking"
        ;;
    debug)
        echo -e "${BLUE}▶ Starting interactive debug shell...${NC}"
        echo "You can run CI commands manually inside the container"
        docker-compose -f docker-compose.ci.yml run --rm ci-debug
        ;;
    build)
        echo -e "${BLUE}▶ Building CI Docker image...${NC}"
        docker-compose -f docker-compose.ci.yml build
        echo -e "${GREEN}✓ Build complete${NC}"
        ;;
    clean)
        echo -e "${BLUE}▶ Cleaning up Docker containers...${NC}"
        docker-compose -f docker-compose.ci.yml down
        echo -e "${GREEN}✓ Cleanup complete${NC}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
