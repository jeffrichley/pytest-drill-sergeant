"""Base protocol for test validators."""

from typing import Protocol, runtime_checkable

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue


@runtime_checkable
class Validator(Protocol):
    """Protocol for test validators.

    All validators must implement this interface to ensure consistent
    behavior across different validation strategies.
    """

    def validate(
        self, item: pytest.Item, config: DrillSergeantConfig
    ) -> list[ValidationIssue]:
        """Validate a test item and return any issues found.

        Args:
            item: The pytest test item to validate
            config: The drill sergeant configuration

        Returns:
            List of validation issues found
        """
        ...

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if this validator is enabled in the configuration.

        Args:
            config: The drill sergeant configuration

        Returns:
            True if this validator should run, False otherwise
        """
        ...
