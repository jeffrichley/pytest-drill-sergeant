"""Tests for coverage configuration options in CLI test command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import typer
from typer.testing import CliRunner

from pytest_drill_sergeant.cli.main import app, _load_coverage_config, _process_coverage_analysis, _generate_coverage_report, _write_coverage_report


class TestCoverageConfigLoading:
    """Test coverage configuration file loading."""

    def test_load_json_config(self):
        """Test loading JSON configuration file."""
        config_data = {
            "threshold": 80.0,
            "output": "report.json",
            "format": "json"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = _load_coverage_config(config_file)
            assert result == config_data
        finally:
            Path(config_file).unlink()

    def test_load_yaml_config(self):
        """Test loading YAML configuration file."""
        config_data = {
            "threshold": 75.0,
            "output": "report.yaml",
            "format": "html"
        }
        
        yaml_content = """
threshold: 75.0
output: report.yaml
format: html
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_file = f.name
        
        try:
            result = _load_coverage_config(config_file)
            assert result == config_data
        finally:
            Path(config_file).unlink()

    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration file."""
        result = _load_coverage_config("nonexistent.json")
        assert result == {}

    def test_load_invalid_json_config(self):
        """Test loading invalid JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            config_file = f.name
        
        try:
            result = _load_coverage_config(config_file)
            assert result == {}
        finally:
            Path(config_file).unlink()

    def test_load_unsupported_format(self):
        """Test loading unsupported configuration file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text")
            config_file = f.name
        
        try:
            result = _load_coverage_config(config_file)
            assert result == {}
        finally:
            Path(config_file).unlink()


class TestCoverageReportGeneration:
    """Test coverage report generation."""

    def test_generate_text_report(self):
        """Test generating text format report."""
        config = {
            "threshold": 60.0,
            "format": "text"
        }
        
        report = _generate_coverage_report(config, False)
        
        assert "Coverage Analysis Report" in report
        assert "Threshold: 60.0" in report
        assert "Status: Analysis completed successfully" in report

    def test_generate_json_report(self):
        """Test generating JSON format report."""
        config = {
            "threshold": 70.0,
            "format": "json"
        }
        
        report = _generate_coverage_report(config, False)
        
        # Parse JSON to verify it's valid
        report_data = json.loads(report)
        assert "coverage_analysis" in report_data
        assert report_data["coverage_analysis"]["threshold"] == 70.0
        assert report_data["coverage_analysis"]["summary"] == "Coverage analysis completed"

    def test_generate_html_report(self):
        """Test generating HTML format report."""
        config = {
            "threshold": 80.0,
            "format": "html"
        }
        
        report = _generate_coverage_report(config, False)
        
        assert "<html>" in report
        assert "<title>Coverage Analysis Report</title>" in report
        assert "<h1>Coverage Analysis Report</h1>" in report
        assert "Threshold: 80.0" in report

    def test_generate_report_with_default_format(self):
        """Test generating report with default format (text)."""
        config = {
            "threshold": 50.0
        }
        
        report = _generate_coverage_report(config, False)
        
        assert "Coverage Analysis Report" in report
        assert "Threshold: 50.0" in report


class TestCoverageReportWriting:
    """Test coverage report writing to files."""

    def test_write_report_to_file(self):
        """Test writing report to file."""
        report_content = "Test coverage report content"
        output_file = "test_report.txt"
        
        try:
            _write_coverage_report(report_content, output_file, "text")
            
            assert Path(output_file).exists()
            with open(output_file, 'r') as f:
                content = f.read()
            assert content == report_content
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()

    def test_write_report_to_nested_directory(self):
        """Test writing report to nested directory."""
        report_content = "Test coverage report content"
        output_file = "reports/coverage/test_report.json"
        
        try:
            _write_coverage_report(report_content, output_file, "json")
            
            assert Path(output_file).exists()
            with open(output_file, 'r') as f:
                content = f.read()
            assert content == report_content
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


class TestCoverageAnalysisProcessing:
    """Test coverage analysis processing."""

    @patch('pytest_drill_sergeant.cli.main.typer.echo')
    def test_process_coverage_analysis_success(self, mock_echo):
        """Test successful coverage analysis processing."""
        config = {
            "threshold": 65.0,
            "output": "test_report.json",
            "format": "json"
        }
        
        _process_coverage_analysis(config, True)
        
        # Verify that echo was called with expected messages
        mock_echo.assert_called()
        calls = [call.args[0] for call in mock_echo.call_args_list]
        
        assert any("Coverage Analysis Results:" in call for call in calls)
        assert any("Threshold: 65.0" in call for call in calls)
        assert any("Output: test_report.json" in call for call in calls)
        assert any("Format: json" in call for call in calls)

    @patch('pytest_drill_sergeant.cli.main.typer.echo')
    def test_process_coverage_analysis_with_exception(self, mock_echo):
        """Test coverage analysis processing with exception."""
        config = {
            "threshold": 70.0,
            "output": None,
            "format": "text"
        }
        
        # Mock the import to raise an exception
        with patch('builtins.__import__', side_effect=ImportError("Test error")):
            _process_coverage_analysis(config, False)
        
        # Verify error message was echoed
        mock_echo.assert_called()
        calls = [call.args[0] for call in mock_echo.call_args_list]
        assert any("Failed to process coverage analysis" in call for call in calls)


class TestCLICoverageOptions:
    """Test CLI coverage configuration options."""

    @patch('subprocess.run')
    def test_ds_coverage_threshold_option(self, mock_run):
        """Test --ds-coverage-threshold option."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, [
            "test", 
            "tests/unit/test_gitignore_fixes.py",
            "--coverage",
            "--ds-coverage-threshold=85.0"
        ])
        
        assert result.exit_code == 0
        assert "Running tests with coverage analysis" in result.output

    @patch('subprocess.run')
    def test_ds_coverage_output_option(self, mock_run):
        """Test --ds-coverage-output option."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, [
            "test", 
            "tests/unit/test_gitignore_fixes.py",
            "--coverage",
            "--ds-coverage-output=custom_report.json"
        ])
        
        assert result.exit_code == 0
        assert "Running tests with coverage analysis" in result.output

    @patch('subprocess.run')
    def test_ds_coverage_format_option(self, mock_run):
        """Test --ds-coverage-format option."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, [
            "test", 
            "tests/unit/test_gitignore_fixes.py",
            "--coverage",
            "--ds-coverage-format=html"
        ])
        
        assert result.exit_code == 0
        assert "Running tests with coverage analysis" in result.output

    @patch('subprocess.run')
    def test_config_file_option(self, mock_run):
        """Test --config option."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        # Create a temporary config file
        config_data = {
            "threshold": 90.0,
            "output": "config_report.json",
            "format": "json"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = runner.invoke(app, [
                "test", 
                "tests/unit/test_gitignore_fixes.py",
                "--coverage",
                f"--config={config_file}"
            ])
            
            assert result.exit_code == 0
            assert "Running tests with coverage analysis" in result.output
        finally:
            Path(config_file).unlink()

    @patch('subprocess.run')
    def test_all_coverage_options_together(self, mock_run):
        """Test all coverage options used together."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, [
            "test", 
            "tests/unit/test_gitignore_fixes.py",
            "--coverage",
            "--ds-coverage-threshold=95.0",
            "--ds-coverage-output=comprehensive_report.html",
            "--ds-coverage-format=html",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert "Running tests with coverage analysis" in result.output
        assert "--cov=src" in result.output  # Verify pytest-cov is enabled

    @patch('subprocess.run')
    def test_coverage_options_without_coverage_flag(self, mock_run):
        """Test that coverage options are ignored when --coverage is not used."""
        runner = CliRunner()
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, [
            "test", 
            "tests/unit/test_gitignore_fixes.py",
            "--ds-coverage-threshold=50.0",
            "--ds-coverage-output=report.json",
            "--ds-coverage-format=json"
        ])
        
        assert result.exit_code == 0
        assert "Running tests..." in result.output  # Should not show coverage analysis
        assert "--cov=src" not in result.output  # pytest-cov should not be enabled

    def test_help_shows_coverage_options(self):
        """Test that help shows all coverage options."""
        runner = CliRunner()
        
        result = runner.invoke(app, ["test", "--help"])
        
        assert result.exit_code == 0
        assert "--ds-coverage-threshold" in result.output
        assert "--ds-coverage-output" in result.output
        assert "--ds-coverage-format" in result.output
        assert "--config" in result.output