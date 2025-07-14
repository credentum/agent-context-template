⚠️  GitHub CLI not authenticated, issue tracking will be limited
# Sprint 4.1: Infrastructure Bring-Up
**Status**: in_progress
**Period**: 2025-07-14 to 2025-07-21

## Phase Progress
- **Phase 1: Docker Infrastructure Setup** ✅
  - {'title': 'Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20', 'description': 'Author a reproducible Docker Compose stack pinned to Qdrant v1.14.x and Neo4j 5.20.\n\n## Acceptance Criteria\n- [x] File `infra/docker-compose.yml` exists.\n- [x] `make up` starts Qdrant (6333) and Neo4j (7474/7687); `make down` stops & removes volumes.\n- [x] Named volumes `qdrant_data`, `neo4j_data` created.\n- [x] Neo4j runs with `NEO4J_AUTH=none` for dev.\n- [x] README updates include quick-start prerequisites.\n\n## Implementation Notes\n- mkdir -p infra\n- Populate compose with pinned images and volumes\n- Ensure platform-agnostic (linux/amd64 & linux/arm64) tags if available.\n', 'labels': ['sprint-current', 'phase:4.1', 'component:infra', 'priority:high'], 'dependencies': [], 'estimate': '4 hours', 'github_issue': 28}
- **Phase 2: Health Check Implementation** ⏳
  - {'title': 'Add infra/healthcheck.sh smoke test', 'description': 'Create a bash script verifying Qdrant and Neo4j are healthy after `make up`.\n\n## Acceptance Criteria\n- [ ] `infra/healthcheck.sh` exits 0 on healthy stack.\n- [ ] Script checks:\n      curl localhost:6333/collections ⇒ `[]`\n      python -c "from neo4j import GraphDatabase; GraphDatabase.driver(\'bolt://localhost:7687\').verify_connectivity()"\n- [ ] Neo4j driver added to `requirements-dev.txt`.\n- [ ] CONTRIBUTING updated with run instructions.\n\n## Implementation Notes\n- chmod +x infra/healthcheck.sh\n- add to Makefile: make health\n', 'labels': ['sprint-current', 'phase:4.1', 'component:infra', 'priority:high'], 'dependencies': ['Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20'], 'estimate': '2 hours', 'github_issue': 29}
- **Phase 3: CI Integration** ⏳
  - {'title': 'Configure GitHub Actions service containers', 'description': 'Spin up Qdrant and Neo4j as service containers in CI to run all test jobs against live stores.\n\n## Acceptance Criteria\n- [ ] `ci.yml` includes `services:` for Qdrant v1.14.x and Neo4j 5.20.\n- [ ] Tests run green on live services.\n- [ ] Docker layers cached; total CI spin-up < 4 minutes.\n\n## Implementation Notes\n- Use GitHub Actions service-container syntax\n- Ensure ports match compose stack.\n', 'labels': ['sprint-current', 'phase:4.1', 'component:ci', 'priority:high'], 'dependencies': ['Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20'], 'estimate': '3 hours', 'github_issue': 30}
- **Phase 4: Validation & Testing** ⏳
  - {'title': 'Embedder sanity test with README.md', 'description': 'Index README.md via embed pipeline and confirm both vector and graph entries exist.\n\n## Acceptance Criteria\n- [ ] New test `tests/smoke/test_embed_readme.py` passes.\n- [ ] Qdrant vector count ≥ 1; corresponding Neo4j node present.\n\n## Implementation Notes\n- pytest -k test_embed_readme\n- use qdrant_client & neo4j driver inside test.\n', 'labels': ['sprint-current', 'phase:4.1', 'component:vector', 'priority:medium'], 'dependencies': ['Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20', 'Configure GitHub Actions service containers'], 'estimate': '2 hours', 'github_issue': 31}
- **Phase 5: Developer Experience** ⏳
  - {'title': 'Makefile convenience targets', 'description': 'Provide `make up`, `make down`, `make health` for local development.\n\n## Acceptance Criteria\n- [ ] Make targets wrap docker-compose and healthcheck script.\n- [ ] Root README documents usage.\n\n## Implementation Notes\n- .PHONY: up down health\n', 'labels': ['sprint-current', 'phase:4.1', 'component:dx', 'priority:low'], 'dependencies': ['Draft docker-compose.yml for Qdrant v1.14.x & Neo4j 5.20', 'Add infra/healthcheck.sh smoke test'], 'estimate': '1 hour', 'github_issue': 32}
- **Phase 6: Security** ⏳
  - {'title': 'Sigstore sign compose & images', 'description': 'Begin supply-chain integrity chain for infra artefacts using Sigstore/cosign.\n\n## Acceptance Criteria\n- [ ] cosign signatures committed under `context/logs/signatures/infra/`.\n- [ ] CI step verifies signatures before tests execute.\n\n## Implementation Notes\n- cosign sign --key k.json docker.io/qdrant/qdrant@sha256:...\n- cosign verify ...\n', 'labels': ['sprint-current', 'phase:4.1', 'component:security', 'priority:medium'], 'dependencies': [], 'estimate': '3 hours', 'github_issue': 33}

## Goals
- Establish reproducible local development infrastructure
- Set up CI service containers for reliable testing
- Implement health checks and automation for infrastructure
- Ensure platform-agnostic Docker setup

## Success Metrics
- **task_completion**: 100 percent
- **ci_reliability**: 95 percent
- **setup_time**: 4 minutes
