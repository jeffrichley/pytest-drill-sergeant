"""Tests for the core data models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from pytest_drill_sergeant.core.models import (
    Cluster,
    FeaturesData,
    Finding,
    Rule,
    RuleType,
    Severity,
)

# Test constants to avoid magic numbers
LINE_NUMBER_10 = 10
COLUMN_NUMBER_5 = 5
CONFIDENCE_08 = 0.8
SIMILARITY_SCORE_09 = 0.9
THRESHOLD_08 = 0.8
PRIVATE_ACCESS_COUNT_2 = 2
MOCK_ASSERTION_COUNT_3 = 3
STRUCTURAL_EQUALITY_COUNT_1 = 1
TEST_LENGTH_50 = 50
COMPLEXITY_SCORE_25 = 2.5
COVERAGE_PERCENTAGE_855 = 85.5
COVERAGE_PERCENTAGE_100 = 100.0


class TestSeverity:
    """Test the Severity enum."""

    def test_severity_values(self) -> None:
        """Test severity enum values."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"
        assert Severity.HINT.value == "hint"

    def test_severity_string_conversion(self) -> None:
        """Test severity string conversion."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"


class TestRuleType:
    """Test the RuleType enum."""

    def test_rule_type_values(self) -> None:
        """Test rule type enum values."""
        assert RuleType.PRIVATE_ACCESS.value == "private_access"
        assert RuleType.MOCK_OVERSPECIFICATION.value == "mock_overspecification"
        assert RuleType.STRUCTURAL_EQUALITY.value == "structural_equality"
        assert RuleType.AAA_COMMENT.value == "aaa_comment"
        assert RuleType.DUPLICATE_TEST.value == "duplicate_test"
        assert RuleType.PARAMETRIZATION.value == "parametrization"
        assert RuleType.FIXTURE_EXTRACTION.value == "fixture_extraction"


class TestFinding:
    """Test the Finding model."""

    def test_finding_creation(self) -> None:
        """Test creating a finding."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test message",
            file_path=Path("test.py"),
            line_number=10,
            column_number=5,
            code_snippet="test_code",
            suggestion="Fix suggestion",
            confidence=0.8,
            metadata={"key": "value"},
        )

        assert finding.rule_type == RuleType.PRIVATE_ACCESS
        assert finding.severity == Severity.WARNING
        assert finding.message == "Test message"
        assert finding.file_path == Path("test.py")
        assert finding.line_number == LINE_NUMBER_10
        assert finding.column_number == COLUMN_NUMBER_5
        assert finding.code_snippet == "test_code"
        assert finding.suggestion == "Fix suggestion"
        assert finding.confidence == CONFIDENCE_08
        assert finding.metadata == {"key": "value"}

    def test_finding_minimal(self) -> None:
        """Test creating a finding with minimal required fields."""
        finding = Finding(
            rule_type=RuleType.AAA_COMMENT,
            severity=Severity.ERROR,
            message="Minimal message",
            file_path=Path("test.py"),
            line_number=1,
        )

        assert finding.rule_type == RuleType.AAA_COMMENT
        assert finding.severity == Severity.ERROR
        assert finding.message == "Minimal message"
        assert finding.file_path == Path("test.py")
        assert finding.line_number == 1
        assert finding.column_number is None
        assert finding.code_snippet is None
        assert finding.suggestion is None
        assert finding.confidence == 0.0
        assert finding.metadata == {}

    def test_finding_confidence_validation(self) -> None:
        """Test finding confidence validation."""
        # Valid confidence values
        finding1 = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test",
            file_path=Path("test.py"),
            line_number=1,
            confidence=0.0,
        )
        assert finding1.confidence == 0.0

        finding2 = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test",
            file_path=Path("test.py"),
            line_number=1,
            confidence=1.0,
        )
        assert finding2.confidence == 1.0

        # Invalid confidence values
        with pytest.raises(ValidationError):
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test",
                file_path=Path("test.py"),
                line_number=1,
                confidence=-0.1,
            )

        with pytest.raises(ValidationError):
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test",
                file_path=Path("test.py"),
                line_number=1,
                confidence=1.1,
            )

    def test_finding_required_fields(self) -> None:
        """Test finding required fields validation."""
        with pytest.raises(ValidationError):
            Finding()  # type: ignore[call-arg]


