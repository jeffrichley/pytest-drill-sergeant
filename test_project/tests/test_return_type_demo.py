"""Demo tests for return type validation."""

def test_without_return_type() -> None:
    """Test function without return type annotation - should trigger validator."""
    # Arrange - Set up test data
    expected = True

    # Act - Perform test action
    result = True

    # Assert - Verify result
    assert result == expected


def test_with_return_type() -> None:
    """Test function with return type annotation - should pass validation."""
    # Arrange - Set up test data
    expected = True

    # Act - Perform test action
    result = True

    # Assert - Verify result
    assert result == expected


def test_with_wrong_return_type() -> str:
    """Test function with wrong return type annotation - should pass validation."""
    # Arrange - Set up test data
    expected = "hello"

    # Act - Perform test action
    result = "hello"

    # Assert - Verify result
    assert result == expected
    return result
