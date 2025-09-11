"""Unit tests for the utils.__init__.py module."""

from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.utils import (
    detect_test_type_from_path,
    extract_markers_from_config,
    get_available_markers,
    get_bool_option,
    get_default_marker_mappings,
    get_int_option,
    get_marker_mappings,
    get_synonym_list,
)


@pytest.mark.unit
class TestUtilsModuleImports:
    """Test that all expected utility functions are imported and accessible."""

    def test_detect_test_type_from_path_import(self) -> None:
        """Test that detect_test_type_from_path is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the detect_test_type_from_path function

        # Assert - Verify function is accessible and callable
        assert detect_test_type_from_path is not None
        assert callable(detect_test_type_from_path)

    def test_extract_markers_from_config_import(self) -> None:
        """Test that extract_markers_from_config is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the extract_markers_from_config function

        # Assert - Verify function is accessible and callable
        assert extract_markers_from_config is not None
        assert callable(extract_markers_from_config)

    def test_get_available_markers_import(self) -> None:
        """Test that get_available_markers is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_available_markers function

        # Assert - Verify function is accessible and callable
        assert get_available_markers is not None
        assert callable(get_available_markers)

    def test_get_bool_option_import(self) -> None:
        """Test that get_bool_option is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_bool_option function

        # Assert - Verify function is accessible and callable
        assert get_bool_option is not None
        assert callable(get_bool_option)

    def test_get_default_marker_mappings_import(self) -> None:
        """Test that get_default_marker_mappings is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_default_marker_mappings function

        # Assert - Verify function is accessible and callable
        assert get_default_marker_mappings is not None
        assert callable(get_default_marker_mappings)

    def test_get_int_option_import(self) -> None:
        """Test that get_int_option is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_int_option function

        # Assert - Verify function is accessible and callable
        assert get_int_option is not None
        assert callable(get_int_option)

    def test_get_marker_mappings_import(self) -> None:
        """Test that get_marker_mappings is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_marker_mappings function

        # Assert - Verify function is accessible and callable
        assert get_marker_mappings is not None
        assert callable(get_marker_mappings)

    def test_get_synonym_list_import(self) -> None:
        """Test that get_synonym_list is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the get_synonym_list function

        # Assert - Verify function is accessible and callable
        assert get_synonym_list is not None
        assert callable(get_synonym_list)

    def test_imported_functions_are_callable(self) -> None:
        """Test that all imported functions are callable."""
        # Arrange - Set up list of functions to test
        functions = [
            detect_test_type_from_path,
            extract_markers_from_config,
            get_available_markers,
            get_bool_option,
            get_default_marker_mappings,
            get_int_option,
            get_marker_mappings,
            get_synonym_list,
        ]

        # Act - Test each function

        # Assert - Verify all functions are callable
        for func in functions:
            assert callable(func), f"Function {func.__name__} should be callable"

    def test_functions_return_expected_types(self) -> None:
        """Test that functions return expected types when called with defaults."""
        # Arrange - Set up mock config for testing
        mock_config = Mock()
        mock_config.getini.side_effect = lambda _: None

        # Act - Call functions with default parameters
        result1 = get_default_marker_mappings()
        result2 = get_bool_option(mock_config, "test", "TEST", True)
        result3 = get_int_option(mock_config, "test", "TEST", 42)
        result4 = get_synonym_list(mock_config, "test", "TEST")

        # Assert - Verify functions return expected types
        assert isinstance(result1, dict)
        assert isinstance(result2, bool)
        assert isinstance(result3, int)
        assert isinstance(result4, list)
