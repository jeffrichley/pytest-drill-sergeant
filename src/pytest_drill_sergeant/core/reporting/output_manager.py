"""Unified output manager for coordinating all formatters.

This module provides a centralized output management system that coordinates
template-based messaging, Rich terminal output, JSON reports, and SARIF output.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.config import (
        DrillSergeantConfig as Config,
    )
    from pytest_drill_sergeant.core.models import Finding, ResultData, RunMetrics
    from pytest_drill_sergeant.core.reporting.types import JSONDict
from pytest_drill_sergeant.core.reporting.json_formatter import JSONReportBuilder
from pytest_drill_sergeant.core.reporting.sarif_formatter import SARIFReportBuilder
from pytest_drill_sergeant.core.reporting.templates import RichFormatter


class OutputManager:
    """Unified output manager for all formatting needs."""

    def __init__(self, config: Config) -> None:
        """Initialize the output manager.

        Args:
            config: Configuration for output formatting
        """
        self.config = config
        self.rich_formatter = RichFormatter()
        self.json_builder = JSONReportBuilder()
        self.sarif_builder = SARIFReportBuilder()

        # Track results for reporting
        self._test_results: list[ResultData] = []
        self._metrics: RunMetrics | None = None

    def add_test_result(self, result: ResultData) -> None:
        """Add a test result for reporting.

        Args:
            result: Test result to add
        """
        self._test_results.append(result)
        self.json_builder.add_test_result(result)
        self.sarif_builder.add_test_result(result)

    def add_test_results(self, results: list[ResultData]) -> None:
        """Add multiple test results for reporting.

        Args:
            results: List of test results to add
        """
        self._test_results.extend(results)
        self.json_builder.add_test_results(results)
        self.sarif_builder.add_test_results(results)

    def set_metrics(self, metrics: RunMetrics) -> None:
        """Set run metrics for reporting.

        Args:
            metrics: Run metrics
        """
        self._metrics = metrics
        self.json_builder.set_metrics(metrics)
        self.sarif_builder.set_metrics(metrics)

    def set_config(self, config_dict: JSONDict) -> None:
        """Set configuration for reporting.

        Args:
            config_dict: Configuration dictionary
        """
        self.json_builder.set_config(config_dict)
        self.sarif_builder.set_config(config_dict)

    def print_finding(self, finding: Finding) -> None:
        """Print a finding to the terminal.

        Args:
            finding: Finding to print
        """
        if "terminal" in self.config.output_formats:
            self.rich_formatter.print_finding(finding)

    def print_test_result(self, result: ResultData) -> None:
        """Print a test result to the terminal.

        Args:
            result: Test result to print
        """
        if "terminal" in self.config.output_formats:
            self.rich_formatter.print_test_result(result)

    def print_summary(self) -> None:
        """Print run summary to the terminal.

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before printing summary"
            raise ValueError(msg)

        if "terminal" in self.config.output_formats:
            self.rich_formatter.print_summary(self._metrics)

    def generate_json_report(self) -> str:
        """Generate JSON report.

        Returns:
            JSON report string

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before generating JSON report"
            raise ValueError(msg)

        return self.json_builder.to_string()

    def generate_sarif_report(self) -> str:
        """Generate SARIF report.

        Returns:
            SARIF report string

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before generating SARIF report"
            raise ValueError(msg)

        return self.sarif_builder.to_string()

    def save_json_report(self, output_path: Path | None = None) -> None:
        """Save JSON report to file.

        Args:
            output_path: Path to save report (uses config if None)

        Raises:
            ValueError: If metrics are not set or no output path specified
        """
        if self._metrics is None:
            msg = "Metrics must be set before saving JSON report"
            raise ValueError(msg)

        if output_path is None:
            path_str = self.config.json_report_path
            if path_str is not None:
                output_path = Path(path_str)

        if output_path is None:
            msg = "No output path specified for JSON report"
            raise ValueError(msg)

        self.json_builder.save(output_path)

    def save_sarif_report(self, output_path: Path | None = None) -> None:
        """Save SARIF report to file.

        Args:
            output_path: Path to save report (uses config if None)

        Raises:
            ValueError: If metrics are not set or no output path specified
        """
        if self._metrics is None:
            msg = "Metrics must be set before saving SARIF report"
            raise ValueError(msg)

        if output_path is None:
            path_str = self.config.sarif_report_path
            if path_str is not None:
                output_path = Path(path_str)

        if output_path is None:
            msg = "No output path specified for SARIF report"
            raise ValueError(msg)

        self.sarif_builder.save(output_path)

    def generate_all_outputs(self) -> dict[str, str]:
        """Generate all configured outputs.

        Returns:
            Dictionary of output format to content string

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before generating outputs"
            raise ValueError(msg)

        outputs = {}

        # Generate terminal output (already printed)
        if "terminal" in self.config.output_formats:
            outputs["terminal"] = "Printed to console"

        # Generate JSON output
        if self.config.json_report_path or "json" in self.config.output_formats:
            outputs["json"] = self.generate_json_report()

        # Generate SARIF output
        if self.config.sarif_report_path or "sarif" in self.config.output_formats:
            outputs["sarif"] = self.generate_sarif_report()

        return outputs

    def save_all_outputs(self) -> None:
        """Save all configured outputs to files.

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before saving outputs"
            raise ValueError(msg)

        # Save JSON report if configured
        if self.config.json_report_path:
            self.save_json_report()

        # Save SARIF report if configured
        if self.config.sarif_report_path:
            self.save_sarif_report()

    def get_summary_stats(
        self,
    ) -> dict[
        str, str | int | float | bool | list[str] | dict[str, str | int | float | bool]
    ]:
        """Get summary statistics for the current run.

        Returns:
            Summary statistics dictionary

        Raises:
            ValueError: If metrics are not set
        """
        if self._metrics is None:
            msg = "Metrics must be set before getting summary stats"
            raise ValueError(msg)

        return {
            "total_tests": self._metrics.total_tests,
            "analyzed_tests": self._metrics.analyzed_tests,
            "failed_analyses": self._metrics.failed_analyses,
            "total_findings": self._metrics.total_findings,
            "average_bis": self._metrics.average_bis,
            "brs_score": self._metrics.brs_score,
            "brs_grade": self._metrics.brs_grade,
            "findings_by_severity": {
                str(k): v for k, v in self._metrics.findings_by_severity.items()
            },
            "findings_by_rule": {
                str(k): v for k, v in self._metrics.findings_by_rule.items()
            },
        }

    def clear_results(self) -> None:
        """Clear all stored results and reset builders."""
        self._test_results.clear()
        self._metrics = None
        self.json_builder = JSONReportBuilder()
        self.sarif_builder = SARIFReportBuilder()
