"""Core data models for pytest-drill-sergeant.

This module contains all the core data models used throughout the system,
implemented with Pydantic for validation and type safety.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path  # Pydantic needs Path at runtime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(str, Enum):
    """Severity levels for findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class RuleType(str, Enum):
    """Types of analysis rules."""

    PRIVATE_ACCESS = "private_access"
    MOCK_OVERSPECIFICATION = "mock_overspecification"
    STRUCTURAL_EQUALITY = "structural_equality"
    AAA_COMMENT = "aaa_comment"
    DUPLICATE_TEST = "duplicate_test"
    PARAMETRIZATION = "parametrization"
    FIXTURE_EXTRACTION = "fixture_extraction"


class Finding(BaseModel):
    """Represents a single quality finding in a test."""

    code: str = Field(..., description="Rule code (e.g., DS201)")
    name: str = Field(..., description="Rule name (e.g., duplicate_tests)")
    severity: Severity = Field(..., description="Severity level of the finding")
    message: str = Field(
        ..., description="Human-readable message describing the finding"
    )
    file_path: Path = Field(..., description="Path to the file containing the finding")
    line_number: int = Field(..., description="Line number where the finding occurs")
    column_number: int | None = Field(
        None, description="Column number where the finding occurs"
    )
    end_line_number: int | None = Field(
        None, description="End line number for multi-line findings"
    )
    code_snippet: str | None = Field(
        None, description="Code snippet around the finding"
    )
    suggestion: str | None = Field(None, description="Suggested fix for the finding")
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Confidence level (0-1) in the finding"
    )
    fingerprint: str | None = Field(
        None, description="Unique fingerprint for deduplication"
    )
    fixable: bool = Field(False, description="Whether this finding can be auto-fixed")
    tags: list[str] = Field(
        default_factory=list, description="Tags associated with this finding"
    )
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Additional metadata about the finding"
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate rule code format."""
        if not v.startswith("DS"):
            raise ValueError("Rule code must start with 'DS'")
        if len(v) != 5:
            raise ValueError("Rule code must be 5 characters (DS###)")
        try:
            int(v[2:])
        except ValueError:
            raise ValueError("Rule code must be DS followed by 3 digits")
        return v


class Cluster(BaseModel):
    """Represents a cluster of similar findings or tests."""

    cluster_id: str = Field(..., description="Unique identifier for the cluster")
    cluster_type: str = Field(
        ..., description="Type of cluster (e.g., 'duplicate_tests', 'similar_findings')"
    )
    findings: list[Finding] = Field(
        default_factory=list, description="Findings in this cluster"
    )
    similarity_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Similarity score within the cluster"
    )
    representative: Finding | None = Field(
        None, description="Representative finding for the cluster"
    )
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Additional cluster metadata"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class Rule(BaseModel):
    """Represents an analysis rule configuration."""

    rule_id: str = Field(..., description="Unique identifier for the rule")
    rule_type: RuleType = Field(..., description="Type of rule")
    name: str = Field(..., description="Human-readable name of the rule")
    description: str = Field(..., description="Description of what the rule detects")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    severity: Severity = Field(
        Severity.WARNING, description="Default severity for this rule"
    )
    threshold: float | None = Field(None, description="Threshold value for the rule")
    allowlist: list[str] = Field(
        default_factory=list, description="Allowlist patterns for this rule"
    )
    configuration: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Rule-specific configuration"
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )


class FeaturesData(BaseModel):
    """Features extracted from a test for analysis."""

    test_name: str = Field(..., description="Name of the test")
    file_path: Path = Field(..., description="Path to the test file")
    line_number: int = Field(..., description="Line number where the test starts")

    # AST-based features
    has_aaa_comments: bool = Field(False, description="Whether test has AAA comments")
    aaa_comment_order: str | None = Field(
        None, description="Order of AAA comments found"
    )
    private_access_count: int = Field(
        0, description="Number of private access violations"
    )
    mock_assertion_count: int = Field(0, description="Number of mock assertions")
    structural_equality_count: int = Field(
        0, description="Number of structural equality checks"
    )
    test_length: int = Field(0, description="Number of lines in the test")
    complexity_score: float = Field(
        0.0, description="Cyclomatic complexity of the test"
    )

    # Coverage-based features
    coverage_percentage: float = Field(
        0.0, ge=0.0, le=100.0, description="Test coverage percentage"
    )
    coverage_signature: str | None = Field(
        None, description="Coverage signature for similarity"
    )
    assertion_count: int = Field(0, description="Number of assertions in the test")
    setup_lines: int = Field(0, description="Number of setup/arrange lines")
    teardown_lines: int = Field(0, description="Number of teardown lines")

    # Runtime features
    execution_time: float = Field(0.0, description="Test execution time in seconds")
    memory_usage: float = Field(0.0, description="Memory usage in MB")
    exception_count: int = Field(0, description="Number of exceptions raised")

    # Metadata
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict, description="Additional test metadata"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class ResultData(BaseModel):
    """Result of analyzing a single test."""

    test_name: str = Field(..., description="Name of the test")
    file_path: Path = Field(..., description="Path to the test file")
    line_number: int = Field(..., description="Line number where the test starts")

    # Analysis results
    findings: list[Finding] = Field(
        default_factory=list, description="Findings in this test"
    )
    features: FeaturesData = Field(..., description="Features extracted from the test")
    bis_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Behavior Integrity Score"
    )
    bis_grade: str = Field("F", description="BIS grade (A-F)")

    # Status
    analyzed: bool = Field(
        False, description="Whether the test was successfully analyzed"
    )
    error_message: str | None = Field(
        None, description="Error message if analysis failed"
    )

    # Timing
    analysis_time: float = Field(0.0, description="Time taken to analyze this test")
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this result was created"
    )

    model_config = ConfigDict(
        validate_assignment=True,
    )


class RunMetrics(BaseModel):
    """Metrics for an entire test run."""

    # Test counts
    total_tests: int = Field(0, description="Total number of tests analyzed")
    analyzed_tests: int = Field(0, description="Number of tests successfully analyzed")
    failed_analyses: int = Field(0, description="Number of tests that failed analysis")

    # Finding counts
    total_findings: int = Field(0, description="Total number of findings")
    findings_by_severity: dict[Severity, int] = Field(
        default_factory=dict, description="Findings by severity"
    )
    findings_by_rule: dict[str, int] = Field(
        default_factory=dict, description="Findings by rule code"
    )

    # Quality scores
    average_bis: float = Field(0.0, ge=0.0, le=100.0, description="Average BIS score")
    brs_score: float = Field(
        0.0, ge=0.0, le=100.0, description="Battlefield Readiness Score"
    )
    brs_grade: str = Field("F", description="BRS grade (A-F)")

    # Component metrics
    aaa_compliance_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="AAA compliance rate"
    )
    duplicate_test_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="Duplicate test rate"
    )
    parametrization_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="Parametrization rate"
    )
    fixture_reuse_rate: float = Field(
        0.0, ge=0.0, le=100.0, description="Fixture reuse rate"
    )

    # Performance metrics
    total_analysis_time: float = Field(
        0.0, description="Total analysis time in seconds"
    )
    average_test_time: float = Field(0.0, description="Average test analysis time")
    memory_peak: float = Field(0.0, description="Peak memory usage in MB")

    # Timing
    created_at: datetime = Field(
        default_factory=datetime.now, description="When this run was created"
    )
    completed_at: datetime | None = Field(
        None, description="When this run was completed"
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )


class LegacyConfigModel(BaseModel):
    """DEPRECATED - do not use."""

    # General settings
    mode: str = Field(
        "advisory", description="Plugin mode: advisory, quality-gate, strict"
    )
    persona: str = Field("drill_sergeant", description="Default persona to use")
    sut_package: str | None = Field(None, description="System under test package name")
    fail_on_how: bool = Field(
        False, description="Whether to fail tests with low BIS scores"
    )

    # Output settings
    output_format: str = Field(
        "terminal", description="Output format: terminal, json, sarif"
    )
    json_report_path: Path | None = Field(
        None, description="Path for JSON report output"
    )
    sarif_report_path: Path | None = Field(
        None, description="Path for SARIF report output"
    )
    verbose: bool = Field(False, description="Enable verbose output")

    # Analysis settings
    enabled_rules: list[RuleType] = Field(
        default_factory=list, description="Enabled rule types"
    )
    disabled_rules: list[RuleType] = Field(
        default_factory=list, description="Disabled rule types"
    )
    rule_configs: dict[str, dict[str, str | int | float | bool]] = Field(
        default_factory=dict, description="Rule-specific configurations"
    )

    # Thresholds
    bis_threshold: float = Field(
        70.0, ge=0.0, le=100.0, description="BIS threshold for quality gates"
    )
    brs_threshold: float = Field(
        60.0, ge=0.0, le=100.0, description="BRS threshold for quality gates"
    )
    similarity_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Similarity threshold for duplicate detection"
    )

    # Performance settings
    parallel_analysis: bool = Field(True, description="Enable parallel analysis")
    max_workers: int = Field(4, ge=1, description="Maximum number of worker processes")
    cache_ast: bool = Field(True, description="Enable AST parsing cache")

    # LSP settings
    lsp_enabled: bool = Field(False, description="Enable LSP server")
    lsp_port: int = Field(8080, ge=1024, le=65535, description="LSP server port")

    model_config: ClassVar[ConfigDict] = ConfigDict(
        use_enum_values=True,
        validate_assignment=True,
    )

    @field_validator("enabled_rules", "disabled_rules", mode="before")
    @classmethod
    def validate_rules(cls, v: object) -> list[RuleType]:
        """Validate that enabled and disabled rules don't overlap."""
        if isinstance(v, list):
            return v
        return []

    def is_rule_enabled(self, rule_type: RuleType) -> bool:
        """Check if a rule type is enabled."""
        if rule_type in self.disabled_rules:
            return False
        if self.enabled_rules:
            return rule_type in self.enabled_rules
        return True

    def get_rule_config(
        self, rule_type: RuleType
    ) -> dict[str, str | int | float | bool]:
        """Get configuration for a specific rule type."""
        return self.rule_configs.get(rule_type.value, {})
