"""File length validation for pytest-drill-sergeant."""

import warnings
from pathlib import Path
from typing import TextIO

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue

INLINE_SCAN_LIMIT = 50


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
        path_obj = Path(str(file_path))

        if self._is_path_excluded(path_obj, item, config):
            return issues

        try:
            # Count lines in the file and optionally inspect pragma header
            with path_obj.open(encoding="utf-8") as f:
                if self._has_inline_ignore_pragma(f, config):
                    return issues
                f.seek(0)
                line_count = sum(1 for _ in f)

            # Check if file exceeds maximum length
            if line_count > config.max_file_length:
                issue = ValidationIssue(
                    issue_type="file_length",
                    message=f"Test file '{file_path}' is too long ({line_count} lines)",
                    suggestion=f"Split this file into smaller modules. Current length: {line_count} lines, maximum allowed: {config.max_file_length} lines",
                )
                mode = config.file_length_mode.strip().lower()
                if mode == "warn":
                    warnings.warn(pytest.PytestWarning(issue.message), stacklevel=2)
                    return issues
                issues.append(issue)

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
        mode = config.file_length_mode.strip().lower()
        return config.enforce_file_length and mode != "off"

    def _is_path_excluded(
        self, file_path: Path, item: pytest.Item, config: DrillSergeantConfig
    ) -> bool:
        """Check whether file is excluded by glob pattern."""
        if not config.file_length_exclude:
            return False

        rootpath = Path(getattr(item.config, "rootpath", Path.cwd()))
        try:
            relative_path = file_path.relative_to(rootpath)
            relative_path_str = relative_path.as_posix()
        except ValueError:
            relative_path_str = file_path.as_posix()

        for pattern in config.file_length_exclude:
            cleaned_pattern = pattern.strip()
            if not cleaned_pattern:
                continue
            if relative_path_str and Path(relative_path_str).match(cleaned_pattern):
                return True
            if file_path.match(cleaned_pattern):
                return True
        return False

    def _has_inline_ignore_pragma(
        self, file_handle: TextIO, config: DrillSergeantConfig
    ) -> bool:
        """Check top-of-file comments for inline ignore pragma."""
        if not config.file_length_inline_ignore:
            return False

        token = config.file_length_inline_ignore_token.strip().lower()
        if not token:
            return False

        for index, raw_line in enumerate(file_handle):
            if index >= INLINE_SCAN_LIMIT:
                break
            if token in str(raw_line).strip().lower():
                return True
        return False
