"""File length validation for pytest-drill-sergeant."""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue


class FileLengthValidator:
    """Validator for enforcing maximum file length limits."""

    def validate(
        self, item: pytest.Item, config: DrillSergeantConfig
    ) -> list[ValidationIssue]:
        """Validate file length and return issues if file is too long.

        Args:
            item: The pytest test item to validate
            config: The drill sergeant configuration

        Returns:
            List of validation issues found
        """
        if not self.is_enabled(config):
            return []

        issues: list[ValidationIssue] = []

        # Get the file path from the test item
        file_path = item.fspath
        if not file_path:
            return issues

        try:
            # Count lines in the file
            with open(str(file_path), encoding="utf-8") as f:
                line_count = sum(1 for _ in f)

            # Check if file exceeds maximum length
            if line_count > config.max_file_length:
                issues.append(
                    ValidationIssue(
                        issue_type="file_length",
                        message=f"Test file '{file_path}' is too long ({line_count} lines)",
                        suggestion=f"Split this file into smaller modules. Current length: {line_count} lines, maximum allowed: {config.max_file_length} lines",
                    )
                )

        except (OSError, UnicodeDecodeError) as e:
            # If we can't read the file, create a warning issue
            issues.append(
                ValidationIssue(
                    issue_type="file_length",
                    message=f"Could not read file '{file_path}' for length validation",
                    suggestion=f"Check file permissions and encoding. Error: {e}",
                )
            )

        return issues

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if file length validation is enabled.

        Args:
            config: The drill sergeant configuration

        Returns:
            True if file length validation should run, False otherwise
        """
        return config.enforce_file_length
