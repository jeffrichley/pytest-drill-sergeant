"""JSON output formatter for machine-readable reports.

This module provides JSON output formatting for CI/CD integration and
machine-readable analysis results.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_drill_sergeant.core.error_handler import AnalysisError
    from pytest_drill_sergeant.core.models import Finding, ResultData, RunMetrics
    from pytest_drill_sergeant.core.reporting.types import JSONDict


class JSONFormatter:
    """JSON formatter for analysis results."""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False) -> None:
        """Initialize the JSON formatter.

        Args:
            indent: JSON indentation level
            ensure_ascii: Whether to ensure ASCII-only output
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def format_finding(self, finding: Finding) -> JSONDict:
        """Format a finding as JSON.

        Args:
            finding: Finding to format

        Returns:
            JSON-serializable dictionary
        """
        severity_value = (
            finding.severity.value
            if hasattr(finding.severity, "value")
            else str(finding.severity)
        )

        return {
            "code": finding.code,
            "name": finding.name,
            "severity": severity_value,
            "message": finding.message,
            "file_path": str(finding.file_path),
            "line_number": finding.line_number,
            "column_number": finding.column_number or 0,
            "code_snippet": finding.code_snippet or "",
            "suggestion": finding.suggestion or "",
            "confidence": finding.confidence,
            "metadata": dict(finding.metadata or {}),
        }

    def format_test_result(self, result: ResultData) -> JSONDict:
        """Format a test result as JSON.

        Args:
            result: Test result to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "test_name": result.test_name,
            "file_path": str(result.file_path),
            "line_number": result.line_number,
            "findings": [self.format_finding(f) for f in result.findings],
            "features": {
                "has_aaa_comments": result.features.has_aaa_comments,
                "aaa_comment_order": result.features.aaa_comment_order or "",
                "private_access_count": result.features.private_access_count,
                "mock_assertion_count": result.features.mock_assertion_count,
                "structural_equality_count": result.features.structural_equality_count,
                "test_length": result.features.test_length,
                "complexity_score": result.features.complexity_score,
                "coverage_percentage": result.features.coverage_percentage,
                "coverage_signature": result.features.coverage_signature or "",
                "assertion_count": result.features.assertion_count,
                "setup_lines": result.features.setup_lines,
                "teardown_lines": result.features.teardown_lines,
                "execution_time": result.features.execution_time,
                "memory_usage": result.features.memory_usage,
                "exception_count": result.features.exception_count,
                "metadata": dict(result.features.metadata or {}),
            },
            "bis_score": result.bis_score,
            "bis_grade": result.bis_grade,
            "analyzed": result.analyzed,
            "error_message": result.error_message or "",
            "analysis_time": result.analysis_time,
            "created_at": result.created_at.isoformat(),
        }

    def format_analysis_error(self, error: AnalysisError) -> JSONDict:
        """Format an analysis error as JSON.

        Args:
            error: Analysis error to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "error_id": error.error_id,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "suggestion": error.suggestion or "",
            "recoverable": error.recoverable,
            "retry_count": error.retry_count,
            "max_retries": error.max_retries,
            "context": (
                {
                    "file_path": (
                        str(error.context.file_path)
                        if error.context and error.context.file_path
                        else ""
                    ),
                    "line_number": error.context.line_number if error.context else None,
                    "analyzer_name": (
                        error.context.analyzer_name if error.context else ""
                    ),
                    "function_name": (
                        error.context.function_name if error.context else ""
                    ),
                    "timestamp": (
                        error.context.timestamp.isoformat() if error.context else ""
                    ),
                    "user_data": error.context.user_data if error.context else {},
                }
                if error.context
                else {}
            ),
            "original_exception": (
                {
                    "type": (
                        type(error.original_exception).__name__
                        if error.original_exception
                        else ""
                    ),
                    "message": (
                        str(error.original_exception)
                        if error.original_exception
                        else ""
                    ),
                }
                if error.original_exception
                else None
            ),
        }

    def format_run_metrics(self, metrics: RunMetrics) -> JSONDict:
        """Format run metrics as JSON.

        Args:
            metrics: Run metrics to format

        Returns:
            JSON-serializable dictionary
        """
        return {
            "total_tests": metrics.total_tests,
            "analyzed_tests": metrics.analyzed_tests,
            "failed_analyses": metrics.failed_analyses,
            "total_findings": metrics.total_findings,
            "findings_by_severity": {
                severity.value: count
                for severity, count in metrics.findings_by_severity.items()
            },
            "findings_by_rule": {
                rule_type.value: count
                for rule_type, count in metrics.findings_by_rule.items()
            },
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
            "created_at": metrics.created_at.isoformat(),
            "completed_at": (
                metrics.completed_at.isoformat() if metrics.completed_at else ""
            ),
        }

    def format_report(
        self,
        test_results: list[ResultData],
        metrics: RunMetrics,
        config: JSONDict | None = None,
        errors: list[AnalysisError] | None = None,
    ) -> JSONDict:
        """Format a complete report as JSON.

        Args:
            test_results: List of test results
            metrics: Run metrics
            config: Configuration used for analysis
            errors: List of analysis errors

        Returns:
            Complete JSON report
        """
        report = {
            "report_metadata": {
                "tool": "pytest-drill-sergeant",
                "version": "1.0.0-dev",
                "generated_at": datetime.now().isoformat(),
                "format_version": "1.0",
            },
            "configuration": config or {},
            "metrics": self.format_run_metrics(metrics),
            "test_results": [
                self.format_test_result(result) for result in test_results
            ],
            "summary": {
                "total_tests": metrics.total_tests,
                "total_findings": metrics.total_findings,
                "average_bis": metrics.average_bis,
                "brs_score": metrics.brs_score,
                "quality_grade": metrics.brs_grade,
            },
        }

        # Add error information if provided
        if errors:
            report["errors"] = {
                "total_errors": len(errors),
                "errors": [self.format_analysis_error(error) for error in errors],
                "error_summary": {
                    "by_category": {},
                    "by_severity": {},
                },
            }

            # Calculate error summary
            for error in errors:
                category = error.category.value
                severity = error.severity.value

                report["errors"]["error_summary"]["by_category"][category] = (
                    report["errors"]["error_summary"]["by_category"].get(category, 0)
                    + 1
                )
                report["errors"]["error_summary"]["by_severity"][severity] = (
                    report["errors"]["error_summary"]["by_severity"].get(severity, 0)
                    + 1
                )

        return report

    def save_report(self, report: JSONDict, output_path: Path) -> None:
        """Save a report to a JSON file.

        Args:
            report: Report data to save
            output_path: Path to save the report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                report,
                f,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                default=str,
            )

    def to_string(self, data: JSONDict) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to convert

        Returns:
            JSON string
        """
        return json.dumps(
            data, indent=self.indent, ensure_ascii=self.ensure_ascii, default=str
        )


