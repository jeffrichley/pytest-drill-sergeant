"""Unit tests for AAA structure validation functionality."""

from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import _validate_aaa_structure


@pytest.mark.unit
class TestValidateAaaStructure:
    """Test AAA structure validation."""

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_with_complete_structure(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source with complete AAA structure
        # Act - Validate AAA structure
        # Assert - Returns no issues for complete structure
        """
        # Arrange - Complete AAA structure source
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Act - Execute the function under test
    result = process_data(data)

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - No issues for complete structure
        assert issues == []

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_arrange_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Arrange section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Arrange section
        """
        # Arrange - Source missing Arrange section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Act - Execute the function under test
    result = process_data()

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Arrange
        arrange_issues = [i for i in issues if "missing 'Arrange'" in i.message]
        assert len(arrange_issues) == 1
        assert arrange_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_act_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Act section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Act section
        """
        # Arrange - Source missing Act section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Assert - Verify the expected outcome
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Act
        act_issues = [i for i in issues if "missing 'Act'" in i.message]
        assert len(act_issues) == 1
        assert act_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_missing_assert_section(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function source missing Assert section
        # Act - Validate AAA structure
        # Assert - Returns issue for missing Assert section
        """
        # Arrange - Source missing Assert section
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange - Set up test data and dependencies
    data = {"key": "value"}

    # Act - Execute the function under test
    result = process_data(data)
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issue for missing Assert
        assert_issues = [i for i in issues if "missing 'Assert'" in i.message]
        assert len(assert_issues) == 1
        assert assert_issues[0].issue_type == "aaa"

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_with_non_descriptive_comments(
        self, mock_getsource: Mock
    ) -> None:
        """# Arrange - Mock function source with non-descriptive AAA comments
        # Act - Validate AAA structure
        # Assert - Returns issues for non-descriptive comments
        """
        # Arrange - Source with non-descriptive comments
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.return_value = """
def test_example():
    # Arrange
    data = {"key": "value"}

    # Act
    result = process_data(data)

    # Assert
    assert result == expected_value
"""

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - Has issues for missing sections (since comments don't follow proper format)
        assert len(issues) == 3
        for issue in issues:
            assert issue.issue_type == "aaa"
            assert "missing" in issue.message and "section" in issue.message

    @patch("pytest_drill_sergeant.validators.aaa.inspect.getsource")
    def test_validate_aaa_handles_os_error(self, mock_getsource: Mock) -> None:
        """# Arrange - Mock function that raises OSError when getting source
        # Act - Validate AAA structure
        # Assert - Returns no issues when OSError occurs
        """
        # Arrange - Mock that raises OSError
        mock_item = Mock()
        mock_item.name = "test_example"
        mock_getsource.side_effect = OSError("Cannot get source")

        # Act - Validate AAA structure
        config = DrillSergeantConfig()
        issues = _validate_aaa_structure(mock_item, config)

        # Assert - No issues when OSError occurs
        assert issues == []
