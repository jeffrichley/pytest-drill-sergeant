"""Simplified tests for SARIF formatter.

This module provides focused tests for the SARIFFormatter class,
covering the core functionality that works with the actual implementation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sarif_om import SarifLog

from pytest_drill_sergeant.core.models import (
    FeaturesData,
    Finding,
    ResultData,
    RuleType,
    RunMetrics,
    Severity,
)
from pytest_drill_sergeant.core.reporting.sarif_formatter import (
    SARIFFormatter,
    SARIFReportBuilder,
)

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.reporting.types import JSONDict

# Test constants to avoid magic numbers
TEST_LINE_NUMBER = 10
TEST_COLUMN_NUMBER = 5
EXPECTED_RESULTS_COUNT = 2
TOTAL_TESTS = 10
ANALYZED_TESTS = 8
FAILED_ANALYSES = 2
TOTAL_FINDINGS = 5
AVERAGE_BIS = 75.0
BRS_SCORE = 80.0
LARGE_NUMBER = 999999


class TestSARIFFormatterInitialization:
    """Test SARIFFormatter initialization."""

    def test_sarif_formatter_default_initialization(self) -> None:
        """Test default SARIF formatter initialization."""
        formatter = SARIFFormatter()

        assert formatter.base_uri == "file://"
        assert formatter.tool_name == "pytest-drill-sergeant"
        assert formatter.tool_version == "1.0.0-dev"

    def test_sarif_formatter_custom_base_uri(self) -> None:
        """Test SARIF formatter with custom base URI."""
        formatter = SARIFFormatter("https://example.com/")

        assert formatter.base_uri == "https://example.com/"
        assert formatter.tool_name == "pytest-drill-sergeant"
        assert formatter.tool_version == "1.0.0-dev"

    def test_sarif_formatter_base_uri_normalization(self) -> None:
        """Test base URI normalization."""
        formatter = SARIFFormatter("https://example.com")
        assert formatter.base_uri == "https://example.com/"

        formatter = SARIFFormatter("file:///path/to/repo")
        assert formatter.base_uri == "file:///path/to/repo/"


class TestRuleHelpers:
    """Test rule helper methods."""

    def test_get_rule_id(self) -> None:
        """Test getting rule ID for different rule types."""
        formatter = SARIFFormatter()

        assert (
            formatter._get_rule_id(RuleType.PRIVATE_ACCESS)
            == "drill-sergeant/private_access"
        )
        assert (
            formatter._get_rule_id(RuleType.MOCK_OVERSPECIFICATION)
            == "drill-sergeant/mock_overspecification"
        )
        assert (
            formatter._get_rule_id(RuleType.STRUCTURAL_EQUALITY)
            == "drill-sergeant/structural_equality"
        )

    def test_get_rule_name(self) -> None:
        """Test getting rule name for different rule types."""
        formatter = SARIFFormatter()

        assert (
            formatter._get_rule_name(RuleType.PRIVATE_ACCESS)
            == "Private Access Violation"
        )
        assert (
            formatter._get_rule_name(RuleType.MOCK_OVERSPECIFICATION)
            == "Mock Over-Specification"
        )
        assert (
            formatter._get_rule_name(RuleType.STRUCTURAL_EQUALITY)
            == "Structural Equality Check"
        )

    def test_get_rule_description(self) -> None:
        """Test getting rule description for different rule types."""
        formatter = SARIFFormatter()

        desc = formatter._get_rule_description(RuleType.PRIVATE_ACCESS)
        assert "private implementation details" in desc

        desc = formatter._get_rule_description(RuleType.MOCK_OVERSPECIFICATION)
        assert "too many mock assertions" in desc

    def test_get_severity_level(self) -> None:
        """Test getting SARIF severity level."""
        formatter = SARIFFormatter()

        assert formatter._get_severity_level(Severity.ERROR) == "error"
        assert formatter._get_severity_level(Severity.WARNING) == "warning"
        assert formatter._get_severity_level(Severity.INFO) == "note"
        assert formatter._get_severity_level(Severity.HINT) == "note"

    def test_get_help_uri(self) -> None:
        """Test getting help URI for rule types."""
        formatter = SARIFFormatter()

        uri = formatter._get_help_uri(RuleType.PRIVATE_ACCESS)
        assert "github.com/jeffrichley/pytest-drill-sergeant" in uri
        assert "private_access.md" in uri


class TestFindingFormatting:
    """Test finding formatting functionality."""

    def test_format_finding_basic(self) -> None:
        """Test basic finding formatting."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding message",
            file_path=Path("test_file.py"),
            line_number=10,
            column_number=5,
        )

        result = formatter.format_finding(finding)

        assert result.message.text == "Test finding message"
        assert result.rule_id == "drill-sergeant/private_access"
        assert result.level == "warning"
        assert result.locations[0].artifact_location.uri == "file:///test_file.py"
        assert result.locations[0].region.start_line == TEST_LINE_NUMBER
        assert result.locations[0].region.start_column == TEST_COLUMN_NUMBER

    def test_format_finding_with_code_snippet(self) -> None:
        """Test finding formatting with code snippet."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding message",
            file_path=Path("test_file.py"),
            line_number=10,
            column_number=5,
            code_snippet="def test_method(self):",
        )

        result = formatter.format_finding(finding)

        assert result.locations[0].region.snippet.text == "def test_method(self):"

    def test_format_finding_without_column(self) -> None:
        """Test finding formatting without column number."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding message",
            file_path=Path("test_file.py"),
            line_number=10,
        )

        result = formatter.format_finding(finding)

        assert result.locations[0].region.start_column == 1

    def test_format_finding_different_severities(self) -> None:
        """Test finding formatting with different severities."""
        formatter = SARIFFormatter()

        for severity, expected_level in [
            (Severity.ERROR, "error"),
            (Severity.WARNING, "warning"),
            (Severity.INFO, "note"),
            (Severity.HINT, "note"),
        ]:
            finding = Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=severity,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )

            result = formatter.format_finding(finding)
            assert result.level == expected_level

    def test_format_finding_different_rule_types(self) -> None:
        """Test finding formatting with different rule types."""
        formatter = SARIFFormatter()

        for rule_type in RuleType:
            finding = Finding(
                rule_type=rule_type,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )

            result = formatter.format_finding(finding)
            assert result.rule_id == f"drill-sergeant/{rule_type.value}"


