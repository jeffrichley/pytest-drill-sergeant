"""Unit tests for models and path detection functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.utils import detect_test_type_from_path


@pytest.mark.unit
class TestValidationIssue:
    """Test the ValidationIssue dataclass."""

    def test_validation_issue_creation(self) -> None:
        """# Arrange - ValidationIssue with all fields
        # Act - Create a ValidationIssue instance
        # Assert - All fields are properly set
        """
        # Arrange - ValidationIssue with all required fields
        issue_type = "marker"
        message = "Test message"
        suggestion = "Test suggestion"

        # Act - Create ValidationIssue instance
        issue = ValidationIssue(
            issue_type=issue_type, message=message, suggestion=suggestion
        )

        # Assert - All fields are correctly set
        assert issue.issue_type == issue_type
        assert issue.message == message
        assert issue.suggestion == suggestion


@pytest.mark.unit
@patch("pytest_drill_sergeant.utils.helpers.get_available_markers")
class TestDetectTestTypeFromPath:
    """Test test type detection from file paths."""

    def test_detect_unit_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with unit test path
        # Act - Detect test type from path
        # Assert - Returns 'unit' marker
        """
        # Arrange - Mock item with unit test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/unit/test_example.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns unit marker
        assert result == "unit"

    def test_detect_integration_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with integration test path
        # Act - Detect test type from path
        # Assert - Returns 'integration' marker
        """
        # Arrange - Mock item with integration test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/integration/test_api.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns integration marker
        assert result == "integration"

    def test_detect_functional_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with functional test path
        # Act - Detect test type from path
        # Assert - Returns 'functional' marker
        """
        # Arrange - Mock item with functional test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/functional/test_workflow.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns functional marker
        assert result == "functional"

    def test_detect_e2e_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with e2e test path
        # Act - Detect test type from path
        # Assert - Returns 'e2e' marker
        """
        # Arrange - Mock item with e2e test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/e2e/test_full_flow.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns e2e marker
        assert result == "e2e"

    def test_detect_performance_test_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with performance test path
        # Act - Detect test type from path
        # Assert - Returns 'performance' marker
        """
        # Arrange - Mock item with performance test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/performance/test_load.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns performance marker
        assert result == "performance"

    def test_detect_fixtures_as_unit_from_path(self, mock_get_markers: Mock) -> None:
        """# Arrange - Mock pytest item with fixtures test path
        # Act - Detect test type from path
        # Assert - Returns 'unit' marker for fixtures
        """
        # Arrange - Mock item with fixtures test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/fixtures/test_data.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns unit marker for fixtures
        assert result == "unit"

    def test_detect_unknown_test_type_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item with unknown test path
        # Act - Detect test type from path
        # Assert - Returns None for unknown type
        """
        # Arrange - Mock item with unknown test path
        mock_item = Mock()
        mock_item.fspath = Path("/project/tests/unknown/test_something.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None for unknown type
        assert result is None

    def test_detect_no_tests_directory_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item with no tests directory
        # Act - Detect test type from path
        # Assert - Returns None when no tests directory
        """
        # Arrange - Mock item with no tests directory
        mock_item = Mock()
        mock_item.fspath = Path("/project/src/test_module.py")
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None when no tests directory
        assert result is None

    def test_detect_exception_handling_returns_none(
        self, mock_get_markers: Mock
    ) -> None:
        """# Arrange - Mock pytest item that raises exception
        # Act - Detect test type from path
        # Assert - Returns None when exception occurs
        """
        # Arrange - Mock item that raises exception
        mock_item = Mock()
        mock_item.fspath = Mock(side_effect=Exception("Test exception"))
        mock_get_markers.return_value = {
            "unit",
            "integration",
            "functional",
            "e2e",
            "performance",
        }
        config = DrillSergeantConfig()

        # Act - Detect test type
        result = detect_test_type_from_path(mock_item, config)

        # Assert - Returns None when exception occurs
        assert result is None
