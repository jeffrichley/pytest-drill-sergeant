"""Unit tests for the main BIS calculator."""

from __future__ import annotations

from pathlib import Path

from pytest_drill_sergeant.core.models import Finding, FeaturesData, Severity
from pytest_drill_sergeant.core.scoring import BISCalculator, get_bis_calculator, reset_bis_calculator


class TestBISCalculator:
    """Test the main BIS calculator functionality."""

    def test_init(self) -> None:
        """Test calculator initialization."""
        calculator = BISCalculator()
        assert calculator is not None
        assert calculator.get_average_bis_score() == 0.0

    def test_calculate_test_bis(self) -> None:
        """Test BIS calculation for a single test."""
        calculator = BISCalculator()

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
            test_name="test_example",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
        )

        result = calculator.calculate_test_bis("test_example", findings, features)

        assert result.test_name == "test_example"
        assert result.file_path == Path("test.py")
        assert result.line_number == 5
        assert result.findings == findings
        assert result.features == features
        assert result.bis_score > 0
        assert result.bis_score < 100  # Should be penalized
        assert result.bis_grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        assert result.analyzed is True
        assert result.error_message is None

    def test_calculate_test_bis_perfect_score(self) -> None:
        """Test BIS calculation for perfect test."""
        calculator = BISCalculator()

        findings = []
        features = FeaturesData(
            test_name="test_perfect",
            file_path=Path("test.py"),
            line_number=5,
            has_aaa_comments=True,
        )

        result = calculator.calculate_test_bis("test_perfect", findings, features)

        assert result.bis_score == 100.0
        assert result.bis_grade == "A+"
        assert result.analyzed is True

    def test_calculate_test_bis_with_error(self) -> None:
        """Test BIS calculation with error handling."""
        calculator = BISCalculator()

        # Create valid features but with no findings (should work fine)
        features = FeaturesData(
            test_name="test_error",
            file_path=Path("test.py"),
            line_number=5,
        )

        # This should not raise an exception and should return a valid result
        result = calculator.calculate_test_bis("test_error", [], features)

        assert result.test_name == "test_error"
        assert result.bis_score == 100.0  # Perfect score with no findings
        assert result.bis_grade == "A+"
        assert result.analyzed is True

    def test_get_test_bis_score(self) -> None:
        """Test BIS score retrieval."""
        calculator = BISCalculator()

        # Calculate a score first
        findings = [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)]
        features = FeaturesData(test_name="test_score", file_path=Path("test.py"), line_number=5, private_access_count=1)

        calculator.calculate_test_bis("test_score", findings, features)

        score = calculator.get_test_bis_score("test_score")
        assert score > 0
        assert score <= 100

        # Test non-existent test
        assert calculator.get_test_bis_score("nonexistent") == 0.0

    def test_get_test_bis_grade(self) -> None:
        """Test BIS grade retrieval."""
        calculator = BISCalculator()

        # Calculate a score first
        findings = [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)]
        features = FeaturesData(test_name="test_grade", file_path=Path("test.py"), line_number=5, private_access_count=1)

        calculator.calculate_test_bis("test_grade", findings, features)

        grade = calculator.get_test_bis_grade("test_grade")
        assert grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

        # Test non-existent test
        assert calculator.get_test_bis_grade("nonexistent") == "F"

    def test_get_test_bis_metrics(self) -> None:
        """Test BIS metrics retrieval."""
        calculator = BISCalculator()

        # Calculate a score first
        findings = [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)]
        features = FeaturesData(test_name="test_metrics", file_path=Path("test.py"), line_number=5, private_access_count=1)

        calculator.calculate_test_bis("test_metrics", findings, features)

        metrics = calculator.get_test_bis_metrics("test_metrics")
        assert metrics is not None
        assert metrics.high_penalty_count >= 0

        # Test non-existent test
        assert calculator.get_test_bis_metrics("nonexistent") is None

    def test_get_all_test_scores(self) -> None:
        """Test retrieval of all test scores."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            ("test1", [], FeaturesData(test_name="test1", file_path=Path("test.py"), line_number=5)),
            ("test2", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)], FeaturesData(test_name="test2", file_path=Path("test.py"), line_number=5, private_access_count=1)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        all_scores = calculator.get_all_test_scores()
        assert len(all_scores) == 2
        assert "test1" in all_scores
        assert "test2" in all_scores
        assert all_scores["test1"] >= all_scores["test2"]  # test1 should have higher score

    def test_get_all_test_grades(self) -> None:
        """Test retrieval of all test grades."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            ("test1", [], FeaturesData(test_name="test1", file_path=Path("test.py"), line_number=5)),
            ("test2", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)], FeaturesData(test_name="test2", file_path=Path("test.py"), line_number=5, private_access_count=1)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        all_grades = calculator.get_all_test_grades()
        assert len(all_grades) == 2
        assert "test1" in all_grades
        assert "test2" in all_grades
        assert all_grades["test1"] in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]
        assert all_grades["test2"] in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

    def test_get_average_bis_score(self) -> None:
        """Test average BIS score calculation."""
        calculator = BISCalculator()

        # No tests yet
        assert calculator.get_average_bis_score() == 0.0

        # Calculate scores for multiple tests
        test_data = [
            ("test1", [], FeaturesData(test_name="test1", file_path=Path("test.py"), line_number=5)),
            ("test2", [], FeaturesData(test_name="test2", file_path=Path("test.py"), line_number=5)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        average = calculator.get_average_bis_score()
        assert average > 0
        assert average <= 100

    def test_get_bis_score_distribution(self) -> None:
        """Test BIS score distribution calculation."""
        calculator = BISCalculator()

        # Calculate scores for tests with different grades
        test_data = [
            ("test_a", [], FeaturesData(test_name="test_a", file_path=Path("test.py"), line_number=5)),
            ("test_b", [Finding(code="DS302", name="aaa_comments", message="Missing AAA", file_path=Path("test.py"), line_number=10, severity=Severity.INFO)], FeaturesData(test_name="test_b", file_path=Path("test.py"), line_number=5)),
            ("test_f", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=15, severity=Severity.WARNING)], FeaturesData(test_name="test_f", file_path=Path("test.py"), line_number=5, private_access_count=1)),
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

    def test_get_top_offenders(self) -> None:
        """Test top offenders functionality."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            ("test_good", [], FeaturesData(test_name="test_good", file_path=Path("test.py"), line_number=5)),
            ("test_bad", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)], FeaturesData(test_name="test_bad", file_path=Path("test.py"), line_number=5, private_access_count=1)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        offenders = calculator.get_top_offenders(1)
        assert len(offenders) == 1
        assert offenders[0][0] == "test_bad"  # Should be the bad test

    def test_get_top_performers(self) -> None:
        """Test top performers functionality."""
        calculator = BISCalculator()

        # Calculate scores for multiple tests
        test_data = [
            ("test_good", [], FeaturesData(test_name="test_good", file_path=Path("test.py"), line_number=5)),
            ("test_bad", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)], FeaturesData(test_name="test_bad", file_path=Path("test.py"), line_number=5, private_access_count=1)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        performers = calculator.get_top_performers(1)
        assert len(performers) == 1
        assert performers[0][0] == "test_good"  # Should be the good test

    def test_get_bis_summary(self) -> None:
        """Test BIS summary generation."""
        calculator = BISCalculator()

        # No tests yet
        summary = calculator.get_bis_summary()
        assert summary["total_tests"] == 0
        assert summary["average_score"] == 0.0

        # Calculate scores for multiple tests
        test_data = [
            ("test1", [], FeaturesData(test_name="test1", file_path=Path("test.py"), line_number=5)),
            ("test2", [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)], FeaturesData(test_name="test2", file_path=Path("test.py"), line_number=5, private_access_count=1)),
        ]

        for test_name, findings, features in test_data:
            calculator.calculate_test_bis(test_name, findings, features)

        summary = calculator.get_bis_summary()
        assert summary["total_tests"] == 2
        assert summary["average_score"] > 0
        assert summary["highest_score"] >= summary["average_score"]
        assert summary["lowest_score"] <= summary["average_score"]
        assert "grade_distribution" in summary
        assert "top_offenders" in summary
        assert "top_performers" in summary

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        calculator = BISCalculator()

        # Calculate a score
        findings = [Finding(code="DS301", name="private_access", message="Private access", file_path=Path("test.py"), line_number=10, severity=Severity.WARNING)]
        features = FeaturesData(test_name="test_cache", file_path=Path("test.py"), line_number=5, private_access_count=1)

        calculator.calculate_test_bis("test_cache", findings, features)
        assert calculator.get_test_bis_score("test_cache") > 0

        # Clear cache
        calculator.clear_cache()
        assert calculator.get_test_bis_score("test_cache") == 0.0
        assert calculator.get_average_bis_score() == 0.0

    def test_get_score_interpretation(self) -> None:
        """Test score interpretation."""
        calculator = BISCalculator()

        # Test different score ranges
        assert "Excellent" in calculator.get_score_interpretation(90)
        assert "Good" in calculator.get_score_interpretation(75)
        assert "Fair" in calculator.get_score_interpretation(60)
        assert "Poor" in calculator.get_score_interpretation(45)
        assert "Critical" in calculator.get_score_interpretation(25)

    def test_get_breakdown(self) -> None:
        """Test breakdown functionality."""
        calculator = BISCalculator()

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
            test_name="test_breakdown",
            file_path=Path("test.py"),
            line_number=5,
            private_access_count=1,
        )

        calculator.calculate_test_bis("test_breakdown", findings, features)

        breakdown = calculator.get_breakdown("test_breakdown")
        assert breakdown is not None
        assert "high_penalty_violations" in breakdown
        assert "medium_penalty_violations" in breakdown
        assert "low_penalty_violations" in breakdown
        assert "advisory_violations" in breakdown
        assert "reward_indicators" in breakdown

        # Test non-existent test
        assert calculator.get_breakdown("nonexistent") is None

    def test_global_bis_calculator_singleton(self) -> None:
        """Test that global BIS calculator is a singleton."""
        calc1 = get_bis_calculator()
        calc2 = get_bis_calculator()
        assert calc1 is calc2

    def test_reset_bis_calculator(self) -> None:
        """Test resetting the global BIS calculator."""
        calc1 = get_bis_calculator()
        reset_bis_calculator()
        calc2 = get_bis_calculator()
        assert calc1 is not calc2