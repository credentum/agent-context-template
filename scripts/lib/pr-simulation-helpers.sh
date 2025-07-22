#!/bin/bash
# pr-simulation-helpers.sh - Helper functions for PR simulation environment
#
# This file contains utility functions used by simulate-pr-review.sh
# to mock PR environment variables, generate metadata, and handle simulation.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${CYAN}🔍 $1${NC}"
    fi
}

# Generate a mock PR number based on branch and timestamp
generate_mock_pr_number() {
    local branch_name=$(git branch --show-current)
    local timestamp=$(date +%s)

    # Generate a deterministic but unique number based on branch and time
    # This ensures consistent PR numbers for the same branch within a short time
    local hash=$(echo "${branch_name}-${timestamp}" | sha256sum | cut -c1-8)
    local decimal_hash=$(printf "%d" "0x${hash}")
    local pr_num=$((decimal_hash % 9000 + 1000))  # Range: 1000-9999

    echo "$pr_num"
}

# Set up mock GitHub Actions environment variables
setup_mock_environment() {
    local pr_number="$1"
    local base_branch="$2"
    local current_branch=$(git branch --show-current)
    local repo_name=$(basename "$(git rev-parse --show-toplevel)")
    local commit_sha=$(git rev-parse HEAD)

    # Mock GitHub Actions environment
    export GITHUB_ACTIONS="true"
    export GITHUB_WORKFLOW="PR Simulation"
    export GITHUB_RUN_ID="simulation-$(date +%s)"
    export GITHUB_RUN_NUMBER="1"
    export GITHUB_JOB="simulate-pr-review"
    export GITHUB_ACTION="simulate-pr-review"
    export GITHUB_ACTOR="claude-local"
    export GITHUB_REPOSITORY="$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/' || echo "local/${repo_name}")"
    export GITHUB_WORKSPACE="$(git rev-parse --show-toplevel)"
    export GITHUB_SHA="$commit_sha"
    export GITHUB_REF="refs/heads/${current_branch}"
    export GITHUB_HEAD_REF="$current_branch"
    export GITHUB_BASE_REF="$base_branch"
    export GITHUB_EVENT_NAME="pull_request"
    export GITHUB_EVENT_PATH="/tmp/github_event_${pr_number}.json"

    # Mock PR-specific environment
    export PR_NUMBER="$pr_number"
    export PR_HEAD_SHA="$commit_sha"
    export PR_BASE_SHA="$(git rev-parse origin/${base_branch} 2>/dev/null || git rev-parse ${base_branch})"

    # Create mock event payload
    create_mock_event_payload "$pr_number" "$current_branch" "$base_branch" "$commit_sha"

    log_debug "Mock environment variables set:"
    log_debug "  GITHUB_REPOSITORY: $GITHUB_REPOSITORY"
    log_debug "  PR_NUMBER: $PR_NUMBER"
    log_debug "  GITHUB_HEAD_REF: $GITHUB_HEAD_REF"
    log_debug "  GITHUB_BASE_REF: $GITHUB_BASE_REF"
    log_debug "  GITHUB_SHA: $GITHUB_SHA"
}

