"""Unit tests for the models module."""

import pytest

from pytest_drill_sergeant.models import AAAStatus, ValidationIssue


@pytest.mark.unit
class TestValidationIssue:
    """Test the ValidationIssue dataclass."""

    def test_validation_issue_creation(self) -> None:
        """Test creating ValidationIssue with all required fields."""
        # Arrange - Set up test data for ValidationIssue creation
        issue_type = "marker"
        message = "Test message"
        suggestion = "Test suggestion"

        # Act - Create ValidationIssue instance with all fields
        issue = ValidationIssue(
            issue_type=issue_type, message=message, suggestion=suggestion
        )

        # Assert - Verify all fields are correctly set
        assert issue.issue_type == issue_type
        assert issue.message == message
        assert issue.suggestion == suggestion

    def test_validation_issue_equality(self) -> None:
        """Test ValidationIssue equality comparison."""
        # Arrange - Create ValidationIssue instances for equality testing
        issue1 = ValidationIssue("marker", "Test", "Fix")
        issue2 = ValidationIssue("marker", "Test", "Fix")
        issue3 = ValidationIssue("aaa", "Test", "Fix")

        # Act - Compare ValidationIssue instances
        equal_result = issue1 == issue2
        not_equal_result = issue1 != issue3

        # Assert - Verify equality comparison works correctly
        assert equal_result
        assert not_equal_result


@pytest.mark.unit
class TestAAAStatus:
    """Test the AAAStatus dataclass."""

    def test_aaa_status_default_values(self) -> None:
        """Test AAAStatus with default values."""
        # Arrange - No setup needed for default values test

        # Act - Create AAAStatus with default values
        status = AAAStatus()

        # Assert - Verify all default values are correct
        assert status.arrange_found is False
        assert status.act_found is False
        assert status.assert_found is False
        assert status.issues == []

    def test_aaa_status_with_custom_values(self) -> None:
        """Test AAAStatus with custom values."""
        # Arrange - Set up custom values and issues for AAAStatus
        issues = [
            ValidationIssue("aaa", "Missing arrange", "Add # Arrange"),
            ValidationIssue("aaa", "Missing act", "Add # Act"),
        ]

        # Act - Create AAAStatus with custom values
        status = AAAStatus(
            arrange_found=True, act_found=False, assert_found=True, issues=issues
        )

        # Assert - Verify custom values are correctly set
        assert status.arrange_found is True
        assert status.act_found is False
        assert status.assert_found is True
        assert len(status.issues) == 2
        assert status.issues[0].issue_type == "aaa"

    def test_aaa_status_equality(self) -> None:
        """Test AAAStatus equality comparison."""
        # Arrange - Create AAAStatus instances for equality testing
        status1 = AAAStatus(arrange_found=True, act_found=True, assert_found=True)
        status2 = AAAStatus(arrange_found=True, act_found=True, assert_found=True)
        status3 = AAAStatus(arrange_found=False, act_found=True, assert_found=True)

        # Act - Compare AAAStatus instances
        equal_result = status1 == status2
        not_equal_result = status1 != status3

        # Assert - Verify equality comparison works correctly
        assert equal_result
        assert not_equal_result

    def test_aaa_status_string_representation(self) -> None:
        """Test AAAStatus string representation."""
        # Arrange - Create AAAStatus instance for string representation test
        status = AAAStatus(
            arrange_found=True,
            act_found=False,
            assert_found=True,
            issues=[ValidationIssue("aaa", "Test", "Fix")],
        )

        # Act - Convert AAAStatus to string
        str_repr = str(status)

        # Assert - Verify string representation contains expected values
        assert "AAAStatus" in str_repr
        assert "arrange_found=True" in str_repr
        assert "act_found=False" in str_repr
        assert "assert_found=True" in str_repr

    def test_validation_issue_string_representation(self) -> None:
        """Test ValidationIssue string representation."""
        # Arrange - Create ValidationIssue instance for string representation test
        issue = ValidationIssue(
            issue_type="marker", message="Test message", suggestion="Test suggestion"
        )

        # Act - Convert ValidationIssue to string
        str_repr = str(issue)

        # Assert - Verify string representation contains expected values
        assert "marker" in str_repr
        assert "Test message" in str_repr
        assert "Test suggestion" in str_repr
