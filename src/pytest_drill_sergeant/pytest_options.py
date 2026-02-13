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
        "drill_sergeant_marker_severity",
        type="string",
        default="error",
        help="Marker rule severity: 'error' (fail), 'warn' (warning only), or 'off' (disabled)",
    )
    parser.addini(
        "drill_sergeant_aaa_severity",
        type="string",
        default="error",
        help="AAA rule severity: 'error' (fail), 'warn' (warning only), or 'off' (disabled)",
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
        "drill_sergeant_file_length_mode",
        type="string",
        default="error",
        help="File length mode: 'error' (fail), 'warn' (warning only), or 'off' (disabled)",
    )
    parser.addini(
        "drill_sergeant_file_length_exclude",
        type="string",
        default="",
        help="Comma-separated glob patterns to exclude from file length checks",
    )
    parser.addini(
        "drill_sergeant_file_length_inline_ignore",
        type="bool",
        default=True,
        help="Allow inline file-level pragma to skip file length validation",
    )
    parser.addini(
        "drill_sergeant_file_length_inline_ignore_token",
        type="string",
        default="drill-sergeant: file-length ignore",
        help="Inline pragma token used to skip file length validation",
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
    parser.addini(
        "drill_sergeant_aaa_mode",
        type="string",
        default="basic",
        help="AAA enforcement mode: 'basic' (presence only) or 'strict' (presence + order + no duplicates)",
    )
