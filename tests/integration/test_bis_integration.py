"""Integration tests for BIS (Behavior Integrity Score) system.

This module tests the end-to-end functionality of the BIS system,
including feature extraction, score calculation, and reporting.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.models import FeaturesData, Finding, Severity
from pytest_drill_sergeant.core.scoring import (
    BISCalculator,
    DynamicBISCalculator,
    FeatureExtractor,
    get_bis_calculator,
    get_feature_extractor,
)

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import FeaturesData


class TestBISIntegration:
    """Test BIS system integration."""

    def test_bis_calculator_initialization(self) -> None:
        """Test BIS calculator initialization."""
        calculator = BISCalculator()
        assert calculator is not None
        assert calculator.get_average_bis_score() == 0.0

    def test_feature_extractor_initialization(self) -> None:
        """Test feature extractor initialization."""
        extractor = FeatureExtractor()
        assert extractor is not None

    def test_global_bis_calculator_singleton(self) -> None:
        """Test that global BIS calculator is a singleton."""
        calc1 = get_bis_calculator()
        calc2 = get_bis_calculator()
        assert calc1 is calc2

    def test_global_feature_extractor_singleton(self) -> None:
        """Test that global feature extractor is a singleton."""
        extractor1 = get_feature_extractor()
        extractor2 = get_feature_extractor()
        assert extractor1 is extractor2

    def test_bis_calculation_with_findings(self) -> None:
        """Test BIS calculation with various findings."""
        calculator = BISCalculator()

        # Create test findings
        findings = [
            Finding(
                code="DS301",  # Private access (high penalty)
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            ),
            Finding(
                code="DS305",  # Mock overspec (high penalty)
                name="mock_overspecification",
                message="Mock over-specified",
                file_path=Path("test.py"),
                line_number=20,
                severity=Severity.WARNING,
            ),
            Finding(
                code="DS302",  # AAA comments (advisory)
                name="aaa_comments",
                message="Missing AAA structure",
                file_path=Path("test.py"),
                line_number=15,
                severity=Severity.INFO,
            ),
        ]

        # Create basic features
        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
            mock_assertion_count=1,
            structural_equality_count=0,
            has_aaa_comments=False,
        )

        # Calculate BIS score
        result = calculator.calculate_test_bis("test_example", findings, features)

        assert result.bis_score > 0
        assert result.bis_score < 100  # Should be penalized for violations
        assert result.bis_grade in [
            "A+",
            "A",
            "A-",
            "B+",
            "B",
            "B-",
            "C+",
            "C",
            "C-",
            "D",
            "F",
        ]
        assert result.analyzed is True

    def test_bis_calculation_perfect_score(self) -> None:
        """Test BIS calculation for perfect test."""
        calculator = BISCalculator()

        # No findings (perfect test)
        findings = []

        # Create features for a good test
        features = FeaturesData(
            test_name="test_perfect",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            has_aaa_comments=True,  # Good AAA structure
        )

        # Calculate BIS score
        result = calculator.calculate_test_bis("test_perfect", findings, features)

        assert result.bis_score == 100.0
        assert result.bis_grade == "A+"
        assert result.analyzed is True

    def test_bis_score_retrieval(self) -> None:
        """Test BIS score retrieval after calculation."""
        calculator = BISCalculator()

        # Calculate a score first
        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            )
        ]

        features = FeaturesData(
            test_name="test_retrieval",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
        )

        calculator.calculate_test_bis("test_retrieval", findings, features)

        # Test retrieval methods
        assert calculator.get_test_bis_score("test_retrieval") > 0
        assert calculator.get_test_bis_grade("test_retrieval") in [
            "A+",
            "A",
            "A-",
            "B+",
            "B",
            "B-",
            "C+",
            "C",
            "C-",
            "D",
            "F",
        ]
        assert calculator.get_test_bis_metrics("test_retrieval") is not None

        # Test non-existent test
        assert calculator.get_test_bis_score("nonexistent") == 0.0
        assert calculator.get_test_bis_grade("nonexistent") == "F"
        assert calculator.get_test_bis_metrics("nonexistent") is None

    def test_bis_summary_statistics(self) -> None:
        """Test BIS summary statistics."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            (
                "test_good",
                [],
                FeaturesData(
                    test_name="test_good",
                    file_path=Path("test.py"),
                    line_number=5,
                    has_aaa_comments=True,
                ),
            ),
            (
                "test_bad",
                [
                    Finding(
                        code="DS301",
                        name="private_access",
                        message="Private access",
                        file_path=Path("test.py"),
                        line_number=10,
                        severity=Severity.WARNING,
                    )
                ],
                FeaturesData(
                    test_name="test_bad",
                    file_path=Path("test.py"),
                    line_number=5,
                    private_access_count=1,
                ),
            ),
            (
                "test_medium",
                [
                    Finding(
                        code="DS302",
                        name="aaa_comments",
                        message="Missing AAA",
                        file_path=Path("test.py"),
                        line_number=15,
                        severity=Severity.INFO,
                    )
                ],
                FeaturesData(
                    test_name="test_medium", file_path=Path("test.py"), line_number=5
                ),
            ),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        # Test summary statistics
        summary = calculator.get_bis_summary()

        assert summary["total_tests"] == 3
        assert summary["average_score"] > 0
        assert summary["highest_score"] >= summary["average_score"]
        assert summary["lowest_score"] <= summary["average_score"]
        assert "grade_distribution" in summary
        assert "top_offenders" in summary
        assert "top_performers" in summary

    def test_bis_score_distribution(self) -> None:
        """Test BIS score distribution calculation."""
        calculator = BISCalculator()

        # Calculate scores for tests with different grades
        test_data = [
            (
                "test_a",
                [],
                FeaturesData(
                    test_name="test_a",
                    file_path=Path("test.py"),
                    line_number=5,
                    has_aaa_comments=True,
                ),
            ),
            (
                "test_b",
                [
                    Finding(
                        code="DS302",
                        name="aaa_comments",
                        message="Missing AAA",
                        file_path=Path("test.py"),
                        line_number=10,
                        severity=Severity.INFO,
                    )
                ],
                FeaturesData(
                    test_name="test_b", file_path=Path("test.py"), line_number=5
                ),
            ),
            (
                "test_f",
                [
                    Finding(
                        code="DS301",
                        name="private_access",
                        message="Private access",
                        file_path=Path("test.py"),
                        line_number=15,
                        severity=Severity.WARNING,
                    )
                ],
                FeaturesData(
                    test_name="test_f",
                    file_path=Path("test.py"),
                    line_number=5,
                    private_access_count=1,
                ),
            ),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        distribution = calculator.get_bis_score_distribution()

        # Check that distribution has all grades
        expected_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        for grade in expected_grades:
            assert grade in distribution
            assert distribution[grade] >= 0

        # Check that we have some tests in the distribution
        total_tests = sum(distribution.values())
        assert total_tests == 3

    def test_bis_top_offenders_and_performers(self) -> None:
        """Test top offenders and performers functionality."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            (
                "test_excellent",
                [],
                FeaturesData(
                    test_name="test_excellent",
                    file_path=Path("test.py"),
                    line_number=5,
                    has_aaa_comments=True,
                ),
            ),
            (
                "test_good",
                [
                    Finding(
                        code="DS302",
                        name="aaa_comments",
                        message="Missing AAA",
                        file_path=Path("test.py"),
                        line_number=10,
                        severity=Severity.INFO,
                    )
                ],
                FeaturesData(
                    test_name="test_good", file_path=Path("test.py"), line_number=5
                ),
            ),
            (
                "test_poor",
                [
                    Finding(
                        code="DS301",
                        name="private_access",
                        message="Private access",
                        file_path=Path("test.py"),
                        line_number=15,
                        severity=Severity.WARNING,
                    )
                ],
                FeaturesData(
                    test_name="test_poor",
                    file_path=Path("test.py"),
                    line_number=5,
                    private_access_count=1,
                ),
            ),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        # Test top offenders (lowest scores first)
        offenders = calculator.get_top_offenders(2)
        assert len(offenders) <= 2
        if len(offenders) >= 2:
            assert (
                offenders[0][1] <= offenders[1][1]
            )  # Scores should be in ascending order

        # Test top performers (highest scores first)
        performers = calculator.get_top_performers(2)
        assert len(performers) <= 2
        if len(performers) >= 2:
            assert (
                performers[0][1] >= performers[1][1]
            )  # Scores should be in descending order

    def test_bis_breakdown(self) -> None:
        """Test BIS breakdown functionality."""
        calculator = BISCalculator()

        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            ),
            Finding(
                code="DS305",
                name="mock_overspecification",
                message="Mock over-specified",
                file_path=Path("test.py"),
                line_number=20,
                severity=Severity.WARNING,
            ),
        ]

        features = FeaturesData(
            test_name="test_breakdown",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
            mock_assertion_count=1,
        )

        calculator.calculate_test_bis("test_breakdown", findings, features)

        breakdown = calculator.get_breakdown("test_breakdown")
        assert breakdown is not None
        assert "high_penalty_violations" in breakdown
        assert "medium_penalty_violations" in breakdown
        assert "low_penalty_violations" in breakdown
        assert "advisory_violations" in breakdown
        assert "reward_indicators" in breakdown

    def test_bis_score_interpretation(self) -> None:
        """Test BIS score interpretation."""
        calculator = BISCalculator()

        # Test different score ranges
        assert "Excellent" in calculator.get_score_interpretation(90)
        assert "Good" in calculator.get_score_interpretation(75)
        assert "Fair" in calculator.get_score_interpretation(60)
        assert "Poor" in calculator.get_score_interpretation(45)
        assert "Critical" in calculator.get_score_interpretation(25)

    def test_bis_calculator_cache_clearing(self) -> None:
        """Test BIS calculator cache clearing."""
        calculator = BISCalculator()

        # Calculate a score
        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            )
        ]
        features = FeaturesData(
            test_name="test_cache",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
        )

        calculator.calculate_test_bis("test_cache", findings, features)
        assert calculator.get_test_bis_score("test_cache") > 0

        # Clear cache
        calculator.clear_cache()
        assert calculator.get_test_bis_score("test_cache") == 0.0
        assert calculator.get_average_bis_score() == 0.0

    def test_dynamic_bis_calculator_integration(self) -> None:
        """Test integration with dynamic BIS calculator."""
        calculator = BISCalculator()
        dynamic_calculator = DynamicBISCalculator()

        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=Path("test.py"),
                line_number=10,
                severity=Severity.WARNING,
            )
        ]

        # Test that both calculators produce consistent results
        metrics = dynamic_calculator.extract_metrics_from_findings(findings)
        dynamic_score = dynamic_calculator.calculate_bis(metrics)

        features = FeaturesData(
            test_name="test_dynamic",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
        )

        result = calculator.calculate_test_bis("test_dynamic", findings, features)
        calculator_score = result.bis_score

        # Scores should be similar (allowing for small differences due to different calculation paths)
        assert abs(dynamic_score - calculator_score) < 5.0

    def test_feature_extractor_with_real_file(self, tmp_path: Path) -> None:
        """Test feature extractor with a real test file."""
        # Create a test file
        test_file = tmp_path / "test_example.py"
        test_content = '''
def test_simple():
    """A simple test."""
    assert True

def test_with_assertions():
    """A test with multiple assertions."""
    result = some_function()
    assert result is not None
    assert result > 0
    assert result < 100

def test_complex():
    """A complex test."""
    if condition:
        for item in items:
            assert item is not None
    else:
        assert False
'''
        test_file.write_text(test_content)

        extractor = FeatureExtractor()
        findings = []  # No findings for this test

        features = extractor.extract_features_from_file(test_file, findings)

        # Should extract features for all test functions
        assert len(features) >= 3
        assert "test_simple" in features
        assert "test_with_assertions" in features
        assert "test_complex" in features

        # Check that features are properly extracted
        simple_features = features["test_simple"]
        assert simple_features.test_name == "test_simple"
        assert simple_features.file_path == test_file
        assert simple_features.assertion_count >= 1  # At least one assertion

        complex_features = features["test_complex"]
        assert complex_features.complexity_score > 1  # Should have higher complexity

    def test_bis_calculation_with_file(self, tmp_path: Path) -> None:
        """Test BIS calculation with a real test file."""
        # Create a test file
        test_file = tmp_path / "test_bis.py"
        test_content = '''
def test_good():
    """A good test."""
    result = public_function()
    assert result == expected_value

def test_bad():
    """A bad test with private access."""
    obj = SomeClass()
    assert obj._private_method() == expected_value
'''
        test_file.write_text(test_content)

        calculator = BISCalculator()

        # Create findings for the bad test
        findings = [
            Finding(
                code="DS301",
                name="private_access",
                message="Private access detected",
                file_path=test_file,
                line_number=8,
                severity=Severity.WARNING,
            )
        ]

        results = calculator.calculate_file_bis(test_file, findings)

        # Should have results for both tests
        assert len(results) >= 2
        assert "test_good" in results
        assert "test_bad" in results

        # Good test should have higher score
        good_result = results["test_good"]
        bad_result = results["test_bad"]
        assert good_result.bis_score >= bad_result.bis_score
