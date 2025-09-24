"""Integration tests for error handling scenarios."""

import tempfile
from pathlib import Path

from pytest_drill_sergeant.core.analysis_pipeline import AnalysisPipeline
from pytest_drill_sergeant.core.config_validator_enhanced import (
    EnhancedConfigValidator,
    validate_config_file,
)
from pytest_drill_sergeant.core.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
)


class TestAnalysisPipelineErrorHandling:
    """Test error handling in the analysis pipeline."""

    def test_analyzer_failure_graceful_handling(self):
        """Test that analyzer failures are handled gracefully."""

        # Create a mock analyzer that fails
        class FailingAnalyzer:
            def analyze_file(self, file_path):
                raise RuntimeError("Analyzer failed")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(FailingAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Should have no findings but should have errors
        assert len(findings) == 0
        assert len(errors) == 1
        assert errors[0].category == ErrorCategory.UNKNOWN_ERROR
        assert errors[0].severity == ErrorSeverity.HIGH

    def test_multiple_analyzer_failures(self):
        """Test handling multiple analyzer failures."""

        # Create mock analyzers that fail
        class FailingAnalyzer1:
            def analyze_file(self, file_path):
                raise ValueError("Analyzer 1 failed")

        class FailingAnalyzer2:
            def analyze_file(self, file_path):
                raise RuntimeError("Analyzer 2 failed")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(FailingAnalyzer1())
        pipeline.add_analyzer(FailingAnalyzer2())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Should have no findings but should have 2 errors
        assert len(findings) == 0
        assert len(errors) == 2

        # Check error categories
        error_categories = {error.category for error in errors}
        assert ErrorCategory.VALIDATION_ERROR in error_categories
        assert ErrorCategory.UNKNOWN_ERROR in error_categories

    def test_mixed_success_and_failure(self):
        """Test mixed success and failure scenarios."""

        # Create one working and one failing analyzer
        class WorkingAnalyzer:
            def analyze_file(self, file_path):
                return []  # No findings

        class FailingAnalyzer:
            def analyze_file(self, file_path):
                raise RuntimeError("Analyzer failed")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(WorkingAnalyzer())
        pipeline.add_analyzer(FailingAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Should have no findings and 1 error
        assert len(findings) == 0
        assert len(errors) == 1
        assert errors[0].category == ErrorCategory.UNKNOWN_ERROR

    def test_error_recovery_with_retry(self):
        """Test error recovery with retry mechanism."""

        # Create an analyzer that fails then succeeds
        class RetryAnalyzer:
            def __init__(self):
                self.call_count = 0

            def analyze_file(self, file_path):
                self.call_count += 1
                if self.call_count < 3:
                    raise RuntimeError("Temporary failure")
                return []  # Success on third try

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(RetryAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Should succeed with no errors
        assert len(findings) == 0
        assert len(errors) == 0

    def test_error_summary_reporting(self):
        """Test error summary reporting."""

        # Create analyzers that fail with different error types
        class SyntaxErrorAnalyzer:
            def analyze_file(self, file_path):
                raise SyntaxError("Invalid syntax")

        class MemoryErrorAnalyzer:
            def analyze_file(self, file_path):
                raise MemoryError("Out of memory")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(SyntaxErrorAnalyzer())
        pipeline.add_analyzer(MemoryErrorAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Get error summary
        summary = pipeline.get_error_summary()

        assert summary["total_errors"] == 2
        assert summary["critical_errors"] == 1
        assert summary["recoverable_errors"] == 1
        assert "by_category" in summary
        assert "by_severity" in summary

    def test_error_context_preservation(self):
        """Test that error context is preserved correctly."""

        # Create an analyzer that fails with specific context
        class ContextFailingAnalyzer:
            def analyze_file(self, file_path):
                raise ValueError("Context test error")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(ContextFailingAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Check error context
        assert len(errors) == 1
        error = errors[0]
        assert error.context is not None
        assert error.context.file_path == test_file
        assert error.context.analyzer_name == "ContextFailingAnalyzer"
        assert error.context.function_name == "analyze_file"


class TestConfigurationValidationErrorHandling:
    """Test configuration validation error handling."""

    def test_invalid_configuration_validation(self):
        """Test validation of invalid configuration."""
        validator = EnhancedConfigValidator()

        # Test invalid configuration
        invalid_config = {
            "version": "1.0",
            "profiles": {
                "test": {
                    "fail_on": "invalid_severity",  # Invalid severity
                    "enable": 123,  # Should be string or list
                }
            },
            "rules": {
                "test_rule": {
                    "severity": "invalid",  # Invalid severity
                    "enabled": "yes",  # Should be boolean
                }
            },
        }

        errors = validator.validate_config(invalid_config)

        # Should have multiple validation errors
        assert len(errors) > 0

        # Check error categories
        error_categories = {error.category for error in errors}
        assert ErrorCategory.CONFIGURATION_ERROR in error_categories

        # Check error severities
        error_severities = {error.severity for error in errors}
        assert ErrorSeverity.HIGH in error_severities

    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        validator = EnhancedConfigValidator()

        # Test configuration missing required fields
        incomplete_config = {"profiles": {"test": {}}}

        errors = validator.validate_config(incomplete_config)

        # Should have validation errors
        assert len(errors) > 0

        # Check that errors mention missing fields
        error_messages = [error.message for error in errors]
        assert any("Missing required field" in msg for msg in error_messages)

    def test_invalid_file_paths(self):
        """Test validation of invalid file paths."""
        validator = EnhancedConfigValidator()

        # Test configuration with invalid paths
        invalid_paths_config = {
            "version": "1.0",
            "paths": ["/nonexistent/path", "another/invalid/path"],
        }

        errors = validator.validate_config(invalid_paths_config)

        # Should have validation errors for invalid paths
        assert len(errors) > 0

        # Check that errors mention path issues
        error_messages = [error.message for error in errors]
        assert any("Path does not exist" in msg for msg in error_messages)

    def test_configuration_validation_summary(self):
        """Test configuration validation summary."""
        validator = EnhancedConfigValidator()

        # Test configuration with multiple issues
        problematic_config = {
            "profiles": {
                "test": {
                    "fail_on": "invalid",
                    "enable": 123,
                }
            },
            "rules": {
                "test": {
                    "severity": "invalid",
                    "enabled": "yes",
                }
            },
        }

        errors = validator.validate_config(problematic_config)
        summary = validator.get_validation_summary()

        assert summary["total_errors"] > 0
        assert "by_field" in summary
        assert "by_severity" in summary
        assert summary["critical_errors"] >= 0

    def test_config_file_validation(self):
        """Test validation of configuration files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write invalid JSON (missing closing brace)
            f.write('{"version": "1.0", "profiles": {}')
            f.flush()

            config_path = Path(f.name)

            try:
                errors = validate_config_file(config_path)

                # Should have validation errors
                assert len(errors) > 0

                # Check error categories
                error_categories = {error.category for error in errors}
                assert ErrorCategory.CONFIGURATION_ERROR in error_categories

            finally:
                config_path.unlink()

    def test_config_file_not_found(self):
        """Test validation of non-existent configuration file."""
        non_existent_path = Path("/nonexistent/config.json")

        errors = validate_config_file(non_existent_path)

        # Should have file access error
        assert len(errors) == 1
        error = errors[0]
        assert error.category == ErrorCategory.CONFIGURATION_ERROR
        assert error.severity == ErrorSeverity.CRITICAL
        assert "Failed to load configuration file" in error.message


class TestErrorReportingIntegration:
    """Test error reporting integration."""

    def test_error_reporting_in_json_format(self):
        """Test error reporting in JSON format."""
        from pytest_drill_sergeant.core.reporting.json_formatter import JSONFormatter

        # Create some test errors
        error_handler = ErrorHandler()
        error1 = error_handler.handle_error(SyntaxError("syntax error"))
        error2 = error_handler.handle_error(ValueError("value error"))

        # Create JSON formatter
        formatter = JSONFormatter()

        # Format errors
        error1_json = formatter.format_analysis_error(error1)
        error2_json = formatter.format_analysis_error(error2)

        # Check JSON structure
        assert "error_id" in error1_json
        assert "category" in error1_json
        assert "severity" in error1_json
        assert "message" in error1_json
        assert "suggestion" in error1_json
        assert "context" in error1_json

        # Check error values
        assert error1_json["category"] == "syntax_error"
        assert error1_json["severity"] == "high"
        assert error1_json["message"] == "syntax error"

    def test_error_reporting_in_report(self):
        """Test error reporting in complete report."""
        from pytest_drill_sergeant.core.models import RunMetrics
        from pytest_drill_sergeant.core.reporting.json_formatter import JSONFormatter

        # Create test errors
        error_handler = ErrorHandler()
        error1 = error_handler.handle_error(SyntaxError("syntax error"))
        error2 = error_handler.handle_error(ValueError("value error"))
        errors = [error1, error2]

        # Create mock metrics
        metrics = RunMetrics(
            total_tests=10,
            analyzed_tests=8,
            failed_analyses=2,
            total_findings=5,
            findings_by_severity={},
            findings_by_rule={},
            average_bis=75.0,
            brs_score=80.0,
            brs_grade="B",
            aaa_compliance_rate=0.8,
            duplicate_test_rate=0.1,
            parametrization_rate=0.3,
            fixture_reuse_rate=0.7,
            total_analysis_time=10.0,
            average_test_time=1.0,
            memory_peak=100.0,
        )

        # Create JSON formatter and format report
        formatter = JSONFormatter()
        report = formatter.format_report([], metrics, {}, errors)

        # Check that errors are included in report
        assert "errors" in report
        assert report["errors"]["total_errors"] == 2
        assert len(report["errors"]["errors"]) == 2
        assert "error_summary" in report["errors"]
        assert "by_category" in report["errors"]["error_summary"]
        assert "by_severity" in report["errors"]["error_summary"]

    def test_error_statistics_in_report(self):
        """Test error statistics in report."""
        from pytest_drill_sergeant.core.models import RunMetrics
        from pytest_drill_sergeant.core.reporting.json_formatter import JSONFormatter

        # Create test errors of different types
        error_handler = ErrorHandler()
        syntax_error = error_handler.handle_error(SyntaxError("syntax error"))
        memory_error = error_handler.handle_error(MemoryError("memory error"))
        value_error = error_handler.handle_error(ValueError("value error"))
        errors = [syntax_error, memory_error, value_error]

        # Create mock metrics
        metrics = RunMetrics(
            total_tests=10,
            analyzed_tests=7,
            failed_analyses=3,
            total_findings=5,
            findings_by_severity={},
            findings_by_rule={},
            average_bis=75.0,
            brs_score=80.0,
            brs_grade="B",
            aaa_compliance_rate=0.8,
            duplicate_test_rate=0.1,
            parametrization_rate=0.3,
            fixture_reuse_rate=0.7,
            total_analysis_time=10.0,
            average_test_time=1.0,
            memory_peak=100.0,
        )

        # Create JSON formatter and format report
        formatter = JSONFormatter()
        report = formatter.format_report([], metrics, {}, errors)

        # Check error statistics
        error_summary = report["errors"]["error_summary"]

        # Check category breakdown
        by_category = error_summary["by_category"]
        assert by_category["syntax_error"] == 1
        assert by_category["memory_error"] == 1
        assert by_category["validation_error"] == 1

        # Check severity breakdown
        by_severity = error_summary["by_severity"]
        assert by_severity["high"] == 1  # syntax error
        assert by_severity["critical"] == 1  # memory error
        assert by_severity["medium"] == 1  # value error


class TestErrorHandlingEndToEnd:
    """Test end-to-end error handling scenarios."""

    def test_complete_analysis_with_errors(self):
        """Test complete analysis workflow with errors."""

        # Create a pipeline with mixed analyzers
        class WorkingAnalyzer:
            def analyze_file(self, file_path):
                return []  # No findings

        class FailingAnalyzer:
            def analyze_file(self, file_path):
                raise RuntimeError("Analyzer failed")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(WorkingAnalyzer())
        pipeline.add_analyzer(FailingAnalyzer())

        # Analyze multiple files
        test_files = [Path("test1.py"), Path("test2.py")]
        findings_by_file, errors_by_file = pipeline.analyze_files(test_files)

        # Check results
        assert len(findings_by_file) == 2
        assert len(errors_by_file) == 2  # Both files should have errors

        # Check that each file has errors from the failing analyzer
        for file_path, errors in errors_by_file.items():
            assert len(errors) == 1
            assert errors[0].category == ErrorCategory.UNKNOWN_ERROR

    def test_error_recovery_across_multiple_files(self):
        """Test error recovery across multiple files."""

        # Create an analyzer that fails on some files but succeeds on others
        class SelectiveFailingAnalyzer:
            def __init__(self):
                self.fail_count = 0

            def analyze_file(self, file_path):
                self.fail_count += 1
                if self.fail_count <= 2:  # Fail on first two files
                    raise RuntimeError("Temporary failure")
                return []  # Succeed on remaining files

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(SelectiveFailingAnalyzer())

        # Analyze multiple files
        test_files = [Path("test1.py"), Path("test2.py"), Path("test3.py")]
        findings_by_file, errors_by_file = pipeline.analyze_files(test_files)

        # Check results
        assert len(findings_by_file) == 3
        # The retry mechanism should eventually succeed on all files
        # because the analyzer succeeds on the third call
        assert len(errors_by_file) == 0  # All files should succeed after retries

        # Check that all files have empty findings (successful analysis)
        for file_path in test_files:
            assert file_path in findings_by_file
            assert len(findings_by_file[file_path]) == 0

    def test_error_aggregation_and_reporting(self):
        """Test error aggregation and reporting."""

        # Create analyzers with different failure patterns
        class SyntaxErrorAnalyzer:
            def analyze_file(self, file_path):
                raise SyntaxError("Invalid syntax")

        class MemoryErrorAnalyzer:
            def analyze_file(self, file_path):
                raise MemoryError("Out of memory")

        # Create pipeline with error handling
        error_handler = ErrorHandler()
        pipeline = AnalysisPipeline(error_handler=error_handler)
        pipeline.add_analyzer(SyntaxErrorAnalyzer())
        pipeline.add_analyzer(MemoryErrorAnalyzer())

        # Analyze a test file
        test_file = Path("test_file.py")
        findings, errors = pipeline.analyze_file(test_file)

        # Get error summary
        summary = pipeline.get_error_summary()

        # Check summary structure
        assert "total_errors" in summary
        assert "by_category" in summary
        assert "by_severity" in summary
        assert "recoverable_errors" in summary
        assert "critical_errors" in summary

        # Check summary values
        assert summary["total_errors"] == 2
        assert summary["critical_errors"] == 1
        assert summary["recoverable_errors"] == 1

        # Check category breakdown
        by_category = summary["by_category"]
        assert by_category["syntax_error"] == 1
        assert by_category["memory_error"] == 1

        # Check severity breakdown
        by_severity = summary["by_severity"]
        assert by_severity["high"] == 1  # syntax error
        assert by_severity["critical"] == 1  # memory error
