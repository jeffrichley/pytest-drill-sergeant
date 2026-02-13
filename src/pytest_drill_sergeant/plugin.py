"""Pytest Drill Sergeant - Enforce test quality standards.

A pytest plugin that enforces test quality standards by:
- Auto-detecting test markers based on directory structure
- Enforcing AAA (Arrange-Act-Assert) structure with descriptive comments
- Providing comprehensive error reporting for violations
"""

import logging
import os

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.pytest_options import pytest_addoption as _pytest_addoption
from pytest_drill_sergeant.validators import (
    AAAValidator,
    ErrorReporter,
    FileLengthValidator,
    MarkerValidator,
)
from pytest_drill_sergeant.validators.base import Validator

LOGGER = logging.getLogger(__name__)
TRUE_VALUES = {"true", "1", "yes", "on"}


class DrillSergeantPlugin:
    """Main plugin coordinator for pytest-drill-sergeant."""

    def __init__(self) -> None:
        """Initialize the plugin with default validators."""
        self.validators: list[Validator] = [
            MarkerValidator(),
            AAAValidator(),
            FileLengthValidator(),
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


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register drill-sergeant ini options for pytest."""
    _pytest_addoption(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Optionally print effective configuration for troubleshooting."""
    debug_val = os.getenv("DRILL_SERGEANT_DEBUG_CONFIG", "")
    if debug_val.strip().lower() not in TRUE_VALUES:
        return

    resolved = DrillSergeantConfig.from_pytest_config(config)
    message = f"[drill-sergeant] effective config: {resolved}"

    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter is not None:
        terminal_reporter.write_line(message)
        return

    LOGGER.info(message)


def pytest_report_header(config: pytest.Config) -> str | None:
    """Emit effective config in pytest header when debug mode is enabled."""
    debug_val = os.getenv("DRILL_SERGEANT_DEBUG_CONFIG", "")
    if debug_val.strip().lower() not in TRUE_VALUES:
        return None

    resolved = DrillSergeantConfig.from_pytest_config(config)
    return f"drill-sergeant effective config: {resolved}"


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
        test_name = getattr(item, "name", "unknown")
        LOGGER.exception("Drill Sergeant validation crashed for test '%s'", test_name)
        pytest.fail(
            f"Drill Sergeant internal error while validating '{test_name}': {e}",
            pytrace=False,
        )
