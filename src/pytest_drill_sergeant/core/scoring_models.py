"""Scoring system models for BIS and BRS calculation."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from pytest_drill_sergeant.core.models import Severity

# Grade threshold constants
GRADE_A_THRESHOLD = 90
GRADE_B_THRESHOLD = 80
GRADE_C_THRESHOLD = 70
GRADE_D_THRESHOLD = 60


class BISComponent(BaseModel):
    """Individual component of the Behavior Integrity Score."""

    name: str = Field(..., description="Name of the BIS component")
    weight: float = Field(
        0.0, ge=0.0, le=1.0, description="Weight of this component in BIS calculation"
    )
    score: float = Field(
        0.0, ge=0.0, le=100.0, description="Score for this component (0-100)"
    )
    max_score: float = Field(
        100.0, description="Maximum possible score for this component"
    )
    penalty: float = Field(0.0, ge=0.0, description="Penalty applied to this component")
    reward: float = Field(0.0, ge=0.0, description="Reward applied to this component")

    # Component-specific data
    findings_count: int = Field(
        0, description="Number of findings affecting this component"
    )
    findings_by_severity: dict[Severity, int] = Field(
        default_factory=dict, description="Findings by severity"
    )
    details: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Component-specific details"
    )

    model_config = ConfigDict(
        use_enum_values=True,
    )

    @property
    def weighted_score(self) -> float:
        """Calculate the weighted score for this component."""
        return self.score * self.weight

    @property
    def final_score(self) -> float:
        """Calculate the final score after penalties and rewards."""
        return max(0.0, min(100.0, self.score - self.penalty + self.reward))


class BISCalculation(BaseModel):
    """Complete BIS calculation for a test."""

    test_name: str = Field(..., description="Name of the test")
    file_path: str = Field(..., description="Path to the test file")

    # Component scores
    components: dict[str, BISComponent] = Field(
        default_factory=dict, description="BIS components"
    )

    # Overall scores
    raw_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Raw BIS score before adjustments"
    )
    final_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Final BIS score after adjustments"
    )
    grade: str = Field("F", description="BIS grade (A-F)")

    # Calculation metadata
    calculation_time: float = Field(0.0, description="Time taken to calculate BIS")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this calculation was created"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def add_component(self, name: str, component: BISComponent) -> None:
        """Add a component to the BIS calculation."""
        self.components[name] = component
        self._recalculate_scores()

    def _recalculate_scores(self) -> None:
        """Recalculate overall scores based on components."""
        if not self.components:
            self.raw_score = 0.0
            self.final_score = 0.0
            self.grade = "F"
            return

        # Calculate weighted average
        total_weight = sum(comp.weight for comp in self.components.values())
        if total_weight > 0:
            self.raw_score = (
                sum(comp.weighted_score for comp in self.components.values())
                / total_weight
            )
        else:
            self.raw_score = 0.0

        # Apply final adjustments
        self.final_score = max(0.0, min(100.0, self.raw_score))
        self.grade = self._score_to_grade(self.final_score)

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= GRADE_A_THRESHOLD:
            return "A"
        if score >= GRADE_B_THRESHOLD:
            return "B"
        if score >= GRADE_C_THRESHOLD:
            return "C"
        if score >= GRADE_D_THRESHOLD:
            return "D"
        return "F"


class BRSComponent(BaseModel):
    """Individual component of the Battlefield Readiness Score."""

    name: str = Field(..., description="Name of the BRS component")
    weight: float = Field(
        0.0, ge=0.0, le=1.0, description="Weight of this component in BRS calculation"
    )
    score: float = Field(
        0.0, ge=0.0, le=100.0, description="Score for this component (0-100)"
    )
    max_score: float = Field(
        100.0, description="Maximum possible score for this component"
    )

    # Component metrics
    total_tests: int = Field(0, description="Total number of tests")
    compliant_tests: int = Field(0, description="Number of compliant tests")
    non_compliant_tests: int = Field(0, description="Number of non-compliant tests")
    compliance_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="Compliance rate percentage"
    )

    # Component-specific data
    details: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Component-specific details"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )

    @property
    def weighted_score(self) -> float:
        """Calculate the weighted score for this component."""
        return self.score * self.weight


class BRSCalculation(BaseModel):
    """Complete BRS calculation for a test suite."""

    # Suite information
    suite_name: str = Field(..., description="Name of the test suite")
    total_tests: int = Field(0, description="Total number of tests in the suite")

    # Component scores
    components: dict[str, BRSComponent] = Field(
        default_factory=dict, description="BRS components"
    )

    # Overall scores
    raw_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Raw BRS score before adjustments"
    )
    final_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Final BRS score after adjustments"
    )
    grade: str = Field("F", description="BRS grade (A-F)")

    # Quality gates
    passes_quality_gate: bool = Field(
        False, description="Whether the suite passes quality gates"
    )
    quality_gate_threshold: float = Field(
        60.0, ge=0.0, le=100.0, description="Quality gate threshold"
    )

    # Calculation metadata
    calculation_time: float = Field(0.0, description="Time taken to calculate BRS")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this calculation was created"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )

    def add_component(self, name: str, component: BRSComponent) -> None:
        """Add a component to the BRS calculation."""
        self.components[name] = component
        self._recalculate_scores()

    def _recalculate_scores(self) -> None:
        """Recalculate overall scores based on components."""
        if not self.components:
            self.raw_score = 0.0
            self.final_score = 0.0
            self.grade = "F"
            self.passes_quality_gate = False
            return

        # Calculate weighted average
        total_weight = sum(comp.weight for comp in self.components.values())
        if total_weight > 0:
            self.raw_score = (
                sum(comp.weighted_score for comp in self.components.values())
                / total_weight
            )
        else:
            self.raw_score = 0.0

        # Apply final adjustments
        self.final_score = max(0.0, min(100.0, self.raw_score))
        self.grade = self._score_to_grade(self.final_score)
        self.passes_quality_gate = self.final_score >= self.quality_gate_threshold

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= GRADE_A_THRESHOLD:
            return "A"
        if score >= GRADE_B_THRESHOLD:
            return "B"
        if score >= GRADE_C_THRESHOLD:
            return "C"
        if score >= GRADE_D_THRESHOLD:
            return "D"
        return "F"


class QualityTrend(BaseModel):
    """Quality trend over time."""

    metric_name: str = Field(..., description="Name of the metric being tracked")
    values: list[float] = Field(
        default_factory=list, description="Metric values over time"
    )
    timestamps: list[datetime] = Field(
        default_factory=list, description="Timestamps for each value"
    )

    # Trend analysis
    trend_direction: str = Field(
        "stable", description="Trend direction: improving, declining, stable"
    )
    trend_slope: float = Field(0.0, description="Slope of the trend line")
    trend_confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence in the trend"
    )

    # Statistics
    current_value: float = Field(0.0, description="Current value")
    average_value: float = Field(0.0, description="Average value over time")
    min_value: float = Field(0.0, description="Minimum value")
    max_value: float = Field(0.0, description="Maximum value")
    standard_deviation: float = Field(0.0, description="Standard deviation")

    model_config = ConfigDict(
        validate_assignment=True,
    )


class QualityReport(BaseModel):
    """Comprehensive quality report."""

    # Report metadata
    report_id: str = Field(..., description="Unique identifier for this report")
    suite_name: str = Field(..., description="Name of the test suite")
    generated_at: datetime = Field(
        default_factory=datetime.now, description="When this report was generated"
    )

    # Overall metrics
    bis_scores: list[BISCalculation] = Field(
        default_factory=list, description="BIS scores for individual tests"
    )
    brs_calculation: BRSCalculation | None = Field(
        None, description="BRS calculation for the suite"
    )

    # Trends
    trends: dict[str, QualityTrend] = Field(
        default_factory=dict, description="Quality trends over time"
    )

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list, description="Quality improvement recommendations"
    )
    priority_actions: list[str] = Field(
        default_factory=list, description="High-priority actions to take"
    )

    # Report data
    raw_data: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Raw data used in the report"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )
