"""Comprehensive tests for scoring models module.

Tests focus on behavior (what) rather than implementation (how):
- Score calculations and aggregations
- Grade assignments and thresholds
- Component management and weighting
- Quality gates and compliance
- Trend analysis and statistics
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from pytest_drill_sergeant.core.scoring_models import (
    BISComponent,
    BISCalculation,
    BRSComponent,
    BRSCalculation,
    QualityTrend,
    QualityReport,
    GRADE_A_THRESHOLD,
    GRADE_B_THRESHOLD,
    GRADE_C_THRESHOLD,
    GRADE_D_THRESHOLD,
)
from pytest_drill_sergeant.core.models import Severity


class TestBISComponent:
    """Test BIS component behavior and calculations."""

    def test_bis_component_creation_with_defaults(self):
        """Test BIS component creation with default values."""
        component = BISComponent(name="Test Component")
        
        assert component.name == "Test Component"
        assert component.weight == 0.0
        assert component.score == 0.0
        assert component.max_score == 100.0
        assert component.penalty == 0.0
        assert component.reward == 0.0
        assert component.findings_count == 0
        assert component.findings_by_severity == {}
        assert component.details == {}

    def test_bis_component_weighted_score_calculation(self):
        """Test weighted score calculation."""
        component = BISComponent(
            name="Test Component",
            weight=0.5,
            score=80.0
        )
        
        assert component.weighted_score == 40.0  # 80.0 * 0.5

    def test_bis_component_final_score_with_penalty(self):
        """Test final score calculation with penalty."""
        component = BISComponent(
            name="Test Component",
            score=80.0,
            penalty=10.0
        )
        
        assert component.final_score == 70.0  # 80.0 - 10.0

    def test_bis_component_final_score_with_reward(self):
        """Test final score calculation with reward."""
        component = BISComponent(
            name="Test Component",
            score=80.0,
            reward=15.0
        )
        
        assert component.final_score == 95.0  # 80.0 + 15.0

    def test_bis_component_final_score_with_penalty_and_reward(self):
        """Test final score calculation with both penalty and reward."""
        component = BISComponent(
            name="Test Component",
            score=80.0,
            penalty=10.0,
            reward=15.0
        )
        
        assert component.final_score == 85.0  # 80.0 - 10.0 + 15.0

    def test_bis_component_final_score_bounds_enforcement(self):
        """Test that final score is bounded between 0 and 100."""
        # Test lower bound
        component = BISComponent(
            name="Test Component",
            score=5.0,
            penalty=10.0
        )
        assert component.final_score == 0.0  # max(0.0, 5.0 - 10.0)
        
        # Test upper bound
        component = BISComponent(
            name="Test Component",
            score=95.0,
            reward=10.0
        )
        assert component.final_score == 100.0  # min(100.0, 95.0 + 10.0)

    def test_bis_component_findings_tracking(self):
        """Test findings tracking functionality."""
        component = BISComponent(
            name="Test Component",
            findings_count=5,
            findings_by_severity={
                Severity.ERROR: 2,
                Severity.WARNING: 2,
                Severity.INFO: 1
            }
        )
        
        assert component.findings_count == 5
        assert component.findings_by_severity[Severity.ERROR] == 2
        assert component.findings_by_severity[Severity.WARNING] == 2
        assert component.findings_by_severity[Severity.INFO] == 1

    def test_bis_component_details_storage(self):
        """Test component details storage."""
        component = BISComponent(
            name="Test Component",
            details={
                "coverage": 85.5,
                "complexity": 12,
                "has_docs": True,
                "status": "active"
            }
        )
        
        assert component.details["coverage"] == 85.5
        assert component.details["complexity"] == 12
        assert component.details["has_docs"] is True
        assert component.details["status"] == "active"


class TestBISCalculation:
    """Test BIS calculation behavior and score aggregation."""

    def test_bis_calculation_creation(self):
        """Test BIS calculation creation."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        assert calc.test_name == "test_example"
        assert calc.file_path == "/path/to/test_example.py"
        assert calc.components == {}
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"
        assert calc.calculation_time == 0.0
        assert isinstance(calc.created_at, datetime)

    def test_bis_calculation_empty_components(self):
        """Test BIS calculation with no components."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        # Should remain at default values
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"
        
        # Test that _recalculate_scores handles empty components
        calc._recalculate_scores()
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"

    def test_bis_calculation_add_component(self):
        """Test adding components to BIS calculation."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        component = BISComponent(
            name="Coverage",
            weight=0.4,
            score=80.0
        )
        
        calc.add_component("coverage", component)
        
        assert "coverage" in calc.components
        assert calc.components["coverage"] == component
        assert calc.raw_score == 80.0  # Only one component
        assert calc.final_score == 80.0
        assert calc.grade == "B"  # 80 >= GRADE_B_THRESHOLD

    def test_bis_calculation_weighted_average(self):
        """Test weighted average calculation with multiple components."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        # Add components with different weights
        calc.add_component("coverage", BISComponent(
            name="Coverage",
            weight=0.4,
            score=80.0
        ))
        
        calc.add_component("complexity", BISComponent(
            name="Complexity",
            weight=0.3,
            score=70.0
        ))
        
        calc.add_component("documentation", BISComponent(
            name="Documentation",
            weight=0.3,
            score=90.0
        ))
        
        # Expected: (80*0.4 + 70*0.3 + 90*0.3) / (0.4 + 0.3 + 0.3) = 80.0
        assert calc.raw_score == 80.0
        assert calc.final_score == 80.0
        assert calc.grade == "B"

    def test_bis_calculation_zero_weight_components(self):
        """Test BIS calculation with components having zero weight."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        calc.add_component("zero_weight", BISComponent(
            name="Zero Weight",
            weight=0.0,
            score=100.0
        ))
        
        # Should default to 0.0 when total weight is 0
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"

    def test_bis_calculation_grade_assignment(self):
        """Test grade assignment based on score thresholds."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        # Test grade A
        calc.add_component("test", BISComponent(
            name="Test",
            weight=1.0,
            score=95.0
        ))
        assert calc.grade == "A"
        
        # Test grade B
        calc.add_component("test", BISComponent(
            name="Test",
            weight=1.0,
            score=85.0
        ))
        assert calc.grade == "B"
        
        # Test grade C
        calc.add_component("test", BISComponent(
            name="Test",
            weight=1.0,
            score=75.0
        ))
        assert calc.grade == "C"
        
        # Test grade D
        calc.add_component("test", BISComponent(
            name="Test",
            weight=1.0,
            score=65.0
        ))
        assert calc.grade == "D"
        
        # Test grade F
        calc.add_component("test", BISComponent(
            name="Test",
            weight=1.0,
            score=55.0
        ))
        assert calc.grade == "F"

    def test_bis_calculation_boundary_scores(self):
        """Test grade assignment at exact threshold boundaries."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        # Test exact thresholds
        thresholds = [
            (GRADE_A_THRESHOLD, "A"),
            (GRADE_B_THRESHOLD, "B"),
            (GRADE_C_THRESHOLD, "C"),
            (GRADE_D_THRESHOLD, "D"),
            (GRADE_D_THRESHOLD - 0.1, "F"),
        ]
        
        for score, expected_grade in thresholds:
            calc.add_component("test", BISComponent(
                name="Test",
                weight=1.0,
                score=score
            ))
            assert calc.grade == expected_grade, f"Score {score} should be grade {expected_grade}"

    def test_bis_calculation_metadata_tracking(self):
        """Test calculation metadata tracking."""
        calc = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py",
            calculation_time=1.5
        )
        
        assert calc.calculation_time == 1.5
        assert isinstance(calc.created_at, datetime)
        assert calc.created_at <= datetime.now()


