"""Simplified tests for the output manager.

This module provides focused tests for the OutputManager class,
covering the core functionality that works with the actual models.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pytest_drill_sergeant.core.config import DrillSergeantConfig
from pytest_drill_sergeant.core.models import (
    FeaturesData,
    Finding,
    ResultData,
    RuleType,
    RunMetrics,
    Severity,
)
from pytest_drill_sergeant.core.reporting.output_manager import OutputManager

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.reporting.types import JSONDict

# Test constants to avoid magic numbers
EXPECTED_RESULTS_COUNT = 2


class TestOutputManagerInitialization:
    """Test OutputManager initialization."""

    def test_output_manager_initialization(self) -> None:
        """Test basic OutputManager initialization."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        assert manager.config is config
        assert manager.rich_formatter is not None
        assert manager.json_builder is not None
        assert manager.sarif_builder is not None
        assert manager._test_results == []
        assert manager._metrics is None

    def test_output_manager_initialization_with_custom_config(self) -> None:
        """Test OutputManager initialization with custom config."""
        config = DrillSergeantConfig(
            output_formats=["terminal", "json"],
            json_report_path="test_report.json",
            sarif_report_path="test_report.sarif",
        )
        manager = OutputManager(config)

        assert manager.config is config
        assert "terminal" in manager.config.output_formats
        assert "json" in manager.config.output_formats


class TestTestResultManagement:
    """Test test result management functionality."""

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

    def test_add_single_test_result(self) -> None:
        """Test adding a single test result."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        result = self._create_test_result()

        manager.add_test_result(result)

        assert len(manager._test_results) == 1
        assert manager._test_results[0] is result

    def test_add_multiple_test_results(self) -> None:
        """Test adding multiple test results."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        results = [
            self._create_test_result("test_example_1"),
            self._create_test_result("test_example_2"),
        ]

        manager.add_test_results(results)

        assert len(manager._test_results) == EXPECTED_RESULTS_COUNT
        assert manager._test_results[0] is results[0]
        assert manager._test_results[1] is results[1]

    def test_add_test_results_empty_list(self) -> None:
        """Test adding empty list of test results."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        manager.add_test_results([])

        assert len(manager._test_results) == 0

    def test_clear_results(self) -> None:
        """Test clearing all test results."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        results = [
            self._create_test_result("test_1"),
            self._create_test_result("test_2"),
        ]

        manager.add_test_results(results)
        assert len(manager._test_results) == EXPECTED_RESULTS_COUNT

        manager.clear_results()
        assert len(manager._test_results) == 0


class TestMetricsManagement:
    """Test metrics management functionality."""

    def test_set_metrics(self) -> None:
        """Test setting run metrics."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

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
        )

        manager.set_metrics(metrics)

        assert manager._metrics is metrics

    def test_set_metrics_twice(self) -> None:
        """Test setting metrics twice (should overwrite)."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics1 = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        metrics2 = RunMetrics(
            total_tests=10,
            analyzed_tests=8,
            failed_analyses=2,
            total_findings=5,
            findings_by_severity={Severity.WARNING: 3, Severity.ERROR: 2},
            findings_by_rule={RuleType.MOCK_OVERSPECIFICATION: 5},
        )

        manager.set_metrics(metrics1)
        assert manager._metrics is metrics1

        manager.set_metrics(metrics2)
        assert manager._metrics is metrics2


class TestTerminalOutput:
    """Test terminal output functionality."""

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

    def test_print_finding_with_terminal_format(self) -> None:
        """Test printing finding when terminal format is enabled."""
        config = DrillSergeantConfig(output_formats=["terminal"])
        manager = OutputManager(config)

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=10,
            column_number=5,
        )

        with patch.object(manager.rich_formatter, "print_finding") as mock_print:
            manager.print_finding(finding)
            mock_print.assert_called_once_with(finding)

    def test_print_finding_without_terminal_format(self) -> None:
        """Test printing finding when terminal format is disabled."""
        config = DrillSergeantConfig(output_formats=["json"])
        manager = OutputManager(config)

        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test_file.py"),
            line_number=10,
            column_number=5,
        )

        with patch.object(manager.rich_formatter, "print_finding") as mock_print:
            manager.print_finding(finding)
            mock_print.assert_not_called()

    def test_print_test_result_with_terminal_format(self) -> None:
        """Test printing test result when terminal format is enabled."""
        config = DrillSergeantConfig(output_formats=["terminal"])
        manager = OutputManager(config)

        result = self._create_test_result()

        with patch.object(manager.rich_formatter, "print_test_result") as mock_print:
            manager.print_test_result(result)
            mock_print.assert_called_once_with(result)

    def test_print_test_result_without_terminal_format(self) -> None:
        """Test printing test result when terminal format is disabled."""
        config = DrillSergeantConfig(output_formats=["json"])
        manager = OutputManager(config)

        result = self._create_test_result()

        with patch.object(manager.rich_formatter, "print_test_result") as mock_print:
            manager.print_test_result(result)
            mock_print.assert_not_called()

    def test_print_summary_with_terminal_format(self) -> None:
        """Test printing summary when terminal format is enabled."""
        config = DrillSergeantConfig(output_formats=["terminal"])
        manager = OutputManager(config)

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
        )

        manager.set_metrics(metrics)

        with patch.object(manager.rich_formatter, "print_summary") as mock_print:
            manager.print_summary()
            mock_print.assert_called_once_with(metrics)

    def test_print_summary_without_terminal_format(self) -> None:
        """Test printing summary when terminal format is disabled."""
        config = DrillSergeantConfig(output_formats=["json"])
        manager = OutputManager(config)

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
        )

        manager.set_metrics(metrics)

        with patch.object(manager.rich_formatter, "print_summary") as mock_print:
            manager.print_summary()
            mock_print.assert_not_called()

    def test_print_summary_without_metrics(self) -> None:
        """Test printing summary without metrics set."""
        config = DrillSergeantConfig(output_formats=["terminal"])
        manager = OutputManager(config)

        with pytest.raises(
            ValueError, match="Metrics must be set before printing summary"
        ) as exc_info:
            manager.print_summary()
        assert "Metrics must be set before printing summary" in str(exc_info.value)


class TestReportGeneration:
    """Test report generation functionality."""

    def test_generate_json_report(self) -> None:
        """Test generating JSON report."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with patch.object(manager.json_builder, "to_string") as mock_to_string:
            mock_to_string.return_value = '{"test": "report"}'
            result = manager.generate_json_report()

            assert result == '{"test": "report"}'
            mock_to_string.assert_called_once()

    def test_generate_json_report_without_metrics(self) -> None:
        """Test generating JSON report without metrics set."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        with pytest.raises(
            ValueError, match="Metrics must be set before generating JSON report"
        ) as exc_info:
            manager.generate_json_report()
        assert "Metrics must be set before generating JSON report" in str(
            exc_info.value
        )

    def test_generate_sarif_report(self) -> None:
        """Test generating SARIF report."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with patch.object(manager.sarif_builder, "to_string") as mock_to_string:
            mock_to_string.return_value = '{"$schema": "sarif"}'
            result = manager.generate_sarif_report()

            assert result == '{"$schema": "sarif"}'
            mock_to_string.assert_called_once()

    def test_generate_sarif_report_without_metrics(self) -> None:
        """Test generating SARIF report without metrics set."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        with pytest.raises(
            ValueError, match="Metrics must be set before generating SARIF report"
        ) as exc_info:
            manager.generate_sarif_report()
        assert "Metrics must be set before generating SARIF report" in str(
            exc_info.value
        )

    def test_generate_all_outputs(self) -> None:
        """Test generating all configured outputs."""
        config = DrillSergeantConfig(output_formats=["json", "sarif"])
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with (
            patch.object(manager.json_builder, "to_string") as mock_json,
            patch.object(manager.sarif_builder, "to_string") as mock_sarif,
        ):
            mock_json.return_value = '{"test": "json"}'
            mock_sarif.return_value = '{"$schema": "sarif"}'

            result = manager.generate_all_outputs()

            assert result == {
                "json": '{"test": "json"}',
                "sarif": '{"$schema": "sarif"}',
            }
            mock_json.assert_called_once()
            mock_sarif.assert_called_once()

    def test_generate_all_outputs_without_metrics(self) -> None:
        """Test generating all outputs without metrics set."""
        config = DrillSergeantConfig(output_formats=["json", "sarif"])
        manager = OutputManager(config)

        with pytest.raises(
            ValueError, match="Metrics must be set before generating outputs"
        ) as exc_info:
            manager.generate_all_outputs()
        assert "Metrics must be set before generating outputs" in str(exc_info.value)

    def test_generate_all_outputs_empty_formats(self) -> None:
        """Test generating all outputs with empty formats."""
        config = DrillSergeantConfig(output_formats=[])
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        result = manager.generate_all_outputs()
        assert result == {}


class TestReportSaving:
    """Test report saving functionality."""

    def test_save_json_report_with_path(self, tmp_path: Path) -> None:
        """Test saving JSON report with explicit path."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        output_path = tmp_path / "test_report.json"

        with patch.object(manager.json_builder, "save") as mock_save:
            manager.save_json_report(output_path)
            mock_save.assert_called_once_with(output_path)

    def test_save_json_report_with_config_path(self) -> None:
        """Test saving JSON report with config path."""
        config = DrillSergeantConfig(json_report_path="config_report.json")
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with patch.object(manager.json_builder, "save") as mock_save:
            manager.save_json_report()
            mock_save.assert_called_once_with(Path("config_report.json"))

    def test_save_json_report_without_path(self) -> None:
        """Test saving JSON report without path specified."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with pytest.raises(
            ValueError, match="No output path specified for JSON report"
        ) as exc_info:
            manager.save_json_report()
        assert "No output path specified for JSON report" in str(exc_info.value)

    def test_save_json_report_without_metrics(self) -> None:
        """Test saving JSON report without metrics set."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        output_path = Path("test_report.json")

        with pytest.raises(
            ValueError, match="Metrics must be set before saving JSON report"
        ) as exc_info:
            manager.save_json_report(output_path)
        assert "Metrics must be set before saving JSON report" in str(exc_info.value)

    def test_save_sarif_report_with_path(self, tmp_path: Path) -> None:
        """Test saving SARIF report with explicit path."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        output_path = tmp_path / "test_report.sarif"

        with patch.object(manager.sarif_builder, "save") as mock_save:
            manager.save_sarif_report(output_path)
            mock_save.assert_called_once_with(output_path)

    def test_save_sarif_report_with_config_path(self) -> None:
        """Test saving SARIF report with config path."""
        config = DrillSergeantConfig(sarif_report_path="config_report.sarif")
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with patch.object(manager.sarif_builder, "save") as mock_save:
            manager.save_sarif_report()
            mock_save.assert_called_once_with(Path("config_report.sarif"))

    def test_save_sarif_report_without_path(self) -> None:
        """Test saving SARIF report without path specified."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        metrics = RunMetrics(
            total_tests=5,
            analyzed_tests=4,
            failed_analyses=1,
            total_findings=2,
            findings_by_severity={Severity.WARNING: 2},
            findings_by_rule={RuleType.PRIVATE_ACCESS: 2},
        )

        manager.set_metrics(metrics)

        with pytest.raises(
            ValueError, match="No output path specified for SARIF report"
        ) as exc_info:
            manager.save_sarif_report()
        assert "No output path specified for SARIF report" in str(exc_info.value)

    def test_save_sarif_report_without_metrics(self) -> None:
        """Test saving SARIF report without metrics set."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        output_path = Path("test_report.sarif")

        with pytest.raises(
            ValueError, match="Metrics must be set before saving SARIF report"
        ) as exc_info:
            manager.save_sarif_report(output_path)
        assert "Metrics must be set before saving SARIF report" in str(exc_info.value)


class TestIntegrationScenarios:
    """Test integration scenarios."""

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

    def test_full_workflow(self, tmp_path: Path) -> None:  # noqa: ARG002
        """Test full workflow from initialization to report generation."""
        config = DrillSergeantConfig(
            output_formats=["terminal", "json", "sarif"],
            json_report_path="workflow_report.json",
            sarif_report_path="workflow_report.sarif",
        )
        manager = OutputManager(config)

        # Add test results
        results = [
            self._create_test_result("test_example_1"),
            self._create_test_result("test_example_2"),
        ]

        manager.add_test_results(results)

        # Set metrics
        metrics = RunMetrics(
            total_tests=2,
            analyzed_tests=2,
            failed_analyses=0,
            total_findings=0,
            findings_by_severity={},
            findings_by_rule={},
        )

        manager.set_metrics(metrics)

        # Set configuration
        config_dict: JSONDict = {
            "threshold": 0.8,
            "enabled_rules": ["private_access"],
            "strict_mode": True,
        }

        manager.set_config(config_dict)

        # Print findings and results
        with (
            patch.object(
                manager.rich_formatter, "print_test_result"
            ) as mock_print_result,
            patch.object(manager.rich_formatter, "print_summary") as mock_print_summary,
        ):
            for result in results:
                manager.print_test_result(result)

            manager.print_summary()

            assert mock_print_result.call_count == EXPECTED_RESULTS_COUNT
            mock_print_summary.assert_called_once_with(metrics)

        # Generate reports
        with (
            patch.object(manager.json_builder, "to_string") as mock_json,
            patch.object(manager.sarif_builder, "to_string") as mock_sarif,
        ):
            mock_json.return_value = '{"workflow": "json"}'
            mock_sarif.return_value = '{"$schema": "sarif"}'

            json_report = manager.generate_json_report()
            sarif_report = manager.generate_sarif_report()
            all_outputs = manager.generate_all_outputs()

            assert json_report == '{"workflow": "json"}'
            assert sarif_report == '{"$schema": "sarif"}'
            assert all_outputs == {
                "json": '{"workflow": "json"}',
                "sarif": '{"$schema": "sarif"}',
                "terminal": "Printed to console",
            }

        # Save reports
        with (
            patch.object(manager.json_builder, "save") as mock_json_save,
            patch.object(manager.sarif_builder, "save") as mock_sarif_save,
        ):
            manager.save_json_report()
            manager.save_sarif_report()

            mock_json_save.assert_called_once_with(Path("workflow_report.json"))
            mock_sarif_save.assert_called_once_with(Path("workflow_report.sarif"))

        # Verify final state
        assert len(manager._test_results) == EXPECTED_RESULTS_COUNT
        assert manager._metrics is metrics

    def test_error_recovery(self) -> None:
        """Test error recovery scenarios."""
        config = DrillSergeantConfig()
        manager = OutputManager(config)

        # Test that operations fail gracefully when metrics are not set
        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.print_summary()

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.generate_json_report()

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.generate_sarif_report()

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.generate_all_outputs()

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.save_json_report(Path("test.json"))

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.save_sarif_report(Path("test.sarif"))

        # Test that operations work after metrics are set
        metrics = RunMetrics(
            total_tests=1,
            analyzed_tests=1,
            failed_analyses=0,
            total_findings=0,
            findings_by_severity={},
            findings_by_rule={},
        )

        manager.set_metrics(metrics)

        # These should now work
        with patch.object(manager.rich_formatter, "print_summary"):
            manager.print_summary()

        with patch.object(manager.json_builder, "to_string") as mock_json:
            mock_json.return_value = '{"test": "report"}'
            manager.generate_json_report()

        with patch.object(manager.sarif_builder, "to_string") as mock_sarif:
            mock_sarif.return_value = '{"$schema": "sarif"}'
            manager.generate_sarif_report()
