"""Duplicate Test Detector for pytest-drill-sergeant.

This module implements dynamic duplicate test detection using coverage-based similarity,
mock assertion counting, exception pattern analysis, and configurable similarity thresholds.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.analyzers.clone_detector import DynamicCloneDetector
from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.rulespec import RuleRegistry, RuleSpec


class DuplicateTestDetector:
    """Detects duplicate or highly similar tests using dynamic analysis."""

    def __init__(self) -> None:
        """Initialize the duplicate test detector."""
        self.logger = logging.getLogger("drill_sergeant.duplicate_test_detector")
        self.clone_detector = DynamicCloneDetector()

    def _get_rule_spec(self) -> RuleSpec:
        """Get the rule specification for duplicate test detection.

        Returns:
            RuleSpec for duplicate test detection
        """
        return RuleRegistry.get_rule("DS201")

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a single test file for duplicate tests.

        Args:
            file_path: Path to the test file

        Returns:
            List of findings for duplicate tests
        """
        try:
            # For CLI analysis, we can't get real coverage data, so we'll do static analysis
            # This is a simplified version that focuses on structural similarity

            findings = []

            # Read the file and analyze for structural duplicates
            if not file_path.exists():
                return findings

            content = file_path.read_text()

            # Simple heuristic: look for test functions with very similar names
            # This is a basic implementation - the full dynamic analysis requires coverage data
            test_functions = self._extract_test_functions(content)

            # Find potential duplicates based on naming patterns
            potential_duplicates = self._find_naming_duplicates(test_functions)

            for duplicate_group in potential_duplicates:
                if len(duplicate_group) >= 2:
                    # Create a finding for this duplicate group
                    finding = Finding(
                        code=self._get_rule_spec().code,
                        name=self._get_rule_spec().name,
                        severity=Severity.WARNING,
                        message=f"Potential duplicate tests detected: {', '.join(duplicate_group)}",
                        file_path=file_path,
                        line_number=1,  # We'll improve this later
                    )
                    findings.append(finding)

            return findings

        except Exception as e:
            self.logger.error("Failed to analyze file %s: %s", file_path, e)
            return []

    def _extract_test_functions(self, content: str) -> list[str]:
        """Extract test function names from file content.

        Args:
            content: File content as string

        Returns:
            List of test function names
        """
        try:
            tree = ast.parse(content)
            test_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_functions.append(node.name)

            return test_functions
        except SyntaxError:
            return []

    def _find_naming_duplicates(self, test_functions: list[str]) -> list[list[str]]:
        """Find potential duplicates based on naming patterns.

        Args:
            test_functions: List of test function names

        Returns:
            List of duplicate groups
        """
        # Simple heuristic: group tests with very similar names
        groups = []
        processed = set()

        for i, func1 in enumerate(test_functions):
            if func1 in processed:
                continue

            group = [func1]
            processed.add(func1)

            for j, func2 in enumerate(test_functions[i + 1 :], i + 1):
                if func2 in processed:
                    continue

                # Check for similarity in naming
                if self._names_similar(func1, func2):
                    group.append(func2)
                    processed.add(func2)

            if len(group) >= 2:
                groups.append(group)

        return groups

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two test function names are similar.

        Args:
            name1: First test function name
            name2: Second test function name

        Returns:
            True if names are similar
        """
        # Remove common suffixes
        suffixes = ["_test", "_copy", "_duplicate", "_similar", "_basic", "_simple"]

        clean1 = name1.lower()
        clean2 = name2.lower()

        for suffix in suffixes:
            clean1 = clean1.replace(suffix, "")
            clean2 = clean2.replace(suffix, "")

        # Check if one contains the other (after cleaning)
        if clean1 in clean2 or clean2 in clean1:
            return True

        # Check for high character overlap
        if len(clean1) > 10 and len(clean2) > 10:
            overlap = len(set(clean1) & set(clean2))
            total = len(set(clean1) | set(clean2))
            similarity = overlap / total if total > 0 else 0
            return similarity > 0.8

        return False

    def analyze_test_suite_with_coverage(
        self, test_files: list[Path], coverage_data: dict[str, any]
    ) -> list[Finding]:
        """Analyze a test suite for duplicates using coverage data.

        Args:
            test_files: List of test file paths
            coverage_data: Coverage data for tests

        Returns:
            List of findings for duplicate tests
        """
        try:
            self.logger.info("Analyzing %d test files for duplicates", len(test_files))

            # Use the full dynamic clone detector
            clusters = self.clone_detector.analyze_test_suite(test_files, coverage_data)

            findings = []
            for cluster in clusters:
                # Create a finding for each duplicate cluster
                test_names = [test_name for test_name, _ in cluster.tests]
                finding = Finding(
                    code=self._get_rule_spec().code,
                    name=self._get_rule_spec().name,
                    severity=Severity.WARNING,
                    message=f"Duplicate test cluster found: {', '.join(test_names)} (similarity: {cluster.similarity_score:.2f})",
                    file_path=cluster.tests[0][1] if cluster.tests else Path(),
                    line_number=1,
                )
                findings.append(finding)

            self.logger.info("Found %d duplicate clusters", len(findings))
            return findings

        except Exception as e:
            self.logger.error("Failed to analyze test suite: %s", e)
            return []
