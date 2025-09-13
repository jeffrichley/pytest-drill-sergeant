"""Tests for the configuration system."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast
from unittest.mock import patch

import pytest

from pytest_drill_sergeant.core.config import (
    ConfigLoader,
    ConfigurationError,
    DrillSergeantConfig,
    load_config,
)
from pytest_drill_sergeant.core.models import RuleType
from tests.constants import (
    BIS_THRESHOLD_90,
    BIS_THRESHOLD_WARN,
    BIS_THRESHOLD_WARN_DEFAULT,
    BUDGET_ERROR,
    CUSTOM_BUDGET_WARN,
    CUSTOM_THRESHOLD,
    CUSTOM_THRESHOLD_ALT,
    DYNAMIC_COV_JACCARD,
    LSP_PORT,
    MAX_WORKERS,
    SIMILARITY_THRESHOLD,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


# TypedDict for raw configuration data
class RawConfig(TypedDict, total=False):
    """Raw configuration dictionary structure."""

    mode: NotRequired[str]
    persona: NotRequired[str]
    sut_package: NotRequired[str | None]
    budgets: NotRequired[dict[str, int]]
    enabled_rules: NotRequired[set[str]]
    suppressed_rules: NotRequired[set[str]]
    thresholds: NotRequired[dict[str, float]]
    mock_allowlist: NotRequired[set[str]]


def as_raw_config(d: Mapping[str, object]) -> RawConfig:
    """Helper to safely cast a mapping to RawConfig."""
    return cast("RawConfig", d)


class TestDrillSergeantConfig:
    """Test the DrillSergeantConfig model."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = DrillSergeantConfig()

        assert config.mode == "advisory"
        assert config.persona == "drill_sergeant"
        assert config.sut_package is None
        assert config.budgets == {"warn": 25, "error": 0}
        assert config.enabled_rules == {
            "aaa_comments",
            "static_clones",
            "fixture_extract",
            "private_access",
            "mock_overspecification",
            "structural_equality",
        }
        assert config.suppressed_rules == set()
        assert config.thresholds == {
            "static_clone_hamming": 6,
            "dynamic_cov_jaccard": 0.95,
            "bis_threshold_warn": 80,
            "bis_threshold_fail": 65,
            "mock_assert_threshold": 5,
            "private_access_penalty": 10,
        }
        assert config.mock_allowlist == {
            "requests.*",
            "boto3.*",
            "time.*",
            "random.*",
            "datetime.*",
            "uuid.*",
        }
        assert config.output_formats == ["terminal"]
        assert config.json_report_path is None
        assert config.sarif_report_path is None
        assert config.fail_on_how is False
        assert config.verbose is False
        assert config.quiet is False

    def test_config_validation_mode(self) -> None:
        """Test mode validation."""
        # Valid modes
        for mode in ["advisory", "quality-gate", "strict"]:
            config = DrillSergeantConfig(mode=mode)
            assert config.mode == mode

        # Invalid mode
        with pytest.raises(ValueError, match="Mode must be one of"):
            DrillSergeantConfig(mode="invalid")

    def test_config_validation_persona(self) -> None:
        """Test persona validation."""
        # Valid personas
        valid_personas = [
            "drill_sergeant",
            "snoop_dogg",
            "motivational_coach",
            "sarcastic_butler",
            "pirate",
        ]
        for persona in valid_personas:
            config = DrillSergeantConfig(persona=persona)
            assert config.persona == persona

        # Invalid persona
        with pytest.raises(ValueError, match="Persona must be one of"):
            DrillSergeantConfig(persona="invalid")

    def test_config_validation_budgets(self) -> None:
        """Test budget validation."""
        # Valid budgets
        config = DrillSergeantConfig(budgets={"warn": 10, "error": 5})
        assert config.budgets == {"warn": 10, "error": 5}

        # Invalid budgets (negative)
        with pytest.raises(ValueError, match="Budget warn must be non-negative"):
            DrillSergeantConfig(budgets={"warn": -1, "error": 0})

    def test_config_validation_thresholds(self) -> None:
        """Test threshold validation."""
        # Valid thresholds
        config = DrillSergeantConfig(
            thresholds={
                "bis_threshold_warn": BIS_THRESHOLD_WARN,
                "dynamic_cov_jaccard": DYNAMIC_COV_JACCARD,
            }
        )
        assert config.thresholds["bis_threshold_warn"] == BIS_THRESHOLD_WARN
        assert config.thresholds["dynamic_cov_jaccard"] == DYNAMIC_COV_JACCARD

        # Invalid threshold ranges
        with pytest.raises(
            ValueError, match="Threshold bis_threshold_warn must be between 0 and 100"
        ):
            DrillSergeantConfig(thresholds={"bis_threshold_warn": 150})

        with pytest.raises(
            ValueError,
            match="Jaccard threshold dynamic_cov_jaccard must be between 0 and 1",
        ):
            DrillSergeantConfig(thresholds={"dynamic_cov_jaccard": 1.5})

    def test_config_consistency_validation(self) -> None:
        """Test configuration consistency validation."""
        # Can't be both verbose and quiet
        with pytest.raises(ValueError, match="Cannot be both verbose and quiet"):
            DrillSergeantConfig(verbose=True, quiet=True)

        # Suppressed rules must be subset of enabled rules
        with pytest.raises(
            ValueError, match="Cannot suppress rules that are not enabled"
        ):
            DrillSergeantConfig(
                enabled_rules={"aaa_comments"}, suppressed_rules={"static_clones"}
            )

    def test_is_rule_enabled(self) -> None:
        """Test rule enabled checking."""
        config = DrillSergeantConfig(
            enabled_rules={"aaa_comments", "static_clones"},
            suppressed_rules={"static_clones"},
        )

        assert config.is_rule_enabled("aaa_comments") is True
        assert config.is_rule_enabled("static_clones") is False  # Suppressed
        assert config.is_rule_enabled("private_access") is False  # Not enabled

    def test_get_threshold(self) -> None:
        """Test threshold retrieval."""
        config = DrillSergeantConfig(thresholds={"custom_threshold": CUSTOM_THRESHOLD})

        assert config.get_threshold("custom_threshold") == CUSTOM_THRESHOLD
        assert (
            config.get_threshold("nonexistent", CUSTOM_THRESHOLD_ALT)
            == CUSTOM_THRESHOLD_ALT
        )

    def test_get_budget(self) -> None:
        """Test budget retrieval."""
        config = DrillSergeantConfig(
            budgets={"warn": CUSTOM_BUDGET_WARN, "error": BUDGET_ERROR}
        )

        assert config.get_budget("warn") == CUSTOM_BUDGET_WARN
        assert config.get_budget("error") == BUDGET_ERROR
        assert config.get_budget("nonexistent", 0) == 0

    def test_to_base_config(self) -> None:
        """Test conversion to base config."""
        config = DrillSergeantConfig(
            mode="strict",
            persona="snoop_dogg",
            sut_package="myapp",
            budgets={"warn": 10, "error": 0},
            enabled_rules={"aaa_comments"},
            suppressed_rules=set(),
            thresholds={"bis_threshold_warn": 90},
            mock_allowlist={"custom.*"},
        )

        base_config = config.to_base_config()

        assert base_config.mode == "strict"
        assert base_config.persona == "snoop_dogg"
        assert base_config.sut_package == "myapp"
        assert base_config.fail_on_how is False
        assert base_config.output_format == "terminal"
        assert base_config.verbose is False
        assert base_config.enabled_rules == [RuleType.AAA_COMMENT]
        assert base_config.disabled_rules == []
        assert base_config.similarity_threshold == SIMILARITY_THRESHOLD
        assert base_config.bis_threshold == BIS_THRESHOLD_90
        assert base_config.parallel_analysis is True
        assert base_config.max_workers == MAX_WORKERS
        assert base_config.cache_ast is True
        assert base_config.lsp_enabled is False
        assert base_config.lsp_port == LSP_PORT


