"""Pytest hook implementations for drill sergeant plugin."""

import os

import pytest

from pytest_drill_sergeant.core.cli_config import DrillSergeantArgumentParser
from pytest_drill_sergeant.core.config_manager import initialize_config
from pytest_drill_sergeant.core.logging_utils import setup_standard_logging


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options."""
    # Use our CLI argument parser to add options
    cli_parser = DrillSergeantArgumentParser()
    cli_parser.add_pytest_options(parser)


def pytest_configure(config: pytest.Config) -> None:
    """Configure the plugin."""
    # Force standard logging in pytest context
    os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] = "1"

    # Set up standard logging for pytest plugin mode
    setup_standard_logging()

    # Extract drill sergeant options from pytest config
    cli_args = {}
    for option in config.option.__dict__:
        if option.startswith("ds_"):
            cli_args[option] = getattr(config.option, option)

    # Initialize configuration
    initialize_config(cli_args, config)


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test items during collection."""
    # TODO: Analyze test collection


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
