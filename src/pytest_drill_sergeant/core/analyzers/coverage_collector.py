"""Coverage Collection for pytest-drill-sergeant.

This module implements per-test coverage collection using coverage.py,
providing coverage data for CAR calculation and similarity detection.
"""

from __future__ import annotations

import ast
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import coverage

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding


@dataclass
class CoverageData:
    """Coverage data for a single test."""

    test_name: str
    file_path: Path
    line_number: int
    lines_covered: int
    lines_total: int
    branches_covered: int
    branches_total: int
    coverage_percentage: float
    covered_lines: set[int]
    missing_lines: set[int]
    coverage_signature: str | None = None

    def to_dict(self) -> dict:
        """Convert CoverageData to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "lines_covered": self.lines_covered,
            "lines_total": self.lines_total,
            "branches_covered": self.branches_covered,
            "branches_total": self.branches_total,
            "coverage_percentage": self.coverage_percentage,
            "covered_lines": list(self.covered_lines),
            "missing_lines": list(self.missing_lines),
            "coverage_signature": self.coverage_signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CoverageData:
        """Create CoverageData from dictionary."""
        return cls(
            test_name=data["test_name"],
            file_path=Path(data["file_path"]),
            line_number=data["line_number"],
            lines_covered=data["lines_covered"],
            lines_total=data["lines_total"],
            branches_covered=data["branches_covered"],
            branches_total=data["branches_total"],
            coverage_percentage=data["coverage_percentage"],
            covered_lines=set(data["covered_lines"]),
            missing_lines=set(data["missing_lines"]),
            coverage_signature=data.get("coverage_signature"),
        )

    def __eq__(self, other) -> bool:
        """Compare CoverageData objects for equality."""
        if not isinstance(other, CoverageData):
            return False
        return (
            self.test_name == other.test_name
            and self.file_path == other.file_path
            and self.line_number == other.line_number
            and self.lines_covered == other.lines_covered
            and self.lines_total == other.lines_total
            and self.branches_covered == other.branches_covered
            and self.branches_total == other.branches_total
            and abs(self.coverage_percentage - other.coverage_percentage) < 0.1
            and self.covered_lines == other.covered_lines
            and self.missing_lines == other.missing_lines
        )


class CoverageCollector:
    """Collects per-test coverage data using coverage.py."""

    def __init__(self) -> None:
        """Initialize the coverage collector."""
        self.logger = logging.getLogger("drill_sergeant.coverage_collector")
        self._coverage_data: dict[str, CoverageData] = {}
        self._temp_dir: Path | None = None

        # Analysis results storage
        self._imported_files: set[Path] = set()
        self._called_functions: set[str] = set()
        self._analysis_results: dict[str, dict] = {}

    def start_coverage(self) -> None:
        """Start coverage collection."""
        try:
            # Create temporary directory for coverage data
            self._temp_dir = Path(tempfile.mkdtemp(prefix="drill_sergeant_coverage_"))

            # Initialize coverage with per-test data collection
            self.cov = coverage.Coverage(
                data_file=str(self._temp_dir / "coverage.dat"),
                branch=True,
                source=None,  # Will be set per test
            )

            self.logger.debug("Coverage collection started")
        except Exception as e:
            self.logger.error("Failed to start coverage collection: %s", e)
            raise

    def stop_coverage(self) -> None:
        """Stop coverage collection and cleanup."""
        try:
            if hasattr(self, "cov"):
                self.cov.stop()
                self.cov.save()

            # Cleanup temporary directory
            if self._temp_dir and self._temp_dir.exists():
                import shutil

                shutil.rmtree(self._temp_dir)
                self._temp_dir = None

            self.logger.debug("Coverage collection stopped")
        except Exception as e:
            self.logger.error("Failed to stop coverage collection: %s", e)

    def collect_test_coverage(
        self,
        test_file_path: Path,
        test_name: str,
        test_line_number: int,
        source_files: list[Path] | None = None,
    ) -> CoverageData:
        """Collect coverage data for a specific test.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts
            source_files: Source files to include in coverage (optional)

        Returns:
            CoverageData object with coverage information
        """
        try:
            # Determine source files to analyze
            if source_files is None:
                source_files = self._find_source_files(test_file_path)

            # Ensure coverage is initialized
            if not hasattr(self, "cov"):
                self.start_coverage()

            # Start coverage for this test
            self.cov.start()

            # Import and run the test (this would be done by pytest)
            # For now, we'll simulate this by analyzing the test file
            self._analyze_test_coverage(
                test_file_path, test_name, test_line_number, source_files
            )

            # Stop coverage and get data
            self.cov.stop()
            self.cov.save()

            # Extract coverage data with analysis integration
            coverage_data = self._extract_coverage_data_with_analysis(
                test_file_path, test_name, test_line_number, source_files
            )

            # Store coverage data
            key = f"{test_file_path}:{test_name}"
            self._coverage_data[key] = coverage_data

            return coverage_data

        except Exception as e:
            self.logger.error("Failed to collect coverage for %s: %s", test_name, e)
            # Return empty coverage data on error
            return CoverageData(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                lines_covered=0,
                lines_total=0,
                branches_covered=0,
                branches_total=0,
                coverage_percentage=0.0,
                covered_lines=set(),
                missing_lines=set(),
            )

    def get_coverage_data(
        self, test_file_path: Path, test_name: str
    ) -> CoverageData | None:
        """Get stored coverage data for a test.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function

        Returns:
            CoverageData if found, None otherwise
        """
        key = f"{test_file_path}:{test_name}"
        return self._coverage_data.get(key)

    def _find_source_files(self, test_file_path: Path) -> list[Path]:
        """Find source files that should be included in coverage.

        Args:
            test_file_path: Path to the test file

        Returns:
            List of source file paths
        """
        source_files = []

        try:
            # First, check if the test file itself contains source code
            if self._test_file_contains_source_code(test_file_path):
                source_files.append(test_file_path)
                self.logger.debug(
                    f"Test file {test_file_path} contains source code, including it in coverage"
                )

            # Analyze the test file to find imported modules
            imported_modules = self._analyze_test_file_imports(test_file_path)

            # Look for source files in common locations
            test_dir = test_file_path.parent

            # Check for src/ directory
            src_dir = test_dir.parent / "src"
            if src_dir.exists():
                try:
                    source_files.extend(src_dir.rglob("*.py"))
                except (PermissionError, OSError) as e:
                    self.logger.debug("Cannot access src directory %s: %s", src_dir, e)

            # Check for lib/ directory
            lib_dir = test_dir.parent / "lib"
            if lib_dir.exists():
                try:
                    source_files.extend(lib_dir.rglob("*.py"))
                except (PermissionError, OSError) as e:
                    self.logger.debug("Cannot access lib directory %s: %s", lib_dir, e)

            # Check for package directory at same level as tests
            # Limit traversal to avoid system directories
            for parent in self._safe_parent_traversal(test_dir):
                try:
                    for item in parent.iterdir():
                        if (
                            item.is_dir()
                            and not item.name.startswith("test")
                            and item.name != "tests"
                        ):
                            try:
                                if (item / "__init__.py").exists():
                                    try:
                                        source_files.extend(item.rglob("*.py"))
                                    except (PermissionError, OSError) as e:
                                        self.logger.debug(
                                            f"Cannot access package directory {item}: {e}"
                                        )
                                        continue
                            except (PermissionError, OSError) as e:
                                self.logger.debug(
                                    f"Skipping directory {item} due to permission error: {e}"
                                )
                                continue
                except (PermissionError, OSError) as e:
                    self.logger.debug(
                        f"Skipping parent directory {parent} due to permission error: {e}"
                    )
                    continue

            # Filter out test files
            source_files = [f for f in source_files if not self._is_test_file(f)]

            # Prioritize files that are actually imported by the test
            imported_source_files = []
            for module_name in imported_modules:
                matching_file = self._resolve_import_to_file(module_name, source_files)
                if matching_file and matching_file not in imported_source_files:
                    imported_source_files.append(matching_file)

            # Use analysis results to intelligently select source files
            source_files = self._select_source_files_with_analysis(
                source_files, imported_source_files, imported_modules
            )

            self.logger.debug(
                f"Found {len(source_files)} source files for {test_file_path}"
            )

        except Exception as e:
            self.logger.error("Failed to find source files for %s: %s", test_file_path, e)
            # Fallback to basic file discovery
            source_files = self._find_source_files_fallback(test_file_path)

        return source_files

    def _test_file_contains_source_code(self, test_file_path: Path) -> bool:
        """Check if a test file contains source code (non-test functions).

        Args:
            test_file_path: Path to the test file

        Returns:
            True if the file contains source code functions
        """
        try:
            content = test_file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file_path))

            # Look for function definitions that are not test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if it's not a test function
                    if not (
                        node.name.startswith("test_")
                        or node.name.startswith("Test")
                        or "test" in node.name.lower()
                    ):
                        return True

            return False

        except Exception as e:
            self.logger.error("Failed to analyze test file for source code: %s", e)
            return False

    def _safe_parent_traversal(self, start_path: Path) -> list[Path]:
        """Safely traverse parent directories, avoiding system directories.

        Args:
            start_path: Starting path for traversal

        Returns:
            List of parent directories that are safe to traverse
        """
        safe_parents = []

        # Define system directories to avoid
        system_dirs = {
            "/",
            "/usr",
            "/var",
            "/etc",
            "/bin",
            "/sbin",
            "/lib",
            "/lib64",
            "/opt",
            "/home",
            "/root",
            "/tmp",
            "/sys",
            "/proc",
            "/dev",
        }

        # Also avoid Windows system directories
        windows_system_dirs = {
            "C:\\",
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\System32",
            "C:\\Users",
            "C:\\ProgramData",
        }

        try:
            for parent in start_path.parents:
                parent_str = str(parent)

                # Skip if we've reached the root or a system directory
                if parent_str in system_dirs or parent_str in windows_system_dirs:
                    self.logger.debug(
                        f"Stopping traversal at system directory: {parent_str}"
                    )
                    break

                # Skip if parent is the same as current (avoid infinite loops)
                if parent == start_path:
                    continue

                # Check if we can access this directory
                try:
                    # Test if we can list the directory contents
                    list(parent.iterdir())
                    safe_parents.append(parent)
                except (PermissionError, OSError) as e:
                    self.logger.debug("Cannot access parent directory %s: %s", parent, e)
                    break

                # Limit traversal depth to avoid going too far up
                if len(safe_parents) >= 5:  # Reasonable limit for project structure
                    self.logger.debug(
                        f"Reached maximum traversal depth: {len(safe_parents)}"
                    )
                    break

        except Exception as e:
            self.logger.debug("Error during safe parent traversal: %s", e)

        return safe_parents

    def _select_source_files_with_analysis(
        self,
        all_source_files: list[Path],
        imported_source_files: list[Path],
        imported_modules: list[str],
    ) -> list[Path]:
        """Intelligently select source files based on analysis results.

        Args:
            all_source_files: All available source files
            imported_source_files: Files that are directly imported
            imported_modules: List of imported module names

        Returns:
            Intelligently selected source files
        """
        try:
            # If we have imported files, prioritize them
            if imported_source_files:
                # Add imported files first
                selected_files = list(imported_source_files)

                # Add related files (files in the same packages)
                for imported_file in imported_source_files:
                    # Find other files in the same package
                    package_dir = imported_file.parent
                    if package_dir.exists():
                        for file in package_dir.rglob("*.py"):
                            if (
                                file not in selected_files
                                and not self._is_test_file(file)
                                and file != imported_file
                            ):
                                selected_files.append(file)

                # Limit to reasonable number of files
                if len(selected_files) > 20:  # Reasonable limit
                    selected_files = selected_files[:20]

                self.logger.debug(
                    f"Selected {len(selected_files)} files based on import analysis"
                )
                return selected_files

            # If no imported files, use all source files but limit them
            # Limit to reasonable number to avoid performance issues
            limited_files = all_source_files[:50]  # Reasonable limit
            self.logger.debug(
                f"Using {len(limited_files)} files (no import analysis available)"
            )
            return limited_files

        except Exception as e:
            self.logger.error("Failed to select source files with analysis: %s", e)
            # Fallback to imported files or all files
            return imported_source_files if imported_source_files else all_source_files

    def _analyze_test_file_imports(self, test_file_path: Path) -> list[str]:
        """Analyze a test file to find all imported modules.

        Args:
            test_file_path: Path to the test file

        Returns:
            List of imported module names
        """
        imported_modules = []

        try:
            # Read and parse the test file
            content = test_file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file_path))

            # Walk through all nodes to find imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import module
                    for alias in node.names:
                        imported_modules.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name
                    if node.module:
                        imported_modules.append(node.module)

                elif isinstance(node, ast.Call):
                    # Handle dynamic imports like __import__()
                    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                        if node.args and isinstance(node.args[0], ast.Constant):
                            imported_modules.append(node.args[0].value)

            # Remove duplicates and filter out standard library modules
            imported_modules = list(set(imported_modules))
            imported_modules = [
                m for m in imported_modules if not self._is_standard_library_module(m)
            ]

            self.logger.debug(
                f"Test file {test_file_path} imports {len(imported_modules)} modules"
            )

        except Exception as e:
            self.logger.error("Failed to analyze imports in %s: %s", test_file_path, e)

        return imported_modules

    def _is_standard_library_module(self, module_name: str) -> bool:
        """Check if a module is part of the Python standard library.

        Args:
            module_name: Name of the module

        Returns:
            True if it's a standard library module
        """
        # Common standard library modules
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "datetime",
            "time",
            "random",
            "math",
            "collections",
            "itertools",
            "functools",
            "operator",
            "string",
            "re",
            "urllib",
            "http",
            "socket",
            "threading",
            "multiprocessing",
            "subprocess",
            "logging",
            "unittest",
            "pytest",
            "pathlib",
            "typing",
            "dataclasses",
            "enum",
            "abc",
            "contextlib",
            "copy",
            "pickle",
            "hashlib",
            "base64",
            "uuid",
            "tempfile",
            "shutil",
            "glob",
            "fnmatch",
            "stat",
            "fileinput",
            "linecache",
            "codecs",
            "locale",
            "gettext",
            "argparse",
            "configparser",
            "csv",
            "xml",
            "html",
            "email",
            "mimetypes",
            "platform",
            "ctypes",
            "warnings",
            "traceback",
            "inspect",
            "ast",
            "tokenize",
            "keyword",
            "builtins",
            "io",
            "textwrap",
            "unicodedata",
            "codeop",
            "py_compile",
            "compileall",
            "dis",
            "pickletools",
            "distutils",
            "setuptools",
        }

        # Check if it's a known standard library module
        if module_name in stdlib_modules:
            return True

        # Check if it starts with common standard library prefixes
        stdlib_prefixes = ("_", "test", "tests", "conftest")
        if any(module_name.startswith(prefix) for prefix in stdlib_prefixes):
            return True

        return False

    def _find_source_files_fallback(self, test_file_path: Path) -> list[Path]:
        """Fallback method to find source files when import analysis fails.

        Args:
            test_file_path: Path to the test file

        Returns:
            List of source file paths
        """
        source_files = []

        # Look for source files in common locations
        test_dir = test_file_path.parent

        # Check for src/ directory
        src_dir = test_dir.parent / "src"
        if src_dir.exists():
            try:
                source_files.extend(src_dir.rglob("*.py"))
            except (PermissionError, OSError) as e:
                self.logger.debug("Cannot access src directory %s: %s", src_dir, e)

        # Check for lib/ directory
        lib_dir = test_dir.parent / "lib"
        if lib_dir.exists():
            try:
                source_files.extend(lib_dir.rglob("*.py"))
            except (PermissionError, OSError) as e:
                self.logger.debug("Cannot access lib directory %s: %s", lib_dir, e)

        # Check for package directory at same level as tests
        # Limit traversal to avoid system directories
        for parent in self._safe_parent_traversal(test_dir):
            try:
                for item in parent.iterdir():
                    if (
                        item.is_dir()
                        and not item.name.startswith("test")
                        and item.name != "tests"
                    ):
                        try:
                            if (item / "__init__.py").exists():
                                try:
                                    source_files.extend(item.rglob("*.py"))
                                except (PermissionError, OSError) as e:
                                    self.logger.debug(
                                        f"Cannot access package directory {item}: {e}"
                                    )
                                    continue
                        except (PermissionError, OSError) as e:
                            self.logger.debug(
                                f"Skipping directory {item} due to permission error: {e}"
                            )
                            continue
            except (PermissionError, OSError) as e:
                self.logger.debug(
                    f"Skipping parent directory {parent} due to permission error: {e}"
                )
                continue

        # Filter out test files
        source_files = [f for f in source_files if not self._is_test_file(f)]

        return source_files

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to check

        Returns:
            True if file is a test file
        """
        name = file_path.name.lower()
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or name.startswith("test")
            or "test" in file_path.parts
        )

    def _analyze_test_coverage(
        self,
        test_file_path: Path,
        test_name: str,
        test_line_number: int,
        source_files: list[Path],
    ) -> None:
        """Execute test and analyze coverage.

        This method actually executes the test under coverage tracking
        and then analyzes the results.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts
            source_files: Source files to analyze
        """
        try:
            # First, analyze the test structure for imports and calls
            test_content = test_file_path.read_text(encoding="utf-8")
            test_tree = ast.parse(test_content, filename=str(test_file_path))

            # Find the specific test function
            test_func = None
            for node in ast.walk(test_tree):
                if isinstance(node, ast.FunctionDef) and node.name == test_name:
                    test_func = node
                    break

            if not test_func:
                self.logger.warning(
                    f"Test function {test_name} not found in {test_file_path}"
                )
                return

            # Analyze imports and function calls
            self._analyze_test_imports(test_func, source_files)
            self._analyze_test_calls(test_func, source_files)

            # Now execute the test under coverage
            self._execute_test_under_coverage(test_file_path, test_name, source_files)

        except Exception as e:
            self.logger.error("Failed to analyze test coverage: %s", e)

    def _execute_test_under_coverage(
        self, test_file_path: Path, test_name: str, source_files: list[Path]
    ) -> None:
        """Execute the test under coverage tracking.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            source_files: Source files to include in coverage
        """
        try:
            # Set up coverage to track the source files
            if hasattr(self, "cov"):
                # Configure coverage to track specific source files
                # Convert source files to strings for coverage.py
                source_file_paths = [str(f) for f in source_files]
                source_file_paths.append(str(test_file_path))

                if source_file_paths:
                    # Set the source files for coverage tracking
                    self.cov.source = source_file_paths
                    self.logger.debug(
                        f"Coverage source files set to: {source_file_paths}"
                    )

                # Execute the test by importing and running it
                self._run_test_function(test_file_path, test_name)
            else:
                self.logger.warning("Coverage not initialized, skipping test execution")

        except Exception as e:
            self.logger.error("Failed to execute test under coverage: %s", e)

    def _run_test_function(self, test_file_path: Path, test_name: str) -> None:
        """Run a specific test function.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function to run
        """
        try:
            # Import the test module
            import importlib.util
            import sys

            # Load the test module
            spec = importlib.util.spec_from_file_location("test_module", test_file_path)
            if spec is None or spec.loader is None:
                self.logger.error("Could not load test module from %s", test_file_path)
                return

            test_module = importlib.util.module_from_spec(spec)
            sys.modules["test_module"] = test_module
            spec.loader.exec_module(test_module)

            # Get the test function - handle both standalone functions and class methods
            test_func = None

            # First try as a standalone function
            if hasattr(test_module, test_name):
                test_func = getattr(test_module, test_name)
                test_func()
                self.logger.debug(
                    f"Successfully executed standalone test function {test_name}"
                )
            else:
                # Try to find it as a method in a test class
                for name, obj in vars(test_module).items():
                    if (
                        isinstance(obj, type)
                        and name.startswith("Test")
                        and hasattr(obj, test_name)
                    ):
                        # Found the test class, create instance and call method
                        test_class = obj
                        test_instance = test_class()
                        test_method = getattr(test_instance, test_name)
                        test_method()
                        self.logger.debug(
                            f"Successfully executed class method {test_name} in {name}"
                        )
                        test_func = test_method
                        break

                if test_func is None:
                    self.logger.warning(
                        f"Test function {test_name} not found in {test_file_path}"
                    )

        except Exception as e:
            self.logger.error("Failed to run test function %s: %s", test_name, e)

    def _extract_coverage_data_with_analysis(
        self,
        test_file_path: Path,
        test_name: str,
        test_line_number: int,
        source_files: list[Path],
    ) -> CoverageData:
        """Extract coverage data with analysis integration.

        This method integrates the stored analysis results to enhance coverage data
        with insights about imports and function calls.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts
            source_files: Source files that were analyzed

        Returns:
            CoverageData object with enhanced coverage information
        """
        try:
            # Get the base coverage data
            coverage_data = self._extract_coverage_data(
                test_file_path, test_name, test_line_number, source_files
            )

            # Get analysis results for this test
            import_results = self.get_analysis_results(f"{test_name}_imports")
            call_results = self.get_analysis_results(f"{test_name}_calls")

            # Enhance coverage data with analysis insights
            enhanced_coverage = self._enhance_coverage_with_analysis(
                coverage_data, import_results, call_results, source_files
            )

            return enhanced_coverage

        except Exception as e:
            self.logger.error("Failed to extract coverage data with analysis: %s", e)
            # Fallback to basic coverage data
            try:
                return self._extract_coverage_data(
                    test_file_path, test_name, test_line_number, source_files
                )
            except Exception as fallback_error:
                self.logger.error(
                    f"Fallback coverage extraction also failed: {fallback_error}"
                )
                # Return minimal coverage data
                from pytest_drill_sergeant.core.analyzers.coverage_collector import (
                    CoverageData,
                )

                return CoverageData(
                    test_name=test_name,
                    file_path=test_file_path,
                    line_number=test_line_number,
                    lines_covered=0,
                    lines_total=0,
                    branches_covered=0,
                    branches_total=0,
                    coverage_percentage=0.0,
                    covered_lines=set(),
                    missing_lines=set(),
                    coverage_signature="error_fallback",
                )

    def _enhance_coverage_with_analysis(
        self,
        coverage_data: CoverageData,
        import_results: dict | None,
        call_results: dict | None,
        source_files: list[Path],
    ) -> CoverageData:
        """Enhance coverage data with analysis insights.

        Args:
            coverage_data: Base coverage data
            import_results: Import analysis results
            call_results: Call analysis results
            source_files: Source files that were analyzed

        Returns:
            Enhanced CoverageData object
        """
        try:
            # Create enhanced coverage data
            enhanced_data = CoverageData(
                test_name=coverage_data.test_name,
                file_path=coverage_data.file_path,
                line_number=coverage_data.line_number,
                lines_covered=coverage_data.lines_covered,
                lines_total=coverage_data.lines_total,
                branches_covered=coverage_data.branches_covered,
                branches_total=coverage_data.branches_total,
                coverage_percentage=coverage_data.coverage_percentage,
                covered_lines=coverage_data.covered_lines,
                missing_lines=coverage_data.missing_lines,
                coverage_signature=coverage_data.coverage_signature,
            )

            # Add analysis insights
            analysis_insights = self._generate_analysis_insights(
                import_results, call_results, source_files
            )

            # Store analysis insights in the coverage signature
            if analysis_insights:
                enhanced_signature = (
                    f"{coverage_data.coverage_signature}|analysis:{analysis_insights}"
                )
                enhanced_data.coverage_signature = enhanced_signature

            # Log analysis insights
            self.logger.debug(
                f"Analysis insights for {coverage_data.test_name}: {analysis_insights}"
            )

            return enhanced_data

        except Exception as e:
            self.logger.error("Failed to enhance coverage with analysis: %s", e)
            return coverage_data

    def _generate_analysis_insights(
        self,
        import_results: dict | None,
        call_results: dict | None,
        source_files: list[Path],
    ) -> str:
        """Generate analysis insights string.

        Args:
            import_results: Import analysis results
            call_results: Call analysis results
            source_files: Source files that were analyzed

        Returns:
            Analysis insights as string
        """
        insights = []

        # Import analysis insights
        if import_results and not import_results.get("error"):
            try:
                import_count = int(import_results.get("import_count", 0))
                coverage_ratio = float(import_results.get("coverage_ratio", 0.0))
                insights.append(f"imports:{import_count}")
                insights.append(f"import_coverage:{coverage_ratio:.2f}")
            except (ValueError, TypeError):
                # Handle malformed data gracefully
                insights.append("imports:0")
                insights.append("import_coverage:0.00")

        # Call analysis insights
        if call_results and not call_results.get("error"):
            try:
                call_count = int(call_results.get("call_count", 0))
                call_types = call_results.get("call_types", {})
                if isinstance(call_types, dict):
                    assertions = call_types.get("assertions", 0)
                    insights.append(f"calls:{call_count}")
                    insights.append(f"assertions:{assertions}")

                    # Add call type breakdown
                    for call_type, count in call_types.items():
                        if isinstance(count, (int, float)) and count > 0:
                            insights.append(f"{call_type}:{count}")
                else:
                    insights.append(f"calls:{call_count}")
                    insights.append("assertions:0")
            except (ValueError, TypeError):
                # Handle malformed data gracefully
                insights.append("calls:0")
                insights.append("assertions:0")

        # Source file insights
        insights.append(f"source_files:{len(source_files)}")

        return "|".join(insights)

    def _analyze_test_imports(
        self, test_func: ast.FunctionDef, source_files: list[Path]
    ) -> None:
        """Analyze imports in a test function to determine source file coverage.

        Args:
            test_func: AST node for the test function
            source_files: Source files to analyze
        """
        try:
            # Track which source files are imported by this test
            imported_files = set()

            # Walk through all nodes in the test function
            for node in ast.walk(test_func):
                if isinstance(node, ast.Import):
                    # Handle: import module
                    for alias in node.names:
                        module_name = alias.name
                        source_file = self._resolve_import_to_file(
                            module_name, source_files
                        )
                        if source_file:
                            imported_files.add(source_file)

                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name
                    if node.module:
                        source_file = self._resolve_import_to_file(
                            node.module, source_files
                        )
                        if source_file:
                            imported_files.add(source_file)

                elif isinstance(node, ast.Call):
                    # Handle dynamic imports like __import__()
                    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                        if node.args and isinstance(node.args[0], ast.Constant):
                            module_name = node.args[0].value
                            source_file = self._resolve_import_to_file(
                                module_name, source_files
                            )
                            if source_file:
                                imported_files.add(source_file)

            # Store the imported files for this test
            self._imported_files.update(imported_files)
            self.logger.debug(
                f"Test function imports {len(imported_files)} source files"
            )

            # Store detailed analysis results
            test_key = f"{test_func.name}_imports"
            self._analysis_results[test_key] = {
                "imported_files": list(imported_files),
                "import_count": len(imported_files),
                "source_files_available": len(source_files),
                "coverage_ratio": (
                    len(imported_files) / len(source_files) if source_files else 0.0
                ),
            }

        except Exception as e:
            self.logger.error("Failed to analyze test imports: %s", e)
            # Store error state
            test_key = f"{test_func.name}_imports"
            self._analysis_results[test_key] = {
                "error": str(e),
                "imported_files": [],
                "import_count": 0,
            }

    def _analyze_test_calls(
        self, test_func: ast.FunctionDef, source_files: list[Path]
    ) -> None:
        """Analyze function calls in a test to determine coverage.

        Args:
            test_func: AST node for the test function
            source_files: Source files to analyze
        """
        try:
            # Track which functions are called by this test
            called_functions = set()

            # Walk through all nodes in the test function
            for node in ast.walk(test_func):
                if isinstance(node, ast.Call):
                    # Handle function calls
                    if isinstance(node.func, ast.Name):
                        # Direct function call: func()
                        func_name = node.func.id
                        called_functions.add(func_name)

                    elif isinstance(node.func, ast.Attribute):
                        # Method call: obj.method()
                        if isinstance(node.func.value, ast.Name):
                            # obj.method() where obj is a variable
                            obj_name = node.func.value.id
                            method_name = node.func.attr
                            called_functions.add(f"{obj_name}.{method_name}")
                        elif isinstance(node.func.value, ast.Attribute):
                            # obj.attr.method() - nested attribute access
                            attr_chain = self._get_attribute_chain(node.func.value)
                            method_name = node.func.attr
                            called_functions.add(f"{attr_chain}.{method_name}")
                        else:
                            # Other attribute access patterns
                            method_name = node.func.attr
                            called_functions.add(f".{method_name}")

                    elif isinstance(node.func, ast.Subscript):
                        # Callable subscript: obj[key]()
                        called_functions.add("subscript_call")

                    elif isinstance(node.func, ast.Call):
                        # Callable result: func()()
                        called_functions.add("callable_result")

                elif isinstance(node, ast.Assert):
                    # Handle assert statements
                    called_functions.add("assert")

            # Store the called functions for this test
            self._called_functions.update(called_functions)
            self.logger.debug("Test function calls %d functions", len(called_functions))

            # Store detailed analysis results
            test_key = f"{test_func.name}_calls"
            self._analysis_results[test_key] = {
                "called_functions": list(called_functions),
                "call_count": len(called_functions),
                "unique_calls": len(called_functions),
                "call_types": self._categorize_calls(called_functions),
            }

        except Exception as e:
            self.logger.error("Failed to analyze test calls: %s", e)
            # Store error state
            test_key = f"{test_func.name}_calls"
            self._analysis_results[test_key] = {
                "error": str(e),
                "called_functions": [],
                "call_count": 0,
            }

    def _categorize_calls(self, called_functions: set[str]) -> dict[str, int]:
        """Categorize function calls by type.

        Args:
            called_functions: Set of called function names

        Returns:
            Dictionary with call type counts
        """
        categories = {
            "direct_calls": 0,  # func()
            "method_calls": 0,  # obj.method()
            "nested_calls": 0,  # obj.attr.method()
            "dynamic_calls": 0,  # subscript_call, callable_result
            "assertions": 0,  # assert_* calls
        }

        for func_name in called_functions:
            if func_name.startswith("assert"):
                categories["assertions"] += 1
            elif "." in func_name and not func_name.startswith("."):
                if func_name.count(".") == 1:
                    categories["method_calls"] += 1
                else:
                    categories["nested_calls"] += 1
            elif func_name in ["subscript_call", "callable_result"]:
                categories["dynamic_calls"] += 1
            else:
                categories["direct_calls"] += 1

        return categories

    def get_imported_files(self) -> set[Path]:
        """Get all imported files from analysis.

        Returns:
            Set of imported file paths
        """
        return self._imported_files.copy()

    def get_called_functions(self) -> set[str]:
        """Get all called functions from analysis.

        Returns:
            Set of called function names
        """
        return self._called_functions.copy()

    def get_analysis_results(self, test_name: str) -> dict | None:
        """Get analysis results for a specific test.

        Args:
            test_name: Name of the test function

        Returns:
            Dictionary with analysis results or None if not found
        """
        return self._analysis_results.get(test_name)

    def get_all_analysis_results(self) -> dict[str, dict]:
        """Get all analysis results.

        Returns:
            Dictionary with all analysis results
        """
        return self._analysis_results.copy()

    def clear_analysis_results(self) -> None:
        """Clear all stored analysis results."""
        self._imported_files.clear()
        self._called_functions.clear()
        self._analysis_results.clear()

    def get_analysis_enhanced_coverage_data(
        self, test_file_path: Path, test_name: str
    ) -> CoverageData | None:
        """Get coverage data enhanced with analysis insights.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function

        Returns:
            Enhanced CoverageData object or None if not found
        """
        key = f"{test_file_path}:{test_name}"
        coverage_data = self._coverage_data.get(key)

        if coverage_data and "analysis:" in coverage_data.coverage_signature:
            return coverage_data

        return None

    def get_coverage_analysis_summary(
        self, test_file_path: Path, test_name: str
    ) -> dict | None:
        """Get a summary of coverage and analysis data for a test.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function

        Returns:
            Dictionary with coverage and analysis summary or None if not found
        """
        try:
            # Get coverage data
            coverage_data = self.get_coverage_data(test_file_path, test_name)
            if not coverage_data:
                return None

            # Get analysis results
            import_results = self.get_analysis_results(f"{test_name}_imports")
            call_results = self.get_analysis_results(f"{test_name}_calls")

            # Create summary
            summary = {
                "test_name": test_name,
                "file_path": str(test_file_path),
                "coverage": {
                    "percentage": coverage_data.coverage_percentage,
                    "lines_covered": coverage_data.lines_covered,
                    "lines_total": coverage_data.lines_total,
                    "branches_covered": coverage_data.branches_covered,
                    "branches_total": coverage_data.branches_total,
                },
                "analysis": {
                    "imports": import_results,
                    "calls": call_results,
                },
                "signature": coverage_data.coverage_signature,
            }

            return summary

        except Exception as e:
            self.logger.error("Failed to get coverage analysis summary: %s", e)
            return None

    def _resolve_import_to_file(
        self, module_name: str, source_files: list[Path]
    ) -> Path | None:
        """Resolve an import module name to an actual source file.

        Args:
            module_name: Name of the module being imported
            source_files: List of available source files

        Returns:
            Path to the source file if found, None otherwise
        """
        try:
            # Handle relative imports
            if module_name.startswith("."):
                # For relative imports, we'd need the current module context
                # This is a simplified implementation
                module_name = module_name.lstrip(".")

            # Try to find the module file
            for source_file in source_files:
                # Check if the file matches the module name
                if source_file.stem == module_name:
                    return source_file

                # Check if the file is in a package that matches the module
                if (
                    source_file.parent.name == module_name
                    and source_file.name == "__init__.py"
                ):
                    return source_file

                # Check for nested module paths (e.g., "package.module")
                module_parts = module_name.split(".")
                if len(module_parts) > 1:
                    # Check if the file path matches the module structure
                    file_parts = source_file.parts
                    if len(file_parts) >= len(module_parts):
                        # Check if the last parts match
                        if file_parts[-len(module_parts) :] == module_parts:
                            return source_file

            return None

        except Exception as e:
            self.logger.error("Failed to resolve import %s: %s", module_name, e)
            return None

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Get the full attribute chain for nested attribute access.

        Args:
            node: AST Attribute node

        Returns:
            String representation of the attribute chain
        """
        try:
            if isinstance(node.value, ast.Name):
                return f"{node.value.id}.{node.attr}"
            if isinstance(node.value, ast.Attribute):
                parent_chain = self._get_attribute_chain(node.value)
                return f"{parent_chain}.{node.attr}"
            return f".{node.attr}"

        except Exception as e:
            self.logger.error("Failed to get attribute chain: %s", e)
            return "unknown"

    def _extract_coverage_data(
        self,
        test_file_path: Path,
        test_name: str,
        test_line_number: int,
        source_files: list[Path],
    ) -> CoverageData:
        """Extract coverage data from coverage.py results.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts
            source_files: Source files that were analyzed

        Returns:
            CoverageData object with coverage information
        """
        try:
            # Get coverage data from coverage.py
            coverage_data = self.cov.get_data()
            self.logger.debug(
                f"Coverage data retrieved, measured files: {coverage_data.measured_files()}"
            )

            total_lines = 0
            covered_lines = 0
            total_branches = 0
            covered_branches = 0
            all_covered_lines = set()
            all_missing_lines = set()

            # Analyze each source file
            for source_file in source_files:
                self.logger.debug("Analyzing source file: %s", source_file)
                # Normalize the path to handle symlinks
                normalized_path = str(source_file.resolve())
                self.logger.debug("Normalized path: %s", normalized_path)

                # Check both the original path and normalized path
                file_path_in_measured = (
                    str(source_file) in coverage_data.measured_files()
                )
                normalized_path_in_measured = (
                    normalized_path in coverage_data.measured_files()
                )

                if file_path_in_measured or normalized_path_in_measured:
                    # Use the path that's actually in measured files
                    actual_path = (
                        str(source_file) if file_path_in_measured else normalized_path
                    )
                    self.logger.debug(
                        f"Source file {source_file} is in measured files (using path: {actual_path})"
                    )
                    file_lines = coverage_data.lines(actual_path)
                    file_branches = coverage_data.arcs(actual_path)
                    self.logger.debug(
                        f"File lines: {file_lines}, file branches: {file_branches}"
                    )

                    if file_lines:
                        total_lines += len(file_lines)
                        # Get executed lines using Coverage object analysis
                        analysis = self.cov.analysis2(actual_path)
                        all_executable_lines = analysis[1]  # All executable lines
                        missing_lines = analysis[2]  # Missing lines
                        excluded_lines = analysis[3]  # Excluded lines (not executed)

                        # Only count lines that were actually measured
                        executed_lines = [
                            line for line in all_executable_lines if line in file_lines
                        ]
                        covered_lines += len(executed_lines)
                        self.logger.debug(
                            f"Total lines: {total_lines}, covered lines: {covered_lines}"
                        )
                        self.logger.debug(
                            f"All executable lines: {all_executable_lines}"
                        )
                        self.logger.debug(
                            f"Executed lines (measured): {executed_lines}"
                        )
                        self.logger.debug("Missing lines: %s", missing_lines)
                        self.logger.debug("Excluded lines: %s", excluded_lines)

                        # Track covered and missing lines
                        for line in file_lines:
                            if line in executed_lines:
                                all_covered_lines.add(line)
                            else:
                                all_missing_lines.add(line)

                    if file_branches:
                        total_branches += len(file_branches)
                        # For now, assume all branches are covered if the file has branches
                        # TODO: Implement proper branch coverage analysis
                        covered_branches += len(file_branches)
                else:
                    self.logger.debug(
                        f"Source file {source_file} is NOT in measured files"
                    )

            # Calculate coverage percentage
            coverage_percentage = (
                (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            )

            # Generate coverage signature
            coverage_signature = self._generate_coverage_signature(
                all_covered_lines, source_files
            )

            return CoverageData(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                lines_covered=covered_lines,
                lines_total=total_lines,
                branches_covered=covered_branches,
                branches_total=total_branches,
                coverage_percentage=coverage_percentage,
                covered_lines=all_covered_lines,
                missing_lines=all_missing_lines,
                coverage_signature=coverage_signature,
            )

        except Exception as e:
            self.logger.error("Failed to extract coverage data: %s", e)
            # Return empty coverage data on error
            return CoverageData(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                lines_covered=0,
                lines_total=0,
                branches_covered=0,
                branches_total=0,
                coverage_percentage=0.0,
                covered_lines=set(),
                missing_lines=set(),
            )

    def _generate_coverage_signature(
        self, covered_lines: set[int], source_files: list[Path]
    ) -> str:
        """Generate a signature for coverage similarity detection.

        Args:
            covered_lines: Set of covered line numbers
            source_files: Source files that were analyzed

        Returns:
            Coverage signature string
        """
        try:
            # Create a signature based on covered lines and source files
            # This is a simplified implementation - in practice, you'd want
            # a more sophisticated signature that captures the coverage pattern

            signature_parts = []

            # Add source file information
            for source_file in source_files:
                signature_parts.append(f"{source_file.name}:{len(covered_lines)}")

            # Add coverage pattern
            if covered_lines:
                # Create a hash of the coverage pattern
                import hashlib

                coverage_str = ",".join(sorted(str(line) for line in covered_lines))
                coverage_hash = hashlib.md5(coverage_str.encode()).hexdigest()[:8]
                signature_parts.append(f"coverage:{coverage_hash}")

            return "|".join(signature_parts)

        except Exception as e:
            self.logger.error("Failed to generate coverage signature: %s", e)
            return ""

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for coverage-related issues.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for coverage-related issues
        """
        findings: list[Finding] = []

        try:
            if not file_path.exists():
                self.logger.warning("File does not exist: %s", file_path)
                return findings

            if file_path.suffix != ".py":
                self.logger.debug("Skipping non-Python file: %s", file_path)
                return findings

            # Read and parse the file
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                self.logger.debug("Empty file: %s", file_path)
                return findings

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.logger.warning("Syntax error in %s: %s", file_path, e)
                return findings

            # Find test functions and analyze them
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    func_findings = self._analyze_test_function_coverage(
                        node, file_path
                    )
                    findings.extend(func_findings)

            self.logger.debug(
                f"Coverage analysis of {file_path}: {len(findings)} findings"
            )

        except Exception as e:
            self.logger.error("Error analyzing %s: %s", file_path, e)

        return findings

    def _analyze_test_function_coverage(
        self, func_node: ast.FunctionDef, file_path: Path
    ) -> list[Finding]:
        """Analyze coverage aspects of a test function.

        Args:
            func_node: AST node for the test function
            file_path: Path to the file being analyzed

        Returns:
            List of findings for this function
        """
        findings: list[Finding] = []

        # This is a placeholder for coverage-specific analysis
        # In practice, you'd analyze the test for coverage-related issues
        # such as:
        # - Tests that don't cover enough code
        # - Tests with redundant coverage
        # - Tests that could be consolidated for better coverage

        return findings
