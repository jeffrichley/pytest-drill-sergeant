"""SARIF output formatter using the official Microsoft sarif-om library.

This module provides SARIF 2.1.0 compliant output formatting using the official
Microsoft SARIF Python object model for integration with GitHub Actions, security
tools, and other SARIF-compatible systems.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
from urllib.parse import urljoin

from sarif_om import (
    ArtifactLocation,
    Message,
    PhysicalLocation,
    Region,
    ReportingDescriptor,
    Result,
    Run,
    SarifLog,
    Tool,
    ToolComponent,
)

from pytest_drill_sergeant.core.reporting.types import JSONValue

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_drill_sergeant.core.models import (
        Finding,
        ResultData,
        RunMetrics,
        Severity,
    )
    from pytest_drill_sergeant.core.reporting.types import JSONDict

# Union type for SARIF properties that can contain both metrics and config
SarifProperties = dict[
    str,
    str
    | int
    | float
    | bool
    | list[str]
    | dict[str, str | int | float | bool]
    | JSONValue,
]


class SARIFFormatter:
    """SARIF 2.1.0 compliant formatter using the official Microsoft sarif-om library."""

    def __init__(self, base_uri: str = "file://") -> None:
        """Initialize the SARIF formatter.

        Args:
            base_uri: Base URI for file references
        """
        # Normalize base URI to end with single slash
        if not base_uri.endswith("/"):
            base_uri += "/"
        self.base_uri = base_uri
        self.tool_name = "pytest-drill-sergeant"
        self.tool_version = "1.0.0-dev"

    def _get_rule_id(self, rule_code: str) -> str:
        """Get SARIF rule ID for a rule code.

        Args:
            rule_code: Rule code (e.g., "DS201")

        Returns:
            SARIF rule ID
        """
        return f"drill-sergeant/{rule_code}"

    def _get_rule_name(self, rule_name: str) -> str:
        """Get human-readable rule name for a rule name.

        Args:
            rule_name: Rule name (e.g., "private_access")

        Returns:
            Human-readable rule name
        """
        name_mapping = {
            "private_access": "Private Access Violation",
            "mock_overspecification": "Mock Over-Specification",
            "structural_equality": "Structural Equality Check",
            "aaa_comment": "AAA Comment Missing or Incorrect",
            "duplicate_test": "Duplicate Test Detection",
            "parametrization": "Parametrization Opportunity",
            "fixture_extraction": "Fixture Extraction Opportunity",
        }
        return name_mapping.get(rule_name, rule_name.replace("_", " ").title())

    def _get_rule_description(self, rule_name: str) -> str:
        """Get rule description for a rule name.

        Args:
            rule_name: Rule name

        Returns:
            Rule description
        """
        description_mapping = {
            "private_access": "Test accesses private implementation details that may break with refactoring",
            "mock_overspecification": "Test has too many mock assertions, making it brittle",
            "structural_equality": "Test uses structural equality checks instead of semantic equality",
            "aaa_comment": "Test lacks proper Arrange-Act-Assert comment structure",
            "duplicate_test": "Test is similar to other tests and may be redundant",
            "parametrization": "Test could be parametrized to reduce duplication",
            "fixture_extraction": "Test setup could be extracted into a fixture",
        }
        return description_mapping.get(
            rule_name, f"Quality issue detected: {rule_name}"
        )

    def _get_severity_level(self, severity: Severity) -> str:
        """Convert severity to SARIF level.

        Args:
            severity: Finding severity

        Returns:
            SARIF severity level
        """
        severity_value = severity.value if hasattr(severity, "value") else str(severity)
        mapping = {
            "error": "error",
            "warning": "warning",
            "info": "note",
            "hint": "note",
        }
        return mapping.get(severity_value, "note")

    def _get_help_uri(self, rule_name: str) -> str:
        """Get help URI for a rule name.

        Args:
            rule_name: Rule name

        Returns:
            Help URI
        """
        base_url = (
            "https://github.com/jeffrichley/pytest-drill-sergeant/blob/main/docs/rules/"
        )
        return urljoin(base_url, f"{rule_name}.md")

    def format_finding(self, finding: Finding) -> Result:
        """Format a finding as a SARIF result.

        Args:
            finding: Finding to format

        Returns:
            SARIF result object
        """
        # Convert file path to URI
        file_uri = urljoin(self.base_uri, str(finding.file_path))

        # Create region
        region = Region()
        region.start_line = finding.line_number
        region.start_column = (
            finding.column_number if finding.column_number is not None else 1
        )

        # Add code snippet if available
        if finding.code_snippet:
            region.snippet = Message(text=finding.code_snippet)

        # Create artifact location
        artifact_location = ArtifactLocation(uri=file_uri)

        # Create location
        location = PhysicalLocation(
            artifact_location=artifact_location,
            region=region,
        )

        # Create result
        result = Result(
            message=Message(text=finding.message),
            rule_id=self._get_rule_id(finding.code),
            level=self._get_severity_level(finding.severity),
            locations=[location],
        )

        # Add suggestion if available
        if finding.suggestion:
            # Note: Fix objects would need to be implemented for suggestions
            # This is a simplified version
            pass

        # Add properties
        result.properties = {
            "confidence": finding.confidence,
            "metadata": finding.metadata,
        }

        return result

    def format_test_result(self, result: ResultData) -> list[Result]:
        """Format a test result as SARIF results.

        Args:
            result: Test result to format

        Returns:
            List of SARIF result objects
        """
        return [self.format_finding(finding) for finding in result.findings]

    def format_run_metrics(
        self, metrics: RunMetrics
    ) -> dict[
        str, str | int | float | bool | list[str] | dict[str, str | int | float | bool]
    ]:
        """Format run metrics as SARIF properties.

        Args:
            metrics: Run metrics to format

        Returns:
            SARIF properties dictionary
        """
        return {
            "total_tests": metrics.total_tests,
            "analyzed_tests": metrics.analyzed_tests,
            "failed_analyses": metrics.failed_analyses,
            "total_findings": metrics.total_findings,
            "average_bis": metrics.average_bis,
            "brs_score": metrics.brs_score,
            "brs_grade": metrics.brs_grade,
            "component_metrics": {
                "aaa_compliance_rate": metrics.aaa_compliance_rate,
                "duplicate_test_rate": metrics.duplicate_test_rate,
                "parametrization_rate": metrics.parametrization_rate,
                "fixture_reuse_rate": metrics.fixture_reuse_rate,
            },
            "performance_metrics": {
                "total_analysis_time": metrics.total_analysis_time,
                "average_test_time": metrics.average_test_time,
                "memory_peak": metrics.memory_peak,
            },
        }

    def format_report(
        self,
        test_results: list[ResultData],
        metrics: RunMetrics,
        config: JSONDict | None = None,
    ) -> SarifLog:
        """Format a complete report as SARIF.

        Args:
            test_results: List of test results
            metrics: Run metrics
            config: Configuration used for analysis

        Returns:
            SARIF report
        """
        # Collect all findings
        all_findings = []
        for result in test_results:
            all_findings.extend(result.findings)

        # Get unique rule codes and names
        rule_codes = set(finding.code for finding in all_findings)
        rule_names = {finding.code: finding.name for finding in all_findings}

        # Create rules
        rules = []
        for rule_code in rule_codes:
            rule_name = rule_names[rule_code]
            rule = ReportingDescriptor(id=self._get_rule_id(rule_code))  # type: ignore[call-arg]
            rule.name = self._get_rule_name(rule_name)
            rule.short_description = Message(text=self._get_rule_description(rule_name))
            rule.help_uri = self._get_help_uri(rule_name)
            rule.properties = {
                "category": "quality",
                "tags": ["test-quality", "ai-generated-tests"],
            }
            rules.append(rule)

        # Create results
        results = []
        for result in test_results:
            results.extend(self.format_test_result(result))

        # Create tool component
        tool_component = ToolComponent(name=self.tool_name)  # type: ignore[call-arg]
        tool_component.version = self.tool_version
        tool_component.information_uri = (
            "https://github.com/jeffrichley/pytest-drill-sergeant"
        )
        tool_component.rules = rules

        # Create tool
        tool = Tool(driver=tool_component)

        # Create run
        run = Run(tool=tool)  # type: ignore[call-arg]
        run.results = results
        run.properties = cast("SarifProperties", self.format_run_metrics(metrics))

        # Add configuration if provided
        if config:
            run.properties["configuration"] = config

        # Create SARIF log
        sarif_log = SarifLog(version="2.1.0", runs=[run])  # type: ignore[call-arg]
        sarif_log.schema = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"

        return sarif_log

    def save_report(self, report: SarifLog, output_path: Path) -> None:
        """Save a SARIF report to a file.

        Args:
            report: SARIF report to save
            output_path: Path to save the report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report.__dict__, f, indent=2, ensure_ascii=False, default=str)

    def to_string(self, data: SarifLog) -> str:
        """Convert data to SARIF JSON string.

        Args:
            data: Data to convert

        Returns:
            SARIF JSON string
        """
        return json.dumps(data.__dict__, indent=2, ensure_ascii=False, default=str)


