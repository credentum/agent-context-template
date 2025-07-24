#!/usr/bin/env python3
"""
Incremental Build Analyzer - Dependency graph analysis for incremental builds.

This module analyzes file dependencies and determines what needs to be rebuilt
based on changes, optimizing CI build times through intelligent incremental builds.
"""

import ast
import hashlib
import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class FileNode:
    """Represents a file in the dependency graph."""

    path: Path
    hash: str
    last_modified: float
    dependencies: Set[str]
    dependents: Set[str]
    build_artifacts: List[str]
    language: str

    def __post_init__(self):
        # Convert Path to string for JSON serialization
        if isinstance(self.path, Path):
            object.__setattr__(self, "path", str(self.path))

        # Ensure sets are converted to lists for JSON serialization
        if isinstance(self.dependencies, set):
            object.__setattr__(self, "dependencies", list(self.dependencies))
        if isinstance(self.dependents, set):
            object.__setattr__(self, "dependents", list(self.dependents))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileNode":
        """Create from dictionary."""
        data = data.copy()
        data["dependencies"] = set(data.get("dependencies", []))
        data["dependents"] = set(data.get("dependents", []))
        data["path"] = Path(data["path"])
        return cls(**data)


@dataclass
class BuildTarget:
    """Represents a build target with its dependencies."""

    name: str
    input_files: List[str]
    output_files: List[str]
    build_command: str
    dependencies: List[str]  # Other build targets this depends on
    language: str
    last_built: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildTarget":
        """Create from dictionary."""
        return cls(**data)


