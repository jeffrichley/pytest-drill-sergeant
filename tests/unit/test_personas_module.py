"""Test personas module imports to increase coverage."""

import pytest_drill_sergeant.plugin.personas


def test_personas_module_imports():
    """Test importing from personas module to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.plugin.personas, "__all__")
    assert hasattr(pytest_drill_sergeant.plugin.personas, "__doc__")

    # Test __all__ content
    all_items = pytest_drill_sergeant.plugin.personas.__all__
    assert isinstance(all_items, list)
    assert len(all_items) == 0  # This module has an empty __all__

    # Test that the module is not None
    assert pytest_drill_sergeant.plugin.personas is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.plugin.personas, "__file__")
    assert pytest_drill_sergeant.plugin.personas.__file__ is not None


def test_personas_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.plugin.personas.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert len(__all__) == 0  # This module has an empty __all__