class TestReportGeneration:
    """Test report generation functionality."""

    def _create_test_result(self, test_name: str = "test_example") -> ResultData:
        """Helper to create a test result with required fields."""
        features = FeaturesData(
            test_name=test_name, file_path=Path("test_file.py"), line_number=10
        )

        return ResultData(
            test_name=test_name,
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            findings=[],
        )

    def test_format_report_basic(self) -> None:
        """Test basic report formatting."""
        formatter = SARIFFormatter()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding 1",
                file_path=Path("test_file1.py"),
                line_number=10,
            ),
            Finding(
                rule_type=RuleType.MOCK_OVERSPECIFICATION,
                severity=Severity.ERROR,
                message="Test finding 2",
                file_path=Path("test_file2.py"),
                line_number=20,
            ),
        ]

        test_results = [self._create_test_result("test_1")]
        test_results[0].findings = findings

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 1, Severity.ERROR: 1},
            findings_by_rule={
                RuleType.PRIVATE_ACCESS: 1,
                RuleType.MOCK_OVERSPECIFICATION: 1,
            },
        )

        report = formatter.format_report(test_results, metrics)

        assert isinstance(report, SarifLog)
        assert len(report.runs) == 1
        assert len(report.runs[0].results) == EXPECTED_RESULTS_COUNT
        assert report.runs[0].tool.driver.name == "pytest-drill-sergeant"
        assert report.runs[0].tool.driver.version == "1.0.0-dev"

    def test_format_report_with_config(self) -> None:
        """Test report formatting with configuration."""
        formatter = SARIFFormatter()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_results = [self._create_test_result("test_1")]
        test_results[0].findings = findings

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        config: JSONDict = {
            "threshold": 0.8,
            "enabled_rules": ["private_access"],
            "strict_mode": True,
        }

        report = formatter.format_report(test_results, metrics, config)

        assert isinstance(report, SarifLog)
        assert len(report.runs) == 1
        assert "configuration" in report.runs[0].properties

    def test_format_report_empty(self) -> None:
        """Test report formatting with no findings."""
        formatter = SARIFFormatter()

        test_results = [self._create_test_result("test_1")]

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=0,
            findings_by_severity={},
            findings_by_rule={},
        )

        report = formatter.format_report(test_results, metrics)

        assert isinstance(report, SarifLog)
        assert len(report.runs) == 1
        assert len(report.runs[0].results) == 0

    def test_format_run_metrics(self) -> None:
        """Test run metrics formatting."""
        formatter = SARIFFormatter()

        metrics = RunMetrics(
            total_tests=10,
            analyzed_tests=8,
            failed_analyses=2,
            total_findings=5,
            findings_by_severity={Severity.WARNING: 3, Severity.ERROR: 2},
            findings_by_rule={
                RuleType.PRIVATE_ACCESS: 3,
                RuleType.MOCK_OVERSPECIFICATION: 2,
            },
            average_bis=75.0,
            brs_score=80.0,
            brs_grade="B",
        )

        formatted_metrics = formatter.format_run_metrics(metrics)

        assert formatted_metrics["total_tests"] == TOTAL_TESTS
        assert formatted_metrics["analyzed_tests"] == ANALYZED_TESTS
        assert formatted_metrics["failed_analyses"] == FAILED_ANALYSES
        assert formatted_metrics["total_findings"] == TOTAL_FINDINGS
        assert formatted_metrics["average_bis"] == AVERAGE_BIS
        assert formatted_metrics["brs_score"] == BRS_SCORE
        assert formatted_metrics["brs_grade"] == "B"

    def test_format_test_result(self) -> None:
        """Test test result formatting."""
        formatter = SARIFFormatter()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_result = self._create_test_result("test_1")
        test_result.findings = findings

        results = formatter.format_test_result(test_result)

        assert len(results) == 1
        assert results[0].rule_id == "drill-sergeant/private_access"
        assert results[0].level == "warning"


