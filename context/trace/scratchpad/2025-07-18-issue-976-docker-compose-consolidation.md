# Docker Compose Consolidation - Issue #976
**Date**: 2025-07-18
**Issue**: [#976 - Consolidate Docker Compose configurations](https://github.com/repo/issues/976)
**Sprint**: sprint-4.1
**Phase**: Phase 1: Infrastructure Optimization

## Task Template Reference
`context/trace/task-templates/issue-976-consolidate-docker-compose-configurations.md`

## Token Budget & Complexity Assessment
- **Estimated tokens**: 12k
- **Estimated time**: 45 minutes
- **Complexity**: Medium (multiple file coordination)
- **Files affected**: 8 (3 compose files + workflows + scripts + docs)

## Current Port Analysis
### Current Configurations:
1. **infra/docker-compose.yml** (4 ports):
   - Qdrant: 6333, 6334
   - Neo4j: 7474, 7687

2. **docker-compose.ci-optimized.yml** (5 ports):
   - Redis: 6379
   - Qdrant: 6333, 6334
   - Neo4j: 7687, 7474

3. **docker-compose.ci.yml** (5 ports + conflicts):
   - Qdrant: 6335:6333, 6336:6334
   - Neo4j: 7688:7687, 7475:7474
   - Redis: 6379

**Total**: ~14 direct port mappings + GitHub Actions services = ~22 port forwards

## Implementation Plan

### Phase 1: Analysis Complete ✅
- Analyzed all three Docker Compose files
- Identified port conflicts and duplications
- Created task template

### Phase 2: Consolidation Strategy
1. **Create base `docker-compose.yml`**:
   - Merge common services (Qdrant, Neo4j, Redis)
   - Use standard ports (6333, 6334, 7474, 7687, 6379)
   - Total: 5 ports maximum

2. **Create `docker-compose.override.yml`** (development):
   - Local development customizations
   - Override any dev-specific settings

3. **Refactor `docker-compose.ci.yml`**:
   - Keep CI-specific optimizations
   - Use same base services, CI-optimized configs
   - Remove port conflicts

4. **Remove redundant files**:
   - `infra/docker-compose.yml` → consolidate into main
   - `docker-compose.ci-optimized.yml` → consolidate features into ci.yml

### Phase 3: Update References
- Update `.github/workflows/*.yml` for any port references
- Update `scripts/run-ci-docker.sh`
- Update documentation

### Phase 4: Testing & Validation
- Verify all services start correctly
- Test CI workflows
- Confirm port reduction achieved

## Target Port Count: ≤ 8
**Proposed final state**: 5 ports (Qdrant: 2, Neo4j: 2, Redis: 1)
