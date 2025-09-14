"""Integration tests for the configuration system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pytest_drill_sergeant.core.cli_config import (
    create_pytest_config_from_args,
    parse_cli_args,
)
from pytest_drill_sergeant.core.config import DrillSergeantConfig, load_config
from pytest_drill_sergeant.core.config_manager import (
    config_manager,
    get_config,
    initialize_config,
)
from pytest_drill_sergeant.core.config_validator import validate_configuration
from tests.constants import (
    BIS_THRESHOLD_FAIL,
    BIS_THRESHOLD_WARN,
    BUDGET_ERROR,
    BUDGET_WARN,
    CUSTOM_THRESHOLD,
    CUSTOM_THRESHOLD_ALT,
)


class TestConfigurationIntegration:
    """Integration tests for the complete configuration system."""

    def test_full_configuration_loading_workflow(self) -> None:
        """Test the complete configuration loading workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml
            pyproject_content = """
[tool.pytest-drill-sergeant]
mode = "advisory"
persona = "drill_sergeant"
budgets = { warn = 30, error = 5 }
thresholds = { bis_threshold_warn = 85, bis_threshold_fail = 65 }
enabled_rules = ["aaa_comments", "private_access"]
mock_allowlist = ["requests.*", "boto3.*"]
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Create pytest.ini
            pytest_ini_content = """
[tool:pytest-drill-sergeant]
mode = quality-gate
persona = snoop_dogg
verbose = true
budgets = warn=25,error=10
enabled_rules = aaa_comments,static_clones
"""
            (project_root / "pytest.ini").write_text(pytest_ini_content)

            # Test environment variables
            with patch.dict(
                os.environ,
                {
                    "DRILL_SERGEANT_MODE": "strict",
                    "DRILL_SERGEANT_PERSONA": "pirate",
                    "DRILL_SERGEANT_VERBOSE": "false",
                    "DRILL_SERGEANT_QUIET": "true",
                },
            ):
                # Test CLI arguments (highest priority)
                cli_args = {
                    "mode": "advisory",
                    "persona": "motivational_coach",
                    "verbose": True,
                    "quiet": False,
                    "json_report_path": "/tmp/report.json",
                }

                config = load_config(cli_args, project_root=project_root)

                # CLI args should win
                assert config.mode == "advisory"
                assert config.persona == "motivational_coach"
                assert config.verbose is True
                assert config.quiet is False
                assert config.json_report_path == "/tmp/report.json"

                # Other values from files (pytest.ini overrides pyproject.toml)
                assert config.budgets == {"warn": 25, "error": 10}  # From pytest.ini
                assert config.enabled_rules == {
                    "aaa_comments",
                    "static_clones",
                }  # From pytest.ini

                # Values from pyproject.toml (fallback)
                assert config.thresholds["bis_threshold_warn"] == BIS_THRESHOLD_WARN
                assert config.mock_allowlist == {"requests.*", "boto3.*"}

    def test_configuration_hierarchy_without_cli_args(self) -> None:
        """Test configuration hierarchy without CLI arguments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml
            pyproject_content = """
[tool.pytest-drill-sergeant]
mode = "advisory"
persona = "drill_sergeant"
budgets = { warn = 30, error = 5 }
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Test environment variables (should override files)
            with patch.dict(
                os.environ,
                {
                    "DRILL_SERGEANT_MODE": "strict",
                    "DRILL_SERGEANT_PERSONA": "snoop_dogg",
                },
            ):
                config = load_config(project_root=project_root)

                # Environment variables should win
                assert config.mode == "strict"
                assert config.persona == "snoop_dogg"

                # Other values from pyproject.toml
                assert config.budgets == {"warn": 30, "error": 5}

    def test_configuration_with_pytest_integration(self) -> None:
        """Test configuration integration with pytest."""
        # Reset configuration manager to ensure clean state
        config_manager.reset()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create pyproject.toml
            pyproject_content = """
