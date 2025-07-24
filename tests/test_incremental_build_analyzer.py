"""Unit tests for Incremental Build Analyzer."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import pytest

# Import the module under test
try:
    from incremental_build_analyzer import (
        DependencyChange,
        DependencyGraph,
        DockerfileAnalyzer,
        IncrementalBuildAnalyzer,
        JavaScriptAnalyzer,
        PythonAnalyzer,
        YAMLAnalyzer,
    )
except ImportError:
    # If import fails, skip this test module
    pytest.skip("incremental_build_analyzer module not found", allow_module_level=True)


class TestDependencyChange(unittest.TestCase):
    """Test DependencyChange dataclass."""

    def test_change_creation(self):
        """Test creating a dependency change."""
        change = DependencyChange(
            path="src/main.py",
            change_type="modified",
            affected_files={"src/test.py", "src/utils.py"},
        )

        self.assertEqual(change.path, "src/main.py")
        self.assertEqual(change.change_type, "modified")
        self.assertEqual(len(change.affected_files), 2)

    def test_change_to_dict(self):
        """Test converting change to dictionary."""
        change = DependencyChange(
            path="test.py",
            change_type="added",
            affected_files={"main.py"},
        )
        change_dict = change.to_dict()

        self.assertEqual(change_dict["path"], "test.py")
        self.assertEqual(change_dict["change_type"], "added")
        self.assertIsInstance(change_dict["affected_files"], list)


class TestDependencyGraph(unittest.TestCase):
    """Test DependencyGraph dataclass."""

    def test_graph_creation(self):
        """Test creating a dependency graph."""
        graph = DependencyGraph(
            nodes={"file1.py", "file2.py"},
            edges={("file1.py", "file2.py")},
            metadata={"version": "1.0"},
        )

        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.edges), 1)
        self.assertIn("version", graph.metadata)

    def test_graph_to_dict(self):
        """Test converting graph to dictionary."""
        graph = DependencyGraph(
            nodes={"a.py", "b.py"},
            edges={("a.py", "b.py")},
        )
        graph_dict = graph.to_dict()

        self.assertIsInstance(graph_dict["nodes"], list)
        self.assertIsInstance(graph_dict["edges"], list)
        self.assertEqual(len(graph_dict["edges"][0]), 2)


class TestPythonAnalyzer(unittest.TestCase):
    """Test Python dependency analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PythonAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_analyze_imports(self):
        """Test analyzing Python imports."""
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write(
                """
import os
import sys
from pathlib import Path
from .utils import helper
from ..core import base
import package.module
"""
            )

        deps = self.analyzer.analyze_file(test_file)

        self.assertIn("os", deps)
        self.assertIn("sys", deps)
        self.assertIn("pathlib", deps)
        self.assertIn(".utils", deps)
        self.assertIn("..core", deps)
        self.assertIn("package.module", deps)

    def test_analyze_syntax_error(self):
        """Test handling syntax errors."""
        test_file = os.path.join(self.temp_dir, "bad.py")
        with open(test_file, "w") as f:
            f.write("import os\n\ndef bad syntax")

        deps = self.analyzer.analyze_file(test_file)
        self.assertEqual(deps, set())  # Should return empty set on error


class TestJavaScriptAnalyzer(unittest.TestCase):
    """Test JavaScript dependency analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = JavaScriptAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_analyze_imports(self):
        """Test analyzing JavaScript imports."""
        test_file = os.path.join(self.temp_dir, "test.js")
        with open(test_file, "w") as f:
            f.write(
                """
import React from 'react';
import { Component } from 'react';
import './styles.css';
const utils = require('./utils');
const { helper } = require('../core/helper');
require('dotenv').config();
"""
            )

        deps = self.analyzer.analyze_file(test_file)

        self.assertIn("react", deps)
        self.assertIn("./styles.css", deps)
        self.assertIn("./utils", deps)
        self.assertIn("../core/helper", deps)
        self.assertIn("dotenv", deps)


class TestDockerfileAnalyzer(unittest.TestCase):
    """Test Dockerfile dependency analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DockerfileAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_analyze_dockerfile(self):
        """Test analyzing Dockerfile."""
        test_file = os.path.join(self.temp_dir, "Dockerfile")
        with open(test_file, "w") as f:
            f.write(
                """
FROM python:3.11
COPY requirements.txt .
COPY src/ /app/src/
ADD config.json /app/
COPY --from=builder /dist /app/dist
"""
            )

        deps = self.analyzer.analyze_file(test_file)

        self.assertIn("requirements.txt", deps)
        self.assertIn("src/", deps)
        self.assertIn("config.json", deps)
        self.assertIn("/dist", deps)


class TestYAMLAnalyzer(unittest.TestCase):
    """Test YAML dependency analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = YAMLAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_analyze_yaml_includes(self):
        """Test analyzing YAML includes."""
        test_file = os.path.join(self.temp_dir, "test.yaml")
        with open(test_file, "w") as f:
            f.write(
                """
