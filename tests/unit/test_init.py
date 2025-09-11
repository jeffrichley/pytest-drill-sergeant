"""Unit tests for the main __init__.py module."""

import pytest

from pytest_drill_sergeant import (
    AAAValidator,
    DrillSergeantConfig,
    ErrorReporter,
    MarkerValidator,
    ValidationIssue,
    __author__,
    __email__,
    pytest_addoption,
    pytest_runtest_setup,
)


@pytest.mark.unit
class TestModuleImports:
    """Test that all expected items are imported and accessible."""

    def test_author_import(self) -> None:
        """Test that __author__ is imported and accessible."""
        # Arrange - No setup needed for author test

        # Act - Access the author attribute

        # Assert - Verify author is correct
        assert __author__ == "Jeff Richley"

    def test_email_import(self) -> None:
        """Test that __email__ is imported and accessible."""
        # Arrange - No setup needed for email test

        # Act - Access the email attribute

        # Assert - Verify email is correct
        assert __email__ == "jeffrichley@gmail.com"

    def test_config_import(self) -> None:
        """Test that DrillSergeantConfig is imported and accessible."""
        # Arrange - No setup needed for config import test

        # Act - Access the DrillSergeantConfig class

        # Assert - Verify DrillSergeantConfig is accessible and has expected methods
        assert DrillSergeantConfig is not None
        assert hasattr(DrillSergeantConfig, "from_pytest_config")

    def test_models_import(self) -> None:
        """Test that ValidationIssue is imported and accessible."""
        # Arrange - No setup needed for models import test

        # Act - Access the ValidationIssue class

        # Assert - Verify ValidationIssue is accessible and is a dataclass
        assert ValidationIssue is not None
        assert hasattr(ValidationIssue, "__dataclass_fields__")

    def test_plugin_imports(self) -> None:
        """Test that plugin functions are imported and accessible."""
        # Arrange - No setup needed for plugin import test

        # Act - Access the plugin functions

        # Assert - Verify plugin functions are callable
        assert pytest_addoption is not None
        assert pytest_runtest_setup is not None
        assert callable(pytest_addoption)
        assert callable(pytest_runtest_setup)

    def test_validator_imports(self) -> None:
        """Test that validators are imported and accessible."""
        # Arrange - No setup needed for validator import test

        # Act - Access the validator classes

        # Assert - Verify validators are accessible
        assert AAAValidator is not None
        assert ErrorReporter is not None
        assert MarkerValidator is not None

    def test_imported_classes_are_instantiable(self) -> None:
        """Test that imported classes can be instantiated."""
        # Arrange - No setup needed for instantiation test

        # Act - Create instances of imported classes
        config = DrillSergeantConfig()
        issue = ValidationIssue("test", "message", "suggestion")
        aaa_validator = AAAValidator()
        error_reporter = ErrorReporter()
        marker_validator = MarkerValidator()

        # Assert - Verify instances were created successfully
        assert config.enabled is True
        assert issue.issue_type == "test"
        assert issue.message == "message"
        assert issue.suggestion == "suggestion"
        assert aaa_validator is not None
        assert error_reporter is not None
        assert marker_validator is not None