class TestCluster:
    """Test the Cluster model."""

    def test_cluster_creation(self) -> None:
        """Test creating a cluster."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test.py"),
            line_number=1,
        )

        cluster = Cluster(
            cluster_id="cluster_1",
            cluster_type="duplicate_tests",
            findings=[finding],
            similarity_score=0.9,
            representative=finding,
            metadata={"type": "test_cluster"},
        )

        assert cluster.cluster_id == "cluster_1"
        assert cluster.cluster_type == "duplicate_tests"
        assert len(cluster.findings) == 1
        assert cluster.findings[0] == finding
        assert cluster.similarity_score == SIMILARITY_SCORE_09
        assert cluster.representative == finding
        assert cluster.metadata == {"type": "test_cluster"}

    def test_cluster_minimal(self) -> None:
        """Test creating a cluster with minimal fields."""
        cluster = Cluster(
            cluster_id="cluster_2",
            cluster_type="similar_findings",
        )

        assert cluster.cluster_id == "cluster_2"
        assert cluster.cluster_type == "similar_findings"
        assert cluster.findings == []
        assert cluster.similarity_score == 0.0
        assert cluster.representative is None
        assert cluster.metadata == {}

    def test_cluster_similarity_score_validation(self) -> None:
        """Test cluster similarity score validation."""
        # Valid similarity scores
        cluster1 = Cluster(
            cluster_id="test",
            cluster_type="test",
            similarity_score=0.0,
        )
        assert cluster1.similarity_score == 0.0

        cluster2 = Cluster(
            cluster_id="test",
            cluster_type="test",
            similarity_score=1.0,
        )
        assert cluster2.similarity_score == 1.0

        # Invalid similarity scores
        with pytest.raises(ValidationError):
            Cluster(
                cluster_id="test",
                cluster_type="test",
                similarity_score=-0.1,
            )

        with pytest.raises(ValidationError):
            Cluster(
                cluster_id="test",
                cluster_type="test",
                similarity_score=1.1,
            )


class TestRule:
    """Test the Rule model."""

    def test_rule_creation(self) -> None:
        """Test creating a rule."""
        rule = Rule(
            rule_id="rule_1",
            rule_type=RuleType.PRIVATE_ACCESS,
            name="Private Access Rule",
            description="Detects private access violations",
            enabled=True,
            severity=Severity.WARNING,
            threshold=0.8,
            allowlist=["test.*"],
            configuration={"strict": True},
        )

        assert rule.rule_id == "rule_1"
        assert rule.rule_type == RuleType.PRIVATE_ACCESS
        assert rule.name == "Private Access Rule"
        assert rule.description == "Detects private access violations"
        assert rule.enabled is True
        assert rule.severity == Severity.WARNING
        assert rule.threshold == THRESHOLD_08
        assert rule.allowlist == ["test.*"]
        assert rule.configuration == {"strict": True}

    def test_rule_defaults(self) -> None:
        """Test rule with default values."""
        rule = Rule(
            rule_id="rule_2",
            rule_type=RuleType.AAA_COMMENT,
            name="AAA Comment Rule",
            description="Detects AAA comment violations",
        )

        assert rule.enabled is True
        assert rule.severity == Severity.WARNING
        assert rule.threshold is None
        assert rule.allowlist == []
        assert rule.configuration == {}


class TestFeaturesData:
    """Test the FeaturesData model."""

    def test_features_data_creation(self) -> None:
        """Test creating features data."""
        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test_example.py"),
            line_number=10,
            has_aaa_comments=True,
            aaa_comment_order="AAA",
            private_access_count=2,
            mock_assertion_count=3,
            structural_equality_count=1,
            test_length=50,
            complexity_score=2.5,
            coverage_percentage=85.5,
            coverage_signature="abc123",
        )

        assert features.test_name == "test_example"
        assert features.file_path == Path("test_example.py")
        assert features.line_number == LINE_NUMBER_10
        assert features.has_aaa_comments is True
        assert features.aaa_comment_order == "AAA"
        assert features.private_access_count == PRIVATE_ACCESS_COUNT_2
        assert features.mock_assertion_count == MOCK_ASSERTION_COUNT_3
        assert features.structural_equality_count == STRUCTURAL_EQUALITY_COUNT_1
        assert features.test_length == TEST_LENGTH_50
        assert features.complexity_score == COMPLEXITY_SCORE_25
        assert features.coverage_percentage == COVERAGE_PERCENTAGE_855
        assert features.coverage_signature == "abc123"

    def test_features_data_defaults(self) -> None:
        """Test features data with default values."""
        features = FeaturesData(
            test_name="test_minimal",
            file_path=Path("test_minimal.py"),
            line_number=1,
        )

        assert features.has_aaa_comments is False
        assert features.aaa_comment_order is None
        assert features.private_access_count == 0
        assert features.mock_assertion_count == 0
        assert features.structural_equality_count == 0
        assert features.test_length == 0
        assert features.complexity_score == 0.0
        assert features.coverage_percentage == 0.0
        assert features.coverage_signature is None

    def test_features_data_coverage_validation(self) -> None:
        """Test features data coverage percentage validation."""
        # Valid coverage percentages
        features1 = FeaturesData(
            test_name="test",
            file_path=Path("test.py"),
            line_number=1,
            coverage_percentage=0.0,
        )
        assert features1.coverage_percentage == 0.0

        features2 = FeaturesData(
            test_name="test",
            file_path=Path("test.py"),
            line_number=1,
            coverage_percentage=100.0,
        )
        assert features2.coverage_percentage == COVERAGE_PERCENTAGE_100

        # Invalid coverage percentages
        with pytest.raises(ValidationError):
            FeaturesData(
                test_name="test",
                file_path=Path("test.py"),
                line_number=1,
                coverage_percentage=-1.0,
            )

        with pytest.raises(ValidationError):
            FeaturesData(
                test_name="test",
                file_path=Path("test.py"),
                line_number=1,
                coverage_percentage=101.0,
            )

    def test_features_data_required_fields(self) -> None:
        """Test features data required fields validation."""
        with pytest.raises(ValidationError):
            FeaturesData()  # type: ignore[call-arg]


class TestModelIntegration:
    """Integration tests for models."""

    def test_finding_in_cluster(self) -> None:
        """Test finding can be used in cluster."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test.py"),
            line_number=1,
        )

        cluster = Cluster(
            cluster_id="cluster_1",
            cluster_type="test_cluster",
            findings=[finding],
            representative=finding,
        )

        assert finding in cluster.findings
        assert cluster.representative == finding

    def test_rule_with_finding(self) -> None:
        """Test rule can be used with finding."""
        rule = Rule(
            rule_id="private_access_rule",
            rule_type=RuleType.PRIVATE_ACCESS,
            name="Private Access Rule",
            description="Detects private access violations",
        )

        finding = Finding(
            rule_type=rule.rule_type,
            severity=rule.severity,
            message="Private access violation",
            file_path=Path("test.py"),
            line_number=1,
        )

        assert finding.rule_type == rule.rule_type
        assert finding.severity == rule.severity

    def test_features_data_with_finding(self) -> None:
        """Test features data can be used with finding."""
        features = FeaturesData(
            test_name="test_private_access",
            file_path=Path("test_private_access.py"),
            line_number=10,
            private_access_count=3,
        )

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Private access violation",
            file_path=features.file_path,
            line_number=features.line_number,
        )

        assert finding.file_path == features.file_path
        assert finding.line_number == features.line_number