class TestBRSComponent:
    """Test BRS component behavior and compliance calculations."""

    def test_brs_component_creation_with_defaults(self):
        """Test BRS component creation with default values."""
        component = BRSComponent(name="Test Component")
        
        assert component.name == "Test Component"
        assert component.weight == 0.0
        assert component.score == 0.0
        assert component.max_score == 100.0
        assert component.total_tests == 0
        assert component.compliant_tests == 0
        assert component.non_compliant_tests == 0
        assert component.compliance_rate == 0.0
        assert component.details == {}

    def test_brs_component_weighted_score_calculation(self):
        """Test weighted score calculation."""
        component = BRSComponent(
            name="Test Component",
            weight=0.6,
            score=75.0
        )
        
        assert component.weighted_score == 45.0  # 75.0 * 0.6

    def test_brs_component_compliance_tracking(self):
        """Test compliance tracking functionality."""
        component = BRSComponent(
            name="Test Component",
            total_tests=100,
            compliant_tests=85,
            non_compliant_tests=15,
            compliance_rate=85.0
        )
        
        assert component.total_tests == 100
        assert component.compliant_tests == 85
        assert component.non_compliant_tests == 15
        assert component.compliance_rate == 85.0

    def test_brs_component_details_storage(self):
        """Test component details storage."""
        component = BRSComponent(
            name="Test Component",
            details={
                "avg_execution_time": 2.5,
                "memory_usage": 1024,
                "has_cleanup": True,
                "category": "integration"
            }
        )
        
        assert component.details["avg_execution_time"] == 2.5
        assert component.details["memory_usage"] == 1024
        assert component.details["has_cleanup"] is True
        assert component.details["category"] == "integration"


class TestBRSCalculation:
    """Test BRS calculation behavior and quality gates."""

    def test_brs_calculation_creation(self):
        """Test BRS calculation creation."""
        calc = BRSCalculation(suite_name="test_suite")
        
        assert calc.suite_name == "test_suite"
        assert calc.total_tests == 0
        assert calc.components == {}
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"
        assert calc.passes_quality_gate is False
        assert calc.quality_gate_threshold == 60.0
        assert calc.calculation_time == 0.0
        assert isinstance(calc.created_at, datetime)

    def test_brs_calculation_empty_components(self):
        """Test BRS calculation with no components."""
        calc = BRSCalculation(suite_name="test_suite")
        
        # Should remain at default values
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"
        assert calc.passes_quality_gate is False
        
        # Test that _recalculate_scores handles empty components
        calc._recalculate_scores()
        assert calc.raw_score == 0.0
        assert calc.final_score == 0.0
        assert calc.grade == "F"
        assert calc.passes_quality_gate is False

    def test_brs_calculation_add_component(self):
        """Test adding components to BRS calculation."""
        calc = BRSCalculation(suite_name="test_suite")
        
        component = BRSComponent(
            name="Test Quality",
            weight=0.5,
            score=80.0
        )
        
        calc.add_component("test_quality", component)
        
        assert "test_quality" in calc.components
        assert calc.components["test_quality"] == component
        assert calc.raw_score == 80.0
        assert calc.final_score == 80.0
        assert calc.grade == "B"
        assert calc.passes_quality_gate is True  # 80.0 >= 60.0

    def test_brs_calculation_quality_gate_passing(self):
        """Test quality gate passing behavior."""
        calc = BRSCalculation(
            suite_name="test_suite",
            quality_gate_threshold=70.0
        )
        
        # Score above threshold
        calc.add_component("test", BRSComponent(
            name="Test",
            weight=1.0,
            score=75.0
        ))
        assert calc.passes_quality_gate is True
        
        # Score below threshold
        calc.add_component("test", BRSComponent(
            name="Test",
            weight=1.0,
            score=65.0
        ))
        assert calc.passes_quality_gate is False

    def test_brs_calculation_quality_gate_boundary(self):
        """Test quality gate at exact threshold."""
        calc = BRSCalculation(
            suite_name="test_suite",
            quality_gate_threshold=60.0
        )
        
        # Score at exact threshold
        calc.add_component("test", BRSComponent(
            name="Test",
            weight=1.0,
            score=60.0
        ))
        assert calc.passes_quality_gate is True

    def test_brs_calculation_weighted_average(self):
        """Test weighted average calculation with multiple components."""
        calc = BRSCalculation(suite_name="test_suite")
        
        # Add components with different weights
        calc.add_component("performance", BRSComponent(
            name="Performance",
            weight=0.4,
            score=85.0
        ))
        
        calc.add_component("reliability", BRSComponent(
            name="Reliability",
            weight=0.3,
            score=75.0
        ))
        
        calc.add_component("maintainability", BRSComponent(
            name="Maintainability",
            weight=0.3,
            score=95.0
        ))
        
        # Expected: (85*0.4 + 75*0.3 + 95*0.3) / (0.4 + 0.3 + 0.3) = 85.0
        assert calc.raw_score == 85.0
        assert calc.final_score == 85.0
        assert calc.grade == "B"
        assert calc.passes_quality_gate is True

    def test_brs_calculation_grade_assignment(self):
        """Test grade assignment based on score thresholds."""
        calc = BRSCalculation(suite_name="test_suite")
        
        # Test all grades
        test_cases = [
            (95.0, "A"),
            (85.0, "B"),
            (75.0, "C"),
            (65.0, "D"),
            (55.0, "F"),
        ]
        
        for score, expected_grade in test_cases:
            calc.add_component("test", BRSComponent(
                name="Test",
                weight=1.0,
                score=score
            ))
            assert calc.grade == expected_grade, f"Score {score} should be grade {expected_grade}"

    def test_brs_calculation_suite_metrics(self):
        """Test suite-level metrics tracking."""
        calc = BRSCalculation(
            suite_name="integration_tests",
            total_tests=150
        )
        
        assert calc.suite_name == "integration_tests"
        assert calc.total_tests == 150


