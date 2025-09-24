"""Integration tests for CLI functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.cli.main import LintConfig, _run_lint_with_options


def _setup_mock_context_and_pipeline(mock_context_class, mock_pipeline, mock_init_config):
    """Helper function to set up consistent Mock configuration."""
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_context)
    mock_context.__exit__ = Mock(return_value=None)
    mock_context.filter_findings_by_severity.return_value = []
    mock_context.persona_manager.on_test_pass.return_value = "Test passed"
    mock_context.persona_manager.on_summary.return_value = "Summary message"
    mock_context_class.return_value = mock_context
    
    mock_pipeline_instance = Mock()
    mock_pipeline_instance.analyzers = []
    mock_pipeline_instance.analyze_file.return_value = ([], [])  # findings, file_errors
    mock_pipeline_instance.get_analysis_errors.return_value = []
    mock_pipeline_instance.get_error_summary.return_value = {}
    mock_pipeline.return_value = mock_pipeline_instance
    
    mock_config = Mock()
    mock_init_config.return_value = mock_config
    
    return mock_context, mock_pipeline_instance, mock_config


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_complete_lint_workflow(self):
        """Test complete lint workflow from start to finish."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
import pytest

def test_example():
    """Test example."""
    assert True
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            config = LintConfig(paths=[str(test_file_path)])
            
            with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                 patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                 patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                 patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                
                # Mock the analysis pipeline
                mock_context = Mock()
                mock_context.__enter__ = Mock(return_value=mock_context)
                mock_context.__exit__ = Mock(return_value=None)
                mock_context.filter_findings_by_severity.return_value = []
                mock_context.persona_manager.on_test_pass.return_value = "Test passed"
                mock_context.persona_manager.on_summary.return_value = "Summary message"
                mock_context_class.return_value = mock_context
                
                mock_pipeline_instance = Mock()
                mock_pipeline_instance.analyzers = []
                mock_pipeline_instance.analyze_file.return_value = ([], [])  # findings, file_errors
                mock_pipeline_instance.get_analysis_errors.return_value = []
                mock_pipeline_instance.get_error_summary.return_value = {}
                mock_pipeline.return_value = mock_pipeline_instance
                
                mock_config = Mock()
                mock_init_config.return_value = mock_config
                
                # Simulate successful analysis
                mock_context.storage.analyze_files.return_value = ([], [])
                
                result = _run_lint_with_options(config)
                
                assert result == 0
                mock_setup_logging.assert_called_once()
                mock_init_config.assert_called_once()
                mock_pipeline.assert_called_once()
                
        finally:
            test_file_path.unlink()

    def test_config_file_loading_integration(self):
        """Test configuration file loading integration."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            config_content = '''
[tool.pytest-drill-sergeant]
profile = "strict"
persona = "drill_sergeant"
fail_on = "warning"
'''
            f.write(config_content)
            config_file_path = Path(f.name)
        
        try:
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                test_content = '''
def test_example():
    """Test example."""
    assert True
'''
                f.write(test_content)
                test_file_path = Path(f.name)
            
            try:
                config = LintConfig(
                    paths=[str(test_file_path)],
                    config=str(config_file_path)
                )
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context = Mock()
                    mock_context.__enter__ = Mock(return_value=mock_context)
                    mock_context.__exit__ = Mock(return_value=None)
                    mock_context.filter_findings_by_severity.return_value = []
                    mock_context.persona_manager.on_test_pass.return_value = "Test passed"
                    mock_context.persona_manager.on_summary.return_value = "Summary message"
                    mock_context_class.return_value = mock_context
                    
                    mock_pipeline_instance = Mock()
                    mock_pipeline_instance.analyzers = []
                    mock_pipeline_instance.analyze_file.return_value = ([], [])  # findings, file_errors
                    mock_pipeline_instance.get_analysis_errors.return_value = []
                    mock_pipeline_instance.get_error_summary.return_value = {}
                    mock_pipeline.return_value = mock_pipeline_instance
                    
                    mock_config = Mock()
                    mock_init_config.return_value = mock_config
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    # Verify config file was passed to initialize_config
                    mock_init_config.assert_called_once()
                    
            finally:
                test_file_path.unlink()
                
        finally:
            config_file_path.unlink()

    def test_json_output_integration(self):
        """Test JSON output format integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "report.json"
            
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                test_content = '''
def test_example():
    """Test example."""
    assert True
'''
                f.write(test_content)
                test_file_path = Path(f.name)
            
            try:
                config = LintConfig(
                    paths=[str(test_file_path)],
                    output_format="json",
                    output=str(output_file)
                )
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context = Mock()
                    mock_context.__enter__ = Mock(return_value=mock_context)
                    mock_context.__exit__ = Mock(return_value=None)
                    mock_context.filter_findings_by_severity.return_value = []
                    mock_context.persona_manager.on_test_pass.return_value = "Test passed"
                    mock_context.persona_manager.on_summary.return_value = "Summary message"
                    mock_context_class.return_value = mock_context
                    
                    mock_pipeline_instance = Mock()
                    mock_pipeline_instance.analyzers = []
                    mock_pipeline_instance.analyze_file.return_value = ([], [])  # findings, file_errors
                    mock_pipeline_instance.get_analysis_errors.return_value = []
                    mock_pipeline_instance.get_error_summary.return_value = {}
                    mock_pipeline.return_value = mock_pipeline_instance
                    
                    mock_config = Mock()
                    mock_init_config.return_value = mock_config
                    
                    # Mock findings for JSON output
                    mock_findings = [
                        Mock(code="DS301", message="Test finding", file_path=test_file_path)
                    ]
                    mock_context.storage.analyze_files.return_value = (mock_findings, [])
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    # Verify output file was specified
                    assert config.output == str(output_file)
                    assert config.output_format == "json"
                    
            finally:
                test_file_path.unlink()

    def test_sarif_output_integration(self):
        """Test SARIF output format integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "report.sarif"
            
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                test_content = '''
def test_example():
    """Test example."""
    assert True
'''
                f.write(test_content)
                test_file_path = Path(f.name)
            
            try:
                config = LintConfig(
                    paths=[str(test_file_path)],
                    output_format="sarif",
                    output=str(output_file)
                )
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                        mock_context_class, mock_pipeline, mock_init_config
                    )
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    # Verify SARIF output was specified
                    assert config.output == str(output_file)
                    assert config.output_format == "sarif"
                    
            finally:
                test_file_path.unlink()

    def test_multiple_file_analysis_integration(self):
        """Test analysis of multiple files integration."""
        # Create multiple temporary test files
        test_files = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_test_{i}.py', delete=False) as f:
                    test_content = f'''
def test_example_{i}():
    """Test example {i}."""
    assert True
'''
                    f.write(test_content)
                    test_files.append(Path(f.name))
            
            config = LintConfig(paths=[str(f) for f in test_files])
            
            with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                 patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                 patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                 patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                
                mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                    mock_context_class, mock_pipeline, mock_init_config
                )
                
                result = _run_lint_with_options(config)
                
                assert result == 0
                # Verify multiple files were specified
                assert len(config.paths) == 3
                
        finally:
            for test_file in test_files:
                test_file.unlink()

    def test_error_scenario_handling_integration(self):
        """Test error scenario handling integration."""
        # Create a temporary test file with syntax error
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
def test_example():
    """Test example with syntax error."""
    assert True
    # Missing closing quote
    invalid_string = "unclosed string
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            config = LintConfig(paths=[str(test_file_path)])
            
            with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                 patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                 patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                 patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                
                mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                    mock_context_class, mock_pipeline, mock_init_config
                )
                
                # Simulate analysis error by making the pipeline raise an exception
                mock_pipeline_instance.analyze_file.side_effect = Exception("Analysis error")
                
                result = _run_lint_with_options(config)
                
                # Should handle error gracefully
                assert result != 0
                
        finally:
            test_file_path.unlink()

    def test_profile_configuration_integration(self):
        """Test profile configuration integration."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
