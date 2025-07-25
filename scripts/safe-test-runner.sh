#!/usr/bin/env bash
# safe-test-runner.sh - Safe pytest execution with load monitoring and process cleanup
# Wraps pytest with resource protection and orphan process prevention

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
TEST_THROTTLE_ENABLED="${TEST_THROTTLE_ENABLED:-true}"
MAX_LOAD="${MAX_LOAD:-8}"
PYTEST_TIMEOUT="${PYTEST_TIMEOUT:-300}"  # 5 minutes default
CLEANUP_GRACE_PERIOD="${CLEANUP_GRACE_PERIOD:-5}"
VERBOSE="${VERBOSE:-false}"

# Load monitoring functions (simplified versions)
get_load() {
    if command -v uptime >/dev/null 2>&1; then
        uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs
    elif [ -f /proc/loadavg ]; then
        awk '{print $1}' /proc/loadavg
    else
        echo "0"
    fi
}

check_load() {
    local current_load
    current_load=$(get_load)
    local load_int
    load_int=$(echo "$current_load" | awk '{print int($1)}')

    if [ "$load_int" -ge "$MAX_LOAD" ]; then
        return 1
    else
        return 0
    fi
}

suggest_workers() {
    local current_load
    current_load=$(get_load)
    local load_int
    load_int=$(echo "$current_load" | awk '{print int($1)}')

    # Simple logic for worker allocation
    if [ "$load_int" -gt 8 ]; then
        echo "1"
    elif [ "$load_int" -gt 4 ]; then
        echo "2"
    else
        echo "auto"
    fi
}

# Track PIDs for cleanup
TRACKED_PIDS=()
MAIN_PID=$$

# Cleanup function
cleanup_processes() {
    local signal="${1:-TERM}"

    if [ "$VERBOSE" = "true" ]; then
        echo "Cleaning up processes with signal: $signal"
    fi

    # Find all pytest processes spawned by this script
    local pytest_pids
    pytest_pids=$(pgrep -P "$MAIN_PID" -f "pytest" 2>/dev/null || true)

    if [ -n "$pytest_pids" ]; then
        if [ "$VERBOSE" = "true" ]; then
            echo "Found pytest processes: $pytest_pids"
        fi

        # Send signal to pytest processes
        for pid in $pytest_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "-$signal" "$pid" 2>/dev/null || true
            fi
        done

        # Grace period for TERM signal
        if [ "$signal" = "TERM" ]; then
            sleep "$CLEANUP_GRACE_PERIOD"

            # Check if any are still running and KILL if needed
            for pid in $pytest_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    if [ "$VERBOSE" = "true" ]; then
                        echo "Force killing pid: $pid"
                    fi
                    kill -KILL "$pid" 2>/dev/null || true
                fi
            done
        fi
    fi

    # Also check for any orphaned python processes
    local orphan_pids
    orphan_pids=$(pgrep -f "pytest.*test" 2>/dev/null | grep -v "^$$\$" || true)

    if [ -n "$orphan_pids" ] && [ "$VERBOSE" = "true" ]; then
        echo "Warning: Found potential orphaned pytest processes: $orphan_pids"
    fi
}

# Signal handlers
trap 'cleanup_processes TERM; exit 130' INT
trap 'cleanup_processes TERM; exit 143' TERM
trap 'cleanup_processes TERM' EXIT

# Pre-flight checks
preflight_check() {
    if [ "$TEST_THROTTLE_ENABLED" != "true" ]; then
        if [ "$VERBOSE" = "true" ]; then
            echo "Test throttling disabled via TEST_THROTTLE_ENABLED"
        fi
        return 0
    fi

    # Check current load
    if ! check_load; then
        echo "Error: System load too high to start tests" >&2
        echo "Current load: $(get_load), Max allowed: $MAX_LOAD" >&2
        echo "Wait for load to decrease or increase MAX_LOAD" >&2
        return 1
    fi

    return 0
}

# Get dynamic worker count
get_worker_count() {
    if [ "$TEST_THROTTLE_ENABLED" != "true" ]; then
        echo "auto"
        return
    fi

    local workers
    workers=$(suggest_workers)

    if [ "$VERBOSE" = "true" ]; then
        echo "Suggested pytest workers: $workers (based on current load)" >&2
    fi

    echo "$workers"
}

# Run pytest with monitoring
run_pytest_safely() {
    local pytest_args=("$@")
    local workers
    workers=$(get_worker_count)

    # Check if -n flag already provided
    local has_n_flag=false
    for arg in "${pytest_args[@]}"; do
        if [[ "$arg" == "-n" ]] || [[ "$arg" == "-n="* ]]; then
            has_n_flag=true
            break
        fi
    done

    # Add worker flag if not present and not 'auto'
    if [ "$has_n_flag" = false ] && [ "$workers" != "auto" ]; then
        pytest_args=("-n" "$workers" "${pytest_args[@]}")
    fi

    if [ "$VERBOSE" = "true" ]; then
        echo "Running pytest with args: ${pytest_args[*]}"
    fi

    # Run pytest with timeout
    if command -v timeout >/dev/null 2>&1; then
        # GNU timeout with process group kill
        timeout --kill-after=$((CLEANUP_GRACE_PERIOD + 5)) "$PYTEST_TIMEOUT" \
            pytest "${pytest_args[@]}" &
        local pytest_pid=$!
    else
        # Fallback without timeout command
        pytest "${pytest_args[@]}" &
        local pytest_pid=$!

        # Implement manual timeout
        (
            sleep "$PYTEST_TIMEOUT"
            if kill -0 "$pytest_pid" 2>/dev/null; then
                echo "Test timeout reached, terminating pytest" >&2
                cleanup_processes TERM
            fi
        ) &
        local timeout_pid=$!
    fi

    # Wait for pytest to complete
    local exit_code=0
    if wait "$pytest_pid"; then
        exit_code=0
    else
        exit_code=$?
    fi

    # Kill timeout watcher if still running
    if [ -n "${timeout_pid:-}" ] && kill -0 "$timeout_pid" 2>/dev/null; then
        kill "$timeout_pid" 2>/dev/null || true
    fi

    return $exit_code
}

# Main execution
main() {
    # Preflight checks
    if ! preflight_check; then
        exit 1
    fi

    # Run pytest with all arguments
    if run_pytest_safely "$@"; then
        exit 0
    else
        exit $?
    fi
}

# Run main function with all arguments
main "$@"
