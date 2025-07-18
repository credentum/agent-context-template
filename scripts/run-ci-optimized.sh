#!/bin/bash
# run-ci-optimized.sh - Optimized CI runner with parallel execution and smart caching

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Performance tracking
START_TIME=$(date +%s)

# Help function
show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "🚀 Optimized CI Commands:"
    echo "  fast       Run fast checks only (lint + unit tests)"
    echo "  full       Run complete optimized pipeline"
    echo "  parallel   Run all tests in parallel (recommended)"
    echo "  benchmark  Compare performance against legacy CI"
    echo ""
    echo "🔧 Legacy Commands (for comparison):"
    echo "  legacy     Run legacy CI pipeline"
    echo "  compare    Run both optimized and legacy, show timing"
    echo ""
    echo "🛠️ Utility Commands:"
    echo "  build      Build optimized Docker images"
    echo "  clean      Clean up containers and cache"
    echo "  debug      Interactive debug shell"
    echo ""
    echo "📊 Performance Commands:"
    echo "  profile    Profile execution times by component"
    echo "  cache      Show cache status and hit rates"
    echo ""
    echo "Examples:"
    echo "  $0 fast        # Quick feedback (2-3 minutes)"
    echo "  $0 parallel    # Full pipeline with parallelization (5-8 minutes)"
    echo "  $0 benchmark   # Performance comparison"
    echo "  $0 compare     # Side-by-side timing comparison"
}

# Function to run with timing
run_timed() {
    local service=$1
    local description=$2
    local start_time=$(date +%s)

    echo -e "${BLUE}▶ Starting: $description${NC}"

    if docker-compose -f docker-compose.ci.yml run --rm $service; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Completed: $description (${duration}s)${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ Failed: $description (${duration}s)${NC}"
        return 1
    fi
}

# Function to run parallel jobs
run_parallel() {
    local services=("$@")
    local pids=()
    local results=()

    echo -e "${PURPLE}🚀 Running ${#services[@]} jobs in parallel...${NC}"

    for service in "${services[@]}"; do
        echo -e "${BLUE}▶ Starting: $service${NC}"
        docker-compose -f docker-compose.ci.yml run --rm $service &
        pids+=($!)
    done

    # Wait for all jobs and collect results
    local all_success=true
    for i in "${!pids[@]}"; do
        local pid=${pids[$i]}
        local service=${services[$i]}

        if wait $pid; then
            echo -e "${GREEN}✅ $service completed successfully${NC}"
            results+=("success")
        else
            echo -e "${RED}❌ $service failed${NC}"
            results+=("failed")
            all_success=false
        fi
    done

    if $all_success; then
        echo -e "${GREEN}🎉 All parallel jobs completed successfully!${NC}"
        return 0
    else
        echo -e "${RED}💥 Some parallel jobs failed${NC}"
        return 1
    fi
}

# Function to show performance summary
show_performance() {
    local total_time=$(($(date +%s) - START_TIME))
    echo ""
    echo -e "${PURPLE}📊 Performance Summary${NC}"
    echo -e "${PURPLE}=====================${NC}"
    echo -e "Total execution time: ${YELLOW}${total_time}s${NC}"

    # Cache performance
    if command -v docker &> /dev/null; then
        echo -e "Docker cache usage: $(docker system df --format 'table {{.Type}}\t{{.Size}}')"
    fi

    echo ""
}

# Function to benchmark against legacy
benchmark() {
    echo -e "${PURPLE}🏁 Performance Benchmark${NC}"
    echo -e "${PURPLE}========================${NC}"

    # Run optimized version
    echo -e "${BLUE}Running optimized pipeline...${NC}"
    local opt_start=$(date +%s)
    run_parallel "ci-lint-parallel" "ci-test-core" "ci-test-integration"
    local opt_end=$(date +%s)
    local opt_time=$((opt_end - opt_start))

    echo ""
    echo -e "${BLUE}Running legacy pipeline...${NC}"
    local leg_start=$(date +%s)
    docker-compose -f docker-compose.ci.yml run --rm ci-lint
    docker-compose -f docker-compose.ci.yml run --rm ci-unit-tests
    docker-compose -f docker-compose.ci.yml run --rm ci-coverage
    local leg_end=$(date +%s)
    local leg_time=$((leg_end - leg_start))

    # Calculate improvement
    local improvement=$(( (leg_time - opt_time) * 100 / leg_time ))

    echo ""
    echo -e "${PURPLE}📊 Benchmark Results${NC}"
    echo -e "${PURPLE}===================${NC}"
    echo -e "Legacy pipeline:    ${YELLOW}${leg_time}s${NC}"
    echo -e "Optimized pipeline: ${YELLOW}${opt_time}s${NC}"
    echo -e "Improvement:        ${GREEN}${improvement}%${NC} faster"
    echo -e "Time saved:         ${GREEN}$((leg_time - opt_time))s${NC}"
}

# Main command logic
COMMAND=${1:-fast}

case $COMMAND in
    fast)
        echo -e "${GREEN}🚀 Running fast CI checks (optimized)${NC}"
        echo -e "${YELLOW}This runs lint + unit tests with parallel execution${NC}"
        echo ""
        run_parallel "ci-lint-parallel" "ci-test-core"
        ;;

    full)
        echo -e "${GREEN}🚀 Running complete optimized CI pipeline${NC}"
        echo -e "${YELLOW}This runs all tests with maximum parallelization${NC}"
        echo ""
        # Run setup first, then everything in parallel
        run_timed "ci-setup" "Environment setup"
        run_parallel "ci-lint-parallel" "ci-test-core" "ci-test-integration" "ci-test-performance"
        run_timed "ci-coverage-analysis" "Coverage analysis"
        ;;

    parallel)
        echo -e "${GREEN}🚀 Running optimized parallel CI${NC}"
        echo -e "${YELLOW}Maximum parallelization for fastest feedback${NC}"
        echo ""
        run_parallel "ci-lint-parallel" "ci-test-core" "ci-test-integration"
        ;;

    benchmark)
        benchmark
        ;;

    legacy)
        echo -e "${GREEN}🕰️  Running legacy CI pipeline${NC}"
        echo -e "${YELLOW}This replicates the original workflow performance${NC}"
        echo ""
        run_timed "ci-lint" "Legacy lint checks"
        run_timed "ci-unit-tests" "Legacy unit tests"
        run_timed "ci-coverage" "Legacy coverage"
        ;;

    compare)
        echo -e "${PURPLE}⚖️  CI Performance Comparison${NC}"
        echo -e "${PURPLE}=============================${NC}"

        echo -e "${BLUE}1. Testing optimized pipeline...${NC}"
        local opt_start=$(date +%s)
        run_parallel "ci-lint-parallel" "ci-test-core"
        local opt_time=$(($(date +%s) - opt_start))

        echo ""
        echo -e "${BLUE}2. Testing legacy pipeline...${NC}"
        local leg_start=$(date +%s)
        docker-compose -f docker-compose.ci.yml run --rm ci-lint
        docker-compose -f docker-compose.ci.yml run --rm ci-unit-tests
        local leg_time=$(($(date +%s) - leg_start))

        local improvement=$(( (leg_time - opt_time) * 100 / leg_time ))

        echo ""
        echo -e "${PURPLE}📊 Performance Comparison${NC}"
        echo -e "${PURPLE}=========================${NC}"
        echo -e "Legacy:     ${YELLOW}${leg_time}s${NC}"
        echo -e "Optimized:  ${YELLOW}${opt_time}s${NC}"
        echo -e "Improvement: ${GREEN}${improvement}%${NC}"
        ;;

    build)
        echo -e "${BLUE}▶ Building optimized CI Docker images...${NC}"
        docker-compose -f docker-compose.ci.yml build
        echo -e "${GREEN}✓ Build complete${NC}"
        ;;

    clean)
        echo -e "${BLUE}▶ Cleaning up Docker containers and cache...${NC}"
        docker-compose -f docker-compose.ci.yml down
        docker-compose down
        docker system prune -f
        echo -e "${GREEN}✓ Cleanup complete${NC}"
        ;;

    debug)
        echo -e "${BLUE}▶ Starting interactive debug shell...${NC}"
        echo "You can run optimized CI commands manually inside the container"
        docker-compose -f docker-compose.ci.yml run --rm ci-debug
        ;;

    profile)
        echo -e "${PURPLE}📊 Profiling CI execution times${NC}"
        echo -e "${PURPLE}===============================${NC}"

        echo -e "${BLUE}Profiling individual components:${NC}"

        for component in "ci-lint-black" "ci-lint-mypy" "ci-test-core" "ci-test-integration"; do
            local start_time=$(date +%s)
            docker-compose -f docker-compose.ci.yml run --rm $component >/dev/null 2>&1
            local duration=$(($(date +%s) - start_time))
            echo -e "  $component: ${YELLOW}${duration}s${NC}"
        done
        ;;

    cache)
        echo -e "${PURPLE}📦 Cache Status${NC}"
        echo -e "${PURPLE}==============${NC}"

        if command -v docker &> /dev/null; then
            echo -e "${BLUE}Docker system usage:${NC}"
            docker system df
            echo ""
            echo -e "${BLUE}Docker image layers:${NC}"
            docker images | grep agent-context-ci | head -5
        fi
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

# Show performance summary for timed commands
if [[ "$COMMAND" =~ ^(fast|full|parallel|benchmark|compare)$ ]]; then
    show_performance
fi
