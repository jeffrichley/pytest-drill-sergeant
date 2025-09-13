"""Test to boost coverage for models.py which has only 1% coverage."""

from pathlib import Path

from pytest_drill_sergeant.core import models
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


def test_models_import():
    """Test that we can import the models module."""
    assert models is not None


def test_severity_enum():
    """Test Severity enum values."""
    assert Severity.ERROR == "error"
    assert Severity.WARNING == "warning"
    assert Severity.INFO == "info"


def test_rule_type_enum():
    """Test RuleType enum values."""
    assert RuleType.PRIVATE_ACCESS == "private_access"
    assert RuleType.MOCK_OVERSPECIFICATION == "mock_overspecification"
    assert RuleType.STRUCTURAL_EQUALITY == "structural_equality"
    assert RuleType.AAA_COMMENT == "aaa_comment"
    assert RuleType.DUPLICATE_TEST == "duplicate_test"
    assert RuleType.PARAMETRIZATION == "parametrization"
    assert RuleType.FIXTURE_EXTRACTION == "fixture_extraction"


def test_finding_model():
    """Test Finding model creation."""
    finding = Finding(
        rule_type=RuleType.PRIVATE_ACCESS,
        file_path="test.py",
        line_number=10,
        message="Test finding",
        severity=Severity.ERROR,
    )
    assert finding.rule_type == RuleType.PRIVATE_ACCESS
    assert finding.file_path == Path("test.py")
    assert finding.line_number == LINE_NUMBER_10
    assert finding.message == "Test finding"
    assert finding.severity == Severity.ERROR


def test_cluster_model():
    """Test Cluster model creation."""
    cluster = Cluster(
        cluster_id="test-cluster-1",
        cluster_type="duplicate_tests",
    )
    assert cluster.cluster_id == "test-cluster-1"
    assert cluster.cluster_type == "duplicate_tests"
    assert cluster.findings == []
    assert cluster.similarity_score == 0.0
    assert cluster.representative is None
    assert cluster.metadata == {}


def test_rule_model():
    """Test Rule model creation."""
    rule = Rule(
        rule_id="test-rule-1",
        rule_type=RuleType.PRIVATE_ACCESS,
        name="Test Rule",
        description="Test rule description",
        severity=Severity.ERROR,
    )
    assert rule.rule_id == "test-rule-1"
    assert rule.rule_type == RuleType.PRIVATE_ACCESS
    assert rule.name == "Test Rule"
    assert rule.description == "Test rule description"
    assert rule.severity == Severity.ERROR
    assert rule.enabled is True
    assert rule.threshold is None
    assert rule.allowlist == []
    assert rule.configuration == {}


def test_features_data_model():
    """Test FeaturesData model creation."""
    features = FeaturesData(
        test_name="test_example",
        file_path="test.py",
        line_number=10,
    )
    assert features.test_name == "test_example"
    assert features.file_path == Path("test.py")
    assert features.line_number == LINE_NUMBER_10
