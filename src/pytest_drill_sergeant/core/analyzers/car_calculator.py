"""Coverage-to-Assertion Ratio (CAR) Calculator for pytest-drill-sergeant.

This module implements CAR calculation to measure test efficiency
by comparing coverage metrics to assertion counts.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding, Severity


@dataclass
class CARResult:
    """Result of CAR calculation for a test."""

    test_name: str
    file_path: Path
    line_number: int
    assertion_count: int
    coverage_percentage: float
    car_score: float
    car_grade: str
    efficiency_level: str


class CARCalculator:
    """Calculates Coverage-to-Assertion Ratio (CAR) for tests."""

    def __init__(self) -> None:
        """Initialize the CAR calculator."""
        self.logger = logging.getLogger("drill_sergeant.car_calculator")

    def calculate_car(
        self,
        test_file_path: Path,
        test_name: str,
        test_line_number: int,
        coverage_data: CoverageData | None = None,
    ) -> CARResult:
        """Calculate CAR for a specific test.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts
            coverage_data: Coverage data for the test (optional)

        Returns:
            CARResult object with CAR calculation
        """
        try:
            # Count assertions in the test
            assertion_count = self._count_assertions(
                test_file_path, test_name, test_line_number
            )

            # Get coverage percentage
            coverage_percentage = 0.0
            if coverage_data:
                coverage_percentage = coverage_data.coverage_percentage

            # Calculate CAR score
            car_score = self._calculate_car_score(assertion_count, coverage_percentage)

            # Determine CAR grade
            car_grade = self._determine_car_grade(car_score)

            # Determine efficiency level
            efficiency_level = self._determine_efficiency_level(
                car_score, assertion_count, coverage_percentage
            )

            return CARResult(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                assertion_count=assertion_count,
                coverage_percentage=coverage_percentage,
                car_score=car_score,
                car_grade=car_grade,
                efficiency_level=efficiency_level,
            )

        except Exception as e:
            self.logger.error("Failed to calculate CAR for %s: %s", test_name, e)
            # Return default CAR result on error
            return CARResult(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                assertion_count=0,
                coverage_percentage=0.0,
                car_score=0.0,
                car_grade="F",
                efficiency_level="inefficient",
            )

    def _count_assertions(
        self, test_file_path: Path, test_name: str, test_line_number: int
    ) -> int:
        """Count assertions in a test function.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts

        Returns:
            Number of assertions found
        """
        try:
            # Read and parse the file
            content = test_file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file_path))

            # Find the specific test function
            test_func = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == test_name:
                    test_func = node
                    break

            if not test_func:
                self.logger.warning(
                    "Test function %s not found in %s", test_name, test_file_path
                )
                return 0

            # Count assertions in the function
            assertion_count = 0
            for node in ast.walk(test_func):
                if isinstance(node, ast.Assert):
                    assertion_count += 1
                elif isinstance(node, ast.Call):
                    # Check for pytest assertions
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in [
                            "assert_equal",
                            "assert_not_equal",
                            "assert_true",
                            "assert_false",
                            "assert_in",
                            "assert_not_in",
                            "assert_is",
                            "assert_is_not",
                            "assert_is_none",
                            "assert_is_not_none",
                            "assert_almost_equal",
                            "assert_not_almost_equal",
                            "assert_greater",
                            "assert_greater_equal",
                            "assert_less",
                            "assert_less_equal",
                            "assert_regex",
                            "assert_not_regex",
                        ]:
                            assertion_count += 1
                    elif isinstance(node.func, ast.Name):
                        if node.func.id in [
                            "assert",
                            "assertTrue",
                            "assertFalse",
                            "assertEquals",
                            "assertNotEquals",
                        ]:
                            assertion_count += 1

            return assertion_count

        except Exception as e:
            self.logger.error("Failed to count assertions in %s: %s", test_name, e)
            return 0

    def _calculate_car_score(
        self, assertion_count: int, coverage_percentage: float
    ) -> float:
        """Calculate CAR score.

        Args:
            assertion_count: Number of assertions in the test
            coverage_percentage: Coverage percentage achieved

        Returns:
            CAR score (0-100)
        """
        if assertion_count == 0:
            return 0.0

        # CAR formula: (coverage_percentage / assertion_count) * 100
        # Higher coverage with fewer assertions = higher CAR score
        car_score = (coverage_percentage / assertion_count) * 100

        # Cap at 100
        return min(car_score, 100.0)

    def _determine_car_grade(self, car_score: float) -> str:
        """Determine CAR grade based on score.

        Args:
            car_score: CAR score (0-100)

        Returns:
            Grade (A-F)
        """
        if car_score >= 90:
            return "A"
        if car_score >= 80:
            return "B"
        if car_score >= 70:
            return "C"
        if car_score >= 60:
            return "D"
        return "F"

    def _determine_efficiency_level(
        self, car_score: float, assertion_count: int, coverage_percentage: float
    ) -> str:
        """Determine efficiency level based on CAR metrics.

        Args:
            car_score: CAR score (0-100)
            assertion_count: Number of assertions
            coverage_percentage: Coverage percentage

        Returns:
            Efficiency level description
        """
        if car_score >= 80 and coverage_percentage >= 80:
            return "highly_efficient"
        if car_score >= 60 and coverage_percentage >= 60:
            return "efficient"
        if car_score >= 40 and coverage_percentage >= 40:
            return "moderately_efficient"
        if assertion_count == 0:
            return "no_assertions"
        if coverage_percentage < 20:
            return "low_coverage"
        return "inefficient"

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for CAR-related issues.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for CAR-related issues
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
                    func_findings = self._analyze_test_function_car(node, file_path)
                    findings.extend(func_findings)

            self.logger.debug("CAR analysis of %s: %d findings", file_path, len(findings))

        except Exception as e:
            self.logger.error("Error analyzing %s: %s", file_path, e)

        return findings

    def _analyze_test_function_car(
        self, func_node: ast.FunctionDef, file_path: Path
    ) -> list[Finding]:
        """Analyze CAR aspects of a test function.

        Args:
            func_node: AST node for the test function
            file_path: Path to the file being analyzed

        Returns:
            List of findings for this function
        """
        findings: list[Finding] = []

        # Count assertions in this function
        assertion_count = 0
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assert):
                assertion_count += 1
            elif isinstance(node, ast.Call):
                # Check for pytest assertions
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in [
                        "assert_equal",
                        "assert_not_equal",
                        "assert_true",
                        "assert_false",
                    ]:
                        assertion_count += 1

        # Analyze based on assertion count
        if assertion_count == 0:
            finding = Finding(
                code="DS401",
                name="no_assertions",
                severity=Severity.WARNING,
                message=f"Test '{func_node.name}' has no assertions",
                suggestion="Add assertions to verify test behavior",
                file_path=file_path,
                line_number=func_node.lineno,
                confidence=1.0,
                fixable=False,
                tags=["car", "assertions"],
            )
            findings.append(finding)
        elif assertion_count > 10:
            finding = Finding(
                code="DS402",
                name="too_many_assertions",
                severity=Severity.INFO,
                message=f"Test '{func_node.name}' has {assertion_count} assertions (consider splitting)",
                suggestion="Consider splitting this test into multiple focused tests",
                file_path=file_path,
                line_number=func_node.lineno,
                confidence=0.8,
                fixable=False,
                tags=["car", "assertions"],
            )
            findings.append(finding)

        return findings
