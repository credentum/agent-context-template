#!/bin/bash
# run-ci-docker-optimized.sh - Optimized Docker CI runner with performance enhancements
# Targets <5 minute execution time for full CI suite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Performance tracking
START_TIME=$(date +%s)

# Help function
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all       Run all CI lint checks with optimization (default)"
    echo "  parallel  Run checks in parallel for maximum speed"
    echo "  quick     Run only essential checks (<1 minute)"
    echo "  coverage  Run coverage tests with caching"
    echo "  build     Build/rebuild with cache optimization"
    echo "  clean     Clean cache and containers"
    echo ""
    echo "Options:"
    echo "  --timeout SECONDS  Set command timeout (default: 120)"
    echo "  --progress         Show detailed progress"
    echo ""
    echo "Performance features:"
    echo "  - Docker BuildKit caching enabled"
    echo "  - Parallel execution of independent checks"
    echo "  - Incremental testing with cache"
    echo "  - Early termination on critical failures"
}

# Default values
COMMAND=${1:-all}
TIMEOUT=120
SHOW_PROGRESS=false

# Parse options
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --progress)
            SHOW_PROGRESS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Enable Docker BuildKit for better caching
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Function to print timing info
print_timing() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    echo -e "${CYAN}⏱️  Elapsed time: ${duration}s${NC}"
}

# Function to run service with timeout and progress
run_service_optimized() {
    local service=$1
    local description=$2
    local service_start=$(date +%s)

    echo -e "${BLUE}▶ Running $description...${NC}"

    if [ "$SHOW_PROGRESS" = true ]; then
        docker-compose -f docker-compose.yml -f docker-compose.ci.yml run \
            --rm \
            -e TIMEOUT=$TIMEOUT \
            $service
    else
        docker-compose -f docker-compose.yml -f docker-compose.ci.yml run \
            --rm \
            -e TIMEOUT=$TIMEOUT \
            $service >/dev/null 2>&1
        local exit_code=$?

        local service_end=$(date +%s)
        local service_duration=$((service_end - service_start))

        if [ $exit_code -eq 0 ]; then
            echo -e "  ${GREEN}✓ PASSED${NC} (${service_duration}s)"
        else
            echo -e "  ${RED}✗ FAILED${NC} (${service_duration}s)"
            return $exit_code
        fi
    fi
}

# Function to run checks in parallel
run_parallel_checks() {
    echo -e "${GREEN}🚀 Running CI checks in PARALLEL mode${NC}"
    echo -e "${YELLOW}Maximum speed optimization enabled${NC}"
    echo ""

    # Create temp directory for results
    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    # Define check groups that can run in parallel
    declare -a CHECKS=(
        "ci-black:Black formatting"
        "ci-isort:Import sorting"
        "ci-flake8:Flake8 linting"
        "ci-mypy:MyPy type checking"
        "ci-context-lint:Context validation"
    )

    # Launch all checks in parallel
    echo -e "${BLUE}Launching ${#CHECKS[@]} checks in parallel...${NC}"

    for check in "${CHECKS[@]}"; do
        IFS=':' read -r service description <<< "$check"
        (
            echo -e "${BLUE}▶ Starting $description${NC}"
            if docker-compose -f docker-compose.yml -f docker-compose.ci.yml run \
                --rm -e TIMEOUT=$TIMEOUT $service >/dev/null 2>&1; then
                echo "PASSED" > "$TEMP_DIR/$service.result"
            else
                echo "FAILED" > "$TEMP_DIR/$service.result"
            fi
        ) &
    done

    # Wait for all background jobs
    wait

    # Collect results
    echo -e "\n${YELLOW}Results:${NC}"
    local failed=0
    for check in "${CHECKS[@]}"; do
        IFS=':' read -r service description <<< "$check"
        result=$(cat "$TEMP_DIR/$service.result" 2>/dev/null || echo "ERROR")
        if [ "$result" = "PASSED" ]; then
            echo -e "  $description: ${GREEN}✓ PASSED${NC}"
        else
            echo -e "  $description: ${RED}✗ FAILED${NC}"
            failed=$((failed + 1))
        fi
    done

    print_timing

    if [ $failed -gt 0 ]; then
        echo -e "\n${RED}❌ $failed checks failed${NC}"
        return 1
    else
        echo -e "\n${GREEN}✅ All checks passed!${NC}"
        return 0
    fi
}

# Function for quick essential checks only
run_quick_checks() {
    echo -e "${GREEN}🚀 Running QUICK essential checks${NC}"
    echo -e "${YELLOW}Target: <1 minute execution${NC}"
    echo ""

    # Only run the most critical checks
    run_service_optimized ci-black "Black formatting"
    run_service_optimized ci-flake8 "Flake8 linting"
    run_service_optimized ci-mypy "MyPy type checking"

    print_timing
}

# Main logic
case $COMMAND in
    all)
        echo -e "${GREEN}🚀 Running optimized CI checks${NC}"
        echo -e "${YELLOW}Target: <5 minute execution${NC}"
        echo ""

        # Build with cache
        echo -e "${BLUE}Building CI image with cache...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.ci.yml build --pull ci-lint

        # Run comprehensive checks with optimization
        run_service_optimized ci-lint "all CI checks"

        print_timing
        ;;

    parallel)
        run_parallel_checks
        ;;

    quick)
        run_quick_checks
        ;;

    coverage)
        echo -e "${GREEN}🚀 Running coverage tests with optimization${NC}"

        # Use cache mount for coverage data
        docker-compose -f docker-compose.yml -f docker-compose.ci.yml run \
            --rm \
            -v coverage-cache:/app/.coverage_cache \
            -e TIMEOUT=$TIMEOUT \
            ci-coverage

        print_timing
        ;;

    build)
        echo -e "${GREEN}🔨 Building CI image with optimization${NC}"

        # Build with all cache features
        DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.ci.yml \
            build --pull --build-arg BUILDKIT_INLINE_CACHE=1 ci-lint

        echo -e "${GREEN}✅ Build complete${NC}"
        print_timing
        ;;

    clean)
        echo -e "${YELLOW}🧹 Cleaning Docker cache and containers${NC}"

        docker-compose -f docker-compose.yml -f docker-compose.ci.yml down -v
        docker builder prune -f

        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

# Performance summary
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${CYAN}═══════════════════════════════════════${NC}"
echo -e "${CYAN}Total execution time: ${TOTAL_DURATION}s${NC}"

if [ $TOTAL_DURATION -gt 300 ]; then
    echo -e "${YELLOW}⚠️  Execution exceeded 5 minute target${NC}"
elif [ $TOTAL_DURATION -lt 60 ]; then
    echo -e "${GREEN}🚀 Excellent performance! Under 1 minute${NC}"
else
    echo -e "${GREEN}✅ Good performance! Under 5 minutes${NC}"
fi
echo -e "${CYAN}═══════════════════════════════════════${NC}"