# Create mock GitHub event payload JSON
create_mock_event_payload() {
    local pr_number="$1"
    local current_branch="$2"
    local base_branch="$3"
    local commit_sha="$4"
    local repo_name=$(basename "$(git rev-parse --show-toplevel)")
    local commit_message=$(git log -1 --pretty=%B)

    cat > "/tmp/github_event_${pr_number}.json" << EOF
{
  "action": "synchronize",
  "number": ${pr_number},
  "pull_request": {
    "id": ${pr_number}00,
    "number": ${pr_number},
    "state": "open",
    "draft": false,
    "title": "Simulated PR: ${current_branch}",
    "body": "This is a simulated PR for local testing.\n\nBranch: ${current_branch}\nBase: ${base_branch}",
    "head": {
      "ref": "${current_branch}",
      "sha": "${commit_sha}",
      "repo": {
        "name": "${repo_name}",
        "full_name": "local/${repo_name}"
      }
    },
    "base": {
      "ref": "${base_branch}",
      "sha": "$(git rev-parse origin/${base_branch} 2>/dev/null || git rev-parse ${base_branch})",
      "repo": {
        "name": "${repo_name}",
        "full_name": "local/${repo_name}"
      }
    },
    "user": {
      "login": "claude-local",
      "type": "User"
    },
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "repository": {
    "name": "${repo_name}",
    "full_name": "local/${repo_name}",
    "default_branch": "${base_branch}"
  },
  "sender": {
    "login": "claude-local",
    "type": "User"
  }
}
EOF

    log_debug "Mock event payload created at: /tmp/github_event_${pr_number}.json"
}

# Generate simulation metadata and statistics
generate_simulation_metadata() {
    local pr_number="$1"
    local current_branch="$2"
    local base_branch="$3"

    echo ""
    echo "📊 Simulation Metadata"
    echo "─────────────────────────────────────────────────────────"

    # Git statistics
    local commits_ahead=$(git rev-list --count origin/${base_branch}..HEAD 2>/dev/null || git rev-list --count ${base_branch}..HEAD)
    local changed_files=$(git diff --name-only origin/${base_branch}...HEAD 2>/dev/null || git diff --name-only ${base_branch}...HEAD | wc -l)
    local insertions=$(git diff --shortstat origin/${base_branch}...HEAD 2>/dev/null || git diff --shortstat ${base_branch}...HEAD | grep -o '[0-9]\+ insertion' | grep -o '[0-9]\+' || echo "0")
    local deletions=$(git diff --shortstat origin/${base_branch}...HEAD 2>/dev/null || git diff --shortstat ${base_branch}...HEAD | grep -o '[0-9]\+ deletion' | grep -o '[0-9]\+' || echo "0")

    echo "Commits ahead:    $commits_ahead"
    echo "Files changed:    $changed_files"
    echo "Lines added:      $insertions"
    echo "Lines removed:    $deletions"
    echo "Branch:           $current_branch → $base_branch"
    echo "Simulation ID:    sim-${pr_number}"
    echo ""

    # Show changed files if verbose
    if [[ "$VERBOSE" == true ]]; then
        echo "📁 Changed Files:"
        git diff --name-only origin/${base_branch}...HEAD 2>/dev/null || git diff --name-only ${base_branch}...HEAD | head -10 | while read file; do
            echo "  • $file"
        done

        local total_files=$(git diff --name-only origin/${base_branch}...HEAD 2>/dev/null || git diff --name-only ${base_branch}...HEAD | wc -l)
        if [[ $total_files -gt 10 ]]; then
            echo "  ... and $((total_files - 10)) more files"
        fi
        echo ""
    fi
}

# Calculate test coverage matching GitHub CI format exactly
calculate_coverage_matching_ci() {
    local coverage_format="$1"  # json, xml, term, or thresholds

    # Run the exact same coverage command as GitHub CI (.github/workflows/test-coverage.yml)
    cd "$(git rev-parse --show-toplevel)"

    log_info "🔍 Running coverage calculation (matching GitHub CI)..."

    # Clean any existing coverage data first (matching CI)
    rm -f .coverage* coverage.xml coverage.json > /dev/null 2>&1
    find . -name ".coverage*" -type f -delete 2>/dev/null || true

    # Use exact same command as GitHub Actions test-coverage.yml lines 73-78
    local coverage_cmd=(
        "python" "-m" "pytest"
        "--cov=src"
        "--cov-report=term-missing:skip-covered"
        "--cov-report=xml"
        "--cov-report=json"
        "-v"
    )

    # Set same environment variables as GitHub CI
    export REDIS_HOST=localhost
    export REDIS_PORT=6379

    if [[ "$VERBOSE" == true ]]; then
        log_debug "Running coverage calculation: ${coverage_cmd[*]}"
        log_debug "Environment: REDIS_HOST=$REDIS_HOST REDIS_PORT=$REDIS_PORT"
    fi

    # Run coverage and capture results
    local coverage_output
    if coverage_output=$("${coverage_cmd[@]}" 2>&1); then
        if [[ "$VERBOSE" == true ]]; then
            log_success "Coverage calculation completed successfully"
        fi

        if [[ -f "coverage.json" ]]; then
            case "$coverage_format" in
                "json")
                    cat coverage.json
                    ;;
                "percentage")
                    python -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.2f}\")"
                    ;;
                "summary")
                    python -c "
