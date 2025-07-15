#!/bin/bash

# Health check script for Qdrant and Neo4j services
# Exits 0 if both services are healthy, non-zero otherwise

# Note: Not using 'set -e' to allow checking both services even if one fails

# Default configuration
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
NEO4J_HOST="${NEO4J_HOST:-localhost}"
NEO4J_PORT="${NEO4J_PORT:-7687}"
NEO4J_USER="${NEO4J_USER:-}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-}"
CURL_TIMEOUT="${CURL_TIMEOUT:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Exit codes
SUCCESS=0
QDRANT_FAIL=1
NEO4J_FAIL=2
PYTHON_FAIL=3

# Function to check Qdrant
check_qdrant() {
    echo "📊 Checking Qdrant health..."

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl is not available${NC}"
        return $QDRANT_FAIL
    fi

    # Check Qdrant collections endpoint
    local response
    if ! response=$(curl -s -f --max-time "$CURL_TIMEOUT" "http://${QDRANT_HOST}:${QDRANT_PORT}/collections" 2>/dev/null); then
        echo -e "${RED}❌ Qdrant: Failed to connect to ${QDRANT_HOST}:${QDRANT_PORT}/collections${NC}"
        return $QDRANT_FAIL
    fi

    # Parse the response - should contain an empty collections array
    # Response format: {"result":{"collections":[]},"status":"ok"}
    if echo "$response" | grep -q '"collections":\[\]'; then
        echo -e "${GREEN}✅ Qdrant: Healthy (collections endpoint responsive)${NC}"
        return $SUCCESS
    else
        echo -e "${RED}❌ Qdrant: Unexpected response format${NC}"
        echo "   Response: $response"
        return $QDRANT_FAIL
    fi
}

# Function to check Neo4j
check_neo4j() {
    echo "🗄️  Checking Neo4j health..."

    # Check if python is available
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python is not available${NC}"
        return $PYTHON_FAIL
    fi

    # Use python3 if available, otherwise python
    local python_cmd
    python_cmd=$(command -v python3 || command -v python)
    if [ -z "$python_cmd" ]; then
        echo -e "${RED}❌ Neither python3 nor python found${NC}"
        return $PYTHON_FAIL
    fi

    # Test Neo4j connectivity using the driver
    local neo4j_test_result

    neo4j_test_result=$($python_cmd -c "
import sys
import os
try:
    from neo4j import GraphDatabase

    # Check for authentication
    neo4j_user = os.environ.get('NEO4J_USER', '')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', '')

    if neo4j_user and neo4j_password:
        driver = GraphDatabase.driver('bolt://${NEO4J_HOST}:${NEO4J_PORT}', auth=(neo4j_user, neo4j_password))
    else:
        driver = GraphDatabase.driver('bolt://${NEO4J_HOST}:${NEO4J_PORT}')

    driver.verify_connectivity()
    driver.close()
    print('SUCCESS')
except ImportError:
    print('ERROR: neo4j module not found. Run: pip install neo4j>=5.0.0')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)

    local neo4j_exit_code=$?

    if [ $neo4j_exit_code -eq 0 ] && echo "$neo4j_test_result" | grep -q "SUCCESS"; then
        echo -e "${GREEN}✅ Neo4j: Healthy (driver connectivity verified)${NC}"
        return $SUCCESS
    else
        echo -e "${RED}❌ Neo4j: Connection failed${NC}"
        echo "   Error: $neo4j_test_result"
        return $NEO4J_FAIL
    fi
}

# Main execution
main() {
    local qdrant_status=0
    local neo4j_status=0

    echo "🔍 Checking infrastructure health..."
    echo "🚀 Starting health checks..."
    echo

    # Check Qdrant
    check_qdrant
    qdrant_status=$?

    echo

    # Check Neo4j
    check_neo4j
    neo4j_status=$?

    echo
    echo "📋 Health Check Summary:"

    # Report results
    if [ $qdrant_status -eq 0 ]; then
        echo -e "   Qdrant: ${GREEN}✅ Healthy${NC}"
    else
        echo -e "   Qdrant: ${RED}❌ Failed${NC}"
    fi

    if [ $neo4j_status -eq 0 ]; then
        echo -e "   Neo4j:  ${GREEN}✅ Healthy${NC}"
    else
        echo -e "   Neo4j:  ${RED}❌ Failed${NC}"
    fi

    # Overall result
    if [ $qdrant_status -eq 0 ] && [ $neo4j_status -eq 0 ]; then
        echo
        echo -e "${GREEN}🎉 All services are healthy!${NC}"
        exit $SUCCESS
    else
        echo
        echo -e "${RED}💥 One or more services are unhealthy${NC}"

        # Exit with the first error code encountered
        if [ $qdrant_status -ne 0 ]; then
            exit $qdrant_status
        else
            exit $neo4j_status
        fi
    fi
}

# Help function
show_help() {
    echo "Infrastructure Health Check Script"
    echo
    echo "Usage: $0 [--help]"
    echo
    echo "This script checks the health of Qdrant and Neo4j services."
    echo
    echo "Exit codes:"
    echo "  0 - All services healthy"
    echo "  1 - Qdrant failed"
    echo "  2 - Neo4j failed"
    echo "  3 - Python not available"
    echo
    echo "Environment Variables:"
    echo "  QDRANT_HOST     - Qdrant hostname (default: localhost)"
    echo "  QDRANT_PORT     - Qdrant port (default: 6333)"
    echo "  NEO4J_HOST      - Neo4j hostname (default: localhost)"
    echo "  NEO4J_PORT      - Neo4j bolt port (default: 7687)"
    echo "  NEO4J_USER      - Neo4j username (optional, for authenticated instances)"
    echo "  NEO4J_PASSWORD  - Neo4j password (optional, for authenticated instances)"
    echo "  CURL_TIMEOUT    - Curl timeout in seconds (default: 10)"
    echo
    echo "Prerequisites:"
    echo "  - curl (for Qdrant health check)"
    echo "  - python/python3 with neo4j driver (pip install neo4j>=5.0.0)"
    echo "  - Services running on configured hosts/ports"
    echo
    echo "Examples:"
    echo "  # Check default localhost setup"
    echo "  ./healthcheck.sh"
    echo
    echo "  # Check remote services"
    echo "  QDRANT_HOST=qdrant.example.com NEO4J_HOST=neo4j.example.com ./healthcheck.sh"
    echo
    echo "  # Check authenticated Neo4j"
    echo "  NEO4J_USER=neo4j NEO4J_PASSWORD=mypassword ./healthcheck.sh"
    echo
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
