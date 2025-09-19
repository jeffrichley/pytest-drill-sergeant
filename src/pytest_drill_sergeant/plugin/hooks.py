"""Pytest hook implementations for drill sergeant plugin."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.analyzers.private_access_detector import (
    PrivateAccessDetector,
)
from pytest_drill_sergeant.core.cli_config import DrillSergeantArgumentParser
from pytest_drill_sergeant.core.config_context import get_config, initialize_config
from pytest_drill_sergeant.core.file_discovery import create_file_discovery
from pytest_drill_sergeant.core.logging_utils import setup_standard_logging
from pytest_drill_sergeant.plugin.analysis_storage import get_analysis_storage
from pytest_drill_sergeant.plugin.internals import plan_item_order
from pytest_drill_sergeant.plugin.personas.manager import get_persona_manager

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

    # Initialize analyzers
    _initialize_analyzers()


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[Item]
) -> None:
    """Reorder collected test items in place.

    Pytest requires a concrete ``list[Item]``. Internal planners operate on
    abstract ``Sequence[Item]`` and return a new ``list[Item]``. Mutation is
    isolated to this boundary via slice assignment.
    """
    _ = session, config  # Preserve API and clarify parameters are unused
    new_order = plan_item_order(items)
    items[:] = new_order


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup before each test runs."""
    # Run static analysis on the test file
    _analyze_test_file(item)


def pytest_runtest_call(item: pytest.Item) -> None:
    """Execute the test with analysis."""
    # TODO: Execute test with analysis


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Process test report."""
    # Inject persona feedback based on test results
    _inject_persona_feedback(report)


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Generate terminal summary."""
    # Generate persona summary
    _generate_persona_summary(terminalreporter)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up after test session."""
    # Clear analysis storage
    storage = get_analysis_storage()
    storage.clear()


def _initialize_analyzers() -> None:
    """Initialize analyzers for the test session."""
    try:
        storage = get_analysis_storage()

        # Initialize Private Access Detector
        # SUT filtering is now handled by context, not by the detector
        # Initialize config context for pytest plugin mode
        from pytest_drill_sergeant.core.config_context import initialize_config

        initialize_config()  # Use defaults for plugin mode
        detector = PrivateAccessDetector()
        storage.add_analyzer(detector)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize analyzers: {e}")


def _analyze_test_file(item: pytest.Item) -> None:
    """Analyze a test file for violations."""
    try:
        test_file_path = Path(item.fspath)
        storage = get_analysis_storage()

        # Check if file should be analyzed using file discovery
        config = get_config()
        file_discovery = create_file_discovery(config)

        if not file_discovery.should_analyze_file(test_file_path):
            # File is excluded by configuration, skip analysis
            return

        # Only analyze if we haven't already analyzed this file
        if str(test_file_path) not in storage._test_findings:
            findings = storage.analyze_test_file(test_file_path)

            # Apply file-specific rule filtering
            file_config = file_discovery.get_file_config(test_file_path)
            ignored_rules = file_config["ignored_rules"]

            # Filter out findings for ignored rules
            filtered_findings = [
                finding for finding in findings if finding.code not in ignored_rules
            ]

            # Store findings in the item for later use
            if not hasattr(item, "ds_findings"):
                item.ds_findings = filtered_findings
            else:
                item.ds_findings = filtered_findings
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to analyze test file {item.fspath}: {e}")


def _inject_persona_feedback(report: pytest.TestReport) -> None:
    """Inject persona feedback into test reports."""
    try:
        # Only inject feedback for test reports (not setup/teardown)
        if report.when != "call":
            return

        persona_manager = get_persona_manager()
        storage = get_analysis_storage()

        # Get findings for this test file
        test_file_path = Path(report.fspath)
        findings = storage.get_test_findings(test_file_path)

        # Generate appropriate message based on test result
        if report.outcome == "passed":
            if findings:
                # Test passed but has violations - this shouldn't happen in strict mode
                # but could happen in advisory mode
                message = persona_manager.on_test_pass(report.nodeid)
            else:
                # Test passed with no violations
                message = persona_manager.on_test_pass(report.nodeid)
        # Test failed - generate failure message
        elif findings:
            # Use the first finding for the failure message
            message = persona_manager.on_test_fail(report.nodeid, findings[0])
        else:
            # Test failed for other reasons (not our violations)
            from pytest_drill_sergeant.core.models import Finding, RuleType, Severity

            dummy_finding = Finding(
                rule_type=RuleType.PRIVATE_ACCESS,
                severity=Severity.WARNING,
                message="Test failed for unknown reasons",
                file_path=test_file_path,
                line_number=0,
            )
            message = persona_manager.on_test_fail(report.nodeid, dummy_finding)

        # Add the message to the report
        if hasattr(report, "longrepr") and report.longrepr:
            # Append to existing longrepr
            report.longrepr = f"{report.longrepr}\n\n{message}"
        else:
            # Create new longrepr
            report.longrepr = message

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to inject persona feedback: {e}")


def _generate_persona_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Generate persona summary for terminal output."""
    try:
        storage = get_analysis_storage()
        persona_manager = get_persona_manager()

        # Get summary statistics
        stats = storage.get_summary_stats()

        # Create mock metrics for summary
        from pytest_drill_sergeant.core.models import RunMetrics

        metrics = RunMetrics(
            total_tests=stats["total_tests"],
            total_violations=stats["total_violations"],
            brs_score=max(
                0, 100 - (stats["total_violations"] * 15)
            ),  # Simple BRS calculation
        )

        # Generate summary message
        summary_message = persona_manager.on_summary(metrics)

        # Add to terminal output
        terminalreporter.write_sep("=", "DRILL SERGEANT SUMMARY")
        terminalreporter.write_line(summary_message)
        terminalreporter.write_line("")

        # Add detailed statistics
        terminalreporter.write_line(
            f"Total violations found: {stats['total_violations']}"
        )
        terminalreporter.write_line(f"Test files analyzed: {stats['total_test_files']}")
        terminalreporter.write_line(f"Tests run: {stats['total_tests']}")

        if stats["rule_counts"]:
            terminalreporter.write_line("Violations by type:")
            for rule_type, count in stats["rule_counts"].items():
                terminalreporter.write_line(f"  {rule_type}: {count}")

        terminalreporter.write_sep("=", "END DRILL SERGEANT SUMMARY")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to generate persona summary: {e}")
