"""Focused tests for gitignore parsing and file filtering fixes.

This module tests the specific fixes that resolved the coverage and
file discovery issues.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.config_schema import create_default_config
from pytest_drill_sergeant.core.file_discovery import (
    FileDiscovery,
    FileDiscoveryConfig,
    FilePattern,
    parse_gitignore,
)


class TestParseGitignoreFunction:
    """Test the parse_gitignore function specifically."""

    def test_parse_gitignore_basic_patterns(self):
        """Test basic gitignore pattern parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text(
                """
*.pyc
.venv/
node_modules/
"""
            )

            patterns = parse_gitignore(project_root)
            expected = ["**/*.pyc", ".venv/**", "node_modules/**"]
            assert patterns == expected

    def test_parse_gitignore_with_comments(self):
        """Test gitignore parsing with comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text(
                """
# This is a comment
*.pyc
# Another comment
.venv/
"""
            )

            patterns = parse_gitignore(project_root)
            expected = ["**/*.pyc", ".venv/**"]
            assert patterns == expected

    def test_parse_gitignore_file_not_exists(self):
        """Test parsing when .gitignore doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            patterns = parse_gitignore(project_root)
            assert patterns == []

    def test_parse_gitignore_error_handling(self):
        """Test error handling in parse_gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text("*.pyc")

            # Mock open to raise an exception
            with patch("builtins.open", side_effect=OSError("Permission denied")):
                patterns = parse_gitignore(project_root)
                assert patterns == []


class TestFilePatternMatching:
    """Test FilePattern matching with the fixes."""

    def test_recursive_test_pattern_matching(self):
        """Test the recursive test pattern fix."""
        pattern = FilePattern("**/test_*.py")
        project_root = Path("/project")

        # Should match test files in any directory
        assert pattern.matches(Path("/project/test_example.py"), project_root)
        assert pattern.matches(Path("/project/tests/test_unit.py"), project_root)
        assert pattern.matches(Path("/project/tests/unit/test_module.py"), project_root)

        # Should not match non-test files
        assert not pattern.matches(Path("/project/src/module.py"), project_root)

    def test_venv_pattern_matching(self):
        """Test the .venv pattern matching fix."""
        pattern = FilePattern("**/.venv/**")
        project_root = Path("/project")

        # Should match files in .venv directories
        assert pattern.matches(Path("/project/.venv/bin/python"), project_root)
        assert pattern.matches(
            Path("/project/.venv/lib/python3.9/site-packages/package.py"), project_root
        )

        # Should not match files outside .venv
        assert not pattern.matches(Path("/project/src/module.py"), project_root)
        assert not pattern.matches(Path("/project/.venv_backup/file.py"), project_root)

    def test_directory_pattern_matching(self):
        """Test directory pattern matching."""
        pattern = FilePattern(".venv/**")
        project_root = Path("/project")

        # Should match files in .venv directory
        assert pattern.matches(Path("/project/.venv/bin/python"), project_root)
        assert pattern.matches(
            Path("/project/.venv/lib/python3.9/site-packages/package.py"), project_root
        )

        # Should not match files outside .venv
        assert not pattern.matches(Path("/project/src/module.py"), project_root)

    def test_simple_pattern_matching(self):
        """Test simple pattern matching."""
        pattern = FilePattern("**/*.pyc")
        project_root = Path("/project")

        # Should match .pyc files anywhere
        assert pattern.matches(Path("/project/src/module.pyc"), project_root)
        assert pattern.matches(Path("/project/tests/test.pyc"), project_root)

        # Should not match .py files
        assert not pattern.matches(Path("/project/src/module.py"), project_root)


class TestFileDiscoveryIntegration:
    """Test FileDiscovery integration with gitignore."""

    def create_test_config(self, project_root: Path, **overrides):
        """Create a test configuration."""
        config = create_default_config()
        config.project_root = project_root
        for key, value in overrides.items():
            setattr(config, key, value)
        return config

    def test_file_discovery_includes_gitignore_patterns(self):
        """Test that FileDiscovery includes gitignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create .gitignore
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text("*.pyc\n.venv/")

            # Create config
            config = self.create_test_config(project_root)
            discovery_config = FileDiscoveryConfig(config)

            # Check that gitignore patterns are included
            exclude_patterns = [p.pattern for p in discovery_config.exclude_patterns]
            assert "**/*.pyc" in exclude_patterns
            assert ".venv/**" in exclude_patterns

    def test_file_discovery_filters_files_correctly(self):
        """Test that FileDiscovery filters files correctly with gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create .gitignore
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text("*.pyc\n.venv/")

            # Create test files
            test_file = project_root / "test_example.py"
            pyc_file = project_root / "module.pyc"
            venv_file = project_root / ".venv" / "bin" / "python"

            test_file.write_text("def test_something(): pass")
            pyc_file.write_text("compiled")
            venv_file.parent.mkdir(parents=True)
            venv_file.write_text("python")

            # Create config and discovery
            config = self.create_test_config(
                project_root, test_patterns=["**/test_*.py"]
            )
            discovery_config = FileDiscoveryConfig(config)
            discovery = FileDiscovery(config)

            # Discover files
            discovered_files = discovery.discover_files()

            # Should include test file
            assert test_file in discovered_files

            # Should exclude files matching gitignore patterns
            assert pyc_file not in discovered_files
            assert venv_file not in discovered_files

    def test_file_discovery_with_recursive_test_patterns(self):
        """Test FileDiscovery with recursive test patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create test files in subdirectories
            tests_dir = project_root / "tests"
            tests_dir.mkdir()
            unit_dir = tests_dir / "unit"
            unit_dir.mkdir()

            test_file1 = project_root / "test_example.py"
            test_file2 = tests_dir / "test_unit.py"
            test_file3 = unit_dir / "test_module.py"
            non_test_file = project_root / "module.py"

            test_file1.write_text("def test_something(): pass")
            test_file2.write_text("def test_unit(): pass")
            test_file3.write_text("def test_module(): pass")
            non_test_file.write_text("def func(): pass")

            # Create config with recursive test patterns
            config = self.create_test_config(
                project_root, test_patterns=["**/test_*.py"]
            )
            discovery = FileDiscovery(config)

            # Discover files
            discovered_files = discovery.discover_files()

            # Should find all test files
            assert test_file1 in discovered_files
            assert test_file2 in discovered_files
            assert test_file3 in discovered_files

            # Should not find non-test files
            assert non_test_file not in discovered_files

    def test_file_discovery_no_gitignore_file(self):
        """Test FileDiscovery when no .gitignore file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create config without .gitignore
            config = self.create_test_config(
                project_root, ignore_patterns=["existing_pattern"]
            )
            discovery_config = FileDiscoveryConfig(config)

            # Should only have existing patterns
            exclude_patterns = [p.pattern for p in discovery_config.exclude_patterns]
            assert "existing_pattern" in exclude_patterns

    def test_file_discovery_gitignore_parsing_error(self):
        """Test FileDiscovery when gitignore parsing fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create .gitignore
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text("*.pyc")

            # Mock parse_gitignore to raise an exception
            with patch(
                "pytest_drill_sergeant.core.file_discovery.parse_gitignore",
                side_effect=Exception("Parse error"),
            ):
                config = self.create_test_config(
                    project_root, ignore_patterns=["existing_pattern"]
                )
                discovery_config = FileDiscoveryConfig(config)

                # Should still have existing patterns even if gitignore parsing fails
                exclude_patterns = [
                    p.pattern for p in discovery_config.exclude_patterns
                ]
                assert "existing_pattern" in exclude_patterns


