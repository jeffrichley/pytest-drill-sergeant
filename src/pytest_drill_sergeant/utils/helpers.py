"""Helper utility functions for pytest-drill-sergeant."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

    from pytest_drill_sergeant.config import DrillSergeantConfig

# Runtime import for function signatures
import pytest  # noqa: TC002

INI_TO_TOOL_KEY = {
    "drill_sergeant_enabled": "enabled",
    "drill_sergeant_enforce_markers": "enforce_markers",
    "drill_sergeant_enforce_aaa": "enforce_aaa",
    "drill_sergeant_enforce_file_length": "enforce_file_length",
    "drill_sergeant_auto_detect_markers": "auto_detect_markers",
    "drill_sergeant_min_description_length": "min_description_length",
    "drill_sergeant_max_file_length": "max_file_length",
    "drill_sergeant_file_length_mode": "file_length_mode",
    "drill_sergeant_file_length_exclude": "file_length_exclude",
    "drill_sergeant_file_length_inline_ignore": "file_length_inline_ignore",
    "drill_sergeant_file_length_inline_ignore_token": "file_length_inline_ignore_token",
    "drill_sergeant_aaa_synonyms_enabled": "aaa_synonyms_enabled",
    "drill_sergeant_aaa_builtin_synonyms": "aaa_builtin_synonyms",
    "drill_sergeant_aaa_arrange_synonyms": "aaa_arrange_synonyms",
    "drill_sergeant_aaa_act_synonyms": "aaa_act_synonyms",
    "drill_sergeant_aaa_assert_synonyms": "aaa_assert_synonyms",
    "drill_sergeant_marker_mappings": "marker_mappings",
}


def _to_bool(value: object) -> bool | None:
    """Safely coerce values to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    if isinstance(value, int):
        return value != 0
    return None


def _to_int(value: object) -> int | None:
    """Safely coerce values to int."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _parse_list(value: object) -> list[str]:
    """Parse config values into a string list."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _parse_mapping_string(mappings_str: str) -> dict[str, str]:
    """Parse mapping text with format 'dir=marker,dir2=marker2'."""
    mappings: dict[str, str] = {}
    for mapping in mappings_str.split(","):
        if "=" not in mapping:
            continue
        dir_name, marker_name = mapping.split("=", 1)
        dir_name = dir_name.strip()
        marker_name = marker_name.strip()
        if dir_name and marker_name:
            mappings[dir_name] = marker_name
    return mappings


def _get_project_root(config: pytest.Config) -> Path | None:
    """Resolve project root from pytest config."""
    rootpath = getattr(config, "rootpath", None)
    if rootpath is not None:
        try:
            return Path(rootpath)
        except Exception:
            pass

    inipath = getattr(config, "inipath", None)
    if inipath is not None:
        try:
            return Path(inipath).parent
        except Exception:
            pass

    return None


def _load_tool_drill_sergeant_config(config: pytest.Config) -> dict[str, object]:
    """Load [tool.drill_sergeant] from pyproject.toml if available."""
    project_root = _get_project_root(config)
    if project_root is None:
        return {}

    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    try:
        with pyproject_path.open("rb") as f:
            pyproject_data = tomllib.load(f)
    except Exception:
        return {}

    tool_section = pyproject_data.get("tool")
    if not isinstance(tool_section, dict):
        return {}

    ds_section = tool_section.get("drill_sergeant")
    if not isinstance(ds_section, dict):
        return {}

    return ds_section


def _get_tool_value(config: pytest.Config, ini_name: str) -> object | None:
    """Read a setting value from [tool.drill_sergeant]."""
    tool_config = _load_tool_drill_sergeant_config(config)
    key = INI_TO_TOOL_KEY.get(ini_name, ini_name)
    if key in tool_config:
        return tool_config[key]
    if ini_name in tool_config:
        return tool_config[ini_name]
    return None


