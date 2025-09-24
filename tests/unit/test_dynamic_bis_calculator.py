"""Tests for the Dynamic BIS Calculator."""

from __future__ import annotations

import pytest
from pathlib import Path
from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.scoring.dynamic_bis_calculator import DynamicBISCalculator, BISMetrics


class TestDynamicBISCalculator:
    """Test the Dynamic BIS Calculator functionality."""

    def test_init(self) -> None:
        """Test calculator initialization."""
        calculator = DynamicBISCalculator()
        assert calculator is not None

    def test_extract_metrics_from_findings(self) -> None:
        """Test metric extraction from findings."""
        findings = [
            Finding(
                code="DS301",  # Private access (high penalty)
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING
            ),
            Finding(
                code="DS302",  # AAA comments (advisory)
                name="aaa_comments",
                message="Missing AAA structure",
                file_path=Path("test.py"),
                line_number=15,
                severity=Severity.INFO
            ),
            Finding(
                code="DS305",  # Mock overspec (high penalty)
                name="mock_overspecification",
                message="Mock over-specified",
                file_path=Path("test.py"),
                line_number=20,
                severity=Severity.WARNING
            )
        ]
        
        calculator = DynamicBISCalculator()
        metrics = calculator.extract_metrics_from_findings(findings)
        
        # Should have 2 high penalty violations
        assert metrics.high_penalty_count == 2
        assert metrics.weighted_high_penalty > 0
        
        # Should have 1 advisory violation
        assert metrics.advisory_count == 1
        assert metrics.weighted_advisory > 0

    def test_calculate_bis_perfect_score(self) -> None:
        """Test BIS calculation for perfect test suite."""
        metrics = BISMetrics()  # No violations
        calculator = DynamicBISCalculator()
        score = calculator.calculate_bis(metrics)
        
        # Perfect test suite should score 100
        assert score == 100.0

    def test_calculate_bis_with_violations(self) -> None:
        """Test BIS calculation with violations."""
        metrics = BISMetrics(
            high_penalty_count=2,
            weighted_high_penalty=3.0,
            medium_penalty_count=1,
            weighted_medium_penalty=1.0,
            advisory_count=3,
            weighted_advisory=0.9
        )
        
        calculator = DynamicBISCalculator()
        score = calculator.calculate_bis(metrics)
        
        # Should be penalized for violations
        assert score < 100
        assert score > 0

    def test_calculate_bis_with_rewards(self) -> None:
        """Test BIS calculation with reward indicators."""
        metrics = BISMetrics(
            reward_count=2,
            weighted_reward=2.0
        )
        
        calculator = DynamicBISCalculator()
        score = calculator.calculate_bis(metrics)
        
        # Should get bonus for rewards (but capped at 100)
        assert score >= 90  # Should be high due to rewards

    def test_get_grade(self) -> None:
        """Test grade assignment."""
        calculator = DynamicBISCalculator()
        
        assert calculator.get_grade(95) == "A+"
        assert calculator.get_grade(90) == "A+"
        assert calculator.get_grade(85) == "A"
        assert calculator.get_grade(80) == "A-"
        assert calculator.get_grade(75) == "B+"
        assert calculator.get_grade(70) == "B"
        assert calculator.get_grade(65) == "B-"
        assert calculator.get_grade(60) == "C+"
        assert calculator.get_grade(55) == "C"
        assert calculator.get_grade(50) == "C-"
        assert calculator.get_grade(40) == "D"
        assert calculator.get_grade(30) == "F"

    def test_get_score_interpretation(self) -> None:
        """Test score interpretation."""
        calculator = DynamicBISCalculator()
        
        assert "Excellent" in calculator.get_score_interpretation(90)
        assert "Good" in calculator.get_score_interpretation(75)
        assert "Fair" in calculator.get_score_interpretation(60)
        assert "Poor" in calculator.get_score_interpretation(45)
        assert "Critical" in calculator.get_score_interpretation(25)

    def test_get_breakdown(self) -> None:
        """Test breakdown calculation."""
        metrics = BISMetrics(
            high_penalty_count=1,
            medium_penalty_count=2,
            low_penalty_count=1,
            advisory_count=3,
            reward_count=1,
            weighted_high_penalty=1.5,
            weighted_medium_penalty=2.0,
            weighted_low_penalty=1.0,
            weighted_advisory=0.9,
            weighted_reward=1.0
        )
        
        calculator = DynamicBISCalculator()
        breakdown = calculator.get_breakdown(metrics)
        
        assert breakdown["high_penalty_violations"] == 1
        assert breakdown["medium_penalty_violations"] == 2
        assert breakdown["low_penalty_violations"] == 1
        assert breakdown["advisory_violations"] == 3
        assert breakdown["reward_indicators"] == 1
        assert breakdown["weighted_high_penalty"] == 1.5
        assert breakdown["weighted_medium_penalty"] == 2.0
        assert breakdown["weighted_low_penalty"] == 1.0
        assert breakdown["weighted_advisory"] == 0.9
        assert breakdown["weighted_reward"] == 1.0

    def test_unknown_rule_code(self) -> None:
        """Test handling of unknown rule codes."""
        findings = [
            Finding(
                code="DS999",  # Unknown rule code (but valid format)
                name="unknown_rule",
                message="Unknown violation",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING
            )
        ]
        
        calculator = DynamicBISCalculator()
        metrics = calculator.extract_metrics_from_findings(findings)
        
        # Unknown rules should be treated as medium penalty
        assert metrics.medium_penalty_count == 1
        assert metrics.weighted_medium_penalty == 1.0

    def test_score_bounds(self) -> None:
        """Test that BIS scores are always within 0-100 bounds."""
        calculator = DynamicBISCalculator()
        
        # Test extreme violations
        extreme_metrics = BISMetrics(
            high_penalty_count=100,
            weighted_high_penalty=1000.0,
            medium_penalty_count=100,
            weighted_medium_penalty=1000.0,
            advisory_count=100,
            weighted_advisory=1000.0
        )
        
        score = calculator.calculate_bis(extreme_metrics)
        assert 0 <= score <= 100
        
        # Test extreme rewards
        reward_metrics = BISMetrics(
            reward_count=100,
            weighted_reward=1000.0
        )
        
        score = calculator.calculate_bis(reward_metrics)
        assert 0 <= score <= 100

    def test_penalty_capping(self) -> None:
        """Test that penalties are capped to prevent excessive scoring."""
        calculator = DynamicBISCalculator()
        
        # Test that many violations don't result in negative scores
        metrics = BISMetrics(
            high_penalty_count=50,
            weighted_high_penalty=50.0,
            medium_penalty_count=50,
            weighted_medium_penalty=50.0,
            advisory_count=50,
            weighted_advisory=50.0
        )
        
        score = calculator.calculate_bis(metrics)
        assert score >= 0  # Should not go below 0
        assert score < 50  # Should be significantly penalized