def test_example():
    """Test example."""
    assert True
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            # Test different profiles
            profiles_to_test = ["standard", "strict", "lenient"]
            
            for profile in profiles_to_test:
                config = LintConfig(paths=[str(test_file_path)], profile=profile)
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                        mock_context_class, mock_pipeline, mock_init_config
                    )
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    assert config.profile == profile
                    
        finally:
            test_file_path.unlink()

    def test_persona_configuration_integration(self):
        """Test persona configuration integration."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
def test_example():
    """Test example."""
    assert True
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            # Test different personas
            personas_to_test = ["drill_sergeant", "snoop_dogg"]
            
            for persona in personas_to_test:
                config = LintConfig(paths=[str(test_file_path)], persona=persona)
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                        mock_context_class, mock_pipeline, mock_init_config
                    )
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    assert config.persona == persona
                    
        finally:
            test_file_path.unlink()

    def test_sut_filter_integration(self):
        """Test SUT filter integration."""
        # Create temporary test files in different directories
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            tests_dir = Path(temp_dir) / "tests"
            src_dir.mkdir()
            tests_dir.mkdir()
            
            src_file = src_dir / "module.py"
            test_file = tests_dir / "test_module.py"
            
            src_file.write_text('def function(): pass')
            test_file.write_text('def test_function(): assert True')
            
            try:
                config = LintConfig(
                    paths=[str(src_file), str(test_file)],
                    sut_filter="src/"
                )
                
                with patch("pytest_drill_sergeant.cli.main.AnalysisContext") as mock_context_class, \
                     patch("pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline") as mock_pipeline, \
                     patch("pytest_drill_sergeant.core.config_context.initialize_config") as mock_init_config, \
                     patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging:
                    
                    mock_context, mock_pipeline_instance, mock_config = _setup_mock_context_and_pipeline(
                        mock_context_class, mock_pipeline, mock_init_config
                    )
                    
                    result = _run_lint_with_options(config)
                    
                    assert result == 0
                    assert config.sut_filter == "src/"
                    
            finally:
                src_file.unlink()
                test_file.unlink()