class SARIFReportBuilder:
    """Builder for creating SARIF reports using the official sarif-om library."""

    def __init__(self, base_uri: str = "file://") -> None:
        """Initialize the SARIF report builder.

        Args:
            base_uri: Base URI for file references
        """
        self.formatter = SARIFFormatter(base_uri)
        self._test_results: list[ResultData] = []
        self._metrics: RunMetrics | None = None
        self._config: JSONDict | None = None

    def add_test_result(self, result: ResultData) -> None:
        """Add a test result to the report.

        Args:
            result: Test result to add
        """
        self._test_results.append(result)

    def add_test_results(self, results: list[ResultData]) -> None:
        """Add multiple test results to the report.

        Args:
            results: List of test results to add
        """
        self._test_results.extend(results)

    def set_metrics(self, metrics: RunMetrics) -> None:
        """Set the run metrics for the report.

        Args:
            metrics: Run metrics
        """
        self._metrics = metrics

    def set_config(self, config: JSONDict) -> None:
        """Set the configuration for the report.

        Args:
            config: Configuration dictionary
        """
        self._config = config

    def build(self) -> SarifLog:
        """Build the complete SARIF report.

        Returns:
            Complete SARIF report
        """
        if self._metrics is None:
            msg = "Metrics must be set before building report"
            raise ValueError(msg)

        return self.formatter.format_report(
            self._test_results, self._metrics, self._config
        )

    def save(self, output_path: Path) -> None:
        """Build and save the report to a file.

        Args:
            output_path: Path to save the report
        """
        report = self.build()
        self.formatter.save_report(report, output_path)

    def to_string(self) -> str:
        """Build and return the report as a SARIF JSON string.

        Returns:
            SARIF JSON report string
        """
        report = self.build()
        return self.formatter.to_string(report)


# Global SARIF formatter instance
sarif_formatter = SARIFFormatter()
