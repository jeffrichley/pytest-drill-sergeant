"""Configuration manager for global configuration access."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.config import DrillSergeantConfig, load_config
from pytest_drill_sergeant.core.logging_utils import get_logger

if TYPE_CHECKING:
    from pathlib import Path


class ConfigManager:
    """Global configuration manager for the application."""

    _instance: ConfigManager | None = None
    _config: DrillSergeantConfig | None = None
    _project_root: Path | None = None

    def __new__(cls) -> ConfigManager:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        self._logger = get_logger(__name__)
        if self._config is None:
            self._config = None
            self._project_root = None

    def initialize(
        self,
        cli_args: dict[str, object] | None = None,
        pytest_config: object | None = None,  # External pytest boundary
        project_root: Path | None = None,
    ) -> DrillSergeantConfig:
        """Initialize the configuration manager.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object
            project_root: Project root directory

        Returns:
            Loaded configuration
        """
        # Reset configuration to allow re-initialization
        self.reset()

        self._project_root = project_root
        self._config = load_config(cli_args, pytest_config, project_root)

        self._logger.info("Configuration initialized with mode: %s", self._config.mode)
        return self._config

    def get_config(self) -> DrillSergeantConfig:
        """Get the current configuration.

        Returns:
            Current configuration

        Raises:
            RuntimeError: If configuration has not been initialized
        """
        if self._config is None:
            msg = "Configuration not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return self._config

    def reset(self) -> None:
        """Reset the configuration manager to initial state."""
        self._config = None
        self._project_root = None

    def reload_config(
        self,
        cli_args: dict[str, object] | None = None,
        pytest_config: object | None = None,
    ) -> DrillSergeantConfig:
        """Reload configuration from sources.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object

        Returns:
            Reloaded configuration
        """
        self._config = None
        return self.initialize(cli_args, pytest_config, self._project_root)

    def update_config(self, updates: dict[str, object]) -> DrillSergeantConfig:
        """Update configuration with new values.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            Updated configuration
        """
        if self._config is None:
            msg = "Configuration not initialized. Call initialize() first."
            raise RuntimeError(msg)

        # Create new config with updates
        current_data = self._config.model_dump()
        current_data.update(updates)

        self._config = DrillSergeantConfig(**current_data)
        self._logger.info("Configuration updated")
        return self._config

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled.

        Args:
            rule_id: Rule identifier

        Returns:
            True if rule is enabled
        """
        return self.get_config().is_rule_enabled(rule_id)

    def get_threshold(self, threshold_name: str, default: float = 0.0) -> float:
        """Get a threshold value.

        Args:
            threshold_name: Name of the threshold
            default: Default value if threshold not found

        Returns:
            Threshold value
        """
        return self.get_config().get_threshold(threshold_name, default)

    def get_budget(self, budget_type: str, default: int = 0) -> int:
        """Get a budget value.

        Args:
            budget_type: Type of budget (warn, error)
            default: Default value if budget not found

        Returns:
            Budget value
        """
        return self.get_config().get_budget(budget_type, default)

    def get_persona(self) -> str:
        """Get the current persona.

        Returns:
            Persona name
        """
        return self.get_config().persona

    def get_mode(self) -> str:
        """Get the current mode.

        Returns:
            Mode name
        """
        return self.get_config().mode

    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled.

        Returns:
            True if verbose mode is enabled
        """
        return self.get_config().verbose

    def is_quiet(self) -> bool:
        """Check if quiet mode is enabled.

        Returns:
            True if quiet mode is enabled
        """
        return self.get_config().quiet

    def should_fail_on_how(self) -> bool:
        """Check if tests should fail on low BIS scores.

        Returns:
            True if tests should fail on low BIS scores
        """
        return self.get_config().fail_on_how

    def get_sut_package(self) -> str | None:
        """Get the system under test package.

        Returns:
            SUT package name or None
        """
        return self.get_config().sut_package

    def get_output_formats(self) -> list[str]:
        """Get the output formats.

        Returns:
            List of output formats
        """
        return self.get_config().output_formats

    def get_json_report_path(self) -> str | None:
        """Get the JSON report path.

        Returns:
            JSON report path or None
        """
        return self.get_config().json_report_path

    def get_sarif_report_path(self) -> str | None:
        """Get the SARIF report path.

        Returns:
            SARIF report path or None
        """
        return self.get_config().sarif_report_path

    def get_mock_allowlist(self) -> set[str]:
        """Get the mock allowlist.

        Returns:
            Set of allowed mock patterns
        """
        return self.get_config().mock_allowlist

    def get_enabled_rules(self) -> set[str]:
        """Get the enabled rules.

        Returns:
            Set of enabled rule IDs
        """
        return self.get_config().enabled_rules

    def get_suppressed_rules(self) -> set[str]:
        """Get the suppressed rules.

        Returns:
            Set of suppressed rule IDs
        """
        return self.get_config().suppressed_rules


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> DrillSergeantConfig:
    """Get the global configuration.

    Returns:
        Global configuration

    Raises:
        RuntimeError: If configuration has not been initialized
    """
    return config_manager.get_config()


def initialize_config(
    cli_args: dict[str, object] | None = None,
    pytest_config: object | None = None,  # External pytest boundary
    project_root: Path | None = None,
) -> DrillSergeantConfig:
    """Initialize the global configuration.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object
        project_root: Project root directory

    Returns:
        Initialized configuration
    """
    return config_manager.initialize(cli_args, pytest_config, project_root)


def is_rule_enabled(rule_id: str) -> bool:
    """Check if a rule is enabled globally.

    Args:
        rule_id: Rule identifier

    Returns:
        True if rule is enabled
    """
    return config_manager.is_rule_enabled(rule_id)


def get_threshold(threshold_name: str, default: float = 0.0) -> float:
    """Get a threshold value globally.

    Args:
        threshold_name: Name of the threshold
        default: Default value if threshold not found

    Returns:
        Threshold value
    """
    return config_manager.get_threshold(threshold_name, default)


def get_budget(budget_type: str, default: int = 0) -> int:
    """Get a budget value globally.

    Args:
        budget_type: Type of budget (warn, error)
        default: Default value if budget not found

    Returns:
        Budget value
    """
    return config_manager.get_budget(budget_type, default)
