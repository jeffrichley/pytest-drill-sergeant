"""Direct test of core __init__.py to increase coverage."""

import pytest_drill_sergeant.core


def test_core_init_direct():
    """Test core __init__.py directly to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.core, "__all__")
    assert hasattr(pytest_drill_sergeant.core, "__doc__")

    # Test __all__ content
    all_items = pytest_drill_sergeant.core.__all__
    assert isinstance(all_items, list)
    assert len(all_items) > 0

    # Test that we can access the module's attributes
    assert hasattr(pytest_drill_sergeant.core, "ConfigManager")
    assert hasattr(pytest_drill_sergeant.core, "ConfigurationError")
    assert hasattr(pytest_drill_sergeant.core, "DrillSergeantArgumentParser")
    assert hasattr(pytest_drill_sergeant.core, "DrillSergeantConfig")
    assert hasattr(pytest_drill_sergeant.core, "config_manager")
    assert hasattr(pytest_drill_sergeant.core, "create_pytest_config_from_args")
    assert hasattr(pytest_drill_sergeant.core, "get_budget")
    assert hasattr(pytest_drill_sergeant.core, "get_config")
    assert hasattr(pytest_drill_sergeant.core, "get_threshold")
    assert hasattr(pytest_drill_sergeant.core, "initialize_config")
    assert hasattr(pytest_drill_sergeant.core, "is_rule_enabled")
    assert hasattr(pytest_drill_sergeant.core, "load_config")
    assert hasattr(pytest_drill_sergeant.core, "parse_cli_args")
    assert hasattr(pytest_drill_sergeant.core, "validate_cli_args")

    # Test that the module is not None
    assert pytest_drill_sergeant.core is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.core, "__file__")
    assert pytest_drill_sergeant.core.__file__ is not None