class TestReportSaving:
    """Test report saving functionality."""

    def test_save_report(self, tmp_path: Path) -> None:
        """Test saving report to file."""
        formatter = SARIFFormatter()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_results = [
            ResultData(
                test_name="test_1",
                file_path=Path("test_file.py"),
                line_number=10,
                features=FeaturesData(
                    test_name="test_1", file_path=Path("test_file.py"), line_number=10
                ),
                findings=findings,
            )
        ]

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        report = formatter.format_report(test_results, metrics)
        output_path = tmp_path / "test_report.sarif"
        formatter.save_report(report, output_path)

        assert output_path.exists()

        # Verify the file contains valid JSON
        with output_path.open() as f:
            content = json.load(f)

        assert "schema" in content
        assert (
            content["schema"]
            == "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
        )

    def test_to_string(self) -> None:
        """Test converting report to string."""
        formatter = SARIFFormatter()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_results = [
            ResultData(
                test_name="test_1",
                file_path=Path("test_file.py"),
                line_number=10,
                features=FeaturesData(
                    test_name="test_1", file_path=Path("test_file.py"), line_number=10
                ),
                findings=findings,
            )
        ]

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        report = formatter.format_report(test_results, metrics)
        report_string = formatter.to_string(report)

        assert isinstance(report_string, str)
        assert "drill-sergeant" in report_string
        assert "Test finding" in report_string


