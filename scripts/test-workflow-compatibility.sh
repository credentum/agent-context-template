#!/bin/bash
# test-workflow-compatibility.sh - Test GitHub Actions workflows locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Testing GitHub Actions Workflow Compatibility${NC}"
echo -e "${YELLOW}This validates that our workflows will work in CI/CD${NC}"
echo ""

# Create temporary config for testing
cp .ctxrc.yaml .ctxrc.yaml.backup
cat > .ctxrc.yaml.test << 'EOF'
# Test configuration for CI
system:
  schema_version: "1.0.0"
  created_date: "2025-07-11"

qdrant:
  version: "1.14.x"
  host: "qdrant"
  port: 6333
  collection_name: "project_context"
  embedding_model: "text-embedding-ada-002"
  ssl: false
  verify_ssl: true
  timeout: 30

neo4j:
  version: "5.x"
  host: "neo4j"
  port: 7687
  database: "context_graph"
  ssl: false
  verify_ssl: true
  timeout: 30

redis:
  version: "7.x"
  host: "redis"
  port: 6379
  database: 0
  ssl: false
  verify_ssl: true
  timeout: 30

storage:
  retention_days: 90
  archive_path: "context/archive"

agents:
  cleanup:
    schedule: "0 2 * * *"
    expire_after_days: 30

evaluation:
  cosine_threshold: 0.85
  schema_compliance_threshold: 1.0

security:
  sigstore_enabled: true
  ipfs_pinning: false

mcp:
  contracts_path: "context/mcp_contracts"
  rpc_timeout_seconds: 30
EOF

# Use test config
mv .ctxrc.yaml.test .ctxrc.yaml

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

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=30

    echo -e "${BLUE}▶ Waiting for $service_name...${NC}"

    for i in $(seq 1 $max_attempts); do
        if eval "$check_command" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        printf "."
        sleep 2
    done

    echo -e "  ${RED}✗ $service_name failed to start${NC}"
    return 1
}

# Test vector-graph-sync.yml workflow steps
echo -e "${YELLOW}=== Testing vector-graph-sync.yml workflow ===${NC}"
echo ""

# Wait for services (using service names within Docker network)
wait_for_service "Qdrant" "curl -f -s http://qdrant:6333/collections"
wait_for_service "Neo4j" "curl -f -s http://neo4j:7474"
wait_for_service "Redis" "redis-cli -h redis ping"

# Test health check script
test_step "Infrastructure health check" "bash infra/healthcheck.sh"

# Test Qdrant initialization
test_step "Qdrant initialization" "python -m src.storage.vector_db_init --skip-test"

# Test Neo4j initialization (this should handle Community Edition properly)
test_step "Neo4j initialization" "python -m src.storage.neo4j_init --username neo4j --password testpassword"

# Test context validation (should pass)
test_step "Context YAML validation" "python -m src.agents.context_lint validate context/"

# Test graph builder (without OpenAI key)
test_step "Graph builder dry run" "python -m src.storage.graph_builder context/ --username neo4j --password testpassword --dry-run"

# Test analytics stats (should work even without data)
test_step "Analytics stats" "python -m src.analytics.sum_scores_api stats"

echo ""
echo -e "${GREEN}🎉 All workflow compatibility tests passed!${NC}"
echo -e "${YELLOW}Your GitHub Actions workflows should work correctly${NC}"

# Restore original config
mv .ctxrc.yaml.backup .ctxrc.yaml
