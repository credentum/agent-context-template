#!/bin/bash
# test-workflow-simple.sh - Simple workflow validation without external services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Simple Workflow Validation${NC}"
echo -e "${YELLOW}Testing workflow components without external services${NC}"
echo ""

# Function to test a step
test_step() {
    local step_name=$1
    local command=$2

    echo -e "${BLUE}▶ Testing: $step_name${NC}"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "  ${RED}✗ FAILED${NC}"
        echo -e "  ${YELLOW}Command: $command${NC}"
        # Show the actual error
        eval "$command" || true
        return 1
    fi
}

# Test basic Python imports
test_step "Python imports" "python -c 'import src.storage.neo4j_init, src.storage.vector_db_init, src.storage.graph_builder'"

# Test context validation (should pass)
test_step "Context YAML validation" "python -m src.agents.context_lint validate context/"

# Test Neo4j init without connection
test_step "Neo4j init help" "python -m src.storage.neo4j_init --help"

# Test vector DB init without connection
test_step "Vector DB init help" "python -m src.storage.vector_db_init --help"

# Test graph builder without connection
test_step "Graph builder help" "python -m src.storage.graph_builder --help"

# Test analytics without connection
test_step "Analytics help" "python -m src.analytics.sum_scores_api --help"

# Test healthcheck script exists
test_step "Healthcheck script exists" "test -f infra/healthcheck.sh"

echo ""
echo -e "${GREEN}🎉 Simple workflow validation passed!${NC}"
echo -e "${YELLOW}Core workflow components are properly configured${NC}"
