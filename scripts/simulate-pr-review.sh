#!/bin/bash
# simulate-pr-review.sh - Local PR simulation environment for Claude Code Review
#
# This script creates a local simulation of GitHub Actions PR review environment
# without creating actual PRs. It works with the extracted ARC-Reviewer module
# to provide the same validation as GitHub CI.
#
# Usage:
#   ./scripts/simulate-pr-review.sh [options]
#
# Options:
#   --pr-number NUM     Simulate specific PR number (default: auto-generated)
#   --base-branch NAME  Base branch for comparison (default: main)
#   --mock-env         Enable full environment variable mocking
#   --verbose          Enable verbose output
#   --output-format    Output format: yaml|json|summary (default: summary)
#   --help             Show this help message
#
# Examples:
#   # Basic simulation with current branch
#   ./scripts/simulate-pr-review.sh
#
#   # Simulate specific PR number with verbose output
#   ./scripts/simulate-pr-review.sh --pr-number 1234 --verbose
#
#   # Full environment simulation with YAML output
#   ./scripts/simulate-pr-review.sh --mock-env --output-format yaml

set -e

# Source helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/pr-simulation-helpers.sh"

# Default configuration
PR_NUMBER=""
BASE_BRANCH="main"
MOCK_ENV=false
VERBOSE=false
OUTPUT_FORMAT="summary"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --pr-number)
                PR_NUMBER="$2"
                shift 2
                ;;
            --base-branch)
                BASE_BRANCH="$2"
                shift 2
                ;;
            --mock-env)
                MOCK_ENV=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --output-format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help message
show_help() {
    cat << EOF
Local PR Simulation Environment

This script simulates the GitHub Actions PR review environment locally,
allowing Claude Code to validate PR readiness before pushing to GitHub.

Usage: $0 [options]

Options:
  --pr-number NUM     Simulate specific PR number (default: auto-generated)
  --base-branch NAME  Base branch for comparison (default: main)
  --mock-env         Enable full environment variable mocking
  --verbose          Enable verbose output
  --output-format    Output format: yaml|json|summary (default: summary)
  --help             Show this help message

Examples:
  # Basic simulation
  $0

  # Verbose simulation with specific PR number
  $0 --pr-number 1234 --verbose

  # Full environment simulation
  $0 --mock-env --output-format yaml

Dependencies:
  - ARC-Reviewer module (src/agents/arc_reviewer.py)
  - Python 3.11+ with pytest and coverage
  - Git repository with main branch
EOF
}

# Main simulation function
simulate_pr_review() {
    log_info "🚀 Starting Local PR Review Simulation"

    # Validate prerequisites
    validate_prerequisites

    # Generate or validate PR number
    if [[ -z "$PR_NUMBER" ]]; then
        PR_NUMBER=$(generate_mock_pr_number)
        if [[ "$VERBOSE" == true ]]; then
            log_info "Generated mock PR number: $PR_NUMBER"
        fi
    fi

    # Set up simulation environment
    if [[ "$MOCK_ENV" == true ]]; then
        setup_mock_environment "$PR_NUMBER" "$BASE_BRANCH"
        if [[ "$VERBOSE" == true ]]; then
            log_info "Mock environment variables set up"
        fi
    fi

    # Get branch and diff information
    CURRENT_BRANCH=$(git branch --show-current)
    if [[ "$CURRENT_BRANCH" == "main" ]]; then
        log_error "Cannot simulate PR from main branch"
        exit 1
    fi

    if [[ "$VERBOSE" == true ]]; then
        log_info "Simulating PR from branch: $CURRENT_BRANCH"
        log_info "Comparing against: origin/$BASE_BRANCH"
    fi

    # Run ARC-Reviewer analysis
    log_info "🔍 Running ARC-Reviewer analysis..."
    run_arc_reviewer_analysis "$PR_NUMBER" "$BASE_BRANCH" "$OUTPUT_FORMAT"

    # Generate additional simulation data
    if [[ "$VERBOSE" == true ]]; then
        log_info "📊 Generating simulation metadata..."
        generate_simulation_metadata "$PR_NUMBER" "$CURRENT_BRANCH" "$BASE_BRANCH"
    fi

    log_success "✅ PR simulation completed"
}

