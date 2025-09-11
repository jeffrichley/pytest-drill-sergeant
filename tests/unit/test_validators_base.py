"""Unit tests for the validators.base module."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest import Item
from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.validators.aaa import AAAValidator
from pytest_drill_sergeant.validators.base import Validator
from pytest_drill_sergeant.validators.file_length import FileLengthValidator
from pytest_drill_sergeant.validators.marker import MarkerValidator


@pytest.mark.unit
class TestValidator:
    """Test the Validator protocol."""

    def test_validator_protocol_interface(self) -> None:
        """Test that Validator protocol defines the correct interface."""

        # Arrange - Create a mock validator that implements the protocol
        class MockValidator:
            def validate(
                self, _item: "Item", _config: DrillSergeantConfig
            ) -> list[ValidationIssue]:
                return []

            def is_enabled(self, _config: DrillSergeantConfig) -> bool:
                return True

        # Act - Create an instance of the mock validator

        # Assert - Verify the validator implements the Validator protocol
        validator = MockValidator()
        assert isinstance(validator, Validator)

    def test_validator_protocol_validate_signature(self) -> None:
        """Test that validate method has correct signature."""

        # Arrange - Create a mock validator with proper validate method
        class MockValidator:
            def validate(
                self, _item: "Item", _config: DrillSergeantConfig
            ) -> list[ValidationIssue]:
                return [ValidationIssue("test", "message", "suggestion")]

            def is_enabled(self, _config: DrillSergeantConfig) -> bool:
                return True

        # Act - Create validator and test validate method
        validator = MockValidator()
        mock_item = Mock()
        mock_config = DrillSergeantConfig()

        # Assert - Verify validate method returns expected types
        issues = validator.validate(mock_item, mock_config)
        assert isinstance(issues, list)
        assert len(issues) == 1
        assert isinstance(issues[0], ValidationIssue)

    def test_validator_protocol_is_enabled_signature(self) -> None:
        """Test that is_enabled method has correct signature."""

        # Arrange - Create a mock validator with proper is_enabled method
        class MockValidator:
            def validate(
                self, _item: "Item", _config: DrillSergeantConfig
            ) -> list[ValidationIssue]:
                return []

            def is_enabled(self, _config: DrillSergeantConfig) -> bool:
                return False

        # Act - Create validator and test is_enabled method
        validator = MockValidator()
        mock_config = DrillSergeantConfig()

        # Assert - Verify is_enabled method returns expected types
        result = validator.is_enabled(mock_config)
        assert isinstance(result, bool)
        assert result is False

    def test_validator_protocol_runtime_checkable(self) -> None:
        """Test that Validator is runtime checkable."""

        # Arrange - Create valid and invalid validator classes
        class ValidValidator:
            def validate(
                self, _item: "Item", _config: DrillSergeantConfig
            ) -> list[ValidationIssue]:
                return []

            def is_enabled(self, _config: DrillSergeantConfig) -> bool:
                return True

        class InvalidValidator:
            def validate(
                self, _item: "Item", _config: DrillSergeantConfig
            ) -> list[ValidationIssue]:
                return []

            # Missing is_enabled method

        # Act - Create instances of both validators

        # Assert - Verify runtime checking works correctly
        valid_validator = ValidValidator()
        invalid_validator = InvalidValidator()

        assert isinstance(valid_validator, Validator)
        assert not isinstance(invalid_validator, Validator)

    def test_validator_protocol_with_real_implementations(self) -> None:
        """Test Validator protocol with real validator implementations."""
        # Arrange - Set up mock config
        mock_config = DrillSergeantConfig()

        # Act - Create instances of real validators
        aaa_validator = AAAValidator()
        marker_validator = MarkerValidator()
        file_length_validator = FileLengthValidator()

        # Assert - Verify all real validators implement the protocol correctly
        assert isinstance(aaa_validator, Validator)
        assert isinstance(aaa_validator.is_enabled(mock_config), bool)

        assert isinstance(marker_validator, Validator)
        assert isinstance(marker_validator.is_enabled(mock_config), bool)

        assert isinstance(file_length_validator, Validator)
        assert isinstance(file_length_validator.is_enabled(mock_config), bool)
