"""Sample test file with no private access violations."""

import pytest
from myapp.public import normal_function
from myapp.api import public_api


def test_clean_functionality():
    """Test that uses only public APIs."""
    result = normal_function()
    assert result == "expected"


def test_public_api_usage():
    """Test that uses public API correctly."""
    api = public_api()
    result = api.get_data()
    assert result is not None


def test_proper_test_structure():
    """Test with proper AAA structure."""
    # Arrange
    obj = SomeClass()
    expected = "expected_value"
    
    # Act
    result = obj.public_method()
    
    # Assert
    assert result == expected


class SomeClass:
    """Sample class with only public methods."""
    
    def __init__(self):
        self.public_attr = "public"
    
    def public_method(self):
        return "public"
    
    def another_public_method(self):
        return "another_public"
