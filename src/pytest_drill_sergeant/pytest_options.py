"""Pytest configuration options for drill-sergeant plugin."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register configuration options for the drill-sergeant plugin."""
    # Core plugin options
    parser.addini(
        "drill_sergeant_enabled",
        type="bool",
        default=True,
        help="Enable/disable the drill-sergeant plugin",
    )
    parser.addini(
        "drill_sergeant_enforce_markers",
        type="bool",
        default=True,
        help="Enforce test marker validation",
    )
    parser.addini(
        "drill_sergeant_enforce_aaa",
        type="bool",
        default=True,
        help="Enforce AAA (Arrange-Act-Assert) structure",
    )
    parser.addini(
        "drill_sergeant_enforce_file_length",
        type="bool",
        default=True,
        help="Enforce maximum file length limits",
    )
    parser.addini(
        "drill_sergeant_enforce_return_type",
        type="bool",
        default=True,
        help="Enforce return type annotations on test functions",
    )
    parser.addini(
        "drill_sergeant_auto_detect_markers",
        type="bool",
        default=True,
        help="Auto-detect test markers from directory structure",
    )

    # File length options
    parser.addini(
        "drill_sergeant_max_file_length",
        type="string",
        default="350",
        help="Maximum allowed lines per test file",
    )
    parser.addini(
        "drill_sergeant_min_description_length",
        type="string",
        default="3",
        help="Minimum length for test descriptions",
    )

    # Marker mapping options
    parser.addini(
        "drill_sergeant_marker_mappings",
        type="string",
        default="",
        help="Custom marker mappings (JSON format)",
    )

    # AAA synonym options
    parser.addini(
        "drill_sergeant_aaa_synonyms_enabled",
        type="bool",
        default=False,
        help="Enable custom AAA synonym recognition",
    )
    parser.addini(
        "drill_sergeant_aaa_builtin_synonyms",
        type="bool",
        default=True,
        help="Use built-in AAA synonyms",
    )

    # Return type validation options
    parser.addini(
        "drill_sergeant_return_type_mode",
        type="string",
        default="error",
        help="Return type validation mode: 'error' (report issues), 'auto_fix' (automatically add -> None), or 'disabled' (skip validation)",
    )