includes:
  - common.yaml
  - ./config/base.yaml

imports:
  - ../shared/settings.yaml

extends: base.yaml
"""
            )

        deps = self.analyzer.analyze_file(test_file)

        self.assertIn("common.yaml", deps)
        self.assertIn("./config/base.yaml", deps)
        self.assertIn("../shared/settings.yaml", deps)
        self.assertIn("base.yaml", deps)


class TestIncrementalBuildAnalyzer(unittest.TestCase):
    """Test Incremental Build Analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "cache.json")
        self.analyzer = IncrementalBuildAnalyzer(
            project_root=self.temp_dir,
            cache_file=self.cache_file,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_build_dependency_graph(self):
        """Test building dependency graph."""
        # Create test files
        os.makedirs(os.path.join(self.temp_dir, "src"))

        with open(os.path.join(self.temp_dir, "src", "main.py"), "w") as f:
            f.write("import utils\n")

        with open(os.path.join(self.temp_dir, "src", "utils.py"), "w") as f:
            f.write("import os\n")

        graph = self.analyzer.build_dependency_graph()

        self.assertIn("src/main.py", graph.nodes)
        self.assertIn("src/utils.py", graph.nodes)
        # Should have edge from main.py to utils.py
        self.assertTrue(
            any(
                edge[0].endswith("main.py") and edge[1].endswith("utils.py") for edge in graph.edges
            )
        )

    @patch("incremental_build_analyzer.subprocess.run")
    def test_get_changed_files(self, mock_run):
        """Test getting changed files from git."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M src/main.py\nA src/new.py\nD src/old.py\n",
        )

        changes = self.analyzer.get_changed_files()

        self.assertEqual(len(changes), 3)
        self.assertEqual(changes[0].path, "src/main.py")
        self.assertEqual(changes[0].change_type, "modified")
        self.assertEqual(changes[1].path, "src/new.py")
        self.assertEqual(changes[1].change_type, "added")
        self.assertEqual(changes[2].path, "src/old.py")
        self.assertEqual(changes[2].change_type, "deleted")

    def test_analyze_impact(self):
        """Test analyzing impact of changes."""
        # Build a simple dependency graph
        graph = DependencyGraph(
            nodes={"a.py", "b.py", "c.py"},
            edges={("b.py", "a.py"), ("c.py", "b.py")},  # b depends on a, c depends on b
        )

        changes = [
            DependencyChange("a.py", "modified", set()),
        ]

        # Analyze impact
        self.analyzer.dependency_graph = graph
        impact = self.analyzer.analyze_impact(changes)

        # Should affect b.py and c.py (transitive)
        self.assertIn("b.py", impact)
        self.assertIn("c.py", impact)

    def test_save_load_cache(self):
        """Test saving and loading cache."""
        graph = DependencyGraph(
            nodes={"file1.py", "file2.py"},
            edges={("file1.py", "file2.py")},
            metadata={"test": "data"},
        )

        # Save cache
        self.analyzer.dependency_graph = graph
        self.analyzer._save_cache()

        # Create new analyzer and load cache
        new_analyzer = IncrementalBuildAnalyzer(
            project_root=self.temp_dir,
            cache_file=self.cache_file,
        )
        new_analyzer._load_cache()

        self.assertEqual(new_analyzer.dependency_graph.nodes, graph.nodes)
        self.assertEqual(new_analyzer.dependency_graph.edges, graph.edges)

    def test_get_build_targets(self):
        """Test getting build targets for changes."""
        # Create test structure
        graph = DependencyGraph(
            nodes={"src/main.py", "src/utils.py", "tests/test_main.py"},
            edges={
                ("src/main.py", "src/utils.py"),
                ("tests/test_main.py", "src/main.py"),
            },
        )
        self.analyzer.dependency_graph = graph

        changes = [DependencyChange("src/utils.py", "modified", set())]

        targets = self.analyzer.get_build_targets(changes)

        # Should include main.py and test_main.py
        self.assertIn("src/main.py", targets)
        self.assertIn("tests/test_main.py", targets)
        self.assertIn("src/utils.py", targets)  # The changed file itself

    def test_exclude_patterns(self):
        """Test excluding files from analysis."""
        # Create test files
        os.makedirs(os.path.join(self.temp_dir, "node_modules"))
        with open(os.path.join(self.temp_dir, "node_modules", "lib.js"), "w") as f:
            f.write("module.exports = {}")

        analyzer = IncrementalBuildAnalyzer(
            project_root=self.temp_dir,
            exclude_patterns=["node_modules/**"],
        )

        graph = analyzer.build_dependency_graph()

        # Should not include node_modules files
        self.assertFalse(any("node_modules" in node for node in graph.nodes))


if __name__ == "__main__":
    unittest.main()
