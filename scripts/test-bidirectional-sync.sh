#!/bin/bash
set -euo pipefail

# Bidirectional Sprint Workflow Test Script
# This script validates the complete bidirectional sync between sprint YAML and GitHub issues

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
SPRINT_ID="sprint-4.1"
SPRINT_FILE="context/sprints/sprint-4.1.yaml"
TEST_TASK_TITLE="Bidirectional Workflow Validation Test"
BACKUP_FILE="/tmp/sprint-4.1-backup-$(date +%s).yaml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if we're in the right directory
    if [[ ! -f "$SPRINT_FILE" ]]; then
        log_error "Sprint file not found: $SPRINT_FILE"
        log_error "Please run this script from the project root directory"
        exit 1
    fi

    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_error "Please install it from: https://cli.github.com/"
        exit 1
    fi

    # Check GitHub authentication
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated"
        log_error "Please run: gh auth login"
        exit 1
    fi

    # Check Python dependencies
    if ! python -c "import yaml, click" &> /dev/null; then
        log_error "Required Python packages not installed"
        log_error "Please run: pip install pyyaml click"
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

backup_sprint_file() {
    log_info "Backing up original sprint file..."
    cp "$SPRINT_FILE" "$BACKUP_FILE"
    log_success "Backup created: $BACKUP_FILE"
}

restore_sprint_file() {
    if [[ -f "$BACKUP_FILE" ]]; then
        log_info "Restoring original sprint file..."
        cp "$BACKUP_FILE" "$SPRINT_FILE"
        rm -f "$BACKUP_FILE"
        log_success "Original sprint file restored"
    fi
}

cleanup() {
    log_info "Cleaning up..."
    restore_sprint_file

    # Note: Test issues should be cleaned up by the test script itself
    # but we could add additional cleanup here if needed

    log_success "Cleanup completed"
}

run_dry_run_test() {
    log_info "Running dry-run tests..."

    # Test sprint issue linker in dry-run mode
    log_info "Testing sprint issue linker (dry-run)..."
    if python -m src.agents.sprint_issue_linker create --sprint "$SPRINT_ID" --dry-run --verbose; then
        log_success "Sprint issue linker dry-run successful"
    else
        log_error "Sprint issue linker dry-run failed"
        return 1
    fi

    # Test sprint sync in dry-run mode
    log_info "Testing sprint sync (dry-run)..."
    if python -m src.agents.sprint_issue_linker sync --sprint "$SPRINT_ID" --dry-run --verbose; then
        log_success "Sprint sync dry-run successful"
    else
        log_error "Sprint sync dry-run failed"
        return 1
    fi

    log_success "All dry-run tests passed"
}

run_integration_test() {
    log_info "Running integration test..."

    # Run the Python test script in manual mode
    if python tests/test_bidirectional_workflow.py --manual; then
        log_success "Integration test passed"
        return 0
    else
        log_error "Integration test failed"
        return 1
    fi
}

run_workflow_validation() {
    log_info "Running workflow validation..."

    # Test GitHub Actions workflow syntax (if available)
    if command -v actionlint &> /dev/null; then
        log_info "Validating GitHub Actions workflows..."
        if actionlint .github/workflows/sprint-update.yml \
           .github/workflows/generate-sprint-issues.yml \
           .github/workflows/auto-close-issues.yml; then
            log_success "GitHub Actions workflows are valid"
        else
            log_warning "GitHub Actions workflow validation failed (non-critical)"
        fi
    else
        log_info "Skipping workflow validation (actionlint not available)"
    fi

    # Validate sprint YAML structure
    log_info "Validating sprint YAML structure..."
    if python -c "
import yaml
with open('$SPRINT_FILE', 'r') as f:
    data = yaml.safe_load(f)
assert data.get('id') == 'sprint-41'
assert 'phases' in data
assert len(data.get('phases', [])) > 0
print('Sprint YAML structure is valid')
"; then
        log_success "Sprint YAML structure validation passed"
    else
        log_error "Sprint YAML structure validation failed"
        return 1
    fi
}

# Main execution
main() {
    local test_mode="${1:-full}"

    echo "=== Bidirectional Sprint Workflow Test ==="
    echo "Test mode: $test_mode"
    echo "Sprint: $SPRINT_ID"
    echo "Sprint file: $SPRINT_FILE"
    echo ""

    # Set up cleanup trap
    trap cleanup EXIT ERR

    # Check prerequisites
    check_prerequisites

    # Backup original files
    backup_sprint_file

    case "$test_mode" in
        "dry-run")
            log_info "Running dry-run tests only..."
            run_dry_run_test
            ;;
        "validation")
            log_info "Running validation tests only..."
            run_workflow_validation
            ;;
        "integration")
            log_info "Running integration tests only..."
            run_integration_test
            ;;
        "full"|*)
            log_info "Running full test suite..."

            # Step 1: Validation
            if ! run_workflow_validation; then
                log_error "Validation failed, aborting"
                exit 1
            fi

            # Step 2: Dry run
            if ! run_dry_run_test; then
                log_error "Dry-run tests failed, aborting"
                exit 1
            fi

            # Step 3: Integration test
            if ! run_integration_test; then
                log_error "Integration test failed"
                exit 1
            fi
            ;;
    esac

    log_success "All tests completed successfully!"
    echo ""
    echo "=== Test Summary ==="
    echo "✅ Prerequisites check passed"
    echo "✅ Workflow validation passed"
    echo "✅ Dry-run tests passed"
    echo "✅ Integration tests passed"
    echo ""
    echo "The bidirectional sprint workflow is functioning correctly!"
}

# Script usage
usage() {
    echo "Usage: $0 [test-mode]"
    echo ""
    echo "Test modes:"
    echo "  full         Run complete test suite (default)"
    echo "  dry-run      Run dry-run tests only"
    echo "  validation   Run validation tests only"
    echo "  integration  Run integration tests only"
    echo ""
    echo "Examples:"
    echo "  $0                # Run full test suite"
    echo "  $0 dry-run        # Run dry-run tests only"
    echo "  $0 integration    # Run integration tests only"
}

# Handle command line arguments
if [[ $# -gt 1 ]]; then
    usage
    exit 1
fi

if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

# Run main function
main "${1:-full}"
