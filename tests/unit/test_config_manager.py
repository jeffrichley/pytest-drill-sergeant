"""Tests for the configuration manager."""

from unittest.mock import MagicMock, patch

import pytest

from pytest_drill_sergeant.core.config import DrillSergeantConfig
from pytest_drill_sergeant.core.config_manager import (
    ConfigManager,
    config_manager,
    get_budget,
    get_config,
    get_threshold,
    initialize_config,
    is_rule_enabled,
)
from tests.constants import (
    BUDGET_ERROR,
    CUSTOM_BUDGET_WARN,
    CUSTOM_THRESHOLD,
    CUSTOM_THRESHOLD_ALT,
    EXPECTED_ERROR_COUNT_2,
)


class TestConfigManager:
    """Test the ConfigManager class."""

    def setup_method(self) -> None:
        """Reset the singleton before each test."""
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_singleton_pattern(self) -> None:
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()

        assert manager1 is manager2
        assert manager1 is ConfigManager._instance

    def test_initialize_config(self) -> None:
        """Test configuration initialization."""
        manager = ConfigManager()

        cli_args: dict[str, object] = {"mode": "strict", "persona": "snoop_dogg"}
        pytest_config = MagicMock()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(mode="strict", persona="snoop_dogg")
            mock_load.return_value = mock_config

            result = manager.initialize(cli_args, pytest_config)

            assert result is mock_config
            assert manager.get_config() is mock_config
            mock_load.assert_called_once_with(cli_args, pytest_config, None)

    def test_initialize_config_twice(self) -> None:
        """Test that initializing twice re-initializes the config."""
        manager = ConfigManager()

        cli_args: dict[str, object] = {"mode": "strict"}
        pytest_config = MagicMock()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config1 = DrillSergeantConfig(mode="strict")
            mock_config2 = DrillSergeantConfig(mode="strict")
            mock_load.side_effect = [mock_config1, mock_config2]

            # First initialization
            result1 = manager.initialize(cli_args, pytest_config)

            # Second initialization should re-initialize
            result2 = manager.initialize(cli_args, pytest_config)

            assert result1 is mock_config1
            assert result2 is mock_config2
            assert result1 is not result2  # Different instances due to reset
            assert (
                mock_load.call_count == EXPECTED_ERROR_COUNT_2
            )  # Should be called twice

    def test_get_config_not_initialized(self) -> None:
        """Test getting config when not initialized."""
        manager = ConfigManager()

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            manager.get_config()

    def test_reload_config(self) -> None:
        """Test configuration reloading."""
        manager = ConfigManager()

        # Initialize first time
        cli_args1: dict[str, object] = {"mode": "advisory"}
        pytest_config = MagicMock()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config1 = DrillSergeantConfig(mode="advisory")
            mock_config2 = DrillSergeantConfig(mode="strict")
            mock_load.side_effect = [mock_config1, mock_config2]

            # First initialization
            manager.initialize(cli_args1, pytest_config)
            assert manager.get_config().mode == "advisory"

            # Reload with new args
            cli_args2: dict[str, object] = {"mode": "strict"}
            result = manager.reload_config(cli_args2, pytest_config)

            assert result is mock_config2
            assert manager.get_config().mode == "strict"
            assert mock_load.call_count == EXPECTED_ERROR_COUNT_2

    def test_update_config(self) -> None:
        """Test configuration updates."""
        manager = ConfigManager()

        # Initialize
        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(mode="advisory", persona="drill_sergeant")
            mock_load.return_value = mock_config

            manager.initialize()

            # Update configuration
            updates: dict[str, object] = {"mode": "strict", "persona": "snoop_dogg"}
            result = manager.update_config(updates)

            assert result.mode == "strict"
            assert result.persona == "snoop_dogg"
            assert manager.get_config().mode == "strict"

    def test_update_config_not_initialized(self) -> None:
        """Test updating config when not initialized."""
        manager = ConfigManager()

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            manager.update_config({"mode": "strict"})

    def test_is_rule_enabled(self) -> None:
        """Test rule enabled checking."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(
                enabled_rules={"aaa_comments", "static_clones"},
                suppressed_rules={"static_clones"},
            )
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.is_rule_enabled("aaa_comments") is True
            assert manager.is_rule_enabled("static_clones") is False
            assert manager.is_rule_enabled("private_access") is False

    def test_get_threshold(self) -> None:
        """Test threshold retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(thresholds={"custom_threshold": 42.0})
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_threshold("custom_threshold") == CUSTOM_THRESHOLD
            assert (
                manager.get_threshold("nonexistent", CUSTOM_THRESHOLD_ALT)
                == CUSTOM_THRESHOLD_ALT
            )

    def test_get_budget(self) -> None:
        """Test budget retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(budgets={"warn": 15, "error": 5})
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_budget("warn") == CUSTOM_BUDGET_WARN
            assert manager.get_budget("error") == BUDGET_ERROR
            assert manager.get_budget("nonexistent", 0) == 0

    def test_get_persona(self) -> None:
        """Test persona retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(persona="snoop_dogg")
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_persona() == "snoop_dogg"

    def test_get_mode(self) -> None:
        """Test mode retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(mode="strict")
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_mode() == "strict"

    def test_is_verbose(self) -> None:
        """Test verbose mode checking."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(verbose=True)
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.is_verbose() is True

    def test_is_quiet(self) -> None:
        """Test quiet mode checking."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(quiet=True)
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.is_quiet() is True

    def test_should_fail_on_how(self) -> None:
        """Test fail on how checking."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(fail_on_how=True)
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.should_fail_on_how() is True

    def test_get_sut_package(self) -> None:
        """Test SUT package retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(sut_package="myapp")
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_sut_package() == "myapp"

    def test_get_output_formats(self) -> None:
        """Test output formats retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(output_formats=["terminal", "json"])
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_output_formats() == ["terminal", "json"]

    def test_get_json_report_path(self) -> None:
        """Test JSON report path retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(json_report_path="/tmp/report.json")
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_json_report_path() == "/tmp/report.json"

    def test_get_sarif_report_path(self) -> None:
        """Test SARIF report path retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(sarif_report_path="/tmp/report.sarif")
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_sarif_report_path() == "/tmp/report.sarif"

    def test_get_mock_allowlist(self) -> None:
        """Test mock allowlist retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(mock_allowlist={"custom.*", "test.*"})
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_mock_allowlist() == {"custom.*", "test.*"}

    def test_get_enabled_rules(self) -> None:
        """Test enabled rules retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(
                enabled_rules={"aaa_comments", "private_access"}
            )
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_enabled_rules() == {"aaa_comments", "private_access"}

    def test_get_suppressed_rules(self) -> None:
        """Test suppressed rules retrieval."""
        manager = ConfigManager()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(suppressed_rules={"static_clones"})
            mock_load.return_value = mock_config

            manager.initialize()

            assert manager.get_suppressed_rules() == {"static_clones"}


