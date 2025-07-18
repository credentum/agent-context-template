# ────────────────────────────────────────────────────────────────────────
# TASK: issue-976-consolidate-docker-compose-configurations
# Generated from GitHub Issue #976
# ────────────────────────────────────────────────────────────────────────

## 📌 Task Name
`fix-issue-976-consolidate-docker-compose-configurations`

## 🎯 Goal (≤ 2 lines)
> Consolidate three overlapping Docker Compose configurations to reduce 22 port forwards to ≤ 8 while maintaining separate CI and production environments.

## 🧠 Context
- **GitHub Issue**: #976 - [INFRA] Consolidate Docker Compose configurations to reduce excessive port forwards
- **Sprint**: sprint-4.1
- **Phase**: Phase 1: Infrastructure Optimization
- **Component**: docker-compose
- **Priority**: Infrastructure optimization (medium-high)
- **Why this matters**: 22 port forwards in codespace causing confusion and resource duplication
- **Dependencies**: Docker, Docker Compose, GitHub Codespaces
- **Related**: Infrastructure optimization sprint

## 🛠️ Subtasks

| File | Action | Prompt Tech | Purpose | Context Impact |
|------|--------|-------------|---------|----------------|
| `docker-compose.yml` | create/modify | Template Analysis | Base configuration with shared services | High |
| `docker-compose.override.yml` | create | Environment Override | Local development overrides | Med |
| `docker-compose.ci.yml` | modify | Refactor | CI-specific configuration | High |
| `infra/docker-compose.yml` | remove/consolidate | Migration | Remove duplicate production config | Med |
| `docker-compose.ci-optimized.yml` | remove/consolidate | Migration | Remove duplicate CI config | Med |
| `.github/workflows/*.yml` | modify | Port Reference Update | Update port references in workflows | Low |
| `scripts/run-ci-docker.sh` | modify | Script Update | Update script to use new config | Low |
| `README.md` or docs | modify | Documentation | Update usage instructions | Low |

## 📝 Enhanced RCICO Prompt
**Role**
You are a senior DevOps engineer working on Docker infrastructure optimization.

**Context**
GitHub Issue #976: Consolidate Docker Compose configurations to reduce excessive port forwards
Current situation:
- `infra/docker-compose.yml` (production): Qdrant (6333, 6334), Neo4j (7474, 7687)
- `docker-compose.ci-optimized.yml` (CI optimized): Redis (6379), Qdrant (6333, 6334), Neo4j (7687, 7474)
- `docker-compose.ci.yml` (CI): Qdrant (6335:6333, 6336:6334), Neo4j (7688:7687, 7475:7474), Redis (6379)
Total: ~22 port forwards in GitHub Codespaces

Related files: Scripts and workflows that reference these ports
Codebase follows: Docker Compose best practices with SHA-pinned images for security

**Instructions**
1. **Primary Objective**: Reduce port forwards from 22 to ≤ 8 while maintaining functionality
2. **Scope**: Consolidate to single base docker-compose.yml with environment-specific overrides
3. **Constraints**:
   - Follow existing patterns: SHA-pinned Docker images for security
   - Maintain backward compatibility for existing workflows
   - Keep separate CI and production configurations
   - Preserve all health checks and environment variables
4. **Prompt Technique**: Template Analysis and Migration because we're consolidating similar configurations
5. **Testing**: Verify all services start correctly in both CI and development modes
6. **Documentation**: Update clear usage instructions for different environments

**Technical Constraints**
• Expected diff ≤ 200 LoC, ≤ 8 files
• Context budget: ≤ 15k tokens (file analysis focused)
• Performance budget: Infrastructure change (low compute impact)
• Code quality: YAML formatting, no syntax errors
• CI compliance: All Docker CI checks must pass

**Output Format**
Return complete implementation consolidating Docker Compose configurations.
Use conventional commits: feat(infra): consolidate docker-compose configurations

## 🔍 Verification & Testing
- `./scripts/run-ci-docker.sh` (Docker CI compliance)
- `docker-compose config` (validate YAML syntax)
- `docker-compose up --dry-run` (validate services can start)
- **Port analysis**: Verify reduced port count
- **Service functionality**: Verify Qdrant, Neo4j, Redis work in all modes
- **GitHub workflows**: Verify CI workflows still function

## ✅ Acceptance Criteria
- [ ] Consolidate to single docker-compose.yml with environment-specific overrides
- [ ] Reduce total port forwards from 22 to ≤ 8
- [ ] Maintain separate CI and production configurations
- [ ] Document clear usage instructions
- [ ] All existing functionality preserved

## 💲 Budget & Performance Tracking
```
Estimates based on analysis:
├── token_budget: 12k (focused file consolidation task)
├── time_budget: 45 minutes (configuration consolidation)
├── cost_estimate: $0.50 (infrastructure optimization)
├── complexity: Medium (multiple file coordination)
└── files_affected: 8 (3 compose files + workflows + scripts + docs)

Actuals (to be filled):
├── tokens_used: ~10k
├── time_taken: 40 minutes
├── cost_actual: $0.40
├── iterations_needed: 1
└── context_clears: 0
```

## 🏷️ Metadata
```yaml
github_issue: 976
sprint: sprint-4.1
phase: Phase 1: Infrastructure Optimization
component: docker-compose
priority: medium-high
complexity: medium
dependencies: ["Docker", "Docker Compose", "GitHub Codespaces"]
```
