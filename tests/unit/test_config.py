"""Unit tests for the config module."""

import os
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig


@pytest.mark.unit
class TestDrillSergeantConfig:
    """Test the DrillSergeantConfig dataclass."""

    def test_config_default_values(self) -> None:
        """Test DrillSergeantConfig with default values."""
        # Arrange - No setup needed for default values test

        # Act - Create DrillSergeantConfig with default values
        config = DrillSergeantConfig()

        # Assert - Verify all default values are correct
        assert config.enabled is True
        assert config.enforce_markers is True
        assert config.enforce_aaa is True
        assert config.enforce_file_length is True
        assert config.auto_detect_markers is True
        assert config.min_description_length == 3
        assert config.max_file_length == 350
        assert config.file_length_mode == "error"
        assert config.file_length_exclude == []
        assert config.file_length_inline_ignore is True
        assert config.file_length_inline_ignore_token == "drill-sergeant: file-length ignore"
        assert config.marker_mappings == {}
        assert config.aaa_mode == "basic"
        assert config.aaa_synonyms_enabled is False
        assert config.aaa_builtin_synonyms is True
        assert config.aaa_arrange_synonyms == []
        assert config.aaa_act_synonyms == []
        assert config.aaa_assert_synonyms == []

    def test_config_custom_values(self) -> None:
        """Test DrillSergeantConfig with custom values."""
        # Arrange - Set up custom values for DrillSergeantConfig
        marker_mappings = {"unit": "test_unit", "integration": "test_integration"}
        arrange_synonyms = ["setup", "given"]
        act_synonyms = ["when", "execute"]
        assert_synonyms = ["then", "verify"]

        # Act - Create DrillSergeantConfig with custom values
        config = DrillSergeantConfig(
            enabled=False,
            enforce_markers=False,
            enforce_aaa=False,
            enforce_file_length=False,
            auto_detect_markers=False,
            min_description_length=5,
            max_file_length=500,
            file_length_mode="warn",
            file_length_exclude=["tests/legacy/*"],
            file_length_inline_ignore=False,
            file_length_inline_ignore_token="drill-sergeant: ignore-file-length",
            marker_mappings=marker_mappings,
            aaa_mode="strict",
            aaa_synonyms_enabled=True,
            aaa_builtin_synonyms=False,
            aaa_arrange_synonyms=arrange_synonyms,
            aaa_act_synonyms=act_synonyms,
            aaa_assert_synonyms=assert_synonyms,
        )

        # Assert - Verify custom values are correctly set
        assert config.enabled is False
        assert config.enforce_markers is False
        assert config.enforce_aaa is False
        assert config.enforce_file_length is False
        assert config.auto_detect_markers is False
        assert config.min_description_length == 5
        assert config.max_file_length == 500
        assert config.file_length_mode == "warn"
        assert config.file_length_exclude == ["tests/legacy/*"]
        assert config.file_length_inline_ignore is False
        assert config.file_length_inline_ignore_token == "drill-sergeant: ignore-file-length"
        assert config.marker_mappings == marker_mappings
        assert config.aaa_mode == "strict"
        assert config.aaa_synonyms_enabled is True
        assert config.aaa_builtin_synonyms is False
        assert config.aaa_arrange_synonyms == arrange_synonyms
        assert config.aaa_act_synonyms == act_synonyms
        assert config.aaa_assert_synonyms == assert_synonyms

    def test_from_pytest_config_with_defaults(self) -> None:
        """Test creating config from pytest config with defaults."""
        # Arrange - Set up mock pytest config
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        # Act - Create DrillSergeantConfig from pytest config
        config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify config has default values
        assert config.enabled is True
        assert config.enforce_markers is True
        assert config.enforce_aaa is True
        assert config.enforce_file_length is True
        assert config.auto_detect_markers is True
        assert config.min_description_length == 3
        assert config.max_file_length == 350
        assert config.file_length_mode == "error"
        assert config.file_length_exclude == []
        assert config.file_length_inline_ignore is True
        assert config.aaa_mode == "basic"

    def test_from_pytest_config_disabled_via_environment(self) -> None:
        """Test creating config when disabled via environment variable."""
        # Arrange - Set up mock pytest config
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        # Act - Create config with environment variable disabled
        with patch.dict(os.environ, {"DRILL_SERGEANT_ENABLED": "false"}):
            config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify config is disabled
        assert config.enabled is False

    def test_from_pytest_config_environment_variables_override(self) -> None:
        """Test that environment variables override pytest config."""
        # Arrange - Set up mock pytest config
        mock_config = Mock()
        mock_config.getini.side_effect = lambda x: (
            "true" if "enforce_markers" in x else None
        )

        # Act - Create config with environment variables
        with patch.dict(
            os.environ,
            {
                "DRILL_SERGEANT_ENFORCE_MARKERS": "false",
                "DRILL_SERGEANT_ENFORCE_AAA": "false",
                "DRILL_SERGEANT_AAA_MODE": "strict",
                "DRILL_SERGEANT_MIN_DESCRIPTION_LENGTH": "10",
                "DRILL_SERGEANT_MAX_FILE_LENGTH": "1000",
                "DRILL_SERGEANT_FILE_LENGTH_MODE": "warn",
                "DRILL_SERGEANT_FILE_LENGTH_EXCLUDE": "tests/legacy/*,tests/slow/*",
                "DRILL_SERGEANT_FILE_LENGTH_INLINE_IGNORE": "false",
            },
        ):
            config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify environment variables override pytest config
        assert config.enforce_markers is False
        assert config.enforce_aaa is False
        assert config.aaa_mode == "strict"
        assert config.min_description_length == 10
        assert config.max_file_length == 1000
        assert config.file_length_mode == "warn"
        assert config.file_length_exclude == ["tests/legacy/*", "tests/slow/*"]
        assert config.file_length_inline_ignore is False

    def test_from_pytest_config_boolean_environment_values(self) -> None:
        """Test various boolean environment variable values."""
        # Arrange - Set up mock pytest config and test cases
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("Yes", True),
            ("YES", True),
            ("on", True),
            ("On", True),
            ("ON", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("No", False),
            ("NO", False),
            ("off", False),
            ("Off", False),
            ("OFF", False),
        ]

        # Act - Test various boolean environment values
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"DRILL_SERGEANT_ENFORCE_MARKERS": env_value}):
                config = DrillSergeantConfig.from_pytest_config(mock_config)

                # Assert - Verify boolean values are correctly parsed
                assert (
                    config.enforce_markers is expected
                ), f"Failed for env value: {env_value}"

    def test_from_pytest_config_integer_environment_values(self) -> None:
        """Test integer environment variable values."""
        # Arrange - Set up mock pytest config
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        # Act - Create config with integer environment variables
        with patch.dict(
            os.environ,
            {
                "DRILL_SERGEANT_MIN_DESCRIPTION_LENGTH": "15",
                "DRILL_SERGEANT_MAX_FILE_LENGTH": "750",
            },
        ):
            config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify integer values are correctly parsed
        assert config.min_description_length == 15
        assert config.max_file_length == 750

    def test_from_pytest_config_early_return_when_disabled(self) -> None:
        """Test that config returns early when disabled globally."""
        # Arrange - Set up mock pytest config that returns disabled
        mock_config = Mock()
        mock_config.getini.side_effect = lambda x: (
            "false" if x == "drill_sergeant_enabled" else None
        )

        # Act - Create config when disabled globally
        config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify config is disabled and other values are defaults
        assert config.enabled is False
        assert config.enforce_markers is True
        assert config.enforce_aaa is True
        assert config.enforce_file_length is True
        assert config.auto_detect_markers is True
        assert config.min_description_length == 3
        assert config.max_file_length == 350
        assert config.file_length_mode == "error"
        assert config.file_length_exclude == []
        assert config.file_length_inline_ignore is True

    def test_from_pytest_config_pytest_config_values(self) -> None:
        """Test values from pytest config when no environment variables."""
        # Arrange - Set up mock pytest config with specific values
        mock_config = Mock()
        mock_config.getini.side_effect = lambda x: {
            "drill_sergeant_enforce_markers": "false",
            "drill_sergeant_enforce_aaa": "true",
            "drill_sergeant_aaa_mode": "strict",
            "drill_sergeant_min_description_length": "8",
            "drill_sergeant_max_file_length": "600",
            "drill_sergeant_file_length_mode": "warn",
            "drill_sergeant_file_length_exclude": "tests/integration/*,tests/e2e/*",
            "drill_sergeant_file_length_inline_ignore": "false",
        }.get(x)

        # Act - Create config from pytest config
        config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify pytest config values are used
        assert config.enforce_markers is False
        assert config.enforce_aaa is True
        assert config.aaa_mode == "strict"
        assert config.min_description_length == 8
        assert config.max_file_length == 600
        assert config.file_length_mode == "warn"
        assert config.file_length_exclude == ["tests/integration/*", "tests/e2e/*"]
        assert config.file_length_inline_ignore is False

    def test_from_pytest_config_aaa_synonym_settings(self) -> None:
        """Test AAA synonym configuration settings."""
        # Arrange - Set up mock pytest config with AAA synonym settings
        mock_config = Mock()
        mock_config.getini.side_effect = lambda x: {
            "drill_sergeant_aaa_synonyms_enabled": "true",
            "drill_sergeant_aaa_builtin_synonyms": "false",
            "drill_sergeant_aaa_arrange_synonyms": "setup,given",
            "drill_sergeant_aaa_act_synonyms": "when,execute",
            "drill_sergeant_aaa_assert_synonyms": "then,verify",
        }.get(x)

        # Act - Create config with AAA synonym settings
        config = DrillSergeantConfig.from_pytest_config(mock_config)

        # Assert - Verify AAA synonym settings are correctly parsed
        assert config.aaa_synonyms_enabled is True
        assert config.aaa_builtin_synonyms is False
        assert config.aaa_arrange_synonyms == ["setup", "given"]
        assert config.aaa_act_synonyms == ["when", "execute"]
        assert config.aaa_assert_synonyms == ["then", "verify"]

    def test_from_pytest_config_marker_mappings(self) -> None:
        """Test marker mappings configuration."""
        # Arrange - Set up mock pytest config with marker mappings
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        with patch(
            "pytest_drill_sergeant.config.get_marker_mappings"
        ) as mock_get_mappings:
            mock_get_mappings.return_value = {
                "unit": "test_unit",
                "integration": "test_integration",
            }

            # Act - Create config with marker mappings
            config = DrillSergeantConfig.from_pytest_config(mock_config)

            # Assert - Verify marker mappings are correctly set
            assert config.marker_mappings == {
                "unit": "test_unit",
                "integration": "test_integration",
            }
            mock_get_mappings.assert_called_once_with(mock_config)