import json
data = json.load(open('coverage.json'))
totals = data['totals']
print(f\"Coverage: {totals['percent_covered']:.2f}%\")
print(f\"Lines: {totals['covered_lines']}/{totals['num_statements']}\")
print(f\"Branches: {totals.get('covered_branches', 0)}/{totals.get('num_branches', 0)}\")
print(f\"Functions: {totals.get('covered_functions', 0)}/{totals.get('num_functions', 0)}\")
"
                    ;;
                "thresholds")
                    run_coverage_threshold_checks
                    ;;
                *)
                    echo "Coverage calculation completed"
                    ;;
            esac
        else
            log_warning "Coverage report not generated"
            return 1
        fi
    else
        log_error "Coverage calculation failed"
        if [[ "$VERBOSE" == true ]]; then
            echo "Coverage output:"
            echo "$coverage_output"
        fi
        return 1
    fi
}

# Run coverage threshold checks exactly like GitHub CI
run_coverage_threshold_checks() {
    log_info "📊 Running coverage threshold checks (matching GitHub CI)..."

    # Step 1: Run coverage_summary.py (matching CI line 85)
    if python scripts/coverage_summary.py; then
        log_success "Coverage summary check passed"
    else
        log_error "Coverage summary check failed"
        return 1
    fi

    # Step 2: Enforce coverage thresholds using centralized config (matching CI lines 89-91)
    local threshold
    if threshold=$(python scripts/get_coverage_threshold.py); then
        log_info "Using coverage threshold: ${threshold}%"

        if python -m coverage report --fail-under="$threshold"; then
            log_success "Coverage threshold check passed (≥${threshold}%)"
            return 0
        else
            log_error "Coverage threshold check failed (<${threshold}%)"
            return 1
        fi
    else
        log_error "Failed to get coverage threshold from configuration"
        return 1
    fi
}

# Get coverage data in same format as GitHub CI
get_coverage_data_for_review() {
    if [[ ! -f "coverage.json" ]]; then
        log_error "coverage.json not found - run coverage calculation first"
        return 1
    fi

    # Parse coverage.json to extract metrics in ARC-Reviewer format
    python -c "
import json
try:
    with open('coverage.json') as f:
        data = json.load(f)
    totals = data['totals']

    # Get threshold for baseline comparison
    with open('.coverage-config.json') as f:
        config = json.load(f)
    baseline = config.get('baseline', 78.0)
    tolerance_buffer = config.get('tolerance_buffer', 5.0)
    minimum_threshold = baseline - tolerance_buffer

    current_pct = totals['percent_covered']
    meets_baseline = current_pct >= minimum_threshold

    print(f'current_pct:{current_pct:.2f}')
    print(f'meets_baseline:{meets_baseline}')
    print(f'baseline_threshold:{baseline}')
    print(f'minimum_threshold:{minimum_threshold:.1f}')
    print(f'covered_lines:{totals[\"covered_lines\"]}')
    print(f'total_lines:{totals[\"num_statements\"]}')
except Exception as e:
    print(f'error:{e}')
"
}

# Validate git diff analysis works locally
validate_git_diff_analysis() {
    local base_branch="$1"

    # Check if we can generate diff
    local diff_output
    if diff_output=$(git diff origin/${base_branch}...HEAD 2>/dev/null || git diff ${base_branch}...HEAD); then
        local diff_lines=$(echo "$diff_output" | wc -l)
        log_debug "Git diff analysis: $diff_lines lines of diff generated"
        return 0
    else
        log_error "Git diff analysis failed"
        return 1
    fi
}

# Clean up simulation environment
cleanup_simulation() {
    local pr_number="$1"

    # Remove temporary files
    if [[ -n "$pr_number" && -f "/tmp/github_event_${pr_number}.json" ]]; then
        rm -f "/tmp/github_event_${pr_number}.json"
        log_debug "Cleaned up mock event payload"
    fi

    # Unset mock environment variables
    unset GITHUB_ACTIONS GITHUB_WORKFLOW GITHUB_RUN_ID GITHUB_RUN_NUMBER
    unset GITHUB_JOB GITHUB_ACTION GITHUB_ACTOR GITHUB_REPOSITORY
    unset GITHUB_WORKSPACE GITHUB_SHA GITHUB_REF GITHUB_HEAD_REF
    unset GITHUB_BASE_REF GITHUB_EVENT_NAME GITHUB_EVENT_PATH
    unset PR_NUMBER PR_HEAD_SHA PR_BASE_SHA

    log_debug "Mock environment variables cleaned up"
}

# Trap cleanup on script exit
trap 'cleanup_simulation "$PR_NUMBER"' EXIT
