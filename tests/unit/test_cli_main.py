"""Unit tests for CLI main functionality."""

import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock, patch

from pytest_drill_sergeant.cli.main import (
    AnalysisContext,
    LintConfig,
    SUTFilter,
    _run_lint_with_options,
    cli,
    demo,
    lint,
    personas,
    profiles,
)


class TestLintConfig:
    """Test LintConfig dataclass."""

    def test_lint_config_defaults(self):
        """Test LintConfig default values."""
        config = LintConfig(paths=["test.py"])

        assert config.paths == ["test.py"]
        assert config.profile == "standard"
        assert config.enable is None
        assert config.disable is None
        assert config.only is None
        assert config.fail_on == "error"
        assert config.treat is None
        assert config.output_format == "terminal"
        assert config.output is None
        assert config.config is None
        assert config.persona == "drill_sergeant"
        assert config.sut_filter is None
        assert config.rich_output is True

    def test_lint_config_custom_values(self):
        """Test LintConfig with custom values."""
        config = LintConfig(
            paths=["src/", "tests/"],
            profile="strict",
            enable="DS301,DS302",
            disable="DS303",
            only="DS301",
            fail_on="warning",
            treat="DS302:error",
            output_format="json",
            output="report.json",
            config="custom.toml",
            persona="snoop_dogg",
            sut_filter="src/",
            rich_output=False,
        )

        assert config.paths == ["src/", "tests/"]
        assert config.profile == "strict"
        assert config.enable == "DS301,DS302"
        assert config.disable == "DS303"
        assert config.only == "DS301"
        assert config.fail_on == "warning"
        assert config.treat == "DS302:error"
        assert config.output_format == "json"
        assert config.output == "report.json"
        assert config.config == "custom.toml"
        assert config.persona == "snoop_dogg"
        assert config.sut_filter == "src/"
        assert config.rich_output is False

    def test_lint_config_asdict(self):
        """Test LintConfig can be converted to dict."""
        config = LintConfig(paths=["test.py"], profile="strict")
        config_dict = asdict(config)

        assert isinstance(config_dict, dict)
        assert config_dict["paths"] == ["test.py"]
        assert config_dict["profile"] == "strict"


class TestAnalysisContext:
    """Test AnalysisContext class."""

    def test_analysis_context_initialization(self):
        """Test AnalysisContext initialization."""
        with (
            patch(
                "pytest_drill_sergeant.plugin.analysis_storage.AnalysisStorage"
            ) as mock_storage_class,
            patch(
                "pytest_drill_sergeant.plugin.personas.manager.get_persona_manager"
            ) as mock_persona_manager,
        ):
            mock_storage = Mock()
            mock_persona_mgr = Mock()
            mock_storage_class.return_value = mock_storage
            mock_persona_manager.return_value = mock_persona_mgr

            context = AnalysisContext()

            assert context.storage == mock_storage
            assert context.persona_manager == mock_persona_mgr
            assert context.analyzers == []
            assert context.sut_filter is None

    def test_analysis_context_add_analyzer(self):
        """Test adding analyzer to context."""
        with (
            patch(
                "pytest_drill_sergeant.plugin.analysis_storage.AnalysisStorage"
            ) as mock_storage_class,
            patch(
                "pytest_drill_sergeant.plugin.personas.manager.get_persona_manager"
            ) as mock_persona_manager,
        ):
            mock_storage = Mock()
            mock_storage_class.return_value = mock_storage
            mock_persona_manager.return_value = Mock()

            context = AnalysisContext()
            mock_analyzer = Mock()

            context.add_analyzer(mock_analyzer)

            mock_storage.add_analyzer.assert_called_once_with(mock_analyzer)

    def test_analysis_context_set_sut_filter(self):
        """Test setting SUT filter in context."""
        with (
            patch(
                "pytest_drill_sergeant.plugin.analysis_storage.AnalysisStorage"
            ) as mock_storage_class,
            patch(
                "pytest_drill_sergeant.plugin.personas.manager.get_persona_manager"
            ) as mock_persona_manager,
        ):
            mock_storage_class.return_value = Mock()
            mock_persona_manager.return_value = Mock()

            context = AnalysisContext()
            context.set_sut_filter("src/")

            assert isinstance(context.sut_filter, SUTFilter)
            assert context.sut_filter.sut_pattern == "src/"


class TestSUTFilter:
    """Test SUTFilter class."""

    def test_sut_filter_initialization(self):
        """Test SUTFilter initialization."""
        sut_filter = SUTFilter("src/")

        assert sut_filter.sut_pattern == "src/"

    def test_sut_filter_should_analyze_file(self):
        """Test SUTFilter file analysis logic."""
        sut_filter = SUTFilter("src/")
        base_path = Path("/project")

        # Test file that should be analyzed
        assert (
            sut_filter.should_analyze(Path("/project/src/module.py"), base_path) is True
        )
        assert (
            sut_filter.should_analyze(
                Path("/project/src/tests/test_module.py"), base_path
            )
            is True
        )

        # Test file that should not be analyzed
        assert (
            sut_filter.should_analyze(Path("/project/docs/readme.md"), base_path)
            is False
        )
        assert sut_filter.should_analyze(Path("/project/setup.py"), base_path) is False

    def test_sut_filter_none_pattern(self):
        """Test SUTFilter with None pattern (analyze all files)."""
        sut_filter = SUTFilter(None)
        base_path = Path("/project")

        # Should analyze all files when pattern is None
        assert (
            sut_filter.should_analyze(Path("/project/src/module.py"), base_path) is True
        )
        assert (
            sut_filter.should_analyze(Path("/project/tests/test_module.py"), base_path)
            is True
        )
        assert (
            sut_filter.should_analyze(Path("/project/docs/readme.md"), base_path)
            is True
        )


class TestRunLintWithOptions:
    """Test _run_lint_with_options function."""

    def test_run_lint_with_options_success(self):
        """Test successful lint execution."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            test_content = '''
def test_example():
    """Test example."""
    assert True
'''
            f.write(test_content)
            test_file_path = Path(f.name)

        try:
            config = LintConfig(paths=[str(test_file_path)])

            with (
                patch(
                    "pytest_drill_sergeant.cli.main.AnalysisContext"
                ) as mock_context_class,
                patch(
                    "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
                ) as mock_pipeline,
                patch(
                    "pytest_drill_sergeant.core.config_context.initialize_config"
                ) as mock_init_config,
                patch(
                    "pytest_drill_sergeant.cli.main.setup_logging"
                ) as mock_setup_logging,
            ):
                mock_context = Mock()
                mock_context.__enter__ = Mock(return_value=mock_context)
                mock_context.__exit__ = Mock(return_value=None)
                mock_context_class.return_value = mock_context

                # Create a proper mock pipeline with analyzers attribute
                mock_pipeline_instance = Mock()
                mock_pipeline_instance.analyzers = []  # Empty list of analyzers
                mock_pipeline_instance.analyze_file.return_value = (
                    [],
                    [],
                )  # findings, file_errors
                mock_pipeline_instance.get_analysis_errors.return_value = []
                mock_pipeline_instance.get_error_summary.return_value = {}
                mock_pipeline.return_value = mock_pipeline_instance

                # Mock the context methods that might be called
                mock_context.filter_findings_by_severity.return_value = []
                mock_context.persona_manager.on_test_pass.return_value = "Test passed"
                mock_context.persona_manager.on_summary.return_value = "Summary message"

                mock_init_config.return_value = Mock()

                result = _run_lint_with_options(config)

                assert result == 0
                mock_setup_logging.assert_called_once()
                mock_init_config.assert_called_once()
        finally:
            # Clean up the temporary file
            test_file_path.unlink(missing_ok=True)

    def test_run_lint_with_options_file_not_found(self):
        """Test lint execution with non-existent file."""
        config = LintConfig(paths=["nonexistent.py"])

        with (
            patch(
                "pytest_drill_sergeant.cli.main.AnalysisContext"
            ) as mock_context_class,
            patch(
                "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
            ) as mock_pipeline,
            patch(
                "pytest_drill_sergeant.core.config_context.initialize_config"
            ) as mock_init_config,
            patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging,
        ):
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_context)
            mock_context.__exit__ = Mock(return_value=None)
            mock_context_class.return_value = mock_context

            # Create a proper mock pipeline with analyzers attribute
            mock_pipeline_instance = Mock()
            mock_pipeline_instance.analyzers = []  # Empty list of analyzers
            mock_pipeline_instance.analyze_file.return_value = (
                [],
                [],
            )  # findings, file_errors
            mock_pipeline_instance.get_analysis_errors.return_value = []
            mock_pipeline_instance.get_error_summary.return_value = {}
            mock_pipeline.return_value = mock_pipeline_instance

            # Mock the context methods that might be called
            mock_context.filter_findings_by_severity.return_value = []
            mock_context.persona_manager.on_test_pass.return_value = "Test passed"
            mock_context.persona_manager.on_summary.return_value = "Summary message"

            mock_init_config.return_value = Mock()

            result = _run_lint_with_options(config)

            # Should return 0 even if files don't exist (graceful handling)
            assert result == 0
            mock_setup_logging.assert_called_once()
            mock_init_config.assert_called_once()

    def test_run_lint_with_options_exception_handling(self):
        """Test exception handling in lint execution."""
        config = LintConfig(paths=["test.py"])

        with (
            patch(
                "pytest_drill_sergeant.cli.main.AnalysisContext"
            ) as mock_context_class,
            patch(
                "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
            ) as mock_pipeline,
            patch(
                "pytest_drill_sergeant.core.config_context.initialize_config"
            ) as mock_init_config,
            patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging,
        ):
            # Make initialize_config raise an exception
            mock_init_config.side_effect = Exception("Config error")

            result = _run_lint_with_options(config)

            # Should return non-zero exit code on error
            assert result != 0


class TestCLICommands:
    """Test CLI command functions."""

    def test_lint_command_signature(self):
        """Test lint command function signature."""
        import inspect

        sig = inspect.signature(lint)

        # Should have all the expected parameters
        expected_params = {
            "paths",
            "profile",
            "enable",
            "disable",
            "only",
            "fail_on",
            "treat",
            "output_format",
            "output",
            "config",
            "persona",
            "sut_filter",
            "rich_output",
        }
        actual_params = set(sig.parameters.keys())

        assert expected_params.issubset(actual_params)

    def test_demo_command_signature(self):
        """Test demo command function signature."""
        import inspect

        sig = inspect.signature(demo)

        # Should have expected parameters
        assert "persona" in sig.parameters
        assert "rich_output" in sig.parameters

    def test_profiles_command_signature(self):
        """Test profiles command function signature."""
        import inspect

        sig = inspect.signature(profiles)

        # Should have rich_output parameter
        assert "rich_output" in sig.parameters

    def test_personas_command_signature(self):
        """Test personas command function signature."""
        import inspect

        sig = inspect.signature(personas)

        # Should have rich_output parameter
        assert "rich_output" in sig.parameters

    def test_cli_function_signature(self):
        """Test cli function signature."""
        import inspect

        sig = inspect.signature(cli)

        # Should have no parameters
        assert len(sig.parameters) == 0


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_invalid_path_handling(self):
        """Test handling of invalid file paths."""
        config = LintConfig(paths=["/invalid/path/that/does/not/exist.py"])

        with (
            patch(
                "pytest_drill_sergeant.cli.main.AnalysisContext"
            ) as mock_context_class,
            patch(
                "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
            ) as mock_pipeline,
            patch(
                "pytest_drill_sergeant.core.config_context.initialize_config"
            ) as mock_init_config,
            patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging,
        ):
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_context)
            mock_context.__exit__ = Mock(return_value=None)
            mock_context_class.return_value = mock_context

            # Create a proper mock pipeline with analyzers attribute
            mock_pipeline_instance = Mock()
            mock_pipeline_instance.analyzers = []  # Empty list of analyzers
            mock_pipeline_instance.analyze_file.return_value = (
                [],
                [],
            )  # findings, file_errors
            mock_pipeline_instance.get_analysis_errors.return_value = []
            mock_pipeline_instance.get_error_summary.return_value = {}
            mock_pipeline.return_value = mock_pipeline_instance

            # Mock the context methods that might be called
            mock_context.filter_findings_by_severity.return_value = []
            mock_context.persona_manager.on_test_pass.return_value = "Test passed"
            mock_context.persona_manager.on_summary.return_value = "Summary message"

            mock_init_config.return_value = Mock()

            result = _run_lint_with_options(config)

            # Should handle gracefully and return 0
            assert result == 0
            mock_setup_logging.assert_called_once()
            mock_init_config.assert_called_once()

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        config = LintConfig(paths=["/root/protected_file.py"])

        with (
            patch(
                "pytest_drill_sergeant.cli.main.AnalysisContext"
            ) as mock_context_class,
            patch(
                "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
            ) as mock_pipeline,
            patch(
                "pytest_drill_sergeant.core.config_context.initialize_config"
            ) as mock_init_config,
            patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging,
        ):
            # Make initialize_config raise PermissionError
            mock_init_config.side_effect = PermissionError("Permission denied")

            result = _run_lint_with_options(config)

            # Should return non-zero exit code on permission error
            assert result != 0

    def test_config_file_error_handling(self):
        """Test handling of config file errors."""
        config = LintConfig(paths=["test.py"], config="invalid_config.toml")

        with (
            patch(
                "pytest_drill_sergeant.cli.main.AnalysisContext"
            ) as mock_context_class,
            patch(
                "pytest_drill_sergeant.core.analysis_pipeline.create_analysis_pipeline"
            ) as mock_pipeline,
            patch(
                "pytest_drill_sergeant.core.config_context.initialize_config"
            ) as mock_init_config,
            patch("pytest_drill_sergeant.cli.main.setup_logging") as mock_setup_logging,
        ):
            # Make initialize_config raise FileNotFoundError for config file
            mock_init_config.side_effect = FileNotFoundError("Config file not found")

            result = _run_lint_with_options(config)

            # Should return non-zero exit code on config file error
            assert result != 0


class TestCLIOutputFormatting:
    """Test CLI output formatting."""

    def test_output_format_validation(self):
        """Test output format validation."""
        # Test valid output formats
        valid_formats = ["terminal", "json", "sarif"]

        for fmt in valid_formats:
            config = LintConfig(paths=["test.py"], output_format=fmt)
            assert config.output_format == fmt

    def test_output_file_path_handling(self):
        """Test output file path handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "report.json"

            config = LintConfig(
                paths=["test.py"], output_format="json", output=str(output_file)
            )

            assert config.output == str(output_file)
            assert config.output_format == "json"

    def test_rich_output_configuration(self):
        """Test rich output configuration."""
        # Test with rich output enabled
        config_rich = LintConfig(paths=["test.py"], rich_output=True)
        assert config_rich.rich_output is True

        # Test with rich output disabled
        config_plain = LintConfig(paths=["test.py"], rich_output=False)
        assert config_plain.rich_output is False
