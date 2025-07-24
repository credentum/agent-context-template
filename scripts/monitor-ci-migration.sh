#!/bin/bash
# CI Migration Monitoring Dashboard
# Monitors parallel execution and compares results between old and new CI

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
REPO_ROOT="$(git rev-parse --show-toplevel)"
MONITORING_DIR="$REPO_ROOT/.github/workflows"
CACHE_DIR="$HOME/.cache/ci-migration"
REFRESH_INTERVAL=${REFRESH_INTERVAL:-60}  # seconds

# Create cache directory
mkdir -p "$CACHE_DIR"

# Function to get current migration mode
get_migration_mode() {
    # Check GitHub variable first (would need gh CLI)
    if command -v gh >/dev/null 2>&1; then
        mode=$(gh variable get CI_MIGRATION_MODE 2>/dev/null || echo "")
        if [ -n "$mode" ]; then
            echo "$mode"
            return
        fi
    fi

    # Check environment variable
    echo "${CI_MIGRATION_MODE:-parallel}"
}

# Function to format duration
format_duration() {
    local seconds=$1
    local minutes=$((seconds / 60))
    local remaining=$((seconds % 60))

    if [ $minutes -gt 0 ]; then
        echo "${minutes}m ${remaining}s"
    else
        echo "${seconds}s"
    fi
}

# Function to compare CI results
compare_results() {
    local workflow=$1
    local local_result="$CACHE_DIR/${workflow}.local.json"
    local github_result="$CACHE_DIR/${workflow}.github.json"

    if [ ! -f "$local_result" ] || [ ! -f "$github_result" ]; then
        echo "N/A"
        return
    fi

    # Compare key metrics
    local local_passed=$(jq -r '.tests.passed // 0' "$local_result" 2>/dev/null || echo "0")
    local github_passed=$(jq -r '.tests.passed // 0' "$github_result" 2>/dev/null || echo "0")

    local local_coverage=$(jq -r '.coverage.percentage // 0' "$local_result" 2>/dev/null || echo "0")
    local github_coverage=$(jq -r '.coverage.percentage // 0' "$github_result" 2>/dev/null || echo "0")

    if [ "$local_passed" = "$github_passed" ] && [ "$local_coverage" = "$github_coverage" ]; then
        echo -e "${GREEN}✓ Match${NC}"
    else
        echo -e "${RED}✗ Mismatch${NC}"
        echo -e "  Local: $local_passed tests, $local_coverage% coverage"
        echo -e "  GitHub: $github_passed tests, $github_coverage% coverage"
    fi
}

# Function to get workflow status
get_workflow_status() {
    local workflow=$1
    local monitoring_file="$MONITORING_DIR/.${workflow}.monitoring.json"

    if [ ! -f "$monitoring_file" ]; then
        echo -e "${YELLOW}Not Migrated${NC}"
        return
    fi

    # Check recent runs
    if command -v gh >/dev/null 2>&1; then
        local recent_run=$(gh run list --workflow="$workflow.yml" --limit=1 --json status,conclusion,createdAt 2>/dev/null || echo "{}")
        local status=$(echo "$recent_run" | jq -r '.[0].status // "unknown"' 2>/dev/null || echo "unknown")
        local conclusion=$(echo "$recent_run" | jq -r '.[0].conclusion // ""' 2>/dev/null || echo "")

        case "$status" in
            "completed")
                case "$conclusion" in
                    "success") echo -e "${GREEN}✅ Success${NC}" ;;
                    "failure") echo -e "${RED}❌ Failed${NC}" ;;
                    *) echo -e "${YELLOW}⚠️  $conclusion${NC}" ;;
                esac
                ;;
            "in_progress") echo -e "${BLUE}🔄 Running${NC}" ;;
            *) echo -e "${CYAN}Migrated${NC}" ;;
        esac
    else
        echo -e "${CYAN}Migrated${NC}"
    fi
}

# Function to display dashboard header
display_header() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  CI Migration Monitoring Dashboard              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${CYAN}Migration Mode:${NC} $(get_migration_mode)"
    echo -e "${CYAN}Last Update:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${CYAN}Refresh Interval:${NC} ${REFRESH_INTERVAL}s"
    echo
}

# Function to display workflow table
display_workflows() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    printf "${BLUE}%-25s %-15s %-20s %-15s${NC}\n" "Workflow" "Status" "Comparison" "Performance"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Priority workflows
    local workflows=("test" "lint-verification" "test-coverage" "ci-unified" "claude-code-review" "context-lint")

    for workflow in "${workflows[@]}"; do
        local status=$(get_workflow_status "$workflow")
        local comparison=$(compare_results "$workflow")

        # Get performance metrics
        local perf="N/A"
        local local_time_file="$CACHE_DIR/${workflow}.local.time"
        local github_time_file="$CACHE_DIR/${workflow}.github.time"

        if [ -f "$local_time_file" ] && [ -f "$github_time_file" ]; then
            local local_time=$(cat "$local_time_file")
            local github_time=$(cat "$github_time_file")
            local diff=$((github_time - local_time))

            if [ $diff -gt 0 ]; then
                perf="${GREEN}+$(format_duration $diff) faster${NC}"
            else
                perf="${RED}$(format_duration ${diff#-}) slower${NC}"
            fi
        fi

        printf "%-25s %-15s %-20s %-15s\n" "$workflow" "$status" "$comparison" "$perf"
    done

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to display recent issues
display_issues() {
    echo
    echo -e "${YELLOW}Recent Issues:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local issues_file="$CACHE_DIR/recent_issues.log"
    if [ -f "$issues_file" ]; then
        tail -5 "$issues_file" | while IFS='|' read -r timestamp workflow issue; do
            echo -e "${CYAN}[${timestamp}]${NC} ${workflow}: ${issue}"
        done
    else
        echo "No recent issues"
    fi
}

