#!/usr/bin/env bash
# load-monitor.sh - System load monitoring for CI pipeline
# Provides load checking and resource monitoring capabilities

set -euo pipefail

# Configuration
MAX_LOAD="${MAX_LOAD:-8}"
VERBOSE="${VERBOSE:-false}"
CHECK_MODE="${1:-check}"  # check, monitor, suggest-workers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current system load
get_load() {
    # Extract 1-minute load average
    if command -v uptime >/dev/null 2>&1; then
        uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs
    else
        # Fallback to /proc/loadavg if available
        if [ -f /proc/loadavg ]; then
            awk '{print $1}' /proc/loadavg
        else
            echo "0"
        fi
    fi
}
export -f get_load 2>/dev/null || true

# Get number of CPU cores
get_cpu_count() {
    if command -v nproc >/dev/null 2>&1; then
        nproc
    elif [ -f /proc/cpuinfo ]; then
        grep -c ^processor /proc/cpuinfo
    elif command -v sysctl >/dev/null 2>&1; then
        sysctl -n hw.ncpu 2>/dev/null || echo "1"
    else
        echo "1"
    fi
}

# Check if load is acceptable
check_load() {
    local current_load
    current_load=$(get_load)
    local cpu_count
    cpu_count=$(get_cpu_count)

    # Convert to integer for comparison
    local load_int
    load_int=$(echo "$current_load" | awk '{print int($1)}')

    if [ "$VERBOSE" = "true" ]; then
        echo "System Load Check:"
        echo "  Current load: $current_load"
        echo "  CPU cores: $cpu_count"
        echo "  Max allowed: $MAX_LOAD"
    fi

    if [ "$load_int" -ge "$MAX_LOAD" ]; then
        if [ "$VERBOSE" = "true" ]; then
            echo -e "${RED}Load too high!${NC} ($current_load >= $MAX_LOAD)"
        fi
        return 1
    else
        if [ "$VERBOSE" = "true" ]; then
            echo -e "${GREEN}Load acceptable${NC} ($current_load < $MAX_LOAD)"
        fi
        return 0
    fi
}

# Suggest pytest worker count based on load
suggest_workers() {
    local current_load
    current_load=$(get_load)
    local cpu_count
    cpu_count=$(get_cpu_count)
    local load_int
    load_int=$(echo "$current_load" | awk '{print int($1)}')

    # Calculate available capacity
    local available_capacity=$((cpu_count - load_int))

    if [ "$available_capacity" -le 0 ]; then
        echo "1"  # Minimum 1 worker
    elif [ "$available_capacity" -eq 1 ]; then
        echo "1"
    elif [ "$available_capacity" -eq 2 ]; then
        echo "2"
    elif [ "$available_capacity" -ge 3 ] && [ "$available_capacity" -lt 6 ]; then
        echo "3"
    else
        echo "auto"  # Let pytest decide for high capacity
    fi
}

# Monitor load (for debugging/logging)
monitor_load() {
    local duration="${1:-60}"
    local interval="${2:-5}"
    local iterations=$((duration / interval))

    echo "Monitoring system load for ${duration}s (interval: ${interval}s)"
    echo "Time | Load | Status"
    echo "-----|------|-------"

    for ((i=0; i<iterations; i++)); do
        local current_load
        current_load=$(get_load)
        local load_int
        load_int=$(echo "$current_load" | awk '{print int($1)}')
        local status="OK"

        if [ "$load_int" -ge "$MAX_LOAD" ]; then
            status="HIGH"
        fi

        printf "%4ds | %4s | %s\n" $((i * interval)) "$current_load" "$status"

        if [ $((i + 1)) -lt "$iterations" ]; then
            sleep "$interval"
        fi
    done
}

# Main execution
case "$CHECK_MODE" in
    check)
        check_load
        exit $?
        ;;
    get_load)
        get_load
        ;;
    suggest-workers)
        suggest_workers
        ;;
    monitor)
        duration="${2:-60}"
        interval="${3:-5}"
        monitor_load "$duration" "$interval"
        ;;
    *)
        echo "Usage: $0 {check|get_load|suggest-workers|monitor [duration] [interval]}"
        echo ""
        echo "Modes:"
        echo "  check          - Check if current load is acceptable (exit 0 if OK)"
        echo "  get_load       - Print current system load"
        echo "  suggest-workers - Suggest pytest worker count based on load"
        echo "  monitor        - Monitor load for specified duration"
        echo ""
        echo "Environment variables:"
        echo "  MAX_LOAD - Maximum acceptable load (default: 8)"
        echo "  VERBOSE  - Show detailed output (default: false)"
        exit 1
        ;;
esac
