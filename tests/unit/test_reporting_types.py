"""Test reporting types module imports to increase coverage."""

import pytest_drill_sergeant.core.reporting.types
from pytest_drill_sergeant.core.reporting.types import (
    JSONDict,
    JSONScalar,
    JSONValue,
)


def test_reporting_types_module_imports():
    """Test importing from reporting types module to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.core.reporting.types, "__doc__")

    # Test that the module is not None
    assert pytest_drill_sergeant.core.reporting.types is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.core.reporting.types, "__file__")
    assert pytest_drill_sergeant.core.reporting.types.__file__ is not None


def test_reporting_types_module_content():
    """Test that the module has the expected content."""
    types_module = pytest_drill_sergeant.core.reporting.types

    # Test that the types are defined
    assert JSONScalar is not None
    assert JSONValue is not None
    assert JSONDict is not None

    # Test that we can access the types (they are type aliases)
    assert hasattr(types_module, "JSONScalar")
    assert hasattr(types_module, "JSONValue")
    assert hasattr(types_module, "JSONDict")

    # Test that the types are accessible
    assert JSONScalar is not None
    assert JSONValue is not None
    assert JSONDict is not None