class TestQualityTrend:
    """Test quality trend analysis and statistics."""

    def test_quality_trend_creation(self):
        """Test quality trend creation."""
        trend = QualityTrend(metric_name="test_coverage")
        
        assert trend.metric_name == "test_coverage"
        assert trend.values == []
        assert trend.timestamps == []
        assert trend.trend_direction == "stable"
        assert trend.trend_slope == 0.0
        assert trend.trend_confidence == 0.0
        assert trend.current_value == 0.0
        assert trend.average_value == 0.0
        assert trend.min_value == 0.0
        assert trend.max_value == 0.0
        assert trend.standard_deviation == 0.0

    def test_quality_trend_with_data(self):
        """Test quality trend with sample data."""
        now = datetime.now()
        timestamps = [now, now, now]
        values = [80.0, 85.0, 90.0]
        
        trend = QualityTrend(
            metric_name="test_coverage",
            values=values,
            timestamps=timestamps,
            trend_direction="improving",
            trend_slope=5.0,
            trend_confidence=0.8,
            current_value=90.0,
            average_value=85.0,
            min_value=80.0,
            max_value=90.0,
            standard_deviation=4.08
        )
        
        assert trend.metric_name == "test_coverage"
        assert trend.values == values
        assert trend.timestamps == timestamps
        assert trend.trend_direction == "improving"
        assert trend.trend_slope == 5.0
        assert trend.trend_confidence == 0.8
        assert trend.current_value == 90.0
        assert trend.average_value == 85.0
        assert trend.min_value == 80.0
        assert trend.max_value == 90.0
        assert trend.standard_deviation == 4.08

    def test_quality_trend_directions(self):
        """Test different trend directions."""
        directions = ["improving", "declining", "stable"]
        
        for direction in directions:
            trend = QualityTrend(
                metric_name="test_metric",
                trend_direction=direction
            )
            assert trend.trend_direction == direction


class TestQualityReport:
    """Test quality report aggregation and metadata."""

    def test_quality_report_creation(self):
        """Test quality report creation."""
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite"
        )
        
        assert report.report_id == "report_001"
        assert report.suite_name == "test_suite"
        assert report.bis_scores == []
        assert report.brs_calculation is None
        assert report.trends == {}
        assert report.recommendations == []
        assert report.priority_actions == []
        assert report.raw_data == {}
        assert isinstance(report.generated_at, datetime)

    def test_quality_report_with_bis_scores(self):
        """Test quality report with BIS scores."""
        bis_score = BISCalculation(
            test_name="test_example",
            file_path="/path/to/test_example.py"
        )
        
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite",
            bis_scores=[bis_score]
        )
        
        assert len(report.bis_scores) == 1
        assert report.bis_scores[0] == bis_score

    def test_quality_report_with_brs_calculation(self):
        """Test quality report with BRS calculation."""
        brs_calc = BRSCalculation(suite_name="test_suite")
        
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite",
            brs_calculation=brs_calc
        )
        
        assert report.brs_calculation == brs_calc

    def test_quality_report_with_trends(self):
        """Test quality report with trends."""
        trend = QualityTrend(metric_name="coverage")
        
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite",
            trends={"coverage": trend}
        )
        
        assert "coverage" in report.trends
        assert report.trends["coverage"] == trend

    def test_quality_report_with_recommendations(self):
        """Test quality report with recommendations."""
        recommendations = [
            "Increase test coverage to 90%",
            "Add integration tests for API endpoints",
            "Implement performance benchmarks"
        ]
        
        priority_actions = [
            "Fix critical security vulnerabilities",
            "Update deprecated dependencies"
        ]
        
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite",
            recommendations=recommendations,
            priority_actions=priority_actions
        )
        
        assert report.recommendations == recommendations
        assert report.priority_actions == priority_actions

    def test_quality_report_with_raw_data(self):
        """Test quality report with raw data."""
        raw_data = {
            "total_lines": 15000,
            "covered_lines": 12000,
            "execution_time": 45.5,
            "memory_peak": 1024,
            "has_warnings": True
        }
        
        report = QualityReport(
            report_id="report_001",
            suite_name="test_suite",
            raw_data=raw_data
        )
        
        assert report.raw_data == raw_data


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    def test_complete_bis_workflow(self):
        """Test complete BIS calculation workflow."""
        # Create BIS calculation
        calc = BISCalculation(
            test_name="test_user_authentication",
            file_path="/tests/test_auth.py",
            calculation_time=2.5
        )
        
        # Add multiple components
        calc.add_component("coverage", BISComponent(
            name="Test Coverage",
            weight=0.4,
            score=85.0,
            findings_count=3,
            findings_by_severity={Severity.WARNING: 2, Severity.INFO: 1},
            details={"lines_covered": 850, "total_lines": 1000}
        ))
        
        calc.add_component("complexity", BISComponent(
            name="Test Complexity",
            weight=0.3,
            score=75.0,
            penalty=5.0,
            details={"cyclomatic_complexity": 8, "max_recommended": 10}
        ))
        
        calc.add_component("documentation", BISComponent(
            name="Test Documentation",
            weight=0.3,
            score=95.0,
            reward=5.0,
            details={"docstring_coverage": 95, "examples_count": 12}
        ))
        
        # Verify final calculation
        assert calc.raw_score == 85.0  # Weighted average: (85*0.4 + 75*0.3 + 95*0.3) / 1.0 = 85.0
        assert calc.final_score == 85.0  # No additional adjustments
        assert calc.grade == "B"
        assert len(calc.components) == 3
        assert calc.calculation_time == 2.5

    def test_complete_brs_workflow(self):
        """Test complete BRS calculation workflow."""
        # Create BRS calculation
        calc = BRSCalculation(
            suite_name="integration_test_suite",
            total_tests=200,
            quality_gate_threshold=75.0,
            calculation_time=5.2
        )
        
        # Add multiple components
        calc.add_component("performance", BRSComponent(
            name="Performance Tests",
            weight=0.4,
            score=80.0,
            total_tests=50,
            compliant_tests=45,
            non_compliant_tests=5,
            compliance_rate=90.0,
            details={"avg_response_time": 150, "max_response_time": 500}
        ))
        
        calc.add_component("reliability", BRSComponent(
            name="Reliability Tests",
            weight=0.3,
            score=85.0,
            total_tests=75,
            compliant_tests=70,
            non_compliant_tests=5,
            compliance_rate=93.3,
            details={"failure_rate": 0.067, "retry_count": 2}
        ))
        
        calc.add_component("security", BRSComponent(
            name="Security Tests",
            weight=0.3,
            score=70.0,
            total_tests=75,
            compliant_tests=60,
            non_compliant_tests=15,
            compliance_rate=80.0,
            details={"vulnerabilities_found": 3, "severity_high": 1}
        ))
        
        # Verify final calculation
        assert calc.raw_score == 78.5  # Weighted average
        assert calc.final_score == 78.5
        assert calc.grade == "C"
        assert calc.passes_quality_gate is True  # 78.5 >= 75.0
        assert calc.total_tests == 200
        assert calc.calculation_time == 5.2

    def test_quality_report_integration(self):
        """Test complete quality report integration."""
        # Create BIS scores
        bis_scores = [
            BISCalculation(test_name="test_auth", file_path="/tests/test_auth.py"),
            BISCalculation(test_name="test_api", file_path="/tests/test_api.py"),
        ]
        
        # Create BRS calculation
        brs_calc = BRSCalculation(suite_name="test_suite")
        brs_calc.add_component("overall", BRSComponent(
            name="Overall Quality",
            weight=1.0,
            score=85.0
        ))
        
        # Create trends
        trends = {
            "coverage": QualityTrend(
                metric_name="coverage",
                trend_direction="improving",
                current_value=85.0
            ),
            "performance": QualityTrend(
                metric_name="performance",
                trend_direction="stable",
                current_value=90.0
            )
        }
        
        # Create report
        report = QualityReport(
            report_id="report_2024_001",
            suite_name="integration_suite",
            bis_scores=bis_scores,
            brs_calculation=brs_calc,
            trends=trends,
            recommendations=["Improve test coverage", "Add performance benchmarks"],
            priority_actions=["Fix critical security issues"],
            raw_data={"total_tests": 150, "execution_time": 120.5}
        )
        
        # Verify report
        assert report.report_id == "report_2024_001"
        assert report.suite_name == "integration_suite"
        assert len(report.bis_scores) == 2
        assert report.brs_calculation == brs_calc
        assert len(report.trends) == 2
        assert len(report.recommendations) == 2
        assert len(report.priority_actions) == 1
        assert report.raw_data["total_tests"] == 150


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_zero_scores_and_weights(self):
        """Test behavior with zero scores and weights."""
        # BIS with zero weight
        bis_calc = BISCalculation(test_name="test", file_path="/test.py")
        bis_calc.add_component("zero", BISComponent(
            name="Zero Weight",
            weight=0.0,
            score=100.0
        ))
        assert bis_calc.raw_score == 0.0
        assert bis_calc.grade == "F"
        
        # BRS with zero weight
        brs_calc = BRSCalculation(suite_name="suite")
        brs_calc.add_component("zero", BRSComponent(
            name="Zero Weight",
            weight=0.0,
            score=100.0
        ))
        assert brs_calc.raw_score == 0.0
        assert brs_calc.grade == "F"
        assert brs_calc.passes_quality_gate is False

    def test_maximum_scores(self):
        """Test behavior with maximum scores."""
        bis_calc = BISCalculation(test_name="test", file_path="/test.py")
        bis_calc.add_component("max", BISComponent(
            name="Max Score",
            weight=1.0,
            score=100.0
        ))
        assert bis_calc.raw_score == 100.0
        assert bis_calc.grade == "A"
        
        brs_calc = BRSCalculation(suite_name="suite")
        brs_calc.add_component("max", BRSComponent(
            name="Max Score",
            weight=1.0,
            score=100.0
        ))
        assert brs_calc.raw_score == 100.0
        assert brs_calc.grade == "A"
        assert brs_calc.passes_quality_gate is True

    def test_negative_adjustments(self):
        """Test behavior with penalties exceeding scores."""
        component = BISComponent(
            name="High Penalty",
            score=10.0,
            penalty=20.0
        )
        assert component.final_score == 0.0  # Bounded at 0
        
        component = BISComponent(
            name="High Penalty",
            score=50.0,
            penalty=60.0
        )
        assert component.final_score == 0.0  # Bounded at 0

    def test_large_rewards(self):
        """Test behavior with large rewards."""
        component = BISComponent(
            name="High Reward",
            score=90.0,
            reward=20.0
        )
        assert component.final_score == 100.0  # Bounded at 100
        
        component = BISComponent(
            name="High Reward",
            score=50.0,
            reward=60.0
        )
        assert component.final_score == 100.0  # Bounded at 100

    def test_empty_component_names(self):
        """Test behavior with empty component names."""
        component = BISComponent(name="")
        assert component.name == ""
        
        component = BRSComponent(name="")
        assert component.name == ""

    def test_extreme_compliance_rates(self):
        """Test extreme compliance rates."""
        component = BRSComponent(
            name="Perfect Compliance",
            compliance_rate=100.0
        )
        assert component.compliance_rate == 100.0
        
        component = BRSComponent(
            name="No Compliance",
            compliance_rate=0.0
        )
        assert component.compliance_rate == 0.0

    def test_trend_confidence_bounds(self):
        """Test trend confidence bounds."""
        trend = QualityTrend(
            metric_name="test",
            trend_confidence=0.0
        )
        assert trend.trend_confidence == 0.0
        
        trend = QualityTrend(
            metric_name="test",
            trend_confidence=1.0
        )
        assert trend.trend_confidence == 1.0

    def test_quality_gate_threshold_bounds(self):
        """Test quality gate threshold bounds."""
        calc = BRSCalculation(
            suite_name="suite",
            quality_gate_threshold=0.0
        )
        calc.add_component("test", BRSComponent(
            name="Test",
            weight=1.0,
            score=0.0
        ))
        assert calc.passes_quality_gate is True  # 0.0 >= 0.0
        
        calc = BRSCalculation(
            suite_name="suite",
            quality_gate_threshold=100.0
        )
        calc.add_component("test", BRSComponent(
            name="Test",
            weight=1.0,
            score=99.0
        ))
        assert calc.passes_quality_gate is False  # 99.0 < 100.0