[tool.pytest-drill-sergeant]
mode = "quality-gate"
persona = "drill_sergeant"
budgets = { warn = 20, error = 5 }
"""
            (project_root / "pyproject.toml").write_text(pyproject_content)

            # Mock pytest config
            mock_pytest_config = MagicMock()
            mock_pytest_config.option = MagicMock()
            mock_pytest_config.option.ds_mode = "strict"
            mock_pytest_config.option.ds_persona = "snoop_dogg"
            mock_pytest_config.option.ds_verbose = True

            # Initialize global configuration with CLI args (which override pyproject.toml)
            # Convert CLI args to proper format (strip ds_ prefix)
            cli_args = {"mode": "strict", "persona": "snoop_dogg", "verbose": True}
            initialize_config(cli_args=cli_args, project_root=project_root)

            # Get global configuration
            config = get_config()

        # Should use values from CLI args (which override pyproject.toml)
        assert config.mode == "strict"  # From CLI args
        assert config.persona == "snoop_dogg"  # From CLI args
        assert config.budgets == {
            "warn": 20,
            "error": 5,
        }  # From pyproject.toml (not overridden)
        assert config.verbose is True  # From CLI args

    def test_cli_args_parsing_and_conversion(self) -> None:
        """Test CLI argument parsing and conversion to configuration."""
        # Test complex CLI arguments
        cli_args = [
            "--ds-mode",
            "strict",
            "--ds-persona",
            "snoop_dogg",
            "--ds-sut-package",
            "myapp",
            "--ds-verbose",
            "--ds-fail-on-how",
            "--ds-json-report",
            "/tmp/report.json",
            "--ds-sarif-report",
            "/tmp/report.sarif",
            "--ds-enable-rules",
            "aaa_comments",
            "private_access",
            "--ds-suppress-rules",
            "private_access",
            "--ds-bis-threshold-warn",
            "85",
            "--ds-bis-threshold-fail",
            "65",
            "--ds-warn-budget",
            "20",
            "--ds-error-budget",
            "5",
            "--ds-output-formats",
            "terminal",
            "json",
            "sarif",
            "--ds-mock-allowlist",
            "custom.*",
            "test.*",
        ]

        parsed_args = parse_cli_args(cli_args)

        # Verify parsed arguments
        assert parsed_args["mode"] == "strict"
        assert parsed_args["persona"] == "snoop_dogg"
        assert parsed_args["sut_package"] == "myapp"
        assert parsed_args["verbose"] is True
        assert parsed_args["fail_on_how"] is True
        assert parsed_args["json_report_path"] == "/tmp/report.json"
        assert parsed_args["sarif_report_path"] == "/tmp/report.sarif"
        assert parsed_args["enabled_rules"] == {"aaa_comments", "private_access"}
        assert parsed_args["suppressed_rules"] == {"private_access"}
        # Type assertions for nested dictionaries
        thresholds = parsed_args["thresholds"]
        assert isinstance(thresholds, dict)
        assert thresholds["bis_threshold_warn"] == BIS_THRESHOLD_WARN
        assert thresholds["bis_threshold_fail"] == BIS_THRESHOLD_FAIL

        budgets = parsed_args["budgets"]
        assert isinstance(budgets, dict)
        assert budgets["warn"] == BUDGET_WARN
        assert budgets["error"] == BUDGET_ERROR
        assert parsed_args["output_formats"] == ["terminal", "json", "sarif"]
        assert parsed_args["mock_allowlist"] == {"custom.*", "test.*"}

        # Convert to configuration
        config = create_pytest_config_from_args(parsed_args)

        # Verify configuration
        assert config.mode == "strict"
        assert config.persona == "snoop_dogg"
        assert config.sut_package == "myapp"
        assert config.verbose is True
        assert config.fail_on_how is True
        assert config.json_report_path == "/tmp/report.json"
        assert config.sarif_report_path == "/tmp/report.sarif"
        assert config.enabled_rules == {"aaa_comments", "private_access"}
        assert config.suppressed_rules == {"private_access"}
        assert config.thresholds["bis_threshold_warn"] == BIS_THRESHOLD_WARN
        assert config.thresholds["bis_threshold_fail"] == BIS_THRESHOLD_FAIL
        assert config.budgets == {"warn": BUDGET_WARN, "error": BUDGET_ERROR}
        assert config.output_formats == ["terminal", "json", "sarif"]
        assert config.mock_allowlist == {"custom.*", "test.*"}

    def test_configuration_validation_integration(self) -> None:
        """Test configuration validation integration."""
        # Test valid configuration
        valid_config = DrillSergeantConfig(
            mode="strict",
            persona="snoop_dogg",
            budgets={"warn": 20, "error": 5},
            thresholds={"bis_threshold_warn": 85, "bis_threshold_fail": 65},
            enabled_rules={"aaa_comments", "private_access"},
            suppressed_rules={"private_access"},
        )

        with patch(
            "pytest_drill_sergeant.core.config_validator.ConfigValidator.validate_file_paths",
            return_value=[],
        ):
            is_valid, errors, suggestions = validate_configuration(valid_config)

        assert is_valid is True
        assert errors == []
        assert suggestions == {}

        # Test invalid configuration with file validation errors
        invalid_config = DrillSergeantConfig()

        with patch(
            "pytest_drill_sergeant.core.config_validator.ConfigValidator.validate_file_paths",
            return_value=["SUT package 'missing' could not be imported"],
        ):
            is_valid, errors, suggestions = validate_configuration(invalid_config)

        assert is_valid is False
        assert len(errors) > 0
        assert len(suggestions) > 0

    def test_configuration_error_handling(self) -> None:
        """Test configuration error handling."""
        # Test with invalid TOML
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create invalid pyproject.toml
            (project_root / "pyproject.toml").write_text("invalid toml content")

            # Should not raise exception, should fall back to defaults
            config = load_config(project_root=project_root)
            assert config.mode == "advisory"  # Default value

        # Test with missing files
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # No configuration files
            config = load_config(project_root=project_root)
            assert config.mode == "advisory"  # Default value

    def test_configuration_consistency_validation(self) -> None:
        """Test configuration consistency validation."""
        # Test conflicting verbose and quiet
        with pytest.raises(ValueError, match="Cannot be both verbose and quiet"):
            DrillSergeantConfig(verbose=True, quiet=True)

        # Test suppressed rules not in enabled rules
        with pytest.raises(
            ValueError, match="Cannot suppress rules that are not enabled"
        ):
            DrillSergeantConfig(
                enabled_rules={"aaa_comments"}, suppressed_rules={"static_clones"}
            )

        # Test valid configuration
        config = DrillSergeantConfig(
            verbose=True,
            quiet=False,
            enabled_rules={"aaa_comments", "static_clones"},
            suppressed_rules={"static_clones"},
        )

        assert config.verbose is True
        assert config.quiet is False
        assert config.is_rule_enabled("aaa_comments") is True
        assert config.is_rule_enabled("static_clones") is False  # Suppressed

    def test_configuration_utility_methods(self) -> None:
        """Test configuration utility methods."""
        config = DrillSergeantConfig(
            enabled_rules={"aaa_comments", "static_clones"},
            suppressed_rules={"static_clones"},
            thresholds={"custom_threshold": 42.0, "bis_threshold_warn": 85},
            budgets={"warn": 20, "error": 5},
        )

        # Test rule enabled checking
        assert config.is_rule_enabled("aaa_comments") is True
        assert config.is_rule_enabled("static_clones") is False  # Suppressed
        assert config.is_rule_enabled("private_access") is False  # Not enabled

        # Test threshold retrieval
        assert config.get_threshold("custom_threshold") == CUSTOM_THRESHOLD
        assert (
            config.get_threshold("nonexistent", CUSTOM_THRESHOLD_ALT)
            == CUSTOM_THRESHOLD_ALT
        )

        # Test budget retrieval
        assert config.get_budget("warn") == BUDGET_WARN
        assert config.get_budget("error") == BUDGET_ERROR
        assert config.get_budget("nonexistent", 0) == 0
