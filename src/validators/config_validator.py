#!/usr/bin/env python3
"""
config_validator.py: Configuration validation for the Agent-First Context System
"""

from typing import List, Tuple

import click
import yaml


class ConfigValidator:
    """Validate configuration files for correctness and security"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_main_config(self, config_path: str = ".ctxrc.yaml") -> bool:
        """Validate main configuration file"""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            self.errors.append(f"Configuration file {config_path} not found")
            return False
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {config_path}: {e}")
            return False

        # Validate required sections
        required_sections = ["system", "qdrant", "neo4j", "storage", "agents"]
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section: {section}")

        # Validate Qdrant configuration
        if "qdrant" in config:
            qdrant = config["qdrant"]
            port = qdrant.get("port", 6333)
            if not isinstance(port, int):
                self.errors.append("qdrant.port must be an integer")
            elif port < 1 or port > 65535:
                self.errors.append("qdrant.port must be between 1 and 65535")

        # Validate Neo4j configuration
        if "neo4j" in config:
            neo4j = config["neo4j"]
            port = neo4j.get("port", 7687)
            if not isinstance(port, int):
                self.errors.append("neo4j.port must be an integer")
            elif port < 1 or port > 65535:
                self.errors.append("neo4j.port must be between 1 and 65535")

        # Validate Redis configuration
        if "redis" in config:
            redis_conf = config["redis"]
            port = redis_conf.get("port", 6379)
            if not isinstance(port, int):
                self.errors.append("redis.port must be an integer")
            elif port < 1 or port > 65535:
                self.errors.append("redis.port must be between 1 and 65535")

            db = redis_conf.get("database", 0)
            if not isinstance(db, int) or db < 0:
                self.errors.append("redis.database must be a non-negative integer")

        # Validate DuckDB configuration
        if "duckdb" in config:
            duckdb_conf = config["duckdb"]
            if "database_path" not in duckdb_conf:
                self.errors.append("duckdb.database_path is required")
            if (
                not isinstance(duckdb_conf.get("threads", 4), int)
                or duckdb_conf.get("threads", 4) < 1
            ):
                self.errors.append("duckdb.threads must be a positive integer")

        # Security warnings
        if config.get("qdrant", {}).get("ssl", False) is False:
            self.warnings.append("SSL is disabled for Qdrant - consider enabling for production")
        if config.get("neo4j", {}).get("ssl", False) is False:
            self.warnings.append("SSL is disabled for Neo4j - consider enabling for production")
        if config.get("redis", {}).get("ssl", False) is False:
            self.warnings.append("SSL is disabled for Redis - consider enabling for production")

        return len(self.errors) == 0

    def validate_performance_config(self, config_path: str = "performance.yaml") -> bool:
        """Validate performance configuration file"""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            # Performance config is optional
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in {config_path}: {e}")
            return False

        # Validate vector_db settings
        if "vector_db" in config:
            vdb = config["vector_db"]

            # Embedding settings
            if "embedding" in vdb:
                embed = vdb["embedding"]
                if (
                    not isinstance(embed.get("batch_size", 100), int)
                    or embed.get("batch_size", 100) < 1
                ):
                    self.errors.append("vector_db.embedding.batch_size must be a positive integer")
                if (
                    not isinstance(embed.get("max_retries", 3), int)
                    or embed.get("max_retries", 3) < 0
                ):
                    self.errors.append(
                        "vector_db.embedding.max_retries must be a non-negative integer"
                    )
                if (
                    not isinstance(embed.get("request_timeout", 30), (int, float))
                    or embed.get("request_timeout", 30) < 1
                ):
                    self.errors.append(
                        "vector_db.embedding.request_timeout must be a positive number"
                    )

            # Search settings
            if "search" in vdb:
                search = vdb["search"]
                if search.get("max_limit", 100) < search.get("default_limit", 10):
                    self.errors.append("vector_db.search.max_limit must be >= default_limit")

        # Validate graph_db settings
        if "graph_db" in config:
            gdb = config["graph_db"]

            # Connection pool
            if "connection_pool" in gdb:
                pool = gdb["connection_pool"]
                if pool.get("max_size", 10) < pool.get("min_size", 1):
                    self.errors.append("graph_db.connection_pool.max_size must be >= min_size")

            # Query settings
            if "query" in gdb:
                query = gdb["query"]
                if (
                    not isinstance(query.get("max_path_length", 5), int)
                    or query.get("max_path_length", 5) < 1
                ):
                    self.errors.append("graph_db.query.max_path_length must be a positive integer")
                if query.get("max_path_length", 5) > 10:
                    self.warnings.append(
                        "graph_db.query.max_path_length > 10 may cause performance issues"
                    )

        # Validate search settings
        if "search" in config:
            search = config["search"]
            if "ranking" in search:
                ranking = search["ranking"]
                if not isinstance(ranking.get("temporal_decay_rate", 0.01), (int, float)):
                    self.errors.append("search.ranking.temporal_decay_rate must be a number")
                if (
                    ranking.get("temporal_decay_rate", 0.01) < 0
                    or ranking.get("temporal_decay_rate", 0.01) > 1
                ):
                    self.errors.append("search.ranking.temporal_decay_rate must be between 0 and 1")

                # Validate type boosts
                if "type_boosts" in ranking:
                    for doc_type, boost in ranking["type_boosts"].items():
                        if not isinstance(boost, (int, float)) or boost < 0:
                            self.errors.append(
                                f"search.ranking.type_boosts.{doc_type} must be a "
                                "non-negative number"
                            )

        # Validate resources
        if "resources" in config:
            resources = config["resources"]
            if (
                not isinstance(resources.get("max_memory_gb", 4), (int, float))
                or resources.get("max_memory_gb", 4) < 0.5
            ):
                self.errors.append("resources.max_memory_gb must be at least 0.5")
            if (
                not isinstance(resources.get("max_cpu_percent", 80), (int, float))
                or resources.get("max_cpu_percent", 80) < 1
                or resources.get("max_cpu_percent", 80) > 100
            ):
                self.errors.append("resources.max_cpu_percent must be between 1 and 100")

        # Validate KV store settings
        if "kv_store" in config:
            kv = config["kv_store"]

            # Redis settings
            if "redis" in kv:
                redis = kv["redis"]
                if "connection_pool" in redis:
                    pool = redis["connection_pool"]
                    if pool.get("max_size", 50) < pool.get("min_size", 5):
                        self.errors.append(
                            "kv_store.redis.connection_pool.max_size must be >= min_size"
                        )

                if "cache" in redis:
                    cache = redis["cache"]
                    if (
                        not isinstance(cache.get("ttl_seconds", 3600), int)
                        or cache.get("ttl_seconds", 3600) < 1
                    ):
                        self.errors.append(
                            "kv_store.redis.cache.ttl_seconds must be a positive integer"
                        )

            # DuckDB settings
            if "duckdb" in kv:
                duckdb = kv["duckdb"]
                if "batch_insert" in duckdb:
                    batch = duckdb["batch_insert"]
                    if not isinstance(batch.get("size", 1000), int) or batch.get("size", 1000) < 1:
                        self.errors.append(
                            "kv_store.duckdb.batch_insert.size must be a positive integer"
                        )

                if "analytics" in duckdb:
                    analytics = duckdb["analytics"]
                    if (
                        not isinstance(analytics.get("retention_days", 90), int)
                        or analytics.get("retention_days", 90) < 1
                    ):
                        self.errors.append(
                            "kv_store.duckdb.analytics.retention_days must be a positive integer"
                        )

        return len(self.errors) == 0

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Validate all configuration files"""
        self.errors = []
        self.warnings = []

        # Validate main config
        main_valid = self.validate_main_config()

        # Validate performance config
        perf_valid = self.validate_performance_config()

        return main_valid and perf_valid, self.errors, self.warnings


@click.command()
@click.option("--config", default=".ctxrc.yaml", help="Main configuration file")
@click.option("--perf-config", default="performance.yaml", help="Performance configuration file")
@click.option("--strict", is_flag=True, help="Treat warnings as errors")
def main(config: str, perf_config: str, strict: bool):
    """Validate configuration files"""
    validator = ConfigValidator()

    click.echo("=== Configuration Validation ===\n")

    # Validate main config
    click.echo(f"Validating {config}...")
    validator.validate_main_config(config)

    # Validate performance config
    click.echo(f"Validating {perf_config}...")
    validator.validate_performance_config(perf_config)

    # Show results
    if validator.errors:
        click.echo("\nErrors:")
        for error in validator.errors:
            click.echo(f"  ❌ {error}")

    if validator.warnings:
        click.echo("\nWarnings:")
        for warning in validator.warnings:
            click.echo(f"  ⚠️  {warning}")

    if not validator.errors and not validator.warnings:
        click.echo("\n✅ All configurations are valid!")

    # Exit code
    if validator.errors or (strict and validator.warnings):
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
