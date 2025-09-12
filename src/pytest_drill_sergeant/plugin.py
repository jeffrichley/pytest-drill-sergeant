"""Pytest Drill Sergeant - Enforce test quality standards.

A pytest plugin that enforces test quality standards by:
- Auto-detecting test markers based on directory structure
- Enforcing AAA (Arrange-Act-Assert) structure with descriptive comments
- Providing comprehensive error reporting for violations
"""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.validators import (
    AAAValidator,
    ErrorReporter,
    FileLengthValidator,
    MarkerValidator,
    ReturnTypeValidator,
)
from pytest_drill_sergeant.validators.base import Validator


class DrillSergeantPlugin:
    """Main plugin coordinator for pytest-drill-sergeant."""

    def __init__(self) -> None:
        """Initialize the plugin with default validators."""
        self.validators: list[Validator] = [
            MarkerValidator(),
            AAAValidator(),
            FileLengthValidator(),
            ReturnTypeValidator(),
        ]
        self.error_reporter = ErrorReporter()

    def validate_test(self, item: pytest.Item, config: DrillSergeantConfig) -> None:
        """Validate a test item using all enabled validators."""
        issues = []

        for validator in self.validators:
            if validator.is_enabled(config):
                issues.extend(validator.validate(item, config))

        if issues:
            self.error_reporter.report_issues(item, issues)


# Global plugin instance
_plugin = DrillSergeantPlugin()


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Auto-decorate tests with markers AND enforce AAA structure - report ALL issues."""
    try:
        # Skip non-function items (like classes, modules)
        if not hasattr(item, "function") or not getattr(item, "function", None):
            return

        # Get configuration
        config = DrillSergeantConfig.from_pytest_config(item.config)

        # Skip if disabled
        if not config.enabled:
            return

        # Validate the test
        _plugin.validate_test(item, config)

    except Exception as e:
        # If there's any error, just skip the check to avoid breaking tests
        test_name = getattr(item, "name", "unknown")
        print(f"Warning: Test validation failed for {test_name}: {e}")
