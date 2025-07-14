# Issue #28: Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20

## Problem Statement
Need to create a reproducible Docker Compose stack with:
- Qdrant v1.14.x (port 6333)
- Neo4j 5.20 (ports 7474/7687)
- Named volumes for data persistence
- Neo4j with NEO4J_AUTH=none for dev
- Make targets for up/down operations
- Platform-agnostic image tags

## Acceptance Criteria
- [x] File `infra/docker-compose.yml` exists
- [x] `make up` starts Qdrant (6333) and Neo4j (7474/7687)
- [x] `make down` stops & removes volumes
- [x] Named volumes `qdrant_data`, `neo4j_data` created
- [x] Neo4j runs with `NEO4J_AUTH=none` for dev
- [x] README updates include quick-start prerequisites

## Investigation Notes
- Current directory structure shows no existing infra/ directory
- Existing Makefile exists - need to add up/down targets
- Need to research specific Qdrant v1.14.x and Neo4j 5.20 Docker images
- Should ensure multi-platform support (linux/amd64 & linux/arm64)

## Implementation Plan
1. Create infra/ directory structure
2. Research Docker image tags for Qdrant v1.14.x and Neo4j 5.20
3. Create docker-compose.yml with proper configuration
4. Update/create Makefile with up/down targets
5. Update README with quick-start instructions
6. Test the stack functionality

## Implementation Results
✅ **Completed Successfully**
- Created `infra/docker-compose.yml` with Qdrant v1.14.1 and Neo4j 5.20.0
- Added Makefile targets: `make up`, `make down`, `make health`
- Updated README with quick-start instructions
- Tested stack startup/shutdown - all services healthy
- Named volumes created: `qdrant_data`, `neo4j_data`, `neo4j_logs`
- Neo4j configured with `NEO4J_AUTH=none` for development

## Verification
- `curl localhost:6333/collections` returns `{"result":{"collections":[]},"status":"ok"}`
- `docker exec neo4j cypher-shell "RETURN 1"` returns `1`
- Both services start within 30 seconds and pass health checks
