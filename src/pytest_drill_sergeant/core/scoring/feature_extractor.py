"""Feature extraction for BIS calculation.

This module provides feature extraction capabilities for analyzing test files
and extracting relevant features for Behavior Integrity Score calculation.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.models import FeaturesData, Finding

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

logger = logging.getLogger(__name__)


class TestFeatureExtractor:
    """Extracts features from test files for BIS calculation."""

    def __init__(self) -> None:
        """Initialize the feature extractor."""
        self._cache: dict[str, FeaturesData] = {}

    def extract_features_from_file(
        self, file_path: Path, findings: list[Finding]
    ) -> dict[str, FeaturesData]:
        """Extract features for all tests in a file.

        Args:
            file_path: Path to the test file
            findings: List of findings from static analysis

        Returns:
            Dictionary mapping test names to FeaturesData objects
        """
        try:
            # Check cache first
            cache_key = str(file_path)
            if cache_key in self._cache:
                return {cache_key: self._cache[cache_key]}

            # Parse the file
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                # Empty file - return default features
                default_features = self._create_default_features(file_path)
                self._cache[cache_key] = default_features
                return {cache_key: default_features}

            tree = ast.parse(content, filename=str(file_path))

            # Extract features for each test function
            test_features = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    features = self._extract_test_features(node, findings, file_path)
                    test_features[node.name] = features

            # If no test functions found, return default features for the file
            if not test_features:
                default_features = self._create_default_features(file_path)
                self._cache[cache_key] = default_features
                return {cache_key: default_features}

            # Cache the results
            self._cache[cache_key] = test_features

            return test_features

        except Exception as e:
            logger.error(f"Failed to extract features from {file_path}: {e}")
            default_features = self._create_default_features(file_path)
            return {str(file_path): default_features}

    def _extract_test_features(
        self, test_node: ast.FunctionDef, findings: list[Finding], file_path: Path
    ) -> FeaturesData:
        """Extract features from a single test function.

        Args:
            test_node: AST node for the test function
            findings: List of findings from static analysis
            file_path: Path to the test file

        Returns:
            FeaturesData object with extracted features
        """
        # Count different types of findings for this test
        test_findings = self._filter_findings_for_test(findings, test_node.lineno)

        # Extract AST-based features
        private_access_count = len([f for f in test_findings if f.code == "DS301"])
        mock_assertion_count = len([f for f in test_findings if f.code == "DS305"])
        structural_equality_count = len([f for f in test_findings if f.code == "DS306"])
        aaa_comments_count = len([f for f in test_findings if f.code == "DS302"])

        # Calculate test complexity
        complexity_score = self._calculate_complexity(test_node)

        # Count assertions
        assertion_count = self._count_assertions(test_node)

        # Count setup/teardown lines
        setup_lines = self._count_setup_lines(test_node)
        teardown_lines = self._count_teardown_lines(test_node)

        # Check for AAA structure
        has_aaa_comments = (
            aaa_comments_count == 0
        )  # No AAA violations means good structure

        return FeaturesData(
            test_name=test_node.name,
            file_path=file_path,
            line_number=test_node.lineno,
            has_aaa_comments=has_aaa_comments,
            aaa_comment_order=None,  # Could be enhanced to detect order
            private_access_count=private_access_count,
            mock_assertion_count=mock_assertion_count,
            structural_equality_count=structural_equality_count,
            test_length=self._calculate_test_length(test_node),
            complexity_score=complexity_score,
            assertion_count=assertion_count,
            setup_lines=setup_lines,
            teardown_lines=teardown_lines,
        )

    def _filter_findings_for_test(
        self, findings: list[Finding], test_line: int
    ) -> list[Finding]:
        """Filter findings to only include those relevant to a specific test.

        Args:
            findings: List of all findings
            test_line: Line number where the test starts

        Returns:
            List of findings relevant to this test
        """
        # For now, we'll use all findings since we don't have precise line mapping
        # In a more sophisticated implementation, we'd map findings to specific tests
        return findings

    def _calculate_complexity(self, test_node: ast.FunctionDef) -> float:
        """Calculate cyclomatic complexity of a test function.

        Args:
            test_node: AST node for the test function

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity

        for node in ast.walk(test_node):
            if isinstance(
                node, (ast.If, ast.While, ast.For, ast.AsyncFor)
            ) or isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return float(complexity)

    def _count_assertions(self, test_node: ast.FunctionDef) -> int:
        """Count assertions in a test function.

        Args:
            test_node: AST node for the test function

        Returns:
            Number of assertions
        """
        assertion_count = 0

        for node in ast.walk(test_node):
            if isinstance(node, ast.Assert):
                assertion_count += 1
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr.startswith("assert"):
                        assertion_count += 1
                elif isinstance(node.func, ast.Name):
                    if node.func.id.startswith("assert"):
                        assertion_count += 1

        return assertion_count

    def _count_setup_lines(self, test_node: ast.FunctionDef) -> int:
        """Count setup/arrange lines in a test function.

        Args:
            test_node: AST node for the test function

        Returns:
            Number of setup lines
        """
        # This is a simplified implementation
        # In practice, we'd need to identify setup vs execution vs assertion lines
        body_lines = len(test_node.body)
        return max(0, body_lines - 2)  # Assume at least 2 lines for act/assert

    def _count_teardown_lines(self, test_node: ast.FunctionDef) -> int:
        """Count teardown lines in a test function.

        Args:
            test_node: AST node for the test function

        Returns:
            Number of teardown lines
        """
        # For now, we'll assume minimal teardown
        return 0

    def _calculate_test_length(self, test_node: ast.FunctionDef) -> int:
        """Calculate the length of a test function.

        Args:
            test_node: AST node for the test function

        Returns:
            Number of lines in the test
        """
        if not test_node.body:
            return 0

        start_line = test_node.lineno
        end_line = test_node.end_lineno or start_line

        return end_line - start_line + 1

    def _create_default_features(self, file_path: Path) -> FeaturesData:
        """Create default features for a file.

        Args:
            file_path: Path to the test file

        Returns:
            Default FeaturesData object
        """
        return FeaturesData(
            test_name=file_path.stem,
            file_path=file_path,
            line_number=1,
        )

    def clear_cache(self) -> None:
        """Clear the feature extraction cache."""
        self._cache.clear()


# Global feature extractor instance
_feature_extractor: TestFeatureExtractor | None = None


def get_feature_extractor() -> TestFeatureExtractor:
    """Get the global feature extractor instance.

    Returns:
        TestFeatureExtractor instance
    """
    global _feature_extractor
    if _feature_extractor is None:
        _feature_extractor = TestFeatureExtractor()
    return _feature_extractor


def reset_feature_extractor() -> None:
    """Reset the global feature extractor instance."""
    global _feature_extractor
    _feature_extractor = None
