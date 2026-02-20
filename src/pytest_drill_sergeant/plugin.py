"""Pytest Drill Sergeant - Enforce test quality standards.

A pytest plugin that enforces test quality standards by:
- Auto-detecting test markers based on directory structure
- Enforcing AAA (Arrange-Act-Assert) structure with descriptive comments
- Providing comprehensive error reporting for violations
"""

import logging
import os
import time
from pathlib import Path

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.pytest_options import pytest_addoption as _pytest_addoption
from pytest_drill_sergeant.utils import (
    detect_test_type_from_path,
    write_markers_to_files,
)
from pytest_drill_sergeant.validators import ErrorReporter
from pytest_drill_sergeant.validators.base import Validator
from pytest_drill_sergeant.validators.registry import build_validators

LOGGER = logging.getLogger(__name__)
TRUE_VALUES = {"true", "1", "yes", "on"}


def _is_truthy_env(env_name: str) -> bool:
    """Check if an environment variable is set to a truthy value."""
    raw = os.getenv(env_name, "")
    return raw.strip().lower() in TRUE_VALUES


class DrillSergeantPlugin:
    """Main plugin coordinator for pytest-drill-sergeant."""

    def __init__(self) -> None:
        """Initialize the plugin with default validators."""
        self.validators: list[tuple[str, Validator]] = build_validators()
        self.error_reporter = ErrorReporter()
        self.telemetry_enabled = _is_truthy_env("DRILL_SERGEANT_DEBUG_TELEMETRY")
        self.telemetry_time_ns: dict[str, int] = {}
        self.telemetry_counts: dict[str, int] = {}

    def validate_test(self, item: pytest.Item, config: DrillSergeantConfig) -> None:
        """Validate a test item using all enabled validators."""
        issues = []

        for validator_name, validator in self.validators:
            if validator.is_enabled(config):
                start_ns = time.perf_counter_ns()
                issues.extend(validator.validate(item, config))
                elapsed_ns = time.perf_counter_ns() - start_ns
                self._record_telemetry(validator_name, elapsed_ns)

        if issues:
            self.error_reporter.report_issues(item, issues)

    def _record_telemetry(self, validator_name: str, elapsed_ns: int) -> None:
        """Record validator runtime telemetry when telemetry is enabled."""
        if not self.telemetry_enabled:
            return
        self.telemetry_time_ns[validator_name] = (
            self.telemetry_time_ns.get(validator_name, 0) + elapsed_ns
        )
        self.telemetry_counts[validator_name] = (
            self.telemetry_counts.get(validator_name, 0) + 1
        )

    def emit_telemetry(self, config: pytest.Config) -> None:
        """Emit validator timing telemetry in debug mode."""
        if not self.telemetry_enabled or not self.telemetry_counts:
            return

        lines = ["drill-sergeant telemetry (validator runtime):"]
        for validator_name in sorted(self.telemetry_counts):
            count = self.telemetry_counts[validator_name]
            total_ns = self.telemetry_time_ns.get(validator_name, 0)
            avg_ns = total_ns // max(count, 1)
            lines.append(
                f"- {validator_name}: calls={count}, total_ms={total_ns / 1_000_000:.3f}, avg_ms={avg_ns / 1_000_000:.3f}"
            )

        terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
        if terminal_reporter is not None:
            for line in lines:
                terminal_reporter.write_line(line)
            return
        LOGGER.info("\n".join(lines))


# Global plugin instance
_plugin = DrillSergeantPlugin()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register drill-sergeant ini options for pytest."""
    _pytest_addoption(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Optionally print effective configuration for troubleshooting."""
    if not _is_truthy_env("DRILL_SERGEANT_DEBUG_CONFIG"):
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
    if not _is_truthy_env("DRILL_SERGEANT_DEBUG_CONFIG"):
        return None

    resolved = DrillSergeantConfig.from_pytest_config(config)
    return f"drill-sergeant effective config: {resolved}"


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Add auto-detected markers during collection so pytest -m unit / -m 'not e2e' works.

    When write_markers is true, also writes @pytest.mark.<name> into source files.
    """
    try:
        ds_config = DrillSergeantConfig.from_pytest_config(config)
    except ValueError:
        return
    if not ds_config.enabled or not ds_config.auto_detect_markers:
        return
    to_write: list[tuple[Path | str, int, str]] = []
    for item in items:
        if not getattr(item, "function", None):
            continue
        if any(item.iter_markers()):
            continue
        detected = detect_test_type_from_path(item, ds_config)
        if detected:
            marker = getattr(pytest.mark, detected)
            item.add_marker(marker)
            if ds_config.write_markers:
                path = getattr(item, "path", None) or Path(getattr(item, "fspath", ""))
                lineno = getattr(item, "location", (None, 0, None))[1]
                if path and lineno:
                    to_write.append((path, lineno, detected))
            LOGGER.debug(
                "Auto-decorated test '%s' with @pytest.mark.%s (collection)",
                item.name,
                detected,
            )
    if to_write:
        write_markers_to_files(to_write)


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

    except ValueError as e:
        pytest.fail(f"Invalid drill-sergeant configuration: {e}", pytrace=False)
    except Exception as e:
        test_name = getattr(item, "name", "unknown")
        LOGGER.exception("Drill Sergeant validation crashed for test '%s'", test_name)
        pytest.fail(
            f"Drill Sergeant internal error while validating '{test_name}': {e}",
            pytrace=False,
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Emit end-of-session telemetry when debug telemetry is enabled."""
    _ = exitstatus
    _plugin.emit_telemetry(session.config)
