"""Helper utility functions for pytest-drill-sergeant."""

from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_drill_sergeant.config import DrillSergeantConfig


def get_bool_option(
    config: pytest.Config, ini_name: str, env_var: str, default: bool
) -> bool:
    """Get boolean option from pytest config or environment variable."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val is not None:
        return env_val.lower() in ("true", "1", "yes", "on")

    # Then pytest config
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val is not None:
                return str(ini_val).lower() in ("true", "1", "yes", "on")
        except (ValueError, AttributeError):
            pass

    # Fallback: try to read from ini file directly
    try:
        ini_path = getattr(config, "inipath", None)
        if ini_path and ini_path.exists():
            parser = configparser.ConfigParser()
            parser.read(ini_path)
            if "pytest" in parser and ini_name in parser["pytest"]:
                value = parser["pytest"][ini_name]
                return str(value).lower() in ("true", "1", "yes", "on")
    except Exception:
        pass

    return default


def get_int_option(
    config: pytest.Config, ini_name: str, env_var: str, default: int
) -> int:
    """Get integer option from pytest config or environment variable."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            pass

    # Then pytest config
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val is not None:
                return int(ini_val)
        except (ValueError, AttributeError):
            pass

    # Fallback: try to read from ini file directly
    try:
        ini_path = getattr(config, "inipath", None)
        if ini_path and ini_path.exists():
            parser = configparser.ConfigParser()
            parser.read(ini_path)
            if "pytest" in parser and ini_name in parser["pytest"]:
                value = parser["pytest"][ini_name]
                return int(value)
    except Exception:
        pass

    return default


def get_string_option(
    config: pytest.Config, ini_name: str, env_var: str, default: str
) -> str:
    """Get string option from pytest config or environment variable."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val is not None:
        return env_val

    # Then pytest config
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val is not None:
                return str(ini_val)
        except (ValueError, AttributeError):
            pass

    # Fallback: try to read from ini file directly
    try:
        ini_path = getattr(config, "inipath", None)
        if ini_path and ini_path.exists():
            parser = configparser.ConfigParser()
            parser.read(ini_path)
            if "pytest" in parser and ini_name in parser["pytest"]:
                value = parser["pytest"][ini_name]
                return str(value)
    except Exception:
        pass

    return default


def get_synonym_list(config: pytest.Config, ini_name: str, env_var: str) -> list[str]:
    """Get comma-separated synonym list from pytest config or environment variable."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val:
        return [synonym.strip() for synonym in env_val.split(",") if synonym.strip()]

    # Then pytest config
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val:
                return [
                    synonym.strip() for synonym in ini_val.split(",") if synonym.strip()
                ]
        except (ValueError, AttributeError):
            pass

    return []


def get_marker_mappings(config: pytest.Config) -> dict[str, str]:
    """Get marker mappings with proper layered priority: env vars > pytest.ini.

    Each layer builds on the previous one, allowing selective overrides
    rather than complete replacement.
    """
    mappings = {}

    try:
        # Layer 1: Base mappings from pytest.ini
        if hasattr(config, "getini"):
            try:
                mappings_str = config.getini("drill_sergeant_marker_mappings")
                if mappings_str:
                    # Parse the mappings string
                    # Format: "dir1=marker1,dir2=marker2"
                    for mapping in mappings_str.split(","):
                        if "=" in mapping:
                            dir_name, marker_name = mapping.split("=", 1)
                            mappings[dir_name.strip()] = marker_name.strip()
            except (ValueError, AttributeError):
                pass

        # Layer 2: Environment variable overrides (highest priority)
        # This ADDS to or OVERRIDES specific mappings from pytest.ini
        env_mappings = os.getenv("DRILL_SERGEANT_MARKER_MAPPINGS")
        if env_mappings:
            # Format: "dir1=marker1,dir2=marker2"
            for mapping in env_mappings.split(","):
                if "=" in mapping:
                    dir_name, marker_name = mapping.split("=", 1)
                    mappings[dir_name.strip()] = marker_name.strip()

        # TODO: Add proper TOML parsing for [tool.drill_sergeant.marker_mappings]
        # This requires more sophisticated TOML handling that we can add later

        return mappings
    except Exception:
        return {}


def get_available_markers(item: pytest.Item) -> set[str]:
    """Get available markers from pytest configuration or environment variable."""
    # Check environment variable first (highest priority)
    env_markers = os.getenv("DRILL_SERGEANT_MARKERS")
    if env_markers:
        markers = {m.strip() for m in env_markers.split(",") if m.strip()}
        if markers:
            return markers

    # Try to get markers from pytest config
    markers = extract_markers_from_config(item.config)

    # Fallback to common markers if none found
    return (
        markers
        if markers
        else {"unit", "integration", "functional", "e2e", "performance"}
    )


def extract_markers_from_config(config: pytest.Config) -> set[str]:
    """Extract marker names from pytest configuration."""
    try:
        markers = set()
        if hasattr(config, "_getini"):
            marker_entries = config._getini("markers") or []
            for marker_entry in marker_entries:
                # Marker format: "name: description"
                marker_name = marker_entry.split(":")[0].strip()
                if marker_name:
                    markers.add(marker_name)
        return markers
    except Exception:
        return set()


def get_default_marker_mappings() -> dict[str, str]:
    """Get the default directory-to-marker mappings when no config is available."""
    return {
        # Standard test types
        "unit": "unit",
        "integration": "integration",
        "functional": "functional",
        "e2e": "e2e",
        "performance": "performance",
        # Common aliases
        "fixtures": "unit",  # Test fixtures are typically unit-level
        "func": "functional",  # Common shorthand
        "end2end": "e2e",  # Alternative naming
        "perf": "performance",  # Common shorthand
        "load": "performance",  # Load testing is performance testing
        "benchmark": "performance",  # Benchmarking is performance testing
        # Common alternate names
        "api": "integration",  # API tests are typically integration
        "smoke": "integration",  # Smoke tests are typically integration
        "acceptance": "e2e",  # Acceptance tests are typically e2e
        "contract": "integration",  # Contract tests are typically integration
        "system": "e2e",  # System tests are typically e2e
    }


def detect_test_type_from_path(
    item: pytest.Item, config: DrillSergeantConfig
) -> str | None:
    """Detect test type based on the test file's package location.

    Uses available markers, custom mappings, and default mappings.
    Returns the appropriate marker name or None if detection fails.
    """
    try:
        # Get available markers from pytest config
        available_markers = get_available_markers(item)

        # Get the test file path
        test_file = Path(item.fspath)

        # Check if we're in a test directory structure
        if "tests" in test_file.parts:
            # Find the tests directory and get the subdirectory
            tests_index = test_file.parts.index("tests")
            if tests_index + 1 < len(test_file.parts):
                test_type = test_file.parts[tests_index + 1]

                # 1. First try custom mappings from configuration (highest priority)
                if config.marker_mappings and test_type in config.marker_mappings:
                    custom_marker = config.marker_mappings[test_type]
                    if custom_marker in available_markers:
                        return custom_marker

                # 2. Then try exact match with available markers
                if test_type in available_markers:
                    return test_type

                # 3. Finally try default mappings (built-in intelligent defaults)
                default_mappings = get_default_marker_mappings()
                if test_type in default_mappings:
                    default_marker = default_mappings[test_type]
                    if default_marker in available_markers:
                        return default_marker

        return None
    except Exception:
        return None
