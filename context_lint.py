#!/usr/bin/env python3
"""
context-lint: YAML validation tool for the Agent-First Context System

Usage:
    context-lint validate <path> [--fix] [--verbose]
    context-lint check-config
    context-lint stats <path>
    context-lint --version
    context-lint --help

Commands:
    validate    Validate YAML files against schemas
    check-config    Validate .ctxrc.yaml configuration
    stats      Show statistics about context documents

Options:
    --fix      Auto-fix common issues (update last_modified, etc.)
    --verbose  Show detailed validation output
    --version  Show version
    --help     Show this help message
"""

import os
import sys
import yaml
import json
import fcntl
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import click
import yamale
from yamale import YamaleError


class ContextLinter:
    """Main linter class for context system validation"""

    # Class-level schema cache
    _schema_cache: Dict[str, Any] = {}

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.schema_dir = Path(__file__).parent / "context" / "schemas"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.fixed_count = 0
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .ctxrc.yaml"""
        try:
            with open(".ctxrc.yaml", "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            if self.verbose:
                click.echo("Warning: .ctxrc.yaml not found, using defaults")
        except yaml.YAMLError as e:
            if self.verbose:
                click.echo(f"Warning: Invalid YAML in .ctxrc.yaml: {e}")
        except IOError as e:
            if self.verbose:
                click.echo(f"Warning: Could not read .ctxrc.yaml: {e}")

        # Return default config with configurable thresholds
        return {
            "linter": {"warning_days_old": 90, "warning_days_until_expire": 7},
            "storage": {"retention_days": 90},
            "agents": {"cleanup": {"expire_after_days": 30}},
        }

    def _get_cached_schema(self, schema_file: Path) -> Any:
        """Get schema from cache or load and cache it"""
        cache_key = str(schema_file)

        if cache_key not in ContextLinter._schema_cache:
            if self.verbose:
                click.echo(f"Loading schema: {schema_file.name}")
            ContextLinter._schema_cache[cache_key] = yamale.make_schema(str(schema_file))

        return ContextLinter._schema_cache[cache_key]

    def validate_file(self, file_path: Path, fix: bool = False) -> bool:
        """Validate a single YAML file against its schema"""
        try:
            # Load the YAML file
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            if not data:
                self.errors.append(f"{file_path}: Empty file")
                return False

            # Determine document type and schema
            doc_type = data.get("document_type")
            if not doc_type:
                self.errors.append(f"{file_path}: Missing document_type field")
                return False

            # Try full schema first, then fall back to original
            schema_file = self.schema_dir / f"{doc_type}_full.yaml"
            if not schema_file.exists():
                schema_file = self.schema_dir / f"{doc_type}.yaml"

            if not schema_file.exists():
                self.errors.append(f"{file_path}: Unknown document type '{doc_type}'")
                return False

            # Validate against schema (with caching)
            schema = self._get_cached_schema(schema_file)
            data_obj = yamale.make_data(str(file_path))

            try:
                yamale.validate(schema, data_obj)
                if self.verbose:
                    click.echo(f"✓ {file_path}: Valid {doc_type} document")
            except YamaleError as e:
                self.errors.append(f"{file_path}: {str(e)}")
                return False

            # Additional validations and fixes
            if fix:
                fixed = self._apply_fixes(file_path, data)
                if fixed:
                    self.fixed_count += 1

            # Check for warnings
            self._check_warnings(file_path, data)

            return True

        except yaml.YAMLError as e:
            self.errors.append(f"{file_path}: Invalid YAML - {str(e)}")
            return False
        except Exception as e:
            self.errors.append(f"{file_path}: {str(e)}")
            return False

    def _apply_fixes(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Apply automatic fixes to common issues"""
        fixed = False
        today = datetime.now().strftime("%Y-%m-%d")

        # Update last_modified if file was changed
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
        if data.get("last_modified") != file_mtime:
            data["last_modified"] = today
            fixed = True
            if self.verbose:
                click.echo(f"  Fixed: Updated last_modified to {today}")

        # Update last_referenced to today
        if data.get("last_referenced") != today:
            data["last_referenced"] = today
            fixed = True
            if self.verbose:
                click.echo(f"  Fixed: Updated last_referenced to {today}")

        # Save fixed file with atomic write
        if fixed:
            # Write to temporary file first
            temp_fd, temp_path = tempfile.mkstemp(dir=file_path.parent, text=True)
            try:
                with os.fdopen(temp_fd, "w") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

                # Atomic rename
                os.replace(temp_path, file_path)
            except Exception:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

        return fixed

    def _check_warnings(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Check for non-critical issues that should be warnings"""
        # Get configurable thresholds
        warning_days_until_expire = self.config.get("linter", {}).get(
            "warning_days_until_expire", 7
        )
        warning_days_old = self.config.get("linter", {}).get("warning_days_old", 90)

        # Check if document is about to expire
        expires = data.get("expires")
        if expires:
            expire_date = datetime.strptime(expires, "%Y-%m-%d")
            days_until = (expire_date - datetime.now()).days
            if 0 < days_until <= warning_days_until_expire:
                self.warnings.append(f"{file_path}: Document expires in {days_until} days")

        # Check if document hasn't been modified in a while
        last_modified = data.get("last_modified")
        if last_modified:
            mod_date = datetime.strptime(last_modified, "%Y-%m-%d")
            days_old = (datetime.now() - mod_date).days
            if days_old > warning_days_old:
                self.warnings.append(
                    f"{file_path}: Document hasn't been modified in {days_old} days"
                )

    def validate_directory(self, path: Path, fix: bool = False) -> Tuple[int, int]:
        """Recursively validate all YAML files in a directory"""
        valid_count = 0
        total_count = 0

        for yaml_file in path.rglob("*.yaml"):
            # Skip schema files
            if "schemas" in yaml_file.parts:
                continue

            total_count += 1
            if self.validate_file(yaml_file, fix=fix):
                valid_count += 1

        return valid_count, total_count

    def check_config(self) -> bool:
        """Validate .ctxrc.yaml configuration file"""
        config_path = Path(".ctxrc.yaml")
        if not config_path.exists():
            self.errors.append(".ctxrc.yaml not found")
            return False

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Check required sections
            required_sections = ["system", "qdrant", "neo4j", "storage", "agents"]
            for section in required_sections:
                if section not in config:
                    self.errors.append(f".ctxrc.yaml: Missing required section '{section}'")
                    return False

            # Validate Qdrant version
            qdrant_version = config.get("qdrant", {}).get("version")
            if not qdrant_version or not qdrant_version.startswith("1.14."):
                self.warnings.append(
                    f".ctxrc.yaml: Qdrant version should be 1.14.x, found '{qdrant_version}'"
                )

            if self.verbose:
                click.echo("✓ .ctxrc.yaml: Valid configuration")

            return True

        except yaml.YAMLError as e:
            self.errors.append(f".ctxrc.yaml: Invalid YAML - {str(e)}")
            return False

    def show_stats(self, path: Path) -> None:
        """Show statistics about context documents"""
        stats = {"total_files": 0, "by_type": {}, "by_status": {}, "expired": 0, "expiring_soon": 0}

        for yaml_file in path.rglob("*.yaml"):
            if "schemas" in yaml_file.parts:
                continue

            try:
                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                stats["total_files"] += 1

                # Count by type
                doc_type = data.get("document_type", "unknown")
                stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1

                # Count by status
                status = data.get("status", "unknown")
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

                # Check expiration
                expires = data.get("expires")
                if expires:
                    expire_date = datetime.strptime(expires, "%Y-%m-%d")
                    days_until = (expire_date - datetime.now()).days
                    if days_until < 0:
                        stats["expired"] += 1
                    elif days_until <= 7:
                        stats["expiring_soon"] += 1

            except Exception:
                continue

        # Display stats
        click.echo("\nContext System Statistics")
        click.echo("=" * 40)
        click.echo(f"Total documents: {stats['total_files']}")

        click.echo("\nBy Type:")
        for doc_type, count in sorted(stats["by_type"].items()):
            click.echo(f"  {doc_type}: {count}")

        click.echo("\nBy Status:")
        for status, count in sorted(stats["by_status"].items()):
            click.echo(f"  {status}: {count}")

        click.echo(f"\nExpired documents: {stats['expired']}")
        click.echo(f"Expiring within 7 days: {stats['expiring_soon']}")


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """YAML validation tool for the Agent-First Context System"""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="Auto-fix common issues")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def validate(path, fix, verbose):
    """Validate YAML files against schemas"""
    linter = ContextLinter(verbose=verbose)
    path_obj = Path(path)

    if path_obj.is_file():
        success = linter.validate_file(path_obj, fix=fix)
        valid_count = 1 if success else 0
        total_count = 1
    else:
        valid_count, total_count = linter.validate_directory(path_obj, fix=fix)

    # Show results
    click.echo(f"\nValidation Results:")
    click.echo(f"  Valid: {valid_count}/{total_count}")

    if fix and linter.fixed_count > 0:
        click.echo(f"  Fixed: {linter.fixed_count} files")

    if linter.errors:
        click.echo(f"\nErrors ({len(linter.errors)}):")
        for error in linter.errors:
            click.echo(f"  ❌ {error}")

    if linter.warnings:
        click.echo(f"\nWarnings ({len(linter.warnings)}):")
        for warning in linter.warnings:
            click.echo(f"  ⚠️  {warning}")

    # Exit with appropriate code
    sys.exit(0 if valid_count == total_count else 1)


@cli.command("check-config")
@click.option("--verbose", is_flag=True, help="Show detailed output")
def check_config(verbose):
    """Validate .ctxrc.yaml configuration"""
    linter = ContextLinter(verbose=verbose)
    success = linter.check_config()

    if linter.errors:
        click.echo("\nErrors:")
        for error in linter.errors:
            click.echo(f"  ❌ {error}")

    if linter.warnings:
        click.echo("\nWarnings:")
        for warning in linter.warnings:
            click.echo(f"  ⚠️  {warning}")

    sys.exit(0 if success else 1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def stats(path):
    """Show statistics about context documents"""
    linter = ContextLinter()
    linter.show_stats(Path(path))


if __name__ == "__main__":
    cli()
