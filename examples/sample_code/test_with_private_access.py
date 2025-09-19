"""Sample test file with private access violations for testing the detector."""

import pytest
from myapp._internal import secret_function
from _private_module import something
from myapp.public import normal_function


def test_private_import_violation():
    """Test that uses private imports."""
    result = secret_function()
    assert result == "expected"


def test_private_attribute_access():
    """Test that accesses private attributes."""
    obj = SomeClass()
    obj._private_attr = "value"
    result = obj._internal_data
    assert result is not None


def test_private_method_call():
    """Test that calls private methods."""
    obj = SomeClass()
    obj._private_method()
    result = obj._internal_function()
    assert result == "expected"


def test_mixed_violations():
    """Test with multiple types of private access violations."""
    from myapp._internal import another_secret

    obj = SomeClass()
    obj._private_attr = "value"
    obj._private_method()

    # Nested private access
    data = obj.nested._private_data
    obj.nested._private_method()

    assert data is not None


def test_clean_test():
    """Test with no private access violations."""
    from myapp.public import normal_function

    obj = SomeClass()
    result = obj.public_method()
    assert result == "expected"


class SomeClass:
    """Sample class for testing."""

    def __init__(self):
        self._private_attr = None
        self.public_attr = None
        self.nested = NestedClass()

    def _private_method(self):
        return "private"

    def _internal_function(self):
        return "internal"

    def public_method(self):
        return "public"


class NestedClass:
    """Nested class for testing."""

    def __init__(self):
        self._private_data = "private"
        self.public_data = "public"

    def _private_method(self):
        return "nested_private"

    def public_method(self):
        return "nested_public"
