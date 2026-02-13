"""Unit tests for AAA basic/strict mode behavior."""

from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import _validate_aaa_structure


@pytest.mark.unit
class TestAAAMode:
    """Test AAA enforcement differences between basic and strict modes."""

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_basic_mode_allows_duplicate_sections(self, mock_getsource: Mock) -> None:
        """# Arrange - Source with duplicate AAA section headers
        # Act - Validate with basic mode
        # Assert - No duplicate-section issue is reported
        """
        # Arrange - Duplicate Arrange section with all required sections present
        mock_item = Mock()
        mock_item.name = "test_basic_duplicate"
        mock_getsource.return_value = """
def test_basic_duplicate():
    # Arrange - setup one
    # Arrange - setup two
    # Act - execute action
    # Assert - verify outcome
    assert True
"""

        # Act - Validate in basic mode
        issues = _validate_aaa_structure(mock_item, DrillSergeantConfig(aaa_mode="basic"))

        # Assert - No strict-mode duplicate error
        assert issues == []

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_strict_mode_rejects_duplicate_sections(self, mock_getsource: Mock) -> None:
        """# Arrange - Source with duplicate AAA section headers
        # Act - Validate with strict mode
        # Assert - Duplicate section issue is reported
        """
        # Arrange - Duplicate Arrange section
        mock_item = Mock()
        mock_item.name = "test_strict_duplicate"
        mock_getsource.return_value = """
def test_strict_duplicate():
    # Arrange - setup one
    # Arrange - setup two
    # Act - execute action
    # Assert - verify outcome
    assert True
"""

        # Act - Validate in strict mode
        issues = _validate_aaa_structure(
            mock_item, DrillSergeantConfig(aaa_mode="strict")
        )

        # Assert - Strict mode reports duplicates
        assert any("duplicate AAA section" in issue.message for issue in issues)

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_strict_mode_rejects_out_of_order_sections(
        self, mock_getsource: Mock
    ) -> None:
        """# Arrange - Source with AAA sections out of order
        # Act - Validate with strict mode
        # Assert - Order issue is reported
        """
        # Arrange - Act appears before Arrange
        mock_item = Mock()
        mock_item.name = "test_strict_order"
        mock_getsource.return_value = """
def test_strict_order():
    # Act - execute action
    # Arrange - setup data
    # Assert - verify outcome
    assert True
"""

        # Act - Validate in strict mode
        issues = _validate_aaa_structure(
            mock_item, DrillSergeantConfig(aaa_mode="strict")
        )

        # Assert - Strict mode reports out-of-order sections
        assert any("out of order" in issue.message for issue in issues)
