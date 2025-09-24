"""Tests for the BRS Calculator."""

from __future__ import annotations

from pathlib import Path

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.scoring.brs_calculator import BRSCalculator, RunMetrics


class TestBRSCalculator:
    """Test the BRS Calculator functionality."""

    def test_init(self) -> None:
        """Test calculator initialization."""
        calculator = BRSCalculator()
        assert calculator is not None

    def test_calculate_brs_perfect_score(self) -> None:
        """Test BRS calculation for perfect test suite."""
        metrics = RunMetrics(
            total_files=10,
            total_tests=50,
            total_violations=0,
            bis_scores=[100.0, 100.0, 100.0, 100.0, 100.0],
            aaa_compliant_tests=50,
            duplicate_tests=0,
            files_with_style_issues=0
        )
        
        calculator = BRSCalculator()
        score = calculator.calculate_brs(metrics)
        
        # Perfect test suite should score very high
        assert score >= 95

    def test_calculate_brs_poor_quality(self) -> None:
        """Test BRS calculation with poor quality metrics."""
        metrics = RunMetrics(
            total_files=10,
            total_tests=50,
            total_violations=100,
            bis_scores=[30.0, 40.0, 25.0, 35.0, 20.0],
            aaa_compliant_tests=10,
            duplicate_tests=20,
            files_with_style_issues=8
        )
        
        calculator = BRSCalculator()
        score = calculator.calculate_brs(metrics)
        
        # Poor quality should result in low score
        assert score < 50

    def test_calculate_brs_medium_quality(self) -> None:
        """Test BRS calculation with medium quality metrics."""
        metrics = RunMetrics(
            total_files=10,
            total_tests=50,
            total_violations=25,
            bis_scores=[75.0, 80.0, 70.0, 85.0, 78.0],
            aaa_compliant_tests=35,
            duplicate_tests=5,
            files_with_style_issues=3
        )
        
        calculator = BRSCalculator()
        score = calculator.calculate_brs(metrics)
        
        # Medium quality should result in medium score
        assert 60 <= score <= 85

    def test_calculate_brs_empty_metrics(self) -> None:
        """Test BRS calculation with empty metrics."""
        metrics = RunMetrics()
        
        calculator = BRSCalculator()
        score = calculator.calculate_brs(metrics)
        
        # Empty metrics should return perfect score
        assert score == 100.0

    def test_extract_metrics_from_analysis(self) -> None:
        """Test metric extraction from analysis results."""
        files_analyzed = [Path("test1.py"), Path("test2.py"), Path("test3.py")]
        findings = [
            Finding(
                code="DS201",
                name="private_access",
                message="Private access detected",
                file_path=Path("test1.py"),
                line_number=10,
                severity=Severity.WARNING
            ),
            Finding(
                code="DS302",
                name="aaa_comments",
                message="Missing AAA structure",
                file_path=Path("test2.py"),
                line_number=15,
                severity=Severity.WARNING
            )
        ]
        bis_scores = [85.0, 90.0, 95.0]
        
        calculator = BRSCalculator()
        metrics = calculator.extract_metrics_from_analysis(files_analyzed, findings, bis_scores)
        
        assert metrics.total_files == 3
        assert metrics.total_violations == 2
        assert metrics.bis_scores == bis_scores
        assert metrics.aaa_compliant_tests == 2  # 3 tests - 1 AAA violation = 2
        assert metrics.files_with_style_issues == 2  # 2 files with findings
        assert metrics.total_tests >= 3

    def test_get_brs_interpretation(self) -> None:
        """Test BRS score interpretation."""
        calculator = BRSCalculator()
        
        # Test different score ranges
        assert "CHAMPIONSHIP" in calculator.get_brs_interpretation(95)
        assert "EXCELLENT" in calculator.get_brs_interpretation(85)
        assert "GOOD" in calculator.get_brs_interpretation(75)
        assert "ADEQUATE" in calculator.get_brs_interpretation(65)
        assert "CRITICAL" in calculator.get_brs_interpretation(45)
        assert "DISASTER" in calculator.get_brs_interpretation(25)

    def test_get_brs_grade(self) -> None:
        """Test BRS grade assignment."""
        # Arrange
        calculator = BRSCalculator()
        
        # Act & Assert
        assert calculator.get_brs_grade(95) == "A+"
        assert calculator.get_brs_grade(90) == "A+"
        assert calculator.get_brs_grade(85) == "A"
        assert calculator.get_brs_grade(80) == "A-"
        assert calculator.get_brs_grade(75) == "B+"
        assert calculator.get_brs_grade(70) == "B"
        assert calculator.get_brs_grade(65) == "B-"
        assert calculator.get_brs_grade(60) == "C+"
        assert calculator.get_brs_grade(55) == "C"
        assert calculator.get_brs_grade(50) == "C-"
        assert calculator.get_brs_grade(40) == "D"
        assert calculator.get_brs_grade(30) == "F"

    def test_get_component_breakdown(self) -> None:
        """Test component breakdown calculation."""
        metrics = RunMetrics(
            total_files=10,
            total_tests=50,
            total_violations=25,
            bis_scores=[80.0, 85.0, 90.0],
            aaa_compliant_tests=40,
            duplicate_tests=5,
            files_with_style_issues=3
        )
        
        calculator = BRSCalculator()
        breakdown = calculator.get_component_breakdown(metrics)
        
        # Check that all expected components are present
        assert "bis_score" in breakdown
        assert "aaa_compliance" in breakdown
        assert "violation_density" in breakdown
        assert "style_quality" in breakdown
        
        # Check reasonable values
        assert 0 <= breakdown["bis_score"] <= 100
        assert 0 <= breakdown["aaa_compliance"] <= 100
        assert breakdown["violation_density"] >= 0
        assert 0 <= breakdown["style_quality"] <= 100

    def test_brs_score_bounds(self) -> None:
        """Test that BRS scores are always within 0-100 bounds."""
        calculator = BRSCalculator()
        
        # Test extreme cases
        extreme_metrics = RunMetrics(
            total_files=100,
            total_tests=1000,
            total_violations=10000,
            bis_scores=[0.0] * 100,
            aaa_compliant_tests=0,
            duplicate_tests=500,
            files_with_style_issues=100
        )
        
        score = calculator.calculate_brs(extreme_metrics)
        assert 0 <= score <= 100
        
        # Test with very high quality
        perfect_metrics = RunMetrics(
            total_files=100,
            total_tests=1000,
            total_violations=0,
            bis_scores=[100.0] * 100,
            aaa_compliant_tests=1000,
            duplicate_tests=0,
            files_with_style_issues=0
        )
        
        score = calculator.calculate_brs(perfect_metrics)
        assert 0 <= score <= 100

    def test_bis_component_weighting(self) -> None:
        """Test that BIS scores are properly weighted in BRS calculation."""
        calculator = BRSCalculator()
        
        # Test with high BIS scores
        high_bis_metrics = RunMetrics(
            total_files=5,
            total_tests=25,
            total_violations=10,
            bis_scores=[95.0, 98.0, 92.0, 96.0, 94.0],
            aaa_compliant_tests=20,
            duplicate_tests=0,
            files_with_style_issues=1
        )
        
        high_score = calculator.calculate_brs(high_bis_metrics)
        
        # Test with low BIS scores
        low_bis_metrics = RunMetrics(
            total_files=5,
            total_tests=25,
            total_violations=10,
            bis_scores=[30.0, 35.0, 25.0, 40.0, 32.0],
            aaa_compliant_tests=20,
            duplicate_tests=0,
            files_with_style_issues=1
        )
        
        low_score = calculator.calculate_brs(low_bis_metrics)
        
        # High BIS scores should result in higher BRS
        assert high_score > low_score

    def test_aaa_compliance_weighting(self) -> None:
        """Test that AAA compliance is properly weighted in BRS calculation."""
        calculator = BRSCalculator()
        
        # Test with high AAA compliance
        high_aaa_metrics = RunMetrics(
            total_files=5,
            total_tests=25,
            total_violations=5,
            bis_scores=[80.0] * 5,
            aaa_compliant_tests=25,  # All tests compliant
            duplicate_tests=0,
            files_with_style_issues=0
        )
        
        high_score = calculator.calculate_brs(high_aaa_metrics)
        
        # Test with low AAA compliance
        low_aaa_metrics = RunMetrics(
            total_files=5,
            total_tests=25,
            total_violations=5,
            bis_scores=[80.0] * 5,
            aaa_compliant_tests=5,  # Only 20% compliant
            duplicate_tests=0,
            files_with_style_issues=0
        )
        
        low_score = calculator.calculate_brs(low_aaa_metrics)
        
        # High AAA compliance should result in higher BRS
        assert high_score > low_score
