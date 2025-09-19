"""Centralized configuration registry for pytest-drill-sergeant.

This module provides a single source of truth for all configuration,
eliminating the need to pass configs around throughout the system.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config_schema import DSConfig, create_default_config
from .profile_loader import ProfileConfigLoader


class ConfigRegistry:
    """Centralized configuration registry.

    This class provides a single source of truth for all configuration
    throughout the system. It loads configuration once and provides
    access to it from anywhere in the codebase.
    """

    _instance: ConfigRegistry | None = None
    _config: DSConfig | None = None
    _project_root: Path | None = None

    def __new__(cls) -> ConfigRegistry:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self,
        cli_args: dict[str, Any] | None = None,
        pytest_config: Any | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the configuration registry.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object
            project_root: Project root directory
        """
        if self._config is not None:
            # Already initialized
            return

        self._project_root = project_root or Path.cwd()

        try:
            # Load configuration using the profile loader
            loader = ProfileConfigLoader(self._project_root)
            self._config = loader.load_config(cli_args, pytest_config)
        except Exception as e:
            # Fallback to default configuration
            self._config = create_default_config()

            # Log the error if we have logging available
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning("Failed to load configuration, using defaults: %s", e)
            except ImportError:
                pass

    def get_config(self) -> DSConfig:
        """Get the current configuration.

        Returns:
            The current profile configuration

        Raises:
            RuntimeError: If configuration hasn't been initialized
        """
        if self._config is None:
            # Auto-initialize with defaults if not already done
            self.initialize()

        return self._config

    def reload_config(
        self,
        cli_args: dict[str, Any] | None = None,
        pytest_config: Any | None = None,
    ) -> None:
        """Reload configuration from sources.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object
        """
        self._config = None
        self.initialize(cli_args, pytest_config, self._project_root)

    def get_project_root(self) -> Path:
        """Get the project root directory.

        Returns:
            The project root directory
        """
        if self._project_root is None:
            self._project_root = Path.cwd()
        return self._project_root

    def is_initialized(self) -> bool:
        """Check if the configuration has been initialized.

        Returns:
            True if configuration is initialized
        """
        return self._config is not None

    def reset(self) -> None:
        """Reset the configuration registry (for testing)."""
        self._instance = None
        self._config = None
        self._project_root = None


# Global registry instance
_registry = ConfigRegistry()


def get_config_registry() -> ConfigRegistry:
    """Get the global configuration registry.

    Returns:
        The global configuration registry instance
    """
    return _registry


def initialize_config(
    cli_args: dict[str, Any] | None = None,
    pytest_config: Any | None = None,
    project_root: Path | None = None,
) -> None:
    """Initialize the global configuration registry.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object
        project_root: Project root directory
    """
    _registry.initialize(cli_args, pytest_config, project_root)


def get_config() -> DSConfig:
    """Get the current configuration from the global registry.

    Returns:
        The current profile configuration
    """
    return _registry.get_config()


def reload_config(
    cli_args: dict[str, Any] | None = None,
    pytest_config: Any | None = None,
) -> None:
    """Reload configuration in the global registry.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object
    """
    _registry.reload_config(cli_args, pytest_config)


def get_project_root() -> Path:
    """Get the project root directory from the global registry.

    Returns:
        The project root directory
    """
    return _registry.get_project_root()


def reset_config() -> None:
    """Reset the global configuration registry (for testing)."""
    _registry.reset()


# Convenience functions for common configuration access
def get_active_profile():
    """Get the active profile."""
    return get_config().profile


def get_rule_config(rule_name: str):
    """Get configuration for a specific rule."""
    config = get_config()
    return config.rules.get(rule_name)


def is_rule_enabled(rule_name: str) -> bool:
    """Check if a rule is enabled."""
    rule_config = get_rule_config(rule_name)
    return rule_config.enabled if rule_config else True


def get_rule_severity(rule_name: str):
    """Get the severity level for a rule."""
    rule_config = get_rule_config(rule_name)
    return rule_config.severity if rule_config and rule_config.severity else None


def should_fail_on_severity(severity) -> bool:
    """Check if a severity level should cause a failure."""
    # For now, always fail on ERROR level
    severity_value = severity.value if hasattr(severity, "value") else str(severity)
    return severity_value == "error"


def get_fail_on_level():
    """Get the current fail-on level."""
    # For now, always fail on ERROR level
    from .config_schema import SeverityLevel

    return SeverityLevel.ERROR


def get_output_formats() -> list[str]:
    """Get the configured output formats."""
    config = get_config()
    return [config.output.format.value]


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return get_config().output.verbose


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    # DSConfig doesn't have a quiet field, so return False
    return False