class TestEndToEndFileDiscovery:
    """Test end-to-end file discovery with gitignore."""

    def create_test_config(self, project_root: Path, **overrides):
        """Create a test configuration."""
        config = create_default_config()
        config.project_root = project_root
        for key, value in overrides.items():
            setattr(config, key, value)
        return config

    def test_complete_file_discovery_workflow(self):
        """Test complete file discovery workflow with gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create project structure
            src_dir = project_root / "src"
            tests_dir = project_root / "tests"
            venv_dir = project_root / ".venv"

            src_dir.mkdir()
            tests_dir.mkdir()
            venv_dir.mkdir()

            # Create files
            src_file = src_dir / "module.py"
            test_file = tests_dir / "test_module.py"
            venv_file = venv_dir / "bin" / "python"
            pyc_file = project_root / "module.pyc"

            src_file.write_text("def func(): pass")
            test_file.write_text("def test_func(): pass")
            venv_file.parent.mkdir()
            venv_file.write_text("python")
            pyc_file.write_text("compiled")

            # Create .gitignore
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text(
                """
*.pyc
.venv/
"""
            )

            # Create FileDiscovery
            config = self.create_test_config(
                project_root, test_patterns=["**/test_*.py"]
            )
            discovery = FileDiscovery(config)

            # Discover files
            discovered_files = discovery.discover_files()

            # Should find test files
            assert test_file in discovered_files

            # Should exclude files matching gitignore
            assert src_file not in discovered_files  # Not a test file
            assert venv_file not in discovered_files  # Matches .venv/
            assert pyc_file not in discovered_files  # Matches *.pyc

    def test_file_discovery_with_complex_gitignore(self):
        """Test file discovery with complex gitignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create complex project structure
            (project_root / "src").mkdir()
            (project_root / "tests").mkdir()
            (project_root / "tests" / "unit").mkdir()
            (project_root / "tests" / "integration").mkdir()
            (project_root / ".venv").mkdir()
            (project_root / "node_modules").mkdir()
            (project_root / "build").mkdir()

            # Create various files
            files = [
                "src/module.py",
                "tests/test_unit.py",
                "tests/unit/test_module.py",
                "tests/integration/test_integration.py",
                ".venv/bin/python",
                "node_modules/package/index.js",
                "build/output.txt",
                "module.pyc",
                "test.pyc",
                ".DS_Store",
                "temp.log",
            ]

            for file_path in files:
                full_path = project_root / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("content")

            # Create comprehensive .gitignore
            gitignore_path = project_root / ".gitignore"
            gitignore_path.write_text(
                """
# Compiled files
*.pyc
*.pyo

# Directories
.venv/
node_modules/
build/

# OS files
.DS_Store

# Log files
*.log
"""
            )

            # Create FileDiscovery
            config = self.create_test_config(
                project_root, test_patterns=["**/test_*.py"]
            )
            discovery = FileDiscovery(config)

            # Discover files
            discovered_files = discovery.discover_files()

            # Should find test files
            assert (project_root / "tests/test_unit.py") in discovered_files
            assert (project_root / "tests/unit/test_module.py") in discovered_files
            assert (
                project_root / "tests/integration/test_integration.py"
            ) in discovered_files

            # Should exclude non-test files and gitignore matches
            assert (project_root / "src/module.py") not in discovered_files
            assert (project_root / ".venv/bin/python") not in discovered_files
            assert (
                project_root / "node_modules/package/index.js"
            ) not in discovered_files
            assert (project_root / "build/output.txt") not in discovered_files
            assert (project_root / "module.pyc") not in discovered_files
            assert (project_root / "test.pyc") not in discovered_files
            assert (project_root / ".DS_Store") not in discovered_files
            assert (project_root / "temp.log") not in discovered_files
