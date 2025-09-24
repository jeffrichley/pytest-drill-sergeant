"""Main BIS (Behavior Integrity Score) calculator for pytest-drill-sergeant.

This module provides the main BIS calculator that integrates with the plugin hooks
and provides per-test scoring functionality.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.models import Finding, ResultData
from pytest_drill_sergeant.core.scoring.dynamic_bis_calculator import (
    BISMetrics,
    DynamicBISCalculator,
)
from pytest_drill_sergeant.core.scoring.feature_extractor import get_feature_extractor

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import FeaturesData

logger = logging.getLogger(__name__)


class BISCalculator:
    """Main BIS calculator that integrates with the plugin system."""

    def __init__(self) -> None:
        """Initialize the BIS calculator."""
        self._dynamic_calculator = DynamicBISCalculator()
        self._test_scores: dict[str, float] = {}
        self._test_grades: dict[str, str] = {}
        self._test_metrics: dict[str, BISMetrics] = {}

    def calculate_file_bis(
        self, file_path: Path, findings: list[Finding]
    ) -> dict[str, ResultData]:
        """Calculate BIS scores for all tests in a file.

        Args:
            file_path: Path to the test file
            findings: List of findings from static analysis

        Returns:
            Dictionary mapping test names to ResultData objects
        """
        try:
            feature_extractor = get_feature_extractor()
            test_features = feature_extractor.extract_features_from_file(file_path, findings)

            results = {}
            for test_name, features in test_features.items():
                result = self.calculate_test_bis(test_name, findings, features)
                results[test_name] = result

            return results

        except Exception as e:
            logger.error(f"Failed to calculate BIS scores for file {file_path}: {e}")
            return {}

    def calculate_test_bis(
        self, test_name: str, findings: list[Finding], features: FeaturesData
    ) -> ResultData:
        """Calculate BIS score for a single test.

        Args:
            test_name: Name of the test
            findings: List of findings from static analysis
            features: Extracted features from the test

        Returns:
            ResultData object with BIS score and analysis results
        """
        try:
            # Extract BIS metrics from findings
            metrics = self._dynamic_calculator.extract_metrics_from_findings(findings)

            # Calculate BIS score
            bis_score = self._dynamic_calculator.calculate_bis(metrics)

            # Get grade
            bis_grade = self._dynamic_calculator.get_grade(bis_score)

            # Store for later retrieval
            test_key = f"{test_name}"
            self._test_scores[test_key] = bis_score
            self._test_grades[test_key] = bis_grade
            self._test_metrics[test_key] = metrics

            # Create result data
            result = ResultData(
                test_name=test_name,
                file_path=features.file_path,
                line_number=features.line_number,
                findings=findings,
                features=features,
                bis_score=bis_score,
                bis_grade=bis_grade,
                analyzed=True,
            )

            logger.debug(
                f"Calculated BIS score for {test_name}: {bis_score:.1f} ({bis_grade})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to calculate BIS score for {test_name}: {e}")
            return ResultData(
                test_name=test_name,
                file_path=features.file_path,
                line_number=features.line_number,
                findings=findings,
                features=features,
                bis_score=0.0,
                bis_grade="F",
                analyzed=False,
                error_message=str(e),
            )

    def get_test_bis_score(self, test_name: str) -> float:
        """Get BIS score for a specific test.

        Args:
            test_name: Name of the test

        Returns:
            BIS score (0-100), or 0 if not found
        """
        return self._test_scores.get(test_name, 0.0)

    def get_test_bis_grade(self, test_name: str) -> str:
        """Get BIS grade for a specific test.

        Args:
            test_name: Name of the test

        Returns:
            BIS grade (A-F), or "F" if not found
        """
        return self._test_grades.get(test_name, "F")

    def get_test_bis_metrics(self, test_name: str) -> BISMetrics | None:
        """Get BIS metrics for a specific test.

        Args:
            test_name: Name of the test

        Returns:
            BISMetrics object, or None if not found
        """
        return self._test_metrics.get(test_name)

    def get_all_test_scores(self) -> dict[str, float]:
        """Get all test BIS scores.

        Returns:
            Dictionary mapping test names to BIS scores
        """
        return self._test_scores.copy()

    def get_all_test_grades(self) -> dict[str, str]:
        """Get all test BIS grades.

        Returns:
            Dictionary mapping test names to BIS grades
        """
        return self._test_grades.copy()

    def get_average_bis_score(self) -> float:
        """Get average BIS score across all tests.

        Returns:
            Average BIS score, or 0 if no tests analyzed
        """
        if not self._test_scores:
            return 0.0

        return sum(self._test_scores.values()) / len(self._test_scores)

    def get_bis_score_distribution(self) -> dict[str, int]:
        """Get distribution of BIS grades.

        Returns:
            Dictionary mapping grades to counts
        """
        distribution = {"A+": 0, "A": 0, "A-": 0, "B+": 0, "B": 0, "B-": 0, "C+": 0, "C": 0, "C-": 0, "D": 0, "F": 0}

        for grade in self._test_grades.values():
            if grade in distribution:
                distribution[grade] += 1

        return distribution

    def get_top_offenders(self, limit: int = 10) -> list[tuple[str, float]]:
        """Get tests with lowest BIS scores.

        Args:
            limit: Maximum number of offenders to return

        Returns:
            List of (test_name, score) tuples, sorted by score (lowest first)
        """
        sorted_scores = sorted(self._test_scores.items(), key=lambda x: x[1])
        return sorted_scores[:limit]

    def get_top_performers(self, limit: int = 10) -> list[tuple[str, float]]:
        """Get tests with highest BIS scores.

        Args:
            limit: Maximum number of performers to return

        Returns:
            List of (test_name, score) tuples, sorted by score (highest first)
        """
        sorted_scores = sorted(self._test_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:limit]

    def get_bis_summary(self) -> dict[str, float | int | str]:
        """Get comprehensive BIS summary.

        Returns:
            Dictionary with BIS summary statistics
        """
        if not self._test_scores:
            return {
                "total_tests": 0,
                "average_score": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "grade_distribution": {},
                "top_offenders": [],
                "top_performers": [],
            }

        scores = list(self._test_scores.values())
        distribution = self.get_bis_score_distribution()

        return {
            "total_tests": len(self._test_scores),
            "average_score": self.get_average_bis_score(),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "grade_distribution": distribution,
            "top_offenders": self.get_top_offenders(5),
            "top_performers": self.get_top_performers(5),
        }

    def clear_cache(self) -> None:
        """Clear all cached BIS data."""
        self._test_scores.clear()
        self._test_grades.clear()
        self._test_metrics.clear()

    def get_score_interpretation(self, score: float) -> str:
        """Get human-readable interpretation of BIS score.

        Args:
            score: BIS score (0-100)

        Returns:
            Interpretation string
        """
        return self._dynamic_calculator.get_score_interpretation(score)

    def get_breakdown(self, test_name: str) -> dict[str, float] | None:
        """Get detailed breakdown of BIS components for a test.

        Args:
            test_name: Name of the test

        Returns:
            Dictionary with component breakdown, or None if not found
        """
        metrics = self._test_metrics.get(test_name)
        if metrics is None:
            return None

        return self._dynamic_calculator.get_breakdown(metrics)


# Global BIS calculator instance
_bis_calculator: BISCalculator | None = None


def get_bis_calculator() -> BISCalculator:
    """Get the global BIS calculator instance.

    Returns:
        BISCalculator instance
    """
    global _bis_calculator
    if _bis_calculator is None:
        _bis_calculator = BISCalculator()
    return _bis_calculator


def reset_bis_calculator() -> None:
    """Reset the global BIS calculator instance."""
    global _bis_calculator
    _bis_calculator = None