class TestConfigLoader:
    """Test the ConfigLoader class."""

    def test_get_defaults(self) -> None:
        """Test default configuration retrieval."""
        loader = ConfigLoader()
        defaults: dict[str, object] = loader._get_defaults()

        # Cast to typed config for safe access
        typed_defaults = as_raw_config(defaults)

        assert typed_defaults["mode"] == "advisory"
        assert typed_defaults["persona"] == "drill_sergeant"
        assert typed_defaults["sut_package"] is None
        assert typed_defaults["budgets"] == {"warn": 25, "error": 0}

        # Safe access for optional fields
        enabled_rules = typed_defaults.get("enabled_rules")
        assert isinstance(enabled_rules, set)
        assert "aaa_comments" in enabled_rules

        assert typed_defaults.get("suppressed_rules") == set()

        # Safe access for nested dict
        thresholds = typed_defaults.get("thresholds")
        assert isinstance(thresholds, dict)
        assert thresholds.get("bis_threshold_warn") == BIS_THRESHOLD_WARN_DEFAULT

        # Safe access for mock allowlist
        mock_allowlist = typed_defaults.get("mock_allowlist")
        assert isinstance(mock_allowlist, set)
        assert "requests.*" in mock_allowlist

    def test_load_environment_variables(self) -> None:
        """Test environment variable loading."""
        loader = ConfigLoader()

        with patch.dict(
            os.environ,
            {
                "DRILL_SERGEANT_MODE": "strict",
                "DRILL_SERGEANT_PERSONA": "snoop_dogg",
                "DRILL_SERGEANT_VERBOSE": "true",
                "DRILL_SERGEANT_QUIET": "false",
                "DRILL_SERGEANT_FAIL_ON_HOW": "1",
                "DRILL_SERGEANT_JSON_REPORT": "/tmp/report.json",
            },
        ):
            env_config = loader._load_environment_variables()

            assert env_config["mode"] == "strict"
            assert env_config["persona"] == "snoop_dogg"
            assert env_config["verbose"] is True
            assert env_config["quiet"] is False
            assert env_config["fail_on_how"] is True
            assert env_config["json_report_path"] == "/tmp/report.json"

    def test_convert_pyproject_config(self) -> None:
        """Test pyproject.toml configuration conversion."""
        loader = ConfigLoader()

        pyproject_config: dict[str, object] = {
            "mode": "quality-gate",
            "persona": "motivational_coach",
            "budgets": {"warn": 15, "error": 5},
            "rules": {
                "enable": ["aaa_comments", "private_access"],
                "suppress": ["private_access"],
            },
            "thresholds": {"bis_threshold_warn": 85},
            "mock_allowlist": ["custom.*", "test.*"],
        }

        converted = loader._convert_pyproject_config(pyproject_config)

        assert converted["mode"] == "quality-gate"
        assert converted["persona"] == "motivational_coach"
        assert converted["budgets"] == {"warn": 15, "error": 5}
        assert converted["enabled_rules"] == {"aaa_comments", "private_access"}
        assert converted["suppressed_rules"] == {"private_access"}
        assert converted["thresholds"] == {"bis_threshold_warn": 85}
        assert converted["mock_allowlist"] == {"custom.*", "test.*"}

    def test_convert_pytest_ini_config(self) -> None:
        """Test pytest.ini configuration conversion."""
        loader = ConfigLoader()

        pytest_ini_config = {
            "mode": "strict",
            "persona": "pirate",
            "verbose": "true",
            "quiet": "false",
            "budgets": "warn=20,error=10",
            "enabled_rules": "aaa_comments,static_clones",
            "suppressed_rules": "static_clones",
            "mock_allowlist": "requests.*,boto3.*",
        }

        converted = loader._convert_pytest_ini_config(pytest_ini_config)

        assert converted["mode"] == "strict"
        assert converted["persona"] == "pirate"
        assert converted["verbose"] is True
        assert converted["quiet"] is False
        assert converted["budgets"] == {"warn": 20, "error": 10}
        assert converted["enabled_rules"] == {"aaa_comments", "static_clones"}
        assert converted["suppressed_rules"] == {"static_clones"}
        assert converted["mock_allowlist"] == {"requests.*", "boto3.*"}

    def test_load_config_hierarchy(self) -> None:
        """Test configuration loading with proper hierarchy."""
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

            # Create pytest.ini
            pytest_ini_content = """
[tool:pytest-drill-sergeant]
mode = quality-gate
persona = snoop_dogg
verbose = true
"""
            (project_root / "pytest.ini").write_text(pytest_ini_content)

            loader = ConfigLoader(project_root)

            # Test with environment variables (should override files)
            with patch.dict(
                os.environ,
                {"DRILL_SERGEANT_MODE": "strict", "DRILL_SERGEANT_PERSONA": "pirate"},
            ):
                config = loader.load_config()

                # Environment variables should win
                assert config.mode == "strict"
                assert config.persona == "pirate"
                # Other values from files
                assert config.budgets == {"warn": 30, "error": 5}
                assert config.verbose is True

            # Test with CLI args (should override everything)
            cli_args = {
                "mode": "advisory",
                "persona": "motivational_coach",
                "verbose": False,
            }

            config = loader.load_config(cli_args)

            # CLI args should win
            assert config.mode == "advisory"
            assert config.persona == "motivational_coach"
            assert config.verbose is False
            # Other values from files
            assert config.budgets == {"warn": 30, "error": 5}

    def test_load_config_missing_files(self) -> None:
        """Test configuration loading when files are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            loader = ConfigLoader(project_root)

            # Should work with just defaults
            config = loader.load_config()
            assert config.mode == "advisory"
            assert config.persona == "drill_sergeant"

    def test_load_config_invalid_toml(self) -> None:
        """Test configuration loading with invalid TOML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create invalid pyproject.toml
            (project_root / "pyproject.toml").write_text("invalid toml content")

            loader = ConfigLoader(project_root)

            # Should fall back to defaults
            config = loader.load_config()
            assert config.mode == "advisory"  # Default value