class TestGlobalFunctions:
    """Test the global configuration functions."""

    def setup_method(self) -> None:
        """Reset the singleton before each test."""
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_get_config_not_initialized(self) -> None:
        """Test get_config when not initialized."""
        # Reset configuration manager to ensure clean state
        config_manager.reset()

        with pytest.raises(RuntimeError, match="Configuration not initialized"):
            get_config()

    def test_initialize_config(self) -> None:
        """Test initialize_config function."""
        cli_args: dict[str, object] = {"mode": "strict"}
        pytest_config = MagicMock()

        with patch(
            "pytest_drill_sergeant.core.config_manager.load_config"
        ) as mock_load:
            mock_config = DrillSergeantConfig(mode="strict")
            mock_load.return_value = mock_config

            result = initialize_config(cli_args, pytest_config)

            assert result is mock_config
            assert get_config() is mock_config

    def test_is_rule_enabled_global(self) -> None:
        """Test global is_rule_enabled function."""
        # Reset the singleton
        ConfigManager._instance = None
        ConfigManager._config = None

        with patch(
            "pytest_drill_sergeant.core.config_manager.config_manager"
        ) as mock_manager:
            mock_manager.is_rule_enabled.side_effect = (
                lambda rule: rule == "aaa_comments"
            )

            assert is_rule_enabled("aaa_comments") is True
            assert is_rule_enabled("private_access") is False

    def test_get_threshold_global(self) -> None:
        """Test global get_threshold function."""
        # Reset the singleton
        ConfigManager._instance = None
        ConfigManager._config = None

        with patch(
            "pytest_drill_sergeant.core.config_manager.config_manager"
        ) as mock_manager:
            mock_manager.get_threshold.side_effect = lambda key, default=0: (
                42.0 if key == "custom_threshold" else default
            )

            assert get_threshold("custom_threshold") == CUSTOM_THRESHOLD
            assert (
                get_threshold("nonexistent", CUSTOM_THRESHOLD_ALT)
                == CUSTOM_THRESHOLD_ALT
            )

    def test_get_budget_global(self) -> None:
        """Test global get_budget function."""
        # Reset the singleton
        ConfigManager._instance = None
        ConfigManager._config = None

        with patch(
            "pytest_drill_sergeant.core.config_manager.config_manager"
        ) as mock_manager:
            mock_manager.get_budget.side_effect = lambda key, default=0: {
                "warn": 15,
                "error": 5,
            }.get(key, default)

            assert get_budget("warn") == CUSTOM_BUDGET_WARN
            assert get_budget("error") == BUDGET_ERROR
            assert get_budget("nonexistent", 0) == 0