class TestSARIFReportBuilder:
    """Test SARIFReportBuilder functionality."""

    def _create_test_result(self, test_name: str = "test_example") -> ResultData:
        """Helper to create a test result with required fields."""
        features = FeaturesData(
            test_name=test_name, file_path=Path("test_file.py"), line_number=10
        )

        return ResultData(
            test_name=test_name,
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            findings=[],
        )

    def test_builder_initialization(self) -> None:
        """Test SARIF report builder initialization."""
        builder = SARIFReportBuilder()

        assert builder.formatter is not None
        assert builder._test_results == []
        assert builder._metrics is None
        assert builder._config is None

    def test_builder_initialization_with_custom_uri(self) -> None:
        """Test SARIF report builder initialization with custom URI."""
        builder = SARIFReportBuilder("https://example.com/")

        assert builder.formatter.base_uri == "https://example.com/"

    def test_add_test_result(self) -> None:
        """Test adding test result to builder."""
        builder = SARIFReportBuilder()

        result = self._create_test_result("test_1")
        builder.add_test_result(result)

        assert len(builder._test_results) == 1
        assert builder._test_results[0] is result

    def test_add_test_results(self) -> None:
        """Test adding multiple test results to builder."""
        builder = SARIFReportBuilder()

        results = [
            self._create_test_result("test_1"),
            self._create_test_result("test_2"),
        ]
        builder.add_test_results(results)

        assert len(builder._test_results) == EXPECTED_RESULTS_COUNT
        assert builder._test_results[0] is results[0]
        assert builder._test_results[1] is results[1]

    def test_set_metrics(self) -> None:
        """Test setting metrics in builder."""
        builder = SARIFReportBuilder()

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        builder.set_metrics(metrics)

        assert builder._metrics is metrics

    def test_set_config(self) -> None:
        """Test setting config in builder."""
        builder = SARIFReportBuilder()

        config: JSONDict = {"threshold": 0.8, "strict_mode": True}
        builder.set_config(config)

        assert builder._config is config

    def test_build_report(self) -> None:
        """Test building report."""
        builder = SARIFReportBuilder()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_result = self._create_test_result("test_1")
        test_result.findings = findings

        builder.add_test_result(test_result)

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        builder.set_metrics(metrics)

        report = builder.build()

        assert isinstance(report, SarifLog)
        assert len(report.runs) == 1
        assert len(report.runs[0].results) == 1

    def test_build_report_without_metrics(self) -> None:
        """Test building report without metrics."""
        builder = SARIFReportBuilder()

        test_result = self._create_test_result("test_1")
        builder.add_test_result(test_result)

        with pytest.raises(
            ValueError, match="Metrics must be set before building report"
        ) as exc_info:
            builder.build()
        assert "Metrics must be set before building report" in str(exc_info.value)

    def test_save_report(self, tmp_path: Path) -> None:
        """Test saving report."""
        builder = SARIFReportBuilder()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_result = self._create_test_result("test_1")
        test_result.findings = findings

        builder.add_test_result(test_result)

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        builder.set_metrics(metrics)

        output_path = tmp_path / "test_report.sarif"
        builder.save(output_path)

        assert output_path.exists()

        with output_path.open() as f:
            content = json.load(f)

        assert "schema" in content

    def test_to_string(self) -> None:
        """Test converting report to string."""
        builder = SARIFReportBuilder()

        findings = [
            Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test_file.py"),
                line_number=10,
            )
        ]

        test_result = self._create_test_result("test_1")
        test_result.findings = findings

        builder.add_test_result(test_result)

        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=1,
            findings_by_severity={Severity.WARNING: 1},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 1},
        )

        builder.set_metrics(metrics)

        report_string = builder.to_string()

        assert isinstance(report_string, str)
        assert "drill-sergeant" in report_string
        assert "Test finding" in report_string


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_findings(self) -> None:
        """Test with unicode characters in findings."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="测试消息 🚀",
            file_path=Path("测试文件.py"),
            line_number=10,
            column_number=5,
            code_snippet="def 测试方法(self):",
        )

        result = formatter.format_finding(finding)

        assert result.message.text == "测试消息 🚀"

    def test_very_long_messages(self) -> None:
        """Test with very long messages."""
        formatter = SARIFFormatter()

        long_message = "A" * 10000  # 10KB message

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message=long_message,
            file_path=Path("test_file.py"),
            line_number=10,
        )

        result = formatter.format_finding(finding)

        assert result.message.text == long_message

    def test_special_characters_in_paths(self) -> None:
        """Test with special characters in file paths."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test file with spaces.py"),
            line_number=10,
        )

        result = formatter.format_finding(finding)

        assert "test file with spaces.py" in result.locations[0].artifact_location.uri

    def test_absolute_paths(self) -> None:
        """Test with absolute file paths."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("/absolute/path/to/test_file.py"),
            line_number=10,
        )

        result = formatter.format_finding(finding)

        assert (
            "/absolute/path/to/test_file.py"
            in result.locations[0].artifact_location.uri
        )

    def test_very_large_line_numbers(self) -> None:
        """Test with very large line numbers."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=999999,
            column_number=999999,
        )

        result = formatter.format_finding(finding)

        assert result.locations[0].region.start_line == LARGE_NUMBER
        assert result.locations[0].region.start_column == LARGE_NUMBER

    def test_zero_line_numbers(self) -> None:
        """Test with zero line numbers."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=0,
            column_number=0,
        )

        result = formatter.format_finding(finding)

        assert result.locations[0].region.start_line == 0
        assert result.locations[0].region.start_column == 0

    def test_empty_code_snippet(self) -> None:
        """Test with empty code snippet."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=10,
            code_snippet="",
        )

        result = formatter.format_finding(finding)

        # Empty snippet should not be included
        assert result.locations[0].region.snippet is None

    def test_none_code_snippet(self) -> None:
        """Test with None code snippet."""
        formatter = SARIFFormatter()

        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=10,
            code_snippet=None,
        )

        result = formatter.format_finding(finding)

        # None snippet should not be included
        assert result.locations[0].region.snippet is None
