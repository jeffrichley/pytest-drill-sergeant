"""Unit tests for marker auto-detection path behavior."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.utils import detect_test_type_from_path


@pytest.mark.unit
@patch("pytest_drill_sergeant.utils.helpers.get_available_markers")
class TestMarkerPathBehavior:
    """Test nested path and custom mapping behavior for marker detection."""

    def test_nested_path_uses_first_directory_after_tests(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Nested test path and available integration marker
        # Act - Detect marker from path
        # Assert - First directory after tests is used
        """
        # Arrange - Nested path should resolve to first segment after tests
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/integration/api/test_endpoint.py")
        mock_get_markers.return_value = {"integration", "api", "unit"}
        config = DrillSergeantConfig()

        # Act - Resolve marker type from nested path
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Strategy uses first folder after tests (integration)
        assert result == "integration"

    def test_nested_path_applies_custom_mapping_on_first_directory(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Nested path with custom mapping for first directory
        # Act - Detect marker from path
        # Assert - Custom mapping is applied from first directory key
        """
        # Arrange - Map integration directory to api marker explicitly
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/integration/api/test_contract.py")
        mock_get_markers.return_value = {"integration", "api", "unit"}
        config = DrillSergeantConfig(marker_mappings={"integration": "api"})

        # Act - Resolve marker type from nested path with custom mapping
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Custom mapping on first segment wins
        assert result == "api"

    def test_unknown_nested_path_returns_none_with_no_mapping(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Nested unknown path without matching marker/mapping
        # Act - Detect marker from path
        # Assert - Returns None to enforce explicit classification
        """
        # Arrange - Unknown leading directory should not default silently
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/experimental/api/test_x.py")
        mock_get_markers.return_value = {"unit", "integration", "functional"}
        config = DrillSergeantConfig()

        # Act - Resolve marker type from nested unknown path
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Unknown path returns None (strict behavior)
        assert result is None