def get_bool_option(
    config: pytest.Config, ini_name: str, env_var: str, default: bool
) -> bool:
    """Get boolean option with precedence: env > pytest > tool > default."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val is not None:
        parsed = _to_bool(env_val)
        if parsed is not None:
            return parsed

    # Then pytest config (pytest.ini / pyproject [tool.pytest.ini_options])
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val is not None:
                parsed = _to_bool(ini_val)
                if parsed is not None:
                    return parsed
        except (ValueError, AttributeError):
            pass

    # Then [tool.drill_sergeant] in pyproject.toml
    tool_val = _get_tool_value(config, ini_name)
    parsed_tool = _to_bool(tool_val) if tool_val is not None else None
    if parsed_tool is not None:
        return parsed_tool

    return default


def _get_int_from_env(env_var: str) -> int | None:
    """Get integer from environment variable."""
    env_val = os.getenv(env_var)
    return _to_int(env_val) if env_val is not None else None


def _get_int_from_config(config: pytest.Config, ini_name: str) -> int | None:
    """Get integer from pytest config."""
    if hasattr(config, "getini"):
        try:
            return _to_int(config.getini(ini_name))
        except (ValueError, AttributeError):
            pass
    return None


def get_int_option(
    config: pytest.Config, ini_name: str, env_var: str, default: int
) -> int:
    """Get integer option with precedence: env > pytest > tool > default."""
    # Environment variable takes precedence
    env_val = _get_int_from_env(env_var)
    if env_val is not None:
        return env_val

    # Then pytest config
    config_val = _get_int_from_config(config, ini_name)
    if config_val is not None:
        return config_val

    # Then [tool.drill_sergeant] in pyproject.toml
    tool_val = _get_tool_value(config, ini_name)
    parsed_tool = _to_int(tool_val) if tool_val is not None else None
    if parsed_tool is not None:
        return parsed_tool

    return default


def get_string_option(
    config: pytest.Config, ini_name: str, env_var: str, default: str
) -> str:
    """Get string option with precedence: env > pytest > tool > default."""
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

    # Then [tool.drill_sergeant] in pyproject.toml
    tool_val = _get_tool_value(config, ini_name)
    if tool_val is not None:
        return str(tool_val)

    return default


def get_synonym_list(config: pytest.Config, ini_name: str, env_var: str) -> list[str]:
    """Get synonym list with precedence: env > pytest > tool > default."""
    # Environment variable takes precedence
    env_val = os.getenv(env_var)
    if env_val:
        return _parse_list(env_val)

    # Then pytest config
    if hasattr(config, "getini"):
        try:
            ini_val = config.getini(ini_name)
            if ini_val:
                return _parse_list(ini_val)
        except (ValueError, AttributeError):
            pass

    # Then [tool.drill_sergeant] in pyproject.toml
    tool_val = _get_tool_value(config, ini_name)
    if tool_val is not None:
        return _parse_list(tool_val)

    return []


def get_marker_mappings(config: pytest.Config) -> dict[str, str]:
    """Get marker mappings with layered priority: env > pytest > tool.

    Each layer builds on the previous one and can override specific keys.
    """
    mappings: dict[str, str] = {}

    try:
        # Layer 1: Base mappings from [tool.drill_sergeant] in pyproject.toml
        tool_config = _load_tool_drill_sergeant_config(config)
        tool_mappings = tool_config.get("marker_mappings")
        if isinstance(tool_mappings, dict):
            mappings.update(
                {
                    str(dir_name).strip(): str(marker_name).strip()
                    for dir_name, marker_name in tool_mappings.items()
                    if str(dir_name).strip() and str(marker_name).strip()
                }
            )
        elif isinstance(tool_mappings, str):
            mappings.update(_parse_mapping_string(tool_mappings))

        # Layer 2: pytest config mappings
        if hasattr(config, "getini"):
            try:
                mappings_str = config.getini("drill_sergeant_marker_mappings")
                if mappings_str:
                    mappings.update(_parse_mapping_string(str(mappings_str)))
            except (ValueError, AttributeError):
                pass

        # Layer 3: Environment variable overrides
        env_mappings = os.getenv("DRILL_SERGEANT_MARKER_MAPPINGS")
        if env_mappings:
            mappings.update(_parse_mapping_string(env_mappings))

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
