"""Context-based configuration system for pytest-drill-sergeant.

This module provides a thread-safe, context-based configuration system that replaces
the global singleton registry. It uses ContextVar to ensure proper isolation
between different execution contexts (e.g., pytest xdist workers).
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from .config_schema import DSConfig, create_default_config
from .profile_loader import ProfileConfigLoader

# Context variable for storing the current configuration
_current_config: ContextVar[DSConfig | None] = ContextVar("ds_config", default=None)

# Context variable for storing the project root
_project_root: ContextVar[Path | None] = ContextVar("ds_project_root", default=None)

# Context variable for storing initialization state
_initialized: ContextVar[bool] = ContextVar("ds_initialized", default=False)


class ConfigContext:
    """Context manager for configuration operations.

    This class provides thread-safe access to configuration throughout the system.
    It replaces the global singleton pattern with a context-based approach that
    works properly with pytest xdist and other multi-threaded scenarios.
    """

    def __init__(self, config: DSConfig | None = None):
        """Initialize the configuration context.

        Args:
            config: Optional configuration to set in this context
        """
        self._config = config
        self._project_root = None
        self._config_token = None
        self._project_root_token = None
        self._initialized_token = None
        self._original_config = None
        self._original_project_root = None
        self._original_initialized = None

    def __enter__(self) -> ConfigContext:
        """Enter the configuration context."""
        # Store original state for restoration
        self._original_config = _current_config.get()
        self._original_project_root = _project_root.get()
        self._original_initialized = _initialized.get()

        # Set new state if provided
        if self._config is not None:
            self._config_token = _current_config.set(self._config)
        if self._project_root is not None:
            self._project_root_token = _project_root.set(self._project_root)
        if self._config is not None:
            self._initialized_token = _initialized.set(True)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the configuration context."""
        # Restore original state
        if self._config_token is not None:
            _current_config.reset(self._config_token)
        elif self._original_config is not None:
            _current_config.set(self._original_config)
        else:
            _current_config.set(None)

        if self._project_root_token is not None:
            _project_root.reset(self._project_root_token)
        elif self._original_project_root is not None:
            _project_root.set(self._original_project_root)
        else:
            _project_root.set(None)

        if self._initialized_token is not None:
            _initialized.reset(self._initialized_token)
        else:
            _initialized.set(self._original_initialized)

    @classmethod
    def get_current_config(cls) -> DSConfig:
        """Get the current configuration from the context.

        Returns:
            The current configuration

        Raises:
            RuntimeError: If no configuration is set in the current context
        """
        config = _current_config.get()
        if config is None:
            # Auto-initialize with defaults if not set
            default_config = create_default_config()
            _current_config.set(default_config)
            return default_config
        return config

    @classmethod
    def set_config(cls, config: DSConfig) -> None:
        """Set the configuration in the current context.

        Args:
            config: Configuration to set
        """
        _current_config.set(config)
        _initialized.set(True)

    @classmethod
    def get_project_root(cls) -> Path:
        """Get the project root from the context.

        Returns:
            The project root directory
        """
        root = _project_root.get()
        if root is None:
            root = Path.cwd()
            _project_root.set(root)
        return root

    @classmethod
    def set_project_root(cls, root: Path) -> None:
        """Set the project root in the current context.

        Args:
            root: Project root directory
        """
        _project_root.set(root)

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if configuration is initialized in the current context.

        Returns:
            True if configuration is initialized
        """
        return _initialized.get()

    @classmethod
    def initialize(
        cls,
        cli_args: dict[str, Any] | None = None,
        pytest_config: Any | None = None,
        project_root: Path | None = None,
        force_reload: bool = False,
    ) -> DSConfig:
        """Initialize configuration in the current context.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object
            project_root: Project root directory
            force_reload: Force reload even if already initialized

        Returns:
            The loaded configuration
        """
        if cls.is_initialized() and not force_reload:
            # Already initialized, return current config
            return cls.get_current_config()

        # Set project root
        if project_root is not None:
            cls.set_project_root(project_root)
        else:
            cls.set_project_root(Path.cwd())

        try:
            # Load configuration using the profile loader
            loader = ProfileConfigLoader(cls.get_project_root())
            config = loader.load_config(cli_args, pytest_config)
            cls.set_config(config)
            return config
        except Exception as e:
            # Fallback to default configuration
            default_config = create_default_config()
            cls.set_config(default_config)

            # Log the error if we have logging available
            try:
                logger = logging.getLogger(__name__)
                logger.warning("Failed to load configuration, using defaults: %s", e)
            except Exception:
                pass

            return default_config

    @classmethod
    def reload(
        cls,
        cli_args: dict[str, Any] | None = None,
        pytest_config: Any | None = None,
    ) -> DSConfig:
        """Reload configuration in the current context.

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object

        Returns:
            The reloaded configuration
        """
        # Reload configuration with force_reload=True
        return cls.initialize(
            cli_args, pytest_config, cls.get_project_root(), force_reload=True
        )

    @classmethod
    def reset(cls) -> None:
        """Reset the configuration context (for testing)."""
        _current_config.set(None)
        _project_root.set(None)
        _initialized.set(False)


# Convenience functions for backward compatibility and ease of use
def get_config() -> DSConfig:
    """Get the current configuration from the context.

    Returns:
        The current configuration
    """
    return ConfigContext.get_current_config()


def set_config(config: DSConfig) -> None:
    """Set the configuration in the current context.

    Args:
        config: Configuration to set
    """
    ConfigContext.set_config(config)


def initialize_config(
    cli_args: dict[str, Any] | None = None,
    pytest_config: Any | None = None,
    project_root: Path | None = None,
    force_reload: bool = False,
) -> DSConfig:
    """Initialize configuration in the current context.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object
        project_root: Project root directory
        force_reload: Force reload even if already initialized

    Returns:
        The loaded configuration
    """
    return ConfigContext.initialize(cli_args, pytest_config, project_root, force_reload)


def reload_config(
    cli_args: dict[str, Any] | None = None,
    pytest_config: Any | None = None,
) -> DSConfig:
    """Reload configuration in the current context.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object

    Returns:
        The reloaded configuration
    """
    return ConfigContext.reload(cli_args, pytest_config)


def get_project_root() -> Path:
    """Get the project root from the context.

    Returns:
        The project root directory
    """
    return ConfigContext.get_project_root()


def reset_config() -> None:
    """Reset the configuration context (for testing)."""
    ConfigContext.reset()


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