class JSONReportBuilder:
    """Builder for creating structured JSON reports."""

    def __init__(self) -> None:
        """Initialize the JSON report builder."""
        self.formatter = JSONFormatter()
        self._test_results: list[ResultData] = []
        self._metrics: RunMetrics | None = None
        self._config: JSONDict | None = None
        self._errors: list[AnalysisError] = []

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

    def add_error(self, error: AnalysisError) -> None:
        """Add an analysis error to the report.

        Args:
            error: Analysis error to add
        """
        self._errors.append(error)

    def add_errors(self, errors: list[AnalysisError]) -> None:
        """Add multiple analysis errors to the report.

        Args:
            errors: List of analysis errors to add
        """
        self._errors.extend(errors)

    def set_errors(self, errors: list[AnalysisError]) -> None:
        """Set the analysis errors for the report.

        Args:
            errors: List of analysis errors
        """
        self._errors = errors

    def build(self) -> JSONDict:
        """Build the complete JSON report.

        Returns:
            Complete JSON report
        """
        if self._metrics is None:
            msg = "Metrics must be set before building report"
            raise ValueError(msg)

        return self.formatter.format_report(
            self._test_results, self._metrics, self._config, self._errors
        )

    def save(self, output_path: Path) -> None:
        """Build and save the report to a file.

        Args:
            output_path: Path to save the report
        """
        report = self.build()
        self.formatter.save_report(report, output_path)

    def to_string(self) -> str:
        """Build and return the report as a JSON string.

        Returns:
            JSON report string
        """
        report = self.build()
        return self.formatter.to_string(report)


# Global JSON formatter instance
json_formatter = JSONFormatter()