# Validate that all prerequisites are met
validate_prerequisites() {
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi

    # Check if ARC-Reviewer module exists
    if [[ ! -f "${REPO_ROOT}/src/agents/arc_reviewer.py" ]]; then
        log_error "ARC-Reviewer module not found at src/agents/arc_reviewer.py"
        log_error "Please ensure issue #1130 (ARC-Reviewer extraction) is completed"
        exit 1
    fi

    # Check if Python and required modules are available
    if ! command -v python &> /dev/null; then
        log_error "Python not found in PATH"
        exit 1
    fi

    # Check if pytest is available
    if ! python -c "import pytest" &> /dev/null; then
        log_error "pytest not found. Please install with: pip install pytest"
        exit 1
    fi

    # Check if coverage is available
    if ! python -c "import coverage" &> /dev/null; then
        log_error "coverage not found. Please install with: pip install coverage"
        exit 1
    fi

    # Check if main branch exists
    if ! git show-ref --verify --quiet refs/remotes/origin/$BASE_BRANCH; then
        log_warning "Remote branch origin/$BASE_BRANCH not found, using local $BASE_BRANCH"
        if ! git show-ref --verify --quiet refs/heads/$BASE_BRANCH; then
            log_error "Base branch $BASE_BRANCH not found"
            exit 1
        fi
    fi

    if [[ "$VERBOSE" == true ]]; then
        log_success "All prerequisites validated"
    fi
}

# Run ARC-Reviewer analysis
run_arc_reviewer_analysis() {
    local pr_number="$1"
    local base_branch="$2"
    local output_format="$3"

    cd "${REPO_ROOT}"

    # Prepare arguments for ARC-Reviewer
    local args=""
    if [[ "$VERBOSE" == true ]]; then
        args="$args --verbose"
    fi

    # Run the ARC-Reviewer
    local review_result=""
    if [[ "$output_format" == "yaml" ]]; then
        # Get YAML output directly
        review_result=$(python -m src.agents.arc_reviewer --pr "$pr_number" --base "$base_branch" $args)
        echo "$review_result"
    elif [[ "$output_format" == "json" ]]; then
        # Convert YAML to JSON
        review_result=$(python -m src.agents.arc_reviewer --pr "$pr_number" --base "$base_branch" $args)
        echo "$review_result" | python -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(sys.stdin.read()), indent=2))"
    else
        # Generate summary format
        review_result=$(python -m src.agents.arc_reviewer --pr "$pr_number" --base "$base_branch" $args)
        generate_review_summary "$review_result" "$pr_number" "$base_branch"
    fi
}

# Generate review summary from YAML output
generate_review_summary() {
    local yaml_output="$1"
    local pr_number="$2"
    local base_branch="$3"

    echo "📋 PR Review Simulation Summary"
    echo "═══════════════════════════════════════════════════════════════"
    echo "PR Number:      $pr_number (simulated)"
    echo "Base Branch:    $base_branch"
    echo "Current Branch: $(git branch --show-current)"
    echo "Timestamp:      $(date)"
    echo ""

    # Parse YAML output to extract key information
    python << EOF
import yaml
import sys

yaml_data = """$yaml_output"""
try:
    data = yaml.safe_load(yaml_data)

    # Extract verdict
    verdict = data.get('verdict', 'UNKNOWN')
    print(f"🎯 Verdict: {verdict}")

    # Extract coverage information
    coverage = data.get('coverage', {})
    current_pct = coverage.get('current_pct', 0)
    meets_baseline = coverage.get('meets_baseline', False)
    baseline_status = "✅ PASS" if meets_baseline else "❌ FAIL"
    print(f"📊 Coverage: {current_pct}% {baseline_status}")

    # Extract issues
    issues = data.get('issues', {})
    blocking = issues.get('blocking', [])
    warnings = issues.get('warnings', [])
    nits = issues.get('nits', [])

    print(f"🚫 Blocking Issues: {len(blocking)}")
    if blocking:
        for issue in blocking[:3]:  # Show first 3
            print(f"   • {issue.get('description', 'Unknown issue')}")
        if len(blocking) > 3:
            print(f"   ... and {len(blocking) - 3} more")

    print(f"⚠️  Warnings: {len(warnings)}")
    if warnings:
        for warning in warnings[:2]:  # Show first 2
            print(f"   • {warning.get('description', 'Unknown warning')}")
        if len(warnings) > 2:
            print(f"   ... and {len(warnings) - 2} more")

    print(f"💡 Nits: {len(nits)}")

    # Summary verdict
    print("")
    if verdict == "APPROVE":
        print("🎉 PR Ready: This PR would pass automated review!")
    else:
        print("🔧 Needs Work: Address blocking issues before creating PR")

except Exception as e:
    print(f"Error parsing review output: {e}")
    print("Raw output:")
    print(yaml_data)
EOF
}

# Main execution
main() {
    parse_arguments "$@"
    simulate_pr_review
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
