"""Unit tests for AAA validator functionality."""

from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.aaa import (
    _has_descriptive_comment,
)
from pytest_drill_sergeant.validators.marker import _validate_markers


@pytest.mark.unit
class TestHasDescriptiveComment:
    """Test descriptive comment validation."""

    def test_valid_descriptive_comment(self) -> None:
        """# Arrange - Comment line with proper dash and description
        # Act - Check if comment is descriptive
        # Assert - Returns True for valid descriptive comment
        """
        # Arrange - Comment with proper format
        comment_line = "# Arrange - Set up test data and mocks"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns True for valid comment
        assert result is True

    def test_comment_without_dash_returns_false(self) -> None:
        """# Arrange - Comment line without descriptive dash
        # Act - Check if comment is descriptive
        # Assert - Returns False for comment without dash
        """
        # Arrange - Comment without dash
        comment_line = "# Arrange setup code"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for no dash
        assert result is False

    def test_comment_with_short_description_returns_false(self) -> None:
        """# Arrange - Comment line with too short description
        # Act - Check if comment is descriptive
        # Assert - Returns False for short description
        """
        # Arrange - Comment with short description
        comment_line = "# Act - Do"

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for short description
        assert result is False

    def test_comment_with_empty_description_returns_false(self) -> None:
        """# Arrange - Comment line with empty description after dash
        # Act - Check if comment is descriptive
        # Assert - Returns False for empty description
        """
        # Arrange - Comment with empty description
        comment_line = "# Assert - "

        # Act - Check if descriptive
        result = _has_descriptive_comment(comment_line)

        # Assert - Returns False for empty description
        assert result is False


@pytest.mark.unit
class TestValidateMarkers:
    """Test marker validation functionality."""

    def test_validate_markers_with_existing_markers(self) -> None:
        """# Arrange - Mock pytest item with existing markers
        # Act - Validate markers on the item
        # Assert - Returns empty issues list
        """
        # Arrange - Mock item with existing markers
        mock_item = Mock()
        mock_item.iter_markers.return_value = [Mock()]  # Has markers
        config = DrillSergeantConfig()

        # Act - Validate markers
        issues = _validate_markers(mock_item, config)

        # Assert - No issues when markers exist
        assert issues == []

    def test_validate_markers_auto_detection_enabled_by_default(self) -> None:
        """# Arrange - Config with auto-detection enabled
        # Act - Check if auto-detection is enabled
        # Assert - Auto-detection is enabled by default
        """
        # Arrange - Default config
        config = DrillSergeantConfig()

        # Act & Assert - Auto-detection should be enabled by default
        assert config.auto_detect_markers is True

    @patch("pytest_drill_sergeant.utils.helpers.detect_test_type_from_path")
    def test_validate_markers_creates_issue_when_not_detectable(
        self, mock_detect: Mock
    ) -> None:
        """# Arrange - Mock pytest item without markers and not detectable
        # Act - Validate markers on the item
        # Assert - Creates marker validation issue
        """
        # Arrange - Mock item without markers and not detectable
        mock_item = Mock()
        mock_item.iter_markers.return_value = []  # No markers
        mock_item.name = "test_example"
        mock_detect.return_value = None
        config = DrillSergeantConfig()

        # Act - Validate markers
        issues = _validate_markers(mock_item, config)

        # Assert - Creates marker issue
        assert len(issues) == 1
        assert issues[0].issue_type == "marker"
        assert "test_example" in issues[0].message
        assert "must have at least one marker" in issues[0].message
