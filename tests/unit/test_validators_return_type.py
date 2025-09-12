"""Unit tests for the validators.return_type module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators.return_type import ReturnTypeValidator


@pytest.mark.unit
class TestReturnTypeValidator:
    """Test the ReturnTypeValidator class."""

    def test_is_enabled_when_enforce_return_type_true(self) -> None:
        """Test that validator is enabled when enforce_return_type is True."""
        # Arrange - Set up config with return type enforcement enabled
        config = DrillSergeantConfig(enforce_return_type=True)
        validator = ReturnTypeValidator()

        # Act - Check if validator is enabled
        result = validator.is_enabled(config)

        # Assert - Verify validator is enabled
        assert result is True

    def test_is_enabled_when_enforce_return_type_false(self) -> None:
        """Test that validator is disabled when enforce_return_type is False."""
        # Arrange - Set up config with return type enforcement disabled
        config = DrillSergeantConfig(enforce_return_type=False)
        validator = ReturnTypeValidator()

        # Act - Check if validator is enabled
        result = validator.is_enabled(config)

        # Assert - Verify validator is disabled
        assert result is False

    def test_validate_disabled_mode_returns_empty_list(self) -> None:
        """Test that validate returns empty list when mode is disabled."""
        # Arrange - Set up config with disabled return type mode
        config = DrillSergeantConfig(
            enforce_return_type=True, return_type_mode="disabled"
        )
        validator = ReturnTypeValidator()
        item = Mock()

        # Act - Validate test item
        result = validator.validate(item, config)

        # Assert - Verify no issues are returned
        assert result == []

    def test_validate_error_mode_with_missing_return_type(self) -> None:
        """Test that validate reports error when return type is missing in error mode."""
        # Arrange - Set up config with error mode and create test file without return type
        config = DrillSergeantConfig(enforce_return_type=True, return_type_mode="error")
        validator = ReturnTypeValidator()

        # Create a temporary test file without return type
        test_content = """
def test_example():
    assert True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            temp_file = Path(f.name)

        try:
            # Create mock item
            item = Mock()
            item.fspath = temp_file
            item.name = "test_example"
            item.function = Mock()
            item.function.__name__ = "test_example"

            # Act - Validate test item
            result = validator.validate(item, config)

            # Assert - Verify error is reported
            assert len(result) == 1
            assert result[0].issue_type == "return_type"
            assert "missing return type annotation" in result[0].message
            assert "-> None" in result[0].suggestion

        finally:
            temp_file.unlink()

    def test_validate_error_mode_with_existing_return_type(self) -> None:
        """Test that validate reports no error when return type exists."""
        # Arrange - Set up config with error mode and create test file with return type
        config = DrillSergeantConfig(enforce_return_type=True, return_type_mode="error")
        validator = ReturnTypeValidator()

        # Create a temporary test file with return type
        test_content = """
def test_example() -> None:
    assert True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            temp_file = Path(f.name)

        try:
            # Create mock item
            item = Mock()
            item.fspath = temp_file
            item.name = "test_example"
            item.function = Mock()
            item.function.__name__ = "test_example"

            # Act - Validate test item
            result = validator.validate(item, config)

            # Assert - Verify no issues are reported
            assert len(result) == 0

        finally:
            temp_file.unlink()

    def test_validate_auto_fix_mode_modifies_file(self) -> None:
        """Test that validate modifies file when in auto_fix mode."""
        # Arrange - Set up config with auto_fix mode and create test file without return type
        config = DrillSergeantConfig(
            enforce_return_type=True, return_type_mode="auto_fix"
        )
        validator = ReturnTypeValidator()

        # Create a temporary test file without return type
        test_content = """
def test_example():
    assert True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_content)
            temp_file = Path(f.name)

        try:
            # Create mock item
            item = Mock()
            item.fspath = temp_file
            item.name = "test_example"
            item.function = Mock()
            item.function.__name__ = "test_example"

            # Act - Validate test item (should auto-fix)
            result = validator.validate(item, config)

            # Assert - Verify no issues reported and file was modified
            assert len(result) == 0
            modified_content = temp_file.read_text()
            assert "def test_example() -> None:" in modified_content

        finally:
            temp_file.unlink()

    def test_validate_with_invalid_file_returns_warning(self) -> None:
        """Test that validate returns warning when file cannot be parsed."""
        # Arrange - Set up config with error mode and create invalid test file
        config = DrillSergeantConfig(enforce_return_type=True, return_type_mode="error")
        validator = ReturnTypeValidator()

        # Create a temporary invalid file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("invalid python syntax {")
            temp_file = Path(f.name)

        try:
            # Create mock item
            item = Mock()
            item.fspath = temp_file
            item.name = "test_example"

            # Act - Validate test item
            result = validator.validate(item, config)

            # Assert - Verify warning is reported
            assert len(result) == 1
            assert result[0].issue_type == "return_type"
            assert "Could not parse file" in result[0].message

        finally:
            temp_file.unlink()

    def test_validate_with_no_file_path_returns_empty_list(self) -> None:
        """Test that validate returns empty list when item has no file path."""
        # Arrange - Set up config and mock item without file path
        config = DrillSergeantConfig(enforce_return_type=True, return_type_mode="error")
        validator = ReturnTypeValidator()
        item = Mock()
        item.fspath = None

        # Act - Validate test item
        result = validator.validate(item, config)

        # Assert - Verify no issues are returned
        assert result == []
