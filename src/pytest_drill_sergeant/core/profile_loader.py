"""Profile configuration loader for pytest-drill-sergeant.

This module loads profile-based configuration from multiple sources:
1. CLI arguments (highest priority)
2. Environment variables
3. pytest.ini
4. pyproject.toml
5. Default values (lowest priority)
"""

from __future__ import annotations

import configparser
import os
import tomllib
from pathlib import Path
from typing import Any

from .config_schema import (
    DSConfig,
    Profile,
    create_default_config,
)


class ProfileConfigLoader:
    """Loads profile-based configuration from multiple sources."""

    def __init__(self, project_root: Path | None = None):
        """Initialize the configuration loader.

        Args:
            project_root: Root directory for the project (defaults to current working directory)
        """
        self.project_root = project_root or Path.cwd()

    def load_config(
        self,
        cli_args: dict[str, Any] | None = None,
        pytest_config: Any | None = None,
    ) -> DSConfig:
        """Load configuration from all sources.

        Configuration hierarchy (highest to lowest priority):
        1. CLI arguments
        2. Environment variables
        3. pytest.ini
        4. pyproject.toml
        5. Default values

        Args:
            cli_args: Command line arguments
            pytest_config: Pytest configuration object (unused but kept for compatibility)

        Returns:
            Loaded and validated configuration
        """
        # Start with defaults
        config_data = self._get_defaults()

        # Load from pyproject.toml
        pyproject_config = self._load_pyproject_toml()
        if pyproject_config:
            config_data.update(pyproject_config)

        # Load from pytest.ini
        pytest_ini_config = self._load_pytest_ini()
        if pytest_ini_config:
            config_data.update(pytest_ini_config)

        # Load from environment variables
        env_config = self._load_environment_variables()
        if env_config:
            config_data.update(env_config)

        # Load from CLI arguments (highest priority)
        if cli_args:
            config_data.update(cli_args)

        # Create and validate configuration
        return self._create_ds_config(config_data)

    def _get_defaults(self) -> dict[str, Any]:
        """Get default configuration values."""
        return {
            "profile": "standard",
            "project_root": str(self.project_root),
        }

    def _load_pyproject_toml(self) -> dict[str, Any] | None:
        """Load configuration from pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"

        if not pyproject_path.exists():
            return None

        try:
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)

            drill_sergeant_config = data.get("tool", {}).get(
                "pytest-drill-sergeant", {}
            )
            if not drill_sergeant_config:
                return None

            return self._convert_pyproject_config(drill_sergeant_config)

        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _load_pytest_ini(self) -> dict[str, Any] | None:
        """Load configuration from pytest.ini."""
        pytest_ini_path = self.project_root / "pytest.ini"

        if not pytest_ini_path.exists():
            return None

        try:
            config = configparser.ConfigParser()
            config.read(pytest_ini_path)

            if "tool:pytest-drill-sergeant" not in config:
                return None

            section = config["tool:pytest-drill-sergeant"]
            return self._convert_pytest_ini_config(dict(section))

        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _load_environment_variables(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        env_config: dict[str, Any] = {}

        # Map environment variables to config keys
        env_mappings = {
            "DRILL_SERGEANT_PROFILE": "profile",
            "DRILL_SERGEANT_CI_PROFILE": "ci_profile",
            "DRILL_SERGEANT_FAIL_ON": "fail_on",
            "DRILL_SERGEANT_REPORT": "report",
            "DRILL_SERGEANT_VERBOSE": "verbose",
            "DRILL_SERGEANT_QUIET": "quiet",
            "DRILL_SERGEANT_JSON_REPORT": "json_report_path",
            "DRILL_SERGEANT_SARIF_REPORT": "sarif_report_path",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ["verbose", "quiet"]:
                    env_config[config_key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    env_config[config_key] = value

        return env_config

    def _convert_pyproject_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Convert pyproject.toml configuration to our format."""
        converted: dict[str, Any] = {}

        # Handle direct mappings
        direct_mappings = [
            "profile",
            "ci_profile",
            "fail_on",
            "report",
            "verbose",
            "quiet",
            "json_report_path",
            "sarif_report_path",
        ]

        for key in direct_mappings:
            value = config.get(key)
            if value is not None:
                converted[key] = value

        # Handle output_formats
        if "output_formats" in config:
            converted["output_formats"] = config["output_formats"]

        # Handle rules
        if "rules" in config:
            converted["rules"] = config["rules"]

        # Handle profiles
        if "profiles" in config:
            converted["profiles"] = config["profiles"]

        return converted

    def _convert_pytest_ini_config(self, config: dict[str, str]) -> dict[str, Any]:
        """Convert pytest.ini configuration to our format."""
        converted: dict[str, Any] = {}

        for key, value in config.items():
            converted[key] = self._convert_config_value(key, value)

        return converted

    def _convert_config_value(self, key: str, value: str) -> Any:
        """Convert a single configuration value based on its key."""
        # Direct string mappings
        if key in [
            "profile",
            "ci_profile",
            "fail_on",
            "report",
            "json_report_path",
            "sarif_report_path",
        ]:
            return value

        # Boolean mappings
        if key in ["verbose", "quiet"]:
            return value.lower() in ("true", "1", "yes", "on")

        # List mappings
        if key == "output_formats":
            return [fmt.strip() for fmt in value.split(",") if fmt.strip()]

        # Complex mappings (for now, just return as string - could be enhanced)
        if key in ["rules", "profiles"]:
            # For pytest.ini, these would need to be in a specific format
            # For now, we'll just return the string and let the parser handle it
            return value

        return value

    def _create_ds_config(self, config_data: dict[str, Any]) -> DSConfig:
        """Create DSConfig from configuration data.

        Args:
            config_data: Configuration data dictionary

        Returns:
            Validated DSConfig instance
        """
        # Convert project_root to Path if it's a string
        if "project_root" in config_data and isinstance(
            config_data["project_root"], str
        ):
            config_data["project_root"] = Path(config_data["project_root"])

        # Convert profile string to Profile enum if needed
        if "profile" in config_data and isinstance(config_data["profile"], str):
            try:
                config_data["profile"] = Profile(config_data["profile"])
            except ValueError:
                # Invalid profile, use default
                config_data["profile"] = Profile.STANDARD

        # Create DSConfig with validation
        try:
            # Ensure we have default profiles if not provided
            if "profiles" not in config_data or not config_data["profiles"]:
                default_config = create_default_config()
                config_data["profiles"] = default_config.profiles

            # Filter out fields that DSConfig doesn't accept
            dsconfig_fields = set(DSConfig.model_fields.keys())
            filtered_config_data = {
                k: v for k, v in config_data.items() if k in dsconfig_fields
            }

            return DSConfig(**filtered_config_data)
        except Exception:
            # Fallback to default config if validation fails
            default_config = create_default_config()
            default_config.project_root = self.project_root
            return default_config


def load_profile_config(
    cli_args: dict[str, Any] | None = None,
    pytest_config: Any | None = None,
    project_root: Path | None = None,
) -> DSConfig:
    """Load profile-based configuration from all sources.

    This is the main entry point for loading profile configuration.

    Args:
        cli_args: Command line arguments
        pytest_config: Pytest configuration object (external boundary)
        project_root: Project root directory

    Returns:
        Loaded and validated configuration
    """
    loader = ProfileConfigLoader(project_root)
    return loader.load_config(cli_args, pytest_config)
