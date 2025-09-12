"""Unit tests for error reporter functionality."""

from unittest.mock import Mock

import pytest
from _pytest.outcomes import Failed

from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.validators.error_reporter import _report_all_issues


@pytest.mark.unit
class TestReportAllIssues:
    """Test comprehensive issue reporting."""

    def test_report_all_issues_with_marker_and_aaa_issues(self) -> None:
        """# Arrange - Mock pytest item and mixed validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with comprehensive error message
        """
        # Arrange - Mock item and mixed validation issues
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="marker",
                message="Missing marker",
                suggestion="Add @pytest.mark.unit",
            ),
            ValidationIssue(
                issue_type="aaa",
                message="Missing Arrange",
                suggestion="Add '# Arrange - description'",
            ),
            ValidationIssue(
                issue_type="aaa",
                message="Missing Act",
                suggestion="Add '# Act - description'",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify comprehensive error message content
        error_message = str(exc_info.value)
        assert "test_example" in error_message
        assert "missing test annotations and missing AAA structure" in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" in error_message
        assert "📝 MISSING AAA STRUCTURE" in error_message
        assert "PROJECT REQUIREMENT" in error_message

    def test_report_all_issues_with_only_marker_issues(self) -> None:
        """# Arrange - Mock pytest item and only marker validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with marker-specific error message
        """
        # Arrange - Mock item and marker validation issues only
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="marker",
                message="Missing marker",
                suggestion="Add @pytest.mark.unit",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify marker-specific error message content
        error_message = str(exc_info.value)
        assert "missing test annotations" in error_message
        assert "missing AAA structure" not in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" in error_message
        assert "📝 MISSING AAA STRUCTURE" not in error_message

    def test_report_all_issues_with_only_aaa_issues(self) -> None:
        """# Arrange - Mock pytest item and only AAA validation issues
        # Act - Report all issues
        # Assert - Pytest.fail is called with AAA-specific error message
        """
        # Arrange - Mock item and AAA validation issues only
        mock_item = Mock()
        mock_item.name = "test_example"

        issues = [
            ValidationIssue(
                issue_type="aaa",
                message="Missing Arrange",
                suggestion="Add '# Arrange - description'",
            ),
        ]

        # Act - Call _report_all_issues and capture the pytest.fail exception
        with pytest.raises(Failed) as exc_info:
            _report_all_issues(mock_item, issues)

        # Assert - Verify AAA-specific error message content
        error_message = str(exc_info.value)
        assert "missing AAA structure" in error_message
        assert "missing test annotations" not in error_message
        assert "📝 MISSING AAA STRUCTURE" in error_message
        assert "🏷️  MISSING TEST CLASSIFICATION:" not in error_message