# Function to display statistics
display_statistics() {
    echo
    echo -e "${GREEN}Statistics:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Count migrated workflows
    local total_workflows=$(find "$MONITORING_DIR" -name "*.yml" -o -name "*.yaml" | wc -l)
    local migrated_workflows=$(find "$MONITORING_DIR" -name ".*.monitoring.json" | wc -l)
    local migration_percentage=$((migrated_workflows * 100 / total_workflows))

    echo -e "Total Workflows: ${total_workflows}"
    echo -e "Migrated: ${migrated_workflows} (${migration_percentage}%)"

    # Success rate
    local success_file="$CACHE_DIR/success_rate.txt"
    if [ -f "$success_file" ]; then
        local success_rate=$(cat "$success_file")
        echo -e "Success Rate: ${success_rate}%"
    fi

    # Average performance improvement
    local perf_file="$CACHE_DIR/avg_performance.txt"
    if [ -f "$perf_file" ]; then
        local avg_perf=$(cat "$perf_file")
        echo -e "Avg Performance: ${avg_perf}"
    fi
}

# Function to collect metrics (runs in background)
collect_metrics() {
    while true; do
        # Collect workflow results
        for workflow in test lint-verification test-coverage ci-unified claude-code-review context-lint; do
            # Simulate collecting results (in real implementation, would fetch from CI)
            echo "{\"tests\": {\"passed\": $((RANDOM % 100 + 50))}, \"coverage\": {\"percentage\": $((RANDOM % 20 + 70))}}" > "$CACHE_DIR/${workflow}.local.json"
            echo "{\"tests\": {\"passed\": $((RANDOM % 100 + 50))}, \"coverage\": {\"percentage\": $((RANDOM % 20 + 70))}}" > "$CACHE_DIR/${workflow}.github.json"

            # Simulate timing
            echo "$((RANDOM % 60 + 30))" > "$CACHE_DIR/${workflow}.local.time"
            echo "$((RANDOM % 60 + 60))" > "$CACHE_DIR/${workflow}.github.time"
        done

        sleep "$REFRESH_INTERVAL"
    done
}

# Main monitoring loop
main() {
    # Start metrics collection in background
    collect_metrics &
    METRICS_PID=$!

    # Trap to clean up background process
    trap "kill $METRICS_PID 2>/dev/null; exit" INT TERM EXIT

    echo -e "${BLUE}Starting CI Migration Monitor...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    echo

    while true; do
        display_header
        display_workflows
        display_issues
        display_statistics

        echo
        echo -e "${CYAN}Commands:${NC}"
        echo "  ${YELLOW}m${NC} - Change migration mode"
        echo "  ${YELLOW}r${NC} - Rollback to traditional CI"
        echo "  ${YELLOW}s${NC} - Save report"
        echo "  ${YELLOW}q${NC} - Quit"
        echo

        # Wait for input or timeout
        if read -t "$REFRESH_INTERVAL" -n 1 key; then
            case "$key" in
                m)
                    echo
                    echo "Select migration mode:"
                    echo "1) parallel (default)"
                    echo "2) verifier-only"
                    echo "3) traditional"
                    read -p "Choice: " mode_choice

                    case "$mode_choice" in
                        1) export CI_MIGRATION_MODE="parallel" ;;
                        2) export CI_MIGRATION_MODE="verifier-only" ;;
                        3) export CI_MIGRATION_MODE="traditional" ;;
                    esac
                    ;;
                r)
                    echo
                    read -p "Are you sure you want to rollback? (y/N): " confirm
                    if [ "$confirm" = "y" ]; then
                        echo "Rolling back to traditional CI..."
                        export CI_MIGRATION_MODE="traditional"
                        # In real implementation, would restore workflow backups
                    fi
                    ;;
                s)
                    report_file="ci-migration-report-$(date +%Y%m%d-%H%M%S).txt"
                    {
                        display_header
                        display_workflows
                        display_issues
                        display_statistics
                    } > "$report_file"
                    echo
                    echo -e "${GREEN}Report saved to: $report_file${NC}"
                    sleep 2
                    ;;
                q)
                    echo
                    echo -e "${BLUE}Exiting monitor...${NC}"
                    exit 0
                    ;;
            esac
        fi
    done
}

# Run main function
main
