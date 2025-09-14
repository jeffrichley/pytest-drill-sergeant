"""Pytest hook implementations for drill sergeant plugin."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.cli_config import DrillSergeantArgumentParser
from pytest_drill_sergeant.core.config_manager import initialize_config
from pytest_drill_sergeant.core.logging_utils import setup_standard_logging
from pytest_drill_sergeant.plugin.internals import plan_item_order

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    import pytest
    from _pytest.nodes import Item


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options."""
    cli_parser = DrillSergeantArgumentParser()
    cli_parser.add_pytest_options(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Configure the plugin."""
    os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] = "1"
    setup_standard_logging()

    cli_args = {}
    for option in config.option.__dict__:
        if option.startswith("ds_"):
            cli_args[option] = getattr(config.option, option)

    initialize_config(cli_args, config)


def pytest_collection_modifyitems(
    _session: pytest.Session, _config: pytest.Config, items: list[Item]
) -> None:
    """Reorder collected test items in place.

    Pytest requires a concrete ``list[Item]``. Internal planners operate on
    abstract ``Sequence[Item]`` and return a new ``list[Item]``. Mutation is
    isolated to this boundary via slice assignment.
    """
    new_order = plan_item_order(items)
    items[:] = new_order


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup before each test runs."""
    # TODO: Setup test analysis


def pytest_runtest_call(item: pytest.Item) -> None:
    """Execute the test with analysis."""
    # TODO: Execute test with analysis


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Process test report."""
    # TODO: Process test report


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Generate terminal summary."""
    # TODO: Generate summary


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up after test session."""
    # TODO: Finalize session
