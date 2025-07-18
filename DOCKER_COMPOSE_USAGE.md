# Docker Compose Usage Guide

This document explains the consolidated Docker Compose configuration for the agent-context-template project.

## Overview

The project now uses a consolidated Docker Compose setup to reduce port forwards from 22 to 5 total ports.

## Files Structure

### Base Configuration
- **`docker-compose.yml`**: Base configuration with all shared services
  - Qdrant (ports 6333, 6334)
  - Neo4j (ports 7474, 7687)
  - Redis (port 6379)

### Environment-Specific Overrides
- **`docker-compose.override.yml`**: Local development customizations (automatically applied)
- **`docker-compose.ci.yml`**: CI environment with testing services and optimizations

### Backup Files
- **`infra/docker-compose.yml.backup`**: Backup of previous production config
- **`docker-compose.ci-optimized.yml.backup`**: Backup of previous CI optimized config

## Usage

### Local Development
```bash
# Start all services (uses base + override automatically)
docker-compose up

# Start specific services
docker-compose up qdrant neo4j redis

# Stop all services
docker-compose down
```

### CI Testing
```bash
# Run CI lint checks
./scripts/run-ci-docker.sh

# Run specific CI services
docker-compose -f docker-compose.ci.yml run ci-black
docker-compose -f docker-compose.ci.yml run ci-context-lint

# Run with services
docker-compose -f docker-compose.ci.yml up redis qdrant neo4j
```

## Port Mapping

### Development (5 ports total)
- Qdrant HTTP: `6333:6333`
- Qdrant gRPC: `6334:6334`
- Neo4j HTTP: `7474:7474`
- Neo4j Bolt: `7687:7687`
- Redis: `6379:6379`

### CI Environment (5 ports total)
- Same ports as development
- CI-optimized configurations with reduced memory limits
- Faster health checks for CI speed
- Stronger authentication credentials for testing

### Environment Variables

The setup supports environment-specific authentication:

**Development**:
- `NEO4J_AUTH` - Defaults to `neo4j/devpassword` for local development
- Can be overridden: `NEO4J_AUTH=neo4j/mypassword docker-compose up`

**CI**:
- `NEO4J_CI_AUTH` - Defaults to `neo4j/ci-secure-test-password-2025`
- Stronger credentials for testing environments

**Production**:
- `NEO4J_AUTH` - Must be set for production deployment
- No insecure defaults provided

## Network Configuration

### Agent Context Network
The Docker Compose setup creates a custom network called `agent-context-network` that:

- **Purpose**: Provides isolated networking for all agent-context services
- **Benefits**:
  - Services can communicate using service names (e.g., `redis`, `qdrant`, `neo4j`)
  - Isolated from other Docker networks on the host
  - Consistent networking across development and CI environments
- **Usage**: All services automatically join this network
- **External Access**: Host ports are mapped for external access (6333, 6334, 7474, 7687, 6379)

## Key Improvements

### Port Reduction
- **Before**: 22 port forwards (multiple overlapping configs)
- **After**: 5 port forwards (single consolidated config)

### Configuration Management
- Single source of truth for service definitions
- Environment-specific overrides instead of duplication
- Consistent SHA-pinned Docker images for security

### Developer Experience
- Clear usage instructions for different environments
- Reduced confusion about which compose file to use
- Maintained backward compatibility for existing workflows

## Migration Notes

The consolidation eliminated duplicate service definitions while preserving all functionality:

1. **Merged Services**: Combined Qdrant, Neo4j, Redis from 3 separate files
2. **Removed Conflicts**: Eliminated port conflicts that required different port mappings
3. **Preserved Optimizations**: Maintained CI-specific memory and performance settings
4. **Updated Scripts**: All existing scripts continue to work without changes

## Troubleshooting

### Service Won't Start
```bash
# Check configuration syntax
docker-compose config

# Check for port conflicts
docker-compose ps
netstat -tlnp | grep :6333
```

### CI Issues
```bash
# Validate CI configuration
docker-compose -f docker-compose.ci.yml config

# Debug in CI environment
./scripts/run-ci-docker.sh debug
```

### Performance Issues
```bash
# Check resource usage
docker stats

# View service logs
docker-compose logs qdrant
docker-compose logs neo4j
docker-compose logs redis
```
