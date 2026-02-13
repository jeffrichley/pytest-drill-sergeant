"""Unit tests for validator registry behavior."""

import pytest

from pytest_drill_sergeant.validators.aaa import AAAValidator
from pytest_drill_sergeant.validators.file_length import FileLengthValidator
from pytest_drill_sergeant.validators.marker import MarkerValidator
from pytest_drill_sergeant.validators.registry import (
    DEFAULT_VALIDATOR_REGISTRY,
    build_validators,
)


@pytest.mark.unit
class TestValidatorRegistry:
    """Verify registry definitions and instance construction."""

    def test_default_registry_contains_expected_validator_names(self) -> None:
        """Default registry should expose stable validator names."""
        # Arrange - No setup beyond default registry constants
        # Act - Collect names from registry definitions
        names = [definition.name for definition in DEFAULT_VALIDATOR_REGISTRY]

        # Assert - Default registry order and identifiers are stable
        assert names == ["marker", "aaa", "file_length"]

    def test_build_validators_returns_concrete_instances(self) -> None:
        """Registry build should return named validator instances."""
        # Arrange - No setup needed beyond registry module
        # Act - Build validator instances from registry
        validators = build_validators()

        # Assert - Registry build returns expected names and implementations
        assert len(validators) == 3
        assert validators[0][0] == "marker"
        assert validators[1][0] == "aaa"
        assert validators[2][0] == "file_length"

        assert isinstance(validators[0][1], MarkerValidator)
        assert isinstance(validators[1][1], AAAValidator)
        assert isinstance(validators[2][1], FileLengthValidator)
