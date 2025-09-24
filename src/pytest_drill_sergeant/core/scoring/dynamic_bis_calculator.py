"""Dynamic BIS calculator that uses rule metadata for scoring.

This calculator reads BIS impact and weights from rule definitions,
making it maintainable and configurable without hardcoded rule codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.rulespec import RuleRegistry


@dataclass
class BISMetrics:
    """Metrics for BIS calculation based on rule impact categories."""

    # High penalty violations (major behavior integrity issues)
    high_penalty_count: int = 0

    # Medium penalty violations (moderate behavior integrity issues)
    medium_penalty_count: int = 0

    # Low penalty violations (minor behavior integrity issues)
    low_penalty_count: int = 0

    # Advisory violations (style/structure issues)
    advisory_count: int = 0

    # Reward indicators (positive behavior)
    reward_count: int = 0

    # Weighted totals (considering rule-specific weights)
    weighted_high_penalty: float = 0.0
    weighted_medium_penalty: float = 0.0
    weighted_low_penalty: float = 0.0
    weighted_advisory: float = 0.0
    weighted_reward: float = 0.0


class DynamicBISCalculator:
    """Dynamic BIS calculator that uses rule metadata for scoring."""

    # Base penalty weights by impact category
    PENALTY_WEIGHTS: ClassVar[dict[str, float]] = {
        "high_penalty": 15.0,  # Major behavior integrity issues
        "medium_penalty": 8.0,  # Moderate behavior integrity issues
        "low_penalty": 4.0,  # Minor behavior integrity issues
        "advisory": 1.0,  # Style/structure issues (minimal)
        "reward": -5.0,  # Positive behavior indicators
    }

    def __init__(self) -> None:
        """Initialize the dynamic BIS calculator."""
        self._rule_registry = None
        self._load_rule_registry()

    def _load_rule_registry(self) -> None:
        """Load the rule registry to access rule metadata."""
        try:
            self._rule_registry = RuleRegistry
        except ImportError:
            # Fallback if registry not available
            self._rule_registry = None

    def extract_metrics_from_findings(self, findings: list[Finding]) -> BISMetrics:
        """Extract BIS metrics from analysis findings using rule metadata.

        Args:
            findings: List of findings from static analysis

        Returns:
            BISMetrics object with extracted metrics
        """
        metrics = BISMetrics()

        for finding in findings:
            # Get rule metadata
            rule_impact, rule_weight = self._get_rule_impact(finding.code)

            # Count by impact category
            if rule_impact == "high_penalty":
                metrics.high_penalty_count += 1
                metrics.weighted_high_penalty += rule_weight
            elif rule_impact == "medium_penalty":
                metrics.medium_penalty_count += 1
                metrics.weighted_medium_penalty += rule_weight
            elif rule_impact == "low_penalty":
                metrics.low_penalty_count += 1
                metrics.weighted_low_penalty += rule_weight
            elif rule_impact == "advisory":
                metrics.advisory_count += 1
                metrics.weighted_advisory += rule_weight
            elif rule_impact == "reward":
                metrics.reward_count += 1
                metrics.weighted_reward += rule_weight

        return metrics

    def _get_rule_impact(self, rule_code: str) -> tuple[str, float]:
        """Get BIS impact and weight for a rule code.

        Args:
            rule_code: The rule code to look up

        Returns:
            Tuple of (impact_category, weight)
        """
        if not self._rule_registry:
            # Fallback to default if registry not available
            return "medium_penalty", 1.0

        try:
            rule_spec = self._rule_registry.get_rule(rule_code)
        except (KeyError, AttributeError):
            # Unknown rule - treat as medium penalty
            return "medium_penalty", 1.0
        else:
            return rule_spec.bis_impact.value, rule_spec.bis_weight

    def calculate_bis(self, metrics: BISMetrics) -> float:
        """Calculate Behavior Integrity Score based on metrics.

        Args:
            metrics: BIS metrics extracted from findings

        Returns:
            BIS score from 0-100 (higher is better)
        """
        base_score = 100.0

        # Calculate penalties based on weighted counts
        total_penalty = 0.0

        # High penalty violations (major behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["high_penalty"] * min(
            metrics.weighted_high_penalty, 5.0
        )

        # Medium penalty violations (moderate behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["medium_penalty"] * min(
            metrics.weighted_medium_penalty, 8.0
        )

        # Low penalty violations (minor behavior integrity issues)
        total_penalty += self.PENALTY_WEIGHTS["low_penalty"] * min(
            metrics.weighted_low_penalty, 10.0
        )

        # Advisory violations (style/structure issues)
        total_penalty += self.PENALTY_WEIGHTS["advisory"] * min(
            metrics.weighted_advisory, 15.0
        )

        # Reward for positive behavior indicators
        reward = self.PENALTY_WEIGHTS["reward"] * min(metrics.weighted_reward, 3.0)

        # Calculate final score
        raw_score = base_score - total_penalty + reward

        return max(0, min(100, round(raw_score, 1)))

    def get_grade(self, score: float) -> str:
        """Get letter grade for BIS score.

        Args:
            score: BIS score (0-100)

        Returns:
            Letter grade (A-F)
        """
        grade_thresholds = [
            (90, "A+"), (85, "A"), (80, "A-"), (75, "B+"), (70, "B"),
            (65, "B-"), (60, "C+"), (55, "C"), (50, "C-"), (40, "D")
        ]
        
        for threshold, grade in grade_thresholds:
            if score >= threshold:
                return grade
        return "F"

    def get_score_interpretation(self, score: float) -> str:
        """Get human-readable interpretation of BIS score.

        Args:
            score: BIS score (0-100)

        Returns:
            Interpretation string
        """
        if score >= 85:
            return "Excellent - Focuses on behavior, not implementation"
        if score >= 70:
            return "Good - Mostly behavior-focused with minor implementation details"
        if score >= 55:
            return "Fair - Some implementation details but generally behavior-focused"
        if score >= 40:
            return "Poor - Too focused on implementation details"
        return "Critical - Heavily implementation-focused, needs major refactoring"

    def get_breakdown(self, metrics: BISMetrics) -> dict[str, float]:
        """Get detailed breakdown of BIS components.

        Args:
            metrics: BIS metrics

        Returns:
            Dictionary with component breakdown
        """
        return {
            "high_penalty_violations": metrics.high_penalty_count,
            "medium_penalty_violations": metrics.medium_penalty_count,
            "low_penalty_violations": metrics.low_penalty_count,
            "advisory_violations": metrics.advisory_count,
            "reward_indicators": metrics.reward_count,
            "weighted_high_penalty": metrics.weighted_high_penalty,
            "weighted_medium_penalty": metrics.weighted_medium_penalty,
            "weighted_low_penalty": metrics.weighted_low_penalty,
            "weighted_advisory": metrics.weighted_advisory,
            "weighted_reward": metrics.weighted_reward,
        }