class TestLoadConfigFunction:
    """Test the load_config convenience function."""

    def test_load_config_basic(self) -> None:
        """Test basic configuration loading."""
        config = load_config()

        assert isinstance(config, DrillSergeantConfig)
        assert config.mode == "advisory"
        assert config.persona == "drill_sergeant"

    def test_load_config_with_cli_args(self) -> None:
        """Test configuration loading with CLI arguments."""
        cli_args = {"mode": "strict", "persona": "snoop_dogg", "verbose": True}

        config = load_config(cli_args)

        assert config.mode == "strict"
        assert config.persona == "snoop_dogg"
        assert config.verbose is True

    def test_load_config_error_handling(self) -> None:
        """Test configuration loading error handling."""
        with patch(
            "pytest_drill_sergeant.core.config.ConfigLoader.load_config"
        ) as mock_load:
            mock_load.side_effect = Exception("Test error")

            with pytest.raises(
                ConfigurationError, match="Failed to load configuration"
            ):
                load_config()


class TestConfigurationError:
    """Test the ConfigurationError exception."""

    def test_configuration_error_creation(self) -> None:
        """Test ConfigurationError creation."""
        error = ConfigurationError("Test error message")
        assert str(error) == "Test error message"

    def test_configuration_error_with_cause(self) -> None:
        """Test ConfigurationError with underlying cause."""
        original_error = ValueError("Original error")
        error = ConfigurationError("Configuration failed")
        error.__cause__ = original_error

        assert str(error) == "Configuration failed"
        assert error.__cause__ is original_error
