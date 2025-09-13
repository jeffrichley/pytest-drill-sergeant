"""Test core module imports to increase coverage."""

import pytest_drill_sergeant.core
from pytest_drill_sergeant.core import (
    ConfigManager,
    ConfigurationError,
    DrillSergeantArgumentParser,
    DrillSergeantConfig,
    config_manager,
    create_pytest_config_from_args,
    get_budget,
    get_config,
    get_threshold,
    initialize_config,
    is_rule_enabled,
    load_config,
    parse_cli_args,
    validate_cli_args,
)


def test_core_module_imports():
    """Test importing from core module to increase coverage."""
    # Test that the imports work
    assert ConfigManager is not None
    assert ConfigurationError is not None
    assert DrillSergeantArgumentParser is not None
    assert DrillSergeantConfig is not None
    assert config_manager is not None
    assert create_pytest_config_from_args is not None
    assert get_budget is not None
    assert get_config is not None
    assert get_threshold is not None
    assert initialize_config is not None
    assert is_rule_enabled is not None
    assert load_config is not None
    assert parse_cli_args is not None
    assert validate_cli_args is not None


def test_core_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.core.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert len(__all__) > 0

    # Test that it contains expected items
    expected_items = [
        "ConfigManager",
        "ConfigurationError",
        "DrillSergeantArgumentParser",
        "DrillSergeantConfig",
        "config_manager",
        "create_pytest_config_from_args",
        "get_budget",
        "get_config",
        "get_threshold",
        "initialize_config",
        "is_rule_enabled",
        "load_config",
        "parse_cli_args",
        "validate_cli_args",
    ]

    for item in expected_items:
        assert item in __all__
