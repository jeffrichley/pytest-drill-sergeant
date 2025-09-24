"""Battlefield Readiness Score (BRS) calculator for pytest-drill-sergeant.

This module implements the BRS calculation system that measures overall test suite
quality by combining multiple quality dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_drill_sergeant.core.models import Finding


@dataclass
class RunMetrics:
    """Metrics collected during a test run for BRS calculation."""

    # Core metrics
    total_files: int = 0
    total_tests: int = 0
    total_violations: int = 0

    # BIS scores
    bis_scores: list[float] = None

    # AAA compliance
    aaa_compliant_tests: int = 0

    # Duplicate tests (placeholder for future implementation)
    duplicate_tests: int = 0

    # Style smells (based on current findings)
    files_with_style_issues: int = 0

    def __post_init__(self) -> None:
        """Initialize default values for mutable fields."""
        if self.bis_scores is None:
            self.bis_scores = []


class BRSCalculator:
    """Calculates Battlefield Readiness Score for overall test suite quality."""

    def __init__(self) -> None:
        """Initialize the BRS calculator."""

    def calculate_brs(self, metrics: RunMetrics) -> float:
        """Calculate Battlefield Readiness Score based on run metrics.

        Args:
            metrics: Collected metrics from the test run

        Returns:
            BRS score from 0-100 (higher is better)
        """
        if metrics.total_files == 0:
            return 100.0

        score = 100.0

        # 1. BIS Score Component (40% weight) - Average of all BIS scores
        if metrics.bis_scores:
            avg_bis = sum(metrics.bis_scores) / len(metrics.bis_scores)
            bis_component = (avg_bis / 100.0) * 40  # Convert to 0-40 scale
            score = score - 40 + bis_component

        # 2. AAA Compliance (25% weight)
        if metrics.total_tests > 0:
            aaa_rate = metrics.aaa_compliant_tests / metrics.total_tests
            aaa_component = aaa_rate * 25  # Convert to 0-25 scale
            score = score - 25 + aaa_component

        # 3. Violation Density (20% weight) - Penalty for high violation density
        violation_density = metrics.total_violations / max(1, metrics.total_tests)
        violation_penalty = min(20, violation_density * 10)  # Max 20 point penalty
        score -= violation_penalty

        # 4. Style Quality (10% weight) - Penalty for style issues
        if metrics.total_files > 0:
            style_issue_rate = metrics.files_with_style_issues / metrics.total_files
            style_penalty = style_issue_rate * 10  # Max 10 point penalty
            score -= style_penalty

        # 5. Duplicate Tests (5% weight) - Placeholder for future implementation
        if metrics.duplicate_tests > 0:
            duplicate_penalty = min(
                5, metrics.duplicate_tests * 0.5
            )  # Max 5 point penalty
            score -= duplicate_penalty

        return max(0, min(100, round(score, 1)))

    def extract_metrics_from_analysis(
        self,
        files_analyzed: list[Path],
        all_findings: list[Finding],
        bis_scores: list[float],
    ) -> RunMetrics:
        """Extract metrics from analysis results.

        Args:
            files_analyzed: List of files that were analyzed
            all_findings: All findings from the analysis
            bis_scores: BIS scores for each file

        Returns:
            RunMetrics object with extracted metrics
        """
        metrics = RunMetrics()

        # Basic counts
        metrics.total_files = len(files_analyzed)
        metrics.total_violations = len(all_findings)
        metrics.bis_scores = bis_scores

        # Estimate total tests (rough approximation)
        metrics.total_tests = max(metrics.total_files, len(all_findings) // 2)

        # Count AAA compliant tests (tests without AAA violations)
        aaa_violations = [f for f in all_findings if f.code == "DS302"]
        metrics.aaa_compliant_tests = max(0, metrics.total_tests - len(aaa_violations))

        # Count files with style issues (any violation)
        files_with_issues = set(finding.file_path for finding in all_findings)
        metrics.files_with_style_issues = len(files_with_issues)

        return metrics

    def get_brs_interpretation(self, score: float) -> str:
        """Get human-readable interpretation of BRS score.

        Args:
            score: BRS score (0-100)

        Returns:
            Interpretation string
        """
        if score >= 90:
            return "CHAMPIONSHIP LEVEL! Your test suite is BATTLE-READY!"
        if score >= 80:
            return "EXCELLENT! Your test suite shows strong discipline!"
        if score >= 70:
            return "GOOD! Your test suite is well-structured with minor issues!"
        if score >= 60:
            return "ADEQUATE! Your test suite needs some attention!"
        if score >= 50:
            return "NEEDS IMPROVEMENT! Your test suite requires significant work!"
        if score >= 40:
            return "CRITICAL! Your test suite needs major restructuring!"
        return "DISASTER! Your test suite is completely broken!"

    def get_brs_grade(self, score: float) -> str:
        """Get letter grade for BRS score.

        Args:
            score: BRS score (0-100)

        Returns:
            Letter grade (A-F)
        """
        if score >= 90:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 80:
            return "A-"
        if score >= 75:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 65:
            return "B-"
        if score >= 60:
            return "C+"
        if score >= 55:
            return "C"
        if score >= 50:
            return "C-"
        if score >= 40:
            return "D"
        return "F"

    def get_component_breakdown(self, metrics: RunMetrics) -> dict[str, float]:
        """Get breakdown of BRS components.

        Args:
            metrics: Run metrics

        Returns:
            Dictionary of component scores
        """
        breakdown = {}

        # BIS Component
        if metrics.bis_scores:
            avg_bis = sum(metrics.bis_scores) / len(metrics.bis_scores)
            breakdown["bis_score"] = round(avg_bis, 1)
        else:
            breakdown["bis_score"] = 0.0

        # AAA Compliance
        if metrics.total_tests > 0:
            aaa_rate = metrics.aaa_compliant_tests / metrics.total_tests
            breakdown["aaa_compliance"] = round(aaa_rate * 100, 1)
        else:
            breakdown["aaa_compliance"] = 100.0

        # Violation Density
        if metrics.total_tests > 0:
            violation_density = metrics.total_violations / metrics.total_tests
            breakdown["violation_density"] = round(violation_density, 2)
        else:
            breakdown["violation_density"] = 0.0

        # Style Quality
        if metrics.total_files > 0:
            style_rate = metrics.files_with_style_issues / metrics.total_files
            breakdown["style_quality"] = round((1 - style_rate) * 100, 1)
        else:
            breakdown["style_quality"] = 100.0

        return breakdown
