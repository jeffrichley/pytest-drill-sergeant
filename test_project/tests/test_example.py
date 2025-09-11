"""Test file that should trigger file length validation."""

import pytest


@pytest.mark.unit
class TestExample:
    """Test class for demonstrating plugin functionality."""

    def test_simple_function(self) -> None:
        """# Arrange - Simple test setup
        # Act - Execute simple operation
        # Assert - Verify result
        """
        # Arrange - Simple test setup
        value = 42

        # Act - Execute simple operation
        result = value * 2

        # Assert - Verify result
        assert result == 84

    def test_another_function(self) -> None:
        """# Arrange - Another test setup
        # Act - Execute another operation
        # Assert - Verify another result
        """
        # Arrange - Another test setup
        value = 10

        # Act - Execute another operation
        result = value + 5

        # Assert - Verify another result
        assert result == 15
