# CI Optimization Guide

This guide covers the advanced CI optimization features implemented in Phase 4 of the CI migration project. These features are designed to reduce CI execution time by 50% or more through intelligent caching, distributed execution, incremental builds, and hardware optimization.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Caching System](#caching-system)
4. [Distributed CI](#distributed-ci)
5. [Incremental Builds](#incremental-builds)
6. [Hardware Detection](#hardware-detection)
7. [Analytics Dashboard](#analytics-dashboard)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

## Overview

The CI optimization system consists of several integrated components:

- **Cache Manager**: Content-addressable caching for dependencies and build artifacts
- **Distributed Coordinator**: Multi-runner job scheduling and load balancing
- **Incremental Build Analyzer**: Smart rebuild detection based on dependency analysis
- **Hardware Detector**: GPU and specialized hardware capability detection
- **Analytics System**: Performance monitoring and trend analysis

All features are **opt-in by default** and backward compatible with existing CI workflows.

## Quick Start

### Enable Basic Optimizations

1. **Configure optimization settings**:
   ```bash
   # Copy the default configuration
   cp config/ci-optimization.yaml.example config/ci-optimization.yaml

   # Enable basic optimizations
   vim config/ci-optimization.yaml
   ```

2. **Set up local caching**:
   ```bash
   # Initialize cache manager
   ./scripts/ci-cache-manager.py stats

   # Test caching
   ./scripts/ci-cache-manager.py --verbose
   ```

3. **Enable in your CI workflow**:
   ```yaml
   # Add to .github/workflows/ci-unified.yml
   env:
     CI_OPTIMIZATION_ENABLED: "true"
     CI_CACHE_ENABLED: "true"
   ```

### Verify Setup

```bash
# Check system capabilities
./scripts/ci-hardware-detector.py detect

# Analyze project for incremental builds
./scripts/incremental-build-analyzer.py scan

# View current metrics
./dashboards/ci-analytics/metrics.py summary
```

## Caching System

The caching system provides intelligent, content-addressable storage for CI artifacts.

### Features

- **Content-addressable storage**: Files cached by SHA-256 hash of content
- **Multiple backends**: Local filesystem, Redis, S3 (configurable)
- **Smart invalidation**: Automatic cleanup based on dependency changes
- **Compression support**: Optional compression for large artifacts
- **TTL management**: Configurable time-to-live for cache entries

### Usage

#### Basic Caching

```bash
# Cache command output
./scripts/ci-cache-manager.py cache \
  --command "pytest tests/" \
  --dependencies "src/ tests/ requirements.txt" \
  --output-path "./test-results/"

# Retrieve cached output
./scripts/ci-cache-manager.py get \
  --command "pytest tests/" \
  --dependencies "src/ tests/ requirements.txt"
```

#### Cache Management

```bash
# View cache statistics
./scripts/ci-cache-manager.py stats

# Clean up expired entries
./scripts/ci-cache-manager.py cleanup

# Clear entire cache
./scripts/ci-cache-manager.py clear
```

#### Integration with CI

```yaml
# Example GitHub Actions integration
- name: Check cache
  id: cache-check
  run: |
    CACHE_KEY=$(./scripts/ci-cache-manager.py get-key \
      --command "npm test" \
      --dependencies "package.json src/ tests/")

    if ./scripts/ci-cache-manager.py has-cache $CACHE_KEY; then
      echo "cache_hit=true" >> $GITHUB_OUTPUT
    else
      echo "cache_hit=false" >> $GITHUB_OUTPUT
    fi

- name: Run tests
  if: steps.cache-check.outputs.cache_hit != 'true'
  run: npm test

- name: Cache results
  if: steps.cache-check.outputs.cache_hit != 'true'
  run: |
    ./scripts/ci-cache-manager.py cache \
      --command "npm test" \
      --dependencies "package.json src/ tests/" \
      --output-path "./coverage/"
```

### Configuration

```yaml
# config/ci-optimization.yaml
cache:
  enabled: true
  backend: "local"  # local, redis, s3

  local:
    cache_dir: ".ci-cache"
    max_size_mb: 5000
    compression: true

  targets:
    dependencies: true
    build_artifacts: true
    test_results: true
```

## Distributed CI

The distributed CI system enables job execution across multiple runners with intelligent load balancing.

### Architecture

- **Coordinator**: Central job scheduler and load balancer
- **Runners**: Worker nodes that execute jobs
- **Redis Backend**: Message queue and state storage
- **Job Queue**: Priority-based job scheduling

### Setup

#### Start Coordinator

```bash
# Start the CI coordinator
./scripts/distributed-ci-coordinator.py coordinator \
  --redis-url "redis://localhost:6379" \
  --node-id "main-coordinator"
```

#### Register Runners

```bash
# Start a runner on each available machine
./scripts/distributed-ci-coordinator.py runner \
  --runner-id "runner-$(hostname)" \
  --redis-url "redis://localhost:6379"
```

#### Submit Jobs

```bash
# Submit a job to the distributed system
./scripts/distributed-ci-coordinator.py submit \
  --command "pytest tests/test_module.py" \
  --requirements "python" "docker"
```

### Features

- **Automatic load balancing**: Jobs distributed to least-loaded runners
- **Capability matching**: Jobs routed to runners with required capabilities
- **Fault tolerance**: Failed jobs automatically retried on different runners
- **Health monitoring**: Automatic detection and removal of failed runners
- **Result aggregation**: Centralized collection of job results

### Configuration

```yaml
# config/ci-optimization.yaml
distributed:
  enabled: true
  coordinator:
    redis_url: "redis://localhost:6379"
    job_queue_size: 1000
    heartbeat_interval: 30

  runners:
    auto_discovery: true
    load_balancing: "least_loaded"

  scheduling:
    timeout_default: 3600
    retry_max: 2
    parallel_limit: 10
```

## Incremental Builds

The incremental build system analyzes file dependencies to determine what needs rebuilding.

### Features

- **Dependency graph analysis**: Understands file relationships across languages
- **Git-based change detection**: Uses git diff to identify changed files
- **Language support**: Python, JavaScript, TypeScript, Docker, YAML
- **Smart test selection**: Runs only tests affected by changes
- **Build artifact reuse**: Reuses previous build outputs when possible

### Usage

#### Analyze Project

```bash
# Scan project and build dependency graph
./scripts/incremental-build-analyzer.py scan --output dependency-graph.json

# Show project statistics
./scripts/incremental-build-analyzer.py stats
```

#### Determine What to Rebuild

```bash
# Analyze changes since last commit
./scripts/incremental-build-analyzer.py analyze --base-ref HEAD~1

# Specify changed files explicitly
./scripts/incremental-build-analyzer.py analyze \
  --changed-files "src/module.py" "tests/test_module.py"
```

#### Generate Build Commands

```bash
# Generate optimized build commands
./scripts/incremental-build-analyzer.py build --base-ref HEAD~1

# Execute generated commands
./scripts/incremental-build-analyzer.py build --base-ref HEAD~1 --execute
```

### Integration Example

```yaml
# .github/workflows/incremental-build.yml
name: Incremental Build

on: [push, pull_request]

jobs:
  analyze-changes:
    runs-on: ubuntu-latest
    outputs:
      build-commands: ${{ steps.analyze.outputs.commands }}
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 2  # Need previous commit for diff

      - name: Analyze changes
        id: analyze
        run: |
          ./scripts/incremental-build-analyzer.py build \
            --base-ref ${{ github.event.before }} > build-commands.json
          echo "commands=$(cat build-commands.json)" >> $GITHUB_OUTPUT

  incremental-build:
    needs: analyze-changes
    runs-on: ubuntu-latest
    strategy:
      matrix:
        command: ${{ fromJson(needs.analyze-changes.outputs.build-commands) }}
    steps:
      - uses: actions/checkout@v3
      - name: Execute build command
        run: ${{ matrix.command.command }}
```

### Configuration

```yaml
# config/ci-optimization.yaml
incremental:
  enabled: true

  languages:
    python:
      enabled: true
      test_selection: "affected"
      type_checking: "incremental"

    javascript:
      enabled: true
      build_cache: true
      test_selection: "affected"

  change_detection:
    method: "git"
    base_ref: "origin/main"
    ignore_patterns:
      - "*.md"
      - "docs/**"
```

## Hardware Detection

The hardware detection system identifies available capabilities for job routing.

### Features

- **GPU detection**: NVIDIA, AMD, and Intel GPU support
- **CUDA/OpenCL detection**: Compute framework availability
- **Resource assessment**: CPU, memory, and storage capabilities
- **Docker support**: Container runtime detection
- **Capability matching**: Job routing based on requirements

### Usage

#### Detect Hardware

```bash
# Full hardware detection
./scripts/ci-hardware-detector.py detect

# GPU detection only
./scripts/ci-hardware-detector.py gpu

# Generate runner configuration
./scripts/ci-hardware-detector.py config --job-requirements gpu cuda
```

#### Check Job Compatibility

```bash
# Check if system can run GPU jobs
./scripts/ci-hardware-detector.py check --requirements gpu cuda docker

# Output example:
{
  "can_run": true,
  "missing_requirements": [],
  "checked_requirements": ["gpu", "cuda", "docker"]
}
```

### Job Requirements

Common requirement tags:

- **basic**: Standard CPU/memory jobs
- **gpu**: Requires GPU acceleration
- **cuda**: Requires NVIDIA CUDA support
- **docker**: Requires Docker containers
- **high-memory**: Requires 16GB+ RAM
- **ssd-storage**: Requires SSD storage

### Configuration

```yaml
# config/ci-optimization.yaml
hardware:
  gpu:
    enabled: true
    detection: "auto"
    job_routing: "capability_based"

  limits:
    cpu_cores: null  # Auto-detect
    memory_gb: null  # Auto-detect
    disk_space_gb: 100
```

## Analytics Dashboard

The analytics system provides performance monitoring and trend analysis.

### Features

- **Build performance tracking**: Execution times, success rates, cache hit rates
- **Resource utilization monitoring**: CPU, memory, disk, and network usage
- **Historical trends**: Performance changes over time
- **Cache analysis**: Hit/miss rates and retrieval times
- **Export capabilities**: JSON, CSV, and Prometheus formats

### Usage

#### View Performance Summary

```bash
# Last 24 hours
./dashboards/ci-analytics/metrics.py summary --hours 24

# Performance trends over 7 days
./dashboards/ci-analytics/metrics.py trends --days 7
```

#### Export Metrics

```bash
# Export to JSON
./dashboards/ci-analytics/metrics.py export \
  --output metrics.json --format json --hours 48

# Export to CSV
./dashboards/ci-analytics/metrics.py export \
  --output metrics.csv --format csv --hours 24
```

#### Maintenance

```bash
# Clean up old metrics (keep last 90 days)
./dashboards/ci-analytics/metrics.py cleanup --days 90
```

### Web Dashboard

Start the web dashboard:

```bash
# Start dashboard server
python -m dashboards.ci_analytics.server --port 8080

# Access at http://localhost:8080
```

### Configuration

```yaml
# config/ci-optimization.yaml
analytics:
  enabled: true

  metrics:
    execution_times: true
    cache_performance: true
    resource_utilization: true

  dashboard:
    enabled: true
    port: 8080
    refresh_interval: 30

  alerts:
    performance_degradation: true
    cache_miss_threshold: 30
    failure_rate_threshold: 10
```

## Configuration

The central configuration file `config/ci-optimization.yaml` controls all optimization features.

### Key Settings

```yaml
# Global optimization toggle
optimization:
  enabled: true
  mode: "opt-in"
  performance_target:
    execution_time_reduction: 50
    cache_hit_rate: 80

# Feature toggles
cache:
  enabled: true
  backend: "local"

distributed:
  enabled: false  # Opt-in

incremental:
  enabled: true

hardware:
  gpu:
    enabled: false  # Opt-in

analytics:
  enabled: true
```

### Environment Variables

```bash
# Override configuration via environment
export CI_OPTIMIZATION_ENABLED="true"
export CI_CACHE_BACKEND="redis"
export CI_CACHE_REDIS_URL="redis://cache-server:6379"
export CI_DISTRIBUTED_ENABLED="true"
export CI_ANALYTICS_ENABLED="true"
```

## Troubleshooting

### Common Issues

#### Cache Misses

**Problem**: Low cache hit rate despite unchanged dependencies.

**Solutions**:
```bash
# Check cache statistics
./scripts/ci-cache-manager.py stats

# Enable verbose logging
./scripts/ci-cache-manager.py --verbose

# Verify dependency tracking
./scripts/incremental-build-analyzer.py scan --verbose
```

#### Distributed CI Failures

**Problem**: Jobs failing on distributed runners.

**Solutions**:
```bash
# Check coordinator status
./scripts/distributed-ci-coordinator.py coordinator --check-health

# Verify runner connectivity
./scripts/distributed-ci-coordinator.py runner --test-connection

# Review job logs
redis-cli LRANGE ci:job_results 0 -1
```

#### Hardware Detection Issues

**Problem**: GPU not detected despite being available.

**Solutions**:
```bash
# Manual GPU detection
./scripts/ci-hardware-detector.py gpu --verbose

# Check CUDA installation
nvcc --version
nvidia-smi

# Verify drivers
./scripts/ci-hardware-detector.py detect --verbose
```

### Debug Mode

Enable debug mode for detailed logging:

```yaml
# config/ci-optimization.yaml
debug:
  enabled: true
  verbose_logging: true
  performance_profiling: true
  cache_debugging: true
```

### Log Locations

- **Cache logs**: `.ci-cache/cache.log`
- **Distributed CI logs**: `/tmp/ci-coordinator.log`
- **Analytics logs**: `.ci-analytics/analytics.log`
- **Hardware detection logs**: `/tmp/hardware-detector.log`

## Performance Tuning

### Cache Optimization

```yaml
# Increase cache size for better hit rates
cache:
  local:
    max_size_mb: 10000  # 10GB
    compression: true

# Use Redis for team sharing
cache:
  backend: "redis"
  redis:
    url: "redis://shared-cache:6379"
    ttl_hours: 336  # 2 weeks
```

### Distributed CI Optimization

```yaml
# Increase parallelism
distributed:
  scheduling:
    parallel_limit: 20
    timeout_default: 1800  # 30 minutes

# Optimize load balancing
distributed:
  runners:
    load_balancing: "capability_based"
    capacity_multiplier: 1.5
```

### Resource Limits

```yaml
# Prevent resource exhaustion
performance:
  max_concurrent_builds: 4
  max_concurrent_tests: 8

  memory_limits:
    cache_manager: 1024  # MB
    build_processes: 2048  # MB
```

### Monitoring Thresholds

```yaml
# Adjust alert thresholds
analytics:
  alerts:
    cache_miss_threshold: 20  # More sensitive
    failure_rate_threshold: 5  # More sensitive
    performance_degradation: true
```

## Advanced Features

### Predictive Caching

Enable experimental predictive caching:

```yaml
feature_flags:
  experimental:
    smart_test_selection: true
    build_prediction: true
    adaptive_parallelism: true
```

### Custom Hardware Requirements

Define custom hardware requirements:

```python
# In your CI script
job_requirements = [
    "gpu",
    "cuda",
    "high-memory",
    "ssd-storage",
    "custom:tensorflow"  # Custom requirement
]

# Check compatibility
can_run, missing = detector.can_run_job(job_requirements)
```

### Integration with External Systems

#### Prometheus Metrics

```yaml
# Export metrics to Prometheus
analytics:
  export:
    format: "prometheus"
    endpoint: "http://prometheus:9090/metrics"
    frequency: "minutely"
```

#### Slack Notifications

```bash
# Set up Slack webhook for alerts
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Alerts will be sent to Slack channel
```

## Migration Guide

### From Standard CI

1. **Phase 1**: Enable caching only
   ```yaml
   optimization:
     enabled: true
   cache:
     enabled: true
   ```

2. **Phase 2**: Add incremental builds
   ```yaml
   incremental:
     enabled: true
   ```

3. **Phase 3**: Enable distributed CI
   ```yaml
   distributed:
     enabled: true
   ```

4. **Phase 4**: Add hardware optimization
   ```yaml
   hardware:
     gpu:
       enabled: true
   ```

### Rollback Procedure

If issues occur, disable optimizations:

```yaml
optimization:
  enabled: false
```

Or use environment variable:
```bash
export CI_OPTIMIZATION_ENABLED="false"
```

## Performance Targets

Expected improvements with full optimization:

- **Execution time reduction**: 50-70%
- **Cache hit rate**: 80-95%
- **Resource utilization efficiency**: 85%+
- **Cost reduction**: 40-60%

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review logs with debug mode enabled
3. Create an issue with performance metrics and configuration details