class IncrementalBuildAnalyzer:
    """
    Analyzes file dependencies and determines incremental build requirements.

    Features:
    - Multi-language dependency analysis
    - Git-based change detection
    - Build artifact tracking
    - Intelligent build ordering
    - Cache-aware rebuilding
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Dependency graph
        self.file_graph: Dict[str, FileNode] = {}
        self.build_targets: Dict[str, BuildTarget] = {}

        # Configuration
        self.ignore_patterns = {
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "*.pyc",
            "*.pyo",
            "*.egg-info",
            ".coverage",
            ".tox",
        }

        # Language-specific analyzers
        self.language_analyzers = {
            ".py": self._analyze_python_dependencies,
            ".js": self._analyze_javascript_dependencies,
            ".ts": self._analyze_typescript_dependencies,
            ".dockerfile": self._analyze_dockerfile_dependencies,
            ".yaml": self._analyze_yaml_dependencies,
            ".yml": self._analyze_yaml_dependencies,
        }

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to hash {file_path}: {e}")
            return ""

    def _should_ignore_path(self, path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(path)

        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True

        return False

    def _analyze_python_dependencies(self, file_path: Path) -> Set[str]:
        """Analyze Python file dependencies."""
        dependencies = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse AST to find imports
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            dependencies.add(alias.name.split(".")[0])

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            dependencies.add(node.module.split(".")[0])

            except SyntaxError:
                # Fallback to regex parsing for syntax errors
                import_patterns = [
                    r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                    r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import",
                ]

                for line in content.split("\n"):
                    line = line.strip()
                    for pattern in import_patterns:
                        match = re.match(pattern, line)
                        if match:
                            dependencies.add(match.group(1))

            # Find local imports
            local_deps = set()
            for dep in dependencies:
                # Check if it's a local module
                potential_paths = [
                    self.project_root / f"{dep}.py",
                    self.project_root / dep / "__init__.py",
                ]

                for potential_path in potential_paths:
                    if potential_path.exists():
                        local_deps.add(str(potential_path.relative_to(self.project_root)))

            return local_deps

        except Exception as e:
            self.logger.warning(f"Failed to analyze Python dependencies for {file_path}: {e}")
            return set()

    def _analyze_javascript_dependencies(self, file_path: Path) -> Set[str]:
        """Analyze JavaScript/TypeScript file dependencies."""
        dependencies = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Regex patterns for imports/requires
            import_patterns = [
                r'import.*from\s+[\'"]([^\'"]*)[\'"',
                r'require\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)',
                r'import\s*\(\s*[\'"]([^\'"]*)[\'"]\s*\)',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Skip external modules (those without relative paths)
                    if match.startswith("."):
                        # Resolve relative import
                        dep_path = (file_path.parent / match).resolve()

                        # Try common extensions
                        for ext in [".js", ".ts", ".jsx", ".tsx"]:
                            if (dep_path.parent / f"{dep_path.name}{ext}").exists():
                                rel_path = (dep_path.parent / f"{dep_path.name}{ext}").relative_to(
                                    self.project_root
                                )
                                dependencies.add(str(rel_path))
                                break

        except Exception as e:
            self.logger.warning(f"Failed to analyze JS dependencies for {file_path}: {e}")

        return dependencies

    def _analyze_typescript_dependencies(self, file_path: Path) -> Set[str]:
        """Analyze TypeScript file dependencies."""
        # TypeScript uses same import syntax as JavaScript
        return self._analyze_javascript_dependencies(file_path)

    def _analyze_dockerfile_dependencies(self, file_path: Path) -> Set[str]:
        """Analyze Dockerfile dependencies."""
        dependencies = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for COPY and ADD commands that reference local files
            copy_patterns = [r"^COPY\s+([^\s]+)\s+", r"^ADD\s+([^\s]+)\s+"]

            for line in content.split("\n"):
                line = line.strip()
                for pattern in copy_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        source_path = match.group(1)
                        # Only include local files (not URLs or absolute paths)
                        if not source_path.startswith(("http://", "https://", "/")):
                            dep_path = file_path.parent / source_path
                            if dep_path.exists():
                                dependencies.add(str(dep_path.relative_to(self.project_root)))

        except Exception as e:
            self.logger.warning(f"Failed to analyze Dockerfile dependencies for {file_path}: {e}")

        return dependencies

    def _analyze_yaml_dependencies(self, file_path: Path) -> Set[str]:
        """Analyze YAML file dependencies (e.g., GitHub Actions)."""
        dependencies = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for file references in YAML
            file_patterns = [
                r'path:\s*[\'"]?([^\'"\s]+)[\'"]?',
                r'file:\s*[\'"]?([^\'"\s]+)[\'"]?',
                r'script:\s*[\'"]?([^\'"\s]+)[\'"]?',
            ]

            for pattern in file_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    dep_path = Path(match)
                    if not dep_path.is_absolute():
                        full_path = self.project_root / dep_path
                        if full_path.exists():
                            dependencies.add(str(dep_path))

        except Exception as e:
            self.logger.warning(f"Failed to analyze YAML dependencies for {file_path}: {e}")

        return dependencies

    def scan_project_files(self) -> None:
        """Scan project files and build dependency graph."""
        self.logger.info(f"Scanning project files in {self.project_root}")

        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file() or self._should_ignore_path(file_path):
                continue

            try:
                # Calculate file hash and metadata
                file_hash = self._calculate_file_hash(file_path)
                last_modified = file_path.stat().st_mtime

                # Determine language and analyze dependencies
                suffix = file_path.suffix.lower()
                language = suffix if suffix in self.language_analyzers else "unknown"

                dependencies = set()
                if suffix in self.language_analyzers:
                    dependencies = self.language_analyzers[suffix](file_path)

                # Create file node
                rel_path = file_path.relative_to(self.project_root)
                node = FileNode(
                    path=rel_path,
                    hash=file_hash,
                    last_modified=last_modified,
                    dependencies=dependencies,
                    dependents=set(),
                    build_artifacts=[],
                    language=language,
                )

                self.file_graph[str(rel_path)] = node

            except Exception as e:
                self.logger.warning(f"Failed to process {file_path}: {e}")

        # Build reverse dependency graph
        self._build_reverse_dependencies()

        self.logger.info(f"Scanned {len(self.file_graph)} files")

    def _build_reverse_dependencies(self) -> None:
        """Build reverse dependency relationships."""
        for file_path, node in self.file_graph.items():
            for dep_path in node.dependencies:
                if dep_path in self.file_graph:
                    self.file_graph[dep_path].dependents.add(file_path)

    def get_changed_files_from_git(self, base_ref: str = "HEAD~1") -> Set[str]:
        """Get list of changed files from git."""
        try:
            # Get changed files from git diff
            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )

            changed_files = set()
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    file_path = Path(line.strip())
                    if (self.project_root / file_path).exists():
                        changed_files.add(line.strip())

            return changed_files

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get changed files from git: {e}")
            return set()

    def calculate_affected_files(self, changed_files: Set[str]) -> Set[str]:
        """Calculate all files affected by changes (including dependents)."""
        affected = set(changed_files)

        # Use BFS to find all affected files
        queue = list(changed_files)
        visited = set()

        while queue:
            current_file = queue.pop(0)
            if current_file in visited:
                continue

            visited.add(current_file)

            # Add all files that depend on this file
            if current_file in self.file_graph:
                node = self.file_graph[current_file]
                for dependent in node.dependents:
                    if dependent not in affected:
                        affected.add(dependent)
                        queue.append(dependent)

        return affected

    def determine_rebuild_targets(
        self, changed_files: Optional[Set[str]] = None, base_ref: str = "HEAD~1"
    ) -> Dict[str, List[str]]:
        """
        Determine what needs to be rebuilt based on changes.

        Returns:
            Dictionary mapping rebuild reason to list of files
        """
        if changed_files is None:
            changed_files = self.get_changed_files_from_git(base_ref)

        if not changed_files:
            return {"no_changes": []}

        # Calculate affected files
        affected_files = self.calculate_affected_files(changed_files)

        rebuild_analysis = {
            "changed_files": list(changed_files),
            "affected_dependencies": list(affected_files - changed_files),
            "total_affected": list(affected_files),
        }

        # Categorize by language for targeted rebuilds
        language_groups: Dict[str, List[str]] = {}
        for file_path in affected_files:
            if file_path in self.file_graph:
                language = self.file_graph[file_path].language
                if language not in language_groups:
                    language_groups[language] = []
                language_groups[language].append(file_path)

        rebuild_analysis["by_language"] = dict(language_groups)

        return rebuild_analysis

    def generate_build_commands(self, affected_files: Set[str]) -> List[Dict[str, Any]]:
        """Generate optimized build commands for affected files."""
        commands = []

        # Group by language and generate appropriate commands
        language_groups: Dict[str, List[str]] = {}
        for file_path in affected_files:
            if file_path in self.file_graph:
                language = self.file_graph[file_path].language
                if language not in language_groups:
                    language_groups[language] = []
                language_groups[language].append(file_path)

        # Python builds
        if ".py" in language_groups:
            python_files = language_groups[".py"]

            # Run tests for affected Python files
            test_files = [
                f for f in python_files if f.startswith("tests/") or f.endswith("_test.py")
            ]
            if test_files:
                commands.append(
                    {
                        "language": "python",
                        "type": "test",
                        "command": f"pytest {' '.join(test_files)} -v",
                        "files": test_files,
                    }
                )

            # Type checking for affected Python files
            src_files = [f for f in python_files if f.startswith("src/")]
            if src_files:
                commands.append(
                    {
                        "language": "python",
                        "type": "typecheck",
                        "command": f"mypy {' '.join(src_files)}",
                        "files": src_files,
                    }
                )

        # JavaScript/TypeScript builds
        js_ts_files = []
        for lang in [".js", ".ts", ".jsx", ".tsx"]:
            if lang in language_groups:
                js_ts_files.extend(language_groups[lang])

        if js_ts_files:
            commands.append(
                {
                    "language": "javascript",
                    "type": "build",
                    "command": "npm run build",
                    "files": js_ts_files,
                }
            )

            commands.append(
                {
                    "language": "javascript",
                    "type": "test",
                    "command": f"npm test -- {' '.join(js_ts_files)}",
                    "files": js_ts_files,
                }
            )

        # Docker builds
        if "dockerfile" in language_groups:
            for dockerfile in language_groups["dockerfile"]:
                commands.append(
                    {
                        "language": "docker",
                        "type": "build",
                        "command": f"docker build -f {dockerfile} .",
                        "files": [dockerfile],
                    }
                )

        return commands

    def save_dependency_graph(self, output_file: Path) -> None:
        """Save dependency graph to JSON file."""
        try:
            graph_data = {
                "files": {k: v.to_dict() for k, v in self.file_graph.items()},
                "build_targets": {k: v.to_dict() for k, v in self.build_targets.items()},
                "metadata": {
                    "project_root": str(self.project_root),
                    "total_files": len(self.file_graph),
                    "languages": list(set(node.language for node in self.file_graph.values())),
                },
            }

            with open(output_file, "w") as f:
                json.dump(graph_data, f, indent=2, default=str)

            self.logger.info(f"Saved dependency graph to {output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save dependency graph: {e}")

    def load_dependency_graph(self, input_file: Path) -> bool:
        """Load dependency graph from JSON file."""
        try:
            with open(input_file, "r") as f:
                graph_data = json.load(f)

            # Load file graph
            self.file_graph = {}
            for file_path, node_data in graph_data.get("files", {}).items():
                self.file_graph[file_path] = FileNode.from_dict(node_data)

            # Load build targets
            self.build_targets = {}
            for target_name, target_data in graph_data.get("build_targets", {}).items():
                self.build_targets[target_name] = BuildTarget.from_dict(target_data)

            self.logger.info(f"Loaded dependency graph from {input_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load dependency graph: {e}")
            return False

    def get_build_statistics(self) -> Dict[str, Any]:
        """Get build analysis statistics."""
        languages = {}
        total_dependencies = 0

        for node in self.file_graph.values():
            lang = node.language
            if lang not in languages:
                languages[lang] = {"files": 0, "dependencies": 0}

            languages[lang]["files"] += 1
            languages[lang]["dependencies"] += len(node.dependencies)
            total_dependencies += len(node.dependencies)

        return {
            "total_files": len(self.file_graph),
            "total_dependencies": total_dependencies,
            "languages": languages,
            "build_targets": len(self.build_targets),
            "avg_dependencies_per_file": (
                total_dependencies / len(self.file_graph) if self.file_graph else 0
            ),
        }


def main():
    """CLI interface for incremental build analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Incremental Build Analyzer")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="Project root directory"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan project and build dependency graph")
    scan_parser.add_argument("--output", "-o", type=Path, help="Output file for dependency graph")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze what needs rebuilding")
    analyze_parser.add_argument(
        "--base-ref", default="HEAD~1", help="Git base reference for changes"
    )
    analyze_parser.add_argument("--changed-files", nargs="*", help="Specific changed files")

    # Stats command
    subparsers.add_parser("stats", help="Show build statistics")

    # Build command
    build_parser = subparsers.add_parser("build", help="Generate incremental build commands")
    build_parser.add_argument("--base-ref", default="HEAD~1", help="Git base reference for changes")
    build_parser.add_argument("--execute", action="store_true", help="Execute build commands")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    analyzer = IncrementalBuildAnalyzer(args.project_root)

    if args.command == "scan":
        analyzer.scan_project_files()
        if args.output:
            analyzer.save_dependency_graph(args.output)
        else:
            stats = analyzer.get_build_statistics()
            print(json.dumps(stats, indent=2))

    elif args.command == "analyze":
        analyzer.scan_project_files()

        changed_files = None
        if args.changed_files:
            changed_files = set(args.changed_files)

        rebuild_analysis = analyzer.determine_rebuild_targets(
            changed_files=changed_files, base_ref=args.base_ref
        )

        print(json.dumps(rebuild_analysis, indent=2))

    elif args.command == "stats":
        analyzer.scan_project_files()
        stats = analyzer.get_build_statistics()
        print(json.dumps(stats, indent=2))

    elif args.command == "build":
        analyzer.scan_project_files()

        rebuild_analysis = analyzer.determine_rebuild_targets(base_ref=args.base_ref)
        affected_files = set(rebuild_analysis.get("total_affected", []))

        if not affected_files:
            print("No files need rebuilding")
            return

        commands = analyzer.generate_build_commands(affected_files)

        print(f"Generated {len(commands)} build commands:")
        for i, cmd in enumerate(commands, 1):
            print(f"\n{i}. {cmd['type'].title()} ({cmd['language']})")
            print(f"   Command: {cmd['command']}")
            print(f"   Files: {len(cmd['files'])} files")

            if args.execute:
                print("   Executing...")
                try:
                    result = subprocess.run(
                        cmd["command"],
                        shell=True,
                        cwd=args.project_root,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        print("   ✓ Success")
                    else:
                        print(f"   ✗ Failed (exit code {result.returncode})")
                        print(f"   Error: {result.stderr}")

                except Exception as e:
                    print(f"   ✗ Failed to execute: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
