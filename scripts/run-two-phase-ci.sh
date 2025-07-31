#!/bin/bash
# run-two-phase-ci.sh - Two-phase CI workflow orchestrator
# Phase 1: Run all tests in Docker and generate coverage artifacts
# Phase 2: Run ARC reviewer with LLM mode in Claude Code session

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Run two-phase CI workflow:"
    echo "  Phase 1: Docker CI tests (without ARC reviewer)"
    echo "  Phase 2: ARC reviewer with LLM mode (in Claude Code)"
    echo ""
    echo "Options:"
    echo "  --phase1-only    Only run Phase 1 (Docker tests)"
    echo "  --phase2-only    Only run Phase 2 (ARC reviewer)"
    echo "  --coverage-file  Path to coverage.json (default: test-artifacts/coverage.json)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run both phases"
    echo "  $0 --phase1-only            # Only run Docker tests"
    echo "  $0 --phase2-only            # Only run ARC reviewer"
}

# Parse arguments
PHASE1=true
PHASE2=true
COVERAGE_FILE="test-artifacts/coverage.json"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --phase1-only)
            PHASE2=false
            ;;
        --phase2-only)
            PHASE1=false
            ;;
        --coverage-file)
            COVERAGE_FILE="$2"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown parameter: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

echo -e "${GREEN}🚀 Two-Phase CI Workflow${NC}"
echo "=========================="

# Phase 1: Docker CI Tests
if [ "$PHASE1" = "true" ]; then
    echo -e "\n${BLUE}📦 Phase 1: Running Docker CI tests (without ARC reviewer)${NC}"
    echo "------------------------------------------------------------"
    
    # Clean up any existing test artifacts
    rm -rf test-artifacts
    mkdir -p test-artifacts
    
    # Run CI tests with --no-arc-reviewer flag
    echo -e "${YELLOW}Running comprehensive CI checks...${NC}"
    if ./scripts/run-ci-docker.sh all --no-arc-reviewer; then
        echo -e "${GREEN}✅ Phase 1 completed successfully${NC}"
        
        # Check if coverage files were generated
        if [ -f "test-artifacts/coverage.json" ] && [ -f "test-artifacts/coverage.xml" ]; then
            echo -e "${GREEN}✅ Coverage artifacts generated:${NC}"
            echo "  - test-artifacts/coverage.json"
            echo "  - test-artifacts/coverage.xml"
        else
            echo -e "${RED}❌ Coverage artifacts not found!${NC}"
            echo "Expected files:"
            echo "  - test-artifacts/coverage.json"
            echo "  - test-artifacts/coverage.xml"
            exit 1
        fi
    else
        echo -e "${RED}❌ Phase 1 failed!${NC}"
        exit 1
    fi
fi

# Phase 2: ARC Reviewer with LLM Mode
if [ "$PHASE2" = "true" ]; then
    echo -e "\n${BLUE}🤖 Phase 2: Running ARC reviewer with LLM mode${NC}"
    echo "-----------------------------------------------"
    
    # Check if we're in a Claude Code session
    if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
        echo -e "${YELLOW}⚠️  Warning: CLAUDE_CODE_OAUTH_TOKEN not found${NC}"
        echo "This phase requires running in a Claude Code session for LLM access."
        echo "The OAuth token is automatically provided in Claude Code environments."
    fi
    
    # Check if coverage file exists
    if [ ! -f "$COVERAGE_FILE" ]; then
        echo -e "${RED}❌ Coverage file not found: $COVERAGE_FILE${NC}"
        echo "Please run Phase 1 first to generate coverage artifacts."
        exit 1
    fi
    
    # Copy coverage files to standard locations if they're in test-artifacts
    if [ -f "test-artifacts/coverage.json" ] && [ "$COVERAGE_FILE" = "test-artifacts/coverage.json" ]; then
        echo -e "${YELLOW}Copying coverage files to standard locations...${NC}"
        cp test-artifacts/coverage.json coverage.json 2>/dev/null || true
        cp test-artifacts/coverage.xml coverage.xml 2>/dev/null || true
    fi
    
    # Run ARC reviewer with LLM mode
    echo -e "${YELLOW}Running ARC reviewer with LLM mode...${NC}"
    echo "Using coverage from standard location (coverage.json)"
    
    # Set PYTHONPATH to ensure imports work correctly
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    # Run ARC reviewer with LLM flag
    if python -m src.agents.arc_reviewer --llm; then
        echo -e "${GREEN}✅ Phase 2 completed successfully${NC}"
    else
        echo -e "${RED}❌ Phase 2 failed!${NC}"
        echo ""
        echo "Troubleshooting tips:"
        echo "1. Ensure you're running in a Claude Code session"
        echo "2. Check that coverage.json exists at: $COVERAGE_FILE"
        echo "3. Verify anthropic package is installed: pip install anthropic>=0.8.0"
        echo "4. Check for import errors in src/agents/llm_reviewer.py"
        exit 1
    fi
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Two-Phase CI Workflow Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$PHASE1" = "true" ] && [ "$PHASE2" = "true" ]; then
    echo -e "${GREEN}✅ Both phases completed successfully!${NC}"
    echo ""
    echo "Results:"
    echo "  • All CI checks passed"
    echo "  • Coverage artifacts generated"
    echo "  • ARC reviewer analysis complete with LLM insights"
elif [ "$PHASE1" = "true" ]; then
    echo -e "${GREEN}✅ Phase 1 (Docker CI) completed successfully!${NC}"
    echo ""
    echo "Coverage artifacts available in test-artifacts/"
    echo "Run with --phase2-only to execute ARC reviewer"
elif [ "$PHASE2" = "true" ]; then
    echo -e "${GREEN}✅ Phase 2 (ARC reviewer) completed successfully!${NC}"
fi

echo ""
echo "🚀 CI workflow complete!"