"""Unit tests for the validators.__init__.py module."""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators import (
    AAAValidator,
    ErrorReporter,
    FileLengthValidator,
    MarkerValidator,
    Validator,
)


@pytest.mark.unit
class TestValidatorsModuleImports:
    """Test that all expected validators are imported and accessible."""

    def test_aaa_validator_import(self) -> None:
        """Test that AAAValidator is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the AAAValidator class

        # Assert - Verify AAAValidator is accessible and has expected methods
        assert AAAValidator is not None
        assert hasattr(AAAValidator, "validate")
        assert hasattr(AAAValidator, "is_enabled")

    def test_error_reporter_import(self) -> None:
        """Test that ErrorReporter is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the ErrorReporter class

        # Assert - Verify ErrorReporter is accessible and has expected methods
        assert ErrorReporter is not None
        assert hasattr(ErrorReporter, "report_issues")

    def test_file_length_validator_import(self) -> None:
        """Test that FileLengthValidator is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the FileLengthValidator class

        # Assert - Verify FileLengthValidator is accessible and has expected methods
        assert FileLengthValidator is not None
        assert hasattr(FileLengthValidator, "validate")
        assert hasattr(FileLengthValidator, "is_enabled")

    def test_marker_validator_import(self) -> None:
        """Test that MarkerValidator is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the MarkerValidator class

        # Assert - Verify MarkerValidator is accessible and has expected methods
        assert MarkerValidator is not None
        assert hasattr(MarkerValidator, "validate")
        assert hasattr(MarkerValidator, "is_enabled")

    def test_validator_protocol_import(self) -> None:
        """Test that Validator protocol is imported and accessible."""
        # Arrange - No setup needed for import test

        # Act - Access the Validator protocol

        # Assert - Verify Validator protocol is accessible and has expected methods
        assert Validator is not None
        assert hasattr(Validator, "validate")
        assert hasattr(Validator, "is_enabled")

    def test_validators_are_instantiable(self) -> None:
        """Test that all validators can be instantiated."""
        # Arrange - No setup needed for instantiation test

        # Act - Create instances of validator classes
        aaa_validator = AAAValidator()
        error_reporter = ErrorReporter()
        file_length_validator = FileLengthValidator()
        marker_validator = MarkerValidator()

        # Assert - Verify instances were created successfully
        assert aaa_validator is not None
        assert error_reporter is not None
        assert file_length_validator is not None
        assert marker_validator is not None

    def test_validators_implement_protocol(self) -> None:
        """Test that all validators implement the Validator protocol."""
        # Arrange - Set up mock objects for protocol testing
        mock_config = DrillSergeantConfig()

        # Act - Create validator instances and test protocol compliance
        aaa_validator = AAAValidator()
        file_length_validator = FileLengthValidator()
        marker_validator = MarkerValidator()

        # Assert - Verify all validators implement the Validator protocol
        assert isinstance(aaa_validator, Validator)
        assert isinstance(file_length_validator, Validator)
        assert isinstance(marker_validator, Validator)

        # Verify is_enabled methods return expected types (validate methods need real test items)
        assert isinstance(aaa_validator.is_enabled(mock_config), bool)
        assert isinstance(file_length_validator.is_enabled(mock_config), bool)
        assert isinstance(marker_validator.is_enabled(mock_config), bool)
