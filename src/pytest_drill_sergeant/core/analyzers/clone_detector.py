"""Dynamic Duplicate Detection for pytest-drill-sergeant.

This module implements dynamic duplicate detection using coverage-based similarity,
Jaccard index calculation, runtime mock assertion counting, and exception message analysis.
"""

from __future__ import annotations

import ast
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding


@dataclass
class SimilarityData:
    """Represents similarity between two tests."""

    test1_name: str
    test1_file: Path
    test2_name: str
    test2_file: Path
    jaccard_similarity: float
    coverage_overlap: float
    mock_assertion_similarity: float
    exception_similarity: float
    overall_similarity: float
    similarity_type: str  # "exact", "near", "partial"


@dataclass
class DuplicateCluster:
    """Represents a cluster of duplicate or similar tests."""

    cluster_id: str
    tests: list[tuple[str, Path]]  # (test_name, file_path)
    similarity_score: float
    cluster_type: str  # "exact_duplicates", "near_duplicates", "similar_patterns"
    representative_test: tuple[str, Path]
    consolidation_suggestion: str | None = None


class DynamicCloneDetector:
    """Detects duplicate tests using dynamic analysis techniques."""

    def __init__(self, config: dict | None = None) -> None:
        """Initialize the dynamic clone detector.

        Args:
            config: Configuration dictionary with similarity thresholds
        """
        self.logger = logging.getLogger("drill_sergeant.clone_detector")

        # Default configuration
        self.config = {
            "exact_duplicate_threshold": 0.98,
            "near_duplicate_threshold": 0.85,
            "similar_pattern_threshold": 0.70,
            "min_cluster_size": 2,
            "max_cluster_size": 10,
            "mock_assertion_weight": 0.3,
            "coverage_weight": 0.4,
            "exception_weight": 0.2,
            "structure_weight": 0.1,
        }

        # Update with provided config
        if config:
            self.config.update(config)

        # Storage for analysis results
        self._coverage_data: dict[str, CoverageData] = {}
        self._mock_assertion_counts: dict[str, int] = {}
        self._exception_patterns: dict[str, str] = {}
        self._test_signatures: dict[str, str] = {}

        # Similarity cache
        self._similarity_cache: dict[str, float] = {}

    def analyze_test_suite(
        self, test_files: list[Path], coverage_data: dict[str, CoverageData]
    ) -> list[DuplicateCluster]:
        """Analyze a test suite for duplicate tests.

        Args:
            test_files: List of test file paths
            coverage_data: Coverage data for tests

        Returns:
            List of duplicate clusters found
        """
        try:
            self.logger.info(
                f"Starting dynamic duplicate detection for {len(test_files)} test files"
            )

            # Store coverage data
            self._coverage_data = coverage_data

            # Analyze each test file
            for test_file in test_files:
                self._analyze_test_file(test_file)

            # Find duplicate clusters
            clusters = self._find_duplicate_clusters()

            self.logger.info(f"Found {len(clusters)} duplicate clusters")
            return clusters

        except Exception as e:
            self.logger.error(f"Failed to analyze test suite: {e}")
            return []

    def _analyze_test_file(self, test_file: Path) -> None:
        """Analyze a single test file for dynamic characteristics.

        Args:
            test_file: Path to the test file
        """
        try:
            if not test_file.exists() or test_file.suffix != ".py":
                return

            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file))

            # Find test functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_key = f"{test_file}:{node.name}"

                    # Count mock assertions
                    mock_count = self._count_mock_assertions(node)
                    self._mock_assertion_counts[test_key] = mock_count

                    # Extract exception patterns
                    exception_pattern = self._extract_exception_pattern(node)
                    self._exception_patterns[test_key] = exception_pattern

                    # Generate test signature
                    signature = self._generate_test_signature(node, test_file)
                    self._test_signatures[test_key] = signature

        except Exception as e:
            self.logger.error(f"Failed to analyze test file {test_file}: {e}")

    def _count_mock_assertions(self, test_func: ast.FunctionDef) -> int:
        """Count mock assertions in a test function.

        Args:
            test_func: AST node for the test function

        Returns:
            Number of mock assertions found
        """
        mock_assertions = {
            "assert_called_once",
            "assert_called_with",
            "assert_has_calls",
            "assert_any_call",
            "assert_called_once_with",
            "assert_not_called",
            "assert_called",
            "assert_called_times",
        }

        count = 0
        for node in ast.walk(test_func):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in mock_assertions:
                        count += 1
                elif isinstance(node.func, ast.Name):
                    if node.func.id in mock_assertions:
                        count += 1

        return count

    def _extract_exception_pattern(self, test_func: ast.FunctionDef) -> str:
        """Extract exception handling pattern from a test function.

        Args:
            test_func: AST node for the test function

        Returns:
            Exception pattern string
        """
        patterns = []

        for node in ast.walk(test_func):
            if isinstance(node, ast.Raise):
                # Extract exception type and message
                if node.exc:
                    if isinstance(node.exc, ast.Call):
                        # Exception with arguments
                        if isinstance(node.exc.func, ast.Name):
                            exc_type = node.exc.func.id
                            patterns.append(f"raise_{exc_type}")
                    elif isinstance(node.exc, ast.Name):
                        # Simple exception
                        patterns.append(f"raise_{node.exc.id}")

            elif isinstance(node, ast.ExceptHandler):
                # Exception handling
                if node.type:
                    if isinstance(node.type, ast.Name):
                        patterns.append(f"except_{node.type.id}")
                    elif isinstance(node.type, ast.Attribute):
                        patterns.append(f"except_{node.type.attr}")

            elif isinstance(node, ast.Call):
                # Check for pytest.raises
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "raises":
                        patterns.append("pytest_raises")

        return "|".join(sorted(patterns))

    def _generate_test_signature(
        self, test_func: ast.FunctionDef, test_file: Path
    ) -> str:
        """Generate a signature for a test function.

        Args:
            test_func: AST node for the test function
            test_file: Path to the test file

        Returns:
            Test signature string
        """
        signature_parts = []

        # Add function structure
        signature_parts.append(f"func:{test_func.name}")

        # Add parameter count
        param_count = len(test_func.args.args)
        signature_parts.append(f"params:{param_count}")

        # Add decorator count
        decorator_count = len(test_func.decorator_list)
        signature_parts.append(f"decorators:{decorator_count}")

        # Add statement count
        stmt_count = len(test_func.body)
        signature_parts.append(f"statements:{stmt_count}")

        # Add mock assertion count
        mock_count = self._mock_assertion_counts.get(f"{test_file}:{test_func.name}", 0)
        signature_parts.append(f"mocks:{mock_count}")

        # Add exception pattern
        exception_pattern = self._exception_patterns.get(
            f"{test_file}:{test_func.name}", ""
        )
        if exception_pattern:
            signature_parts.append(f"exceptions:{exception_pattern}")

        return "|".join(signature_parts)

    def _find_duplicate_clusters(self) -> list[DuplicateCluster]:
        """Find clusters of duplicate tests.

        Returns:
            List of duplicate clusters
        """
        clusters = []
        processed_tests = set()

        # Get all test keys
        test_keys = list(self._test_signatures.keys())

        for i, test1_key in enumerate(test_keys):
            if test1_key in processed_tests:
                continue

            # Find similar tests
            similar_tests = [test1_key]
            processed_tests.add(test1_key)

            for j, test2_key in enumerate(test_keys[i + 1 :], i + 1):
                if test2_key in processed_tests:
                    continue

                # Convert test signature keys to coverage data keys
                cov_key1 = self._convert_to_coverage_key(test1_key)
                cov_key2 = self._convert_to_coverage_key(test2_key)
                
                # Calculate similarity
                similarity = self._calculate_test_similarity(cov_key1, cov_key2)

                if similarity >= self.config["similar_pattern_threshold"]:
                    similar_tests.append(test2_key)
                    processed_tests.add(test2_key)

            # Create cluster if we have enough similar tests
            if len(similar_tests) >= self.config["min_cluster_size"]:
                cluster = self._create_cluster(similar_tests)
                if cluster:
                    clusters.append(cluster)

        return clusters

    def _convert_to_coverage_key(self, test_signature_key: str) -> str:
        """Convert test signature key to coverage data key format.
        
        Args:
            test_signature_key: Key in format 'file.py:test_name'
            
        Returns:
            Key in format 'test_name::file.py'
        """
        if ":" in test_signature_key:
            file_path, test_name = test_signature_key.split(":", 1)
            return f"{test_name}::{file_path}"
        return test_signature_key

    def _calculate_test_similarity(self, test1_key: str, test2_key: str) -> float:
        """Calculate similarity between two tests.

        Args:
            test1_key: Key for first test
            test2_key: Key for second test

        Returns:
            Similarity score (0-1)
        """
        # Check cache first
        cache_key = f"{min(test1_key, test2_key)}:{max(test1_key, test2_key)}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        try:
            # Calculate different similarity components
            coverage_sim = self._calculate_coverage_similarity(test1_key, test2_key)
            mock_sim = self._calculate_mock_similarity(test1_key, test2_key)
            exception_sim = self._calculate_exception_similarity(test1_key, test2_key)
            structure_sim = self._calculate_structure_similarity(test1_key, test2_key)

            # Weighted combination
            overall_similarity = (
                coverage_sim * self.config["coverage_weight"]
                + mock_sim * self.config["mock_assertion_weight"]
                + exception_sim * self.config["exception_weight"]
                + structure_sim * self.config["structure_weight"]
            )

            # Cache result
            self._similarity_cache[cache_key] = overall_similarity

            return overall_similarity

        except Exception as e:
            self.logger.error(
                f"Failed to calculate similarity between {test1_key} and {test2_key}: {e}"
            )
            return 0.0

    def _calculate_coverage_similarity(self, test1_key: str, test2_key: str) -> float:
        """Calculate coverage-based similarity using Jaccard index.

        Args:
            test1_key: Key for first test
            test2_key: Key for second test

        Returns:
            Coverage similarity score (0-1)
        """
        try:
            # Get coverage data
            cov1 = self._coverage_data.get(test1_key)
            cov2 = self._coverage_data.get(test2_key)

            if not cov1 or not cov2:
                return 0.0

            # Use covered lines for Jaccard similarity
            lines1 = cov1.covered_lines
            lines2 = cov2.covered_lines

            if not lines1 and not lines2:
                return 1.0  # Both have no coverage

            if not lines1 or not lines2:
                return 0.0  # One has coverage, other doesn't

            # Calculate Jaccard similarity
            intersection = len(lines1 & lines2)
            union = len(lines1 | lines2)

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Failed to calculate coverage similarity: {e}")
            return 0.0

    def _calculate_mock_similarity(self, test1_key: str, test2_key: str) -> float:
        """Calculate mock assertion similarity.

        Args:
            test1_key: Key for first test
            test2_key: Key for second test

        Returns:
            Mock similarity score (0-1)
        """
        try:
            mock1 = self._mock_assertion_counts.get(test1_key, 0)
            mock2 = self._mock_assertion_counts.get(test2_key, 0)

            if mock1 == 0 and mock2 == 0:
                return 1.0  # Both have no mocks

            if mock1 == 0 or mock2 == 0:
                return 0.0  # One has mocks, other doesn't

            # Similarity based on difference in mock count
            max_mocks = max(mock1, mock2)
            min_mocks = min(mock1, mock2)

            return min_mocks / max_mocks

        except Exception as e:
            self.logger.error(f"Failed to calculate mock similarity: {e}")
            return 0.0

    def _calculate_exception_similarity(self, test1_key: str, test2_key: str) -> float:
        """Calculate exception pattern similarity.

        Args:
            test1_key: Key for first test
            test2_key: Key for second test

        Returns:
            Exception similarity score (0-1)
        """
        try:
            exc1 = self._exception_patterns.get(test1_key, "")
            exc2 = self._exception_patterns.get(test2_key, "")

            if not exc1 and not exc2:
                return 1.0  # Both have no exception patterns

            if not exc1 or not exc2:
                return 0.0  # One has exceptions, other doesn't

            # Split patterns and calculate Jaccard similarity
            patterns1 = set(exc1.split("|"))
            patterns2 = set(exc2.split("|"))

            intersection = len(patterns1 & patterns2)
            union = len(patterns1 | patterns2)

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Failed to calculate exception similarity: {e}")
            return 0.0

    def _calculate_structure_similarity(self, test1_key: str, test2_key: str) -> float:
        """Calculate structural similarity based on test signatures.

        Args:
            test1_key: Key for first test
            test2_key: Key for second test

        Returns:
            Structure similarity score (0-1)
        """
        try:
            sig1 = self._test_signatures.get(test1_key, "")
            sig2 = self._test_signatures.get(test2_key, "")

            if not sig1 and not sig2:
                return 1.0

            if not sig1 or not sig2:
                return 0.0

            # Compare signature components
            parts1 = set(sig1.split("|"))
            parts2 = set(sig2.split("|"))

            intersection = len(parts1 & parts2)
            union = len(parts1 | parts2)

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Failed to calculate structure similarity: {e}")
            return 0.0

    def _create_cluster(self, test_keys: list[str]) -> DuplicateCluster | None:
        """Create a duplicate cluster from similar tests.

        Args:
            test_keys: List of test keys in the cluster

        Returns:
            DuplicateCluster object or None
        """
        try:
            if len(test_keys) < self.config["min_cluster_size"]:
                return None

            # Parse test keys to get names and files
            tests = []
            for key in test_keys:
                file_path, test_name = key.split(":", 1)
                tests.append((test_name, Path(file_path)))

            # Calculate average similarity
            similarities = []
            for i in range(len(test_keys)):
                for j in range(i + 1, len(test_keys)):
                    cov_key1 = self._convert_to_coverage_key(test_keys[i])
                    cov_key2 = self._convert_to_coverage_key(test_keys[j])
                    sim = self._calculate_test_similarity(cov_key1, cov_key2)
                    similarities.append(sim)

            avg_similarity = (
                sum(similarities) / len(similarities) if similarities else 0.0
            )

            # Determine cluster type
            if avg_similarity >= self.config["exact_duplicate_threshold"]:
                cluster_type = "exact_duplicates"
            elif avg_similarity >= self.config["near_duplicate_threshold"]:
                cluster_type = "near_duplicates"
            else:
                cluster_type = "similar_patterns"

            # Choose representative test (first one)
            representative_test = tests[0]

            # Generate cluster ID
            cluster_id = hashlib.md5(
                f"{representative_test[0]}:{representative_test[1]}".encode()
            ).hexdigest()[:8]

            # Generate consolidation suggestion
            suggestion = self._generate_consolidation_suggestion(tests, cluster_type)

            return DuplicateCluster(
                cluster_id=cluster_id,
                tests=tests,
                similarity_score=avg_similarity,
                cluster_type=cluster_type,
                representative_test=representative_test,
                consolidation_suggestion=suggestion,
            )

        except Exception as e:
            self.logger.error(f"Failed to create cluster: {e}")
            return None

    def _generate_consolidation_suggestion(
        self, tests: list[tuple[str, Path]], cluster_type: str
    ) -> str:
        """Generate consolidation suggestion for a cluster.

        Args:
            tests: List of tests in the cluster
            cluster_type: Type of cluster

        Returns:
            Consolidation suggestion string
        """
        if cluster_type == "exact_duplicates":
            return f"Consider consolidating {len(tests)} identical tests into a single parametrized test"
        if cluster_type == "near_duplicates":
            return f"Consider consolidating {len(tests)} similar tests using @pytest.mark.parametrize"
        return f"Review {len(tests)} tests for potential consolidation opportunities"

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for duplicate detection issues.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for duplicate detection issues
        """
        findings: list[Finding] = []

        try:
            if not file_path.exists():
                self.logger.warning(f"File does not exist: {file_path}")
                return findings

            if file_path.suffix != ".py":
                self.logger.debug(f"Skipping non-Python file: {file_path}")
                return findings

            # Read and parse the file
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                self.logger.debug(f"Empty file: {file_path}")
                return findings

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                return findings

            # Find test functions and analyze them
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    func_findings = self._analyze_test_function_duplicates(
                        node, file_path
                    )
                    findings.extend(func_findings)

            self.logger.debug(
                f"Duplicate detection analysis of {file_path}: {len(findings)} findings"
            )

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")

        return findings

    def _analyze_test_function_duplicates(
        self, func_node: ast.FunctionDef, file_path: Path
    ) -> list[Finding]:
        """Analyze duplicate aspects of a test function.

        Args:
            func_node: AST node for the test function
            file_path: Path to the file being analyzed

        Returns:
            List of findings for this function
        """
        findings: list[Finding] = []

        # Check for potential duplicate patterns within the function
        # This is a placeholder for more sophisticated analysis

        return findings

    def get_similarity_thresholds(self) -> dict[str, float]:
        """Get current similarity thresholds.

        Returns:
            Dictionary of similarity thresholds
        """
        return {
            "exact_duplicate_threshold": self.config["exact_duplicate_threshold"],
            "near_duplicate_threshold": self.config["near_duplicate_threshold"],
            "similar_pattern_threshold": self.config["similar_pattern_threshold"],
        }

    def update_similarity_thresholds(self, thresholds: dict[str, float]) -> None:
        """Update similarity thresholds.

        Args:
            thresholds: Dictionary of new threshold values
        """
        for key, value in thresholds.items():
            if key in self.config and 0.0 <= value <= 1.0:
                self.config[key] = value
                self.logger.info(f"Updated {key} threshold to {value}")

        # Clear similarity cache when thresholds change
        self._similarity_cache.clear()

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._similarity_cache.clear()
        self._coverage_data.clear()
        self._mock_assertion_counts.clear()
        self._exception_patterns.clear()
        self._test_signatures.clear()
        self.logger.debug("Cleared all cached data")
