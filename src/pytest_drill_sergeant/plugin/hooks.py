"""Pytest hook implementations for drill sergeant plugin."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_drill_sergeant.core.analysis_pipeline import create_analysis_pipeline
from pytest_drill_sergeant.core.cli_config import DrillSergeantArgumentParser
from pytest_drill_sergeant.core.config_context import get_config, initialize_config
from pytest_drill_sergeant.core.file_discovery import create_file_discovery
from pytest_drill_sergeant.core.logging_utils import setup_standard_logging
from pytest_drill_sergeant.core.scoring import get_bis_calculator
from pytest_drill_sergeant.plugin.analysis_storage import get_analysis_storage
from pytest_drill_sergeant.plugin.internals import plan_item_order
from pytest_drill_sergeant.plugin.personas.manager import get_persona_manager
from pytest_drill_sergeant.plugin.pytest_cov_integration import PytestCovIntegration

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    import pytest
    from _pytest.nodes import Item

# Global pytest-cov integration instance
_pytest_cov_integration: PytestCovIntegration | None = None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options."""
    cli_parser = DrillSergeantArgumentParser()
    cli_parser.add_pytest_options(parser)

    # Coverage analysis is automatically enabled when pytest-cov is used


def pytest_configure(config: pytest.Config) -> None:
    """Configure the plugin."""
    global _pytest_cov_integration

    os.environ["PYTEST_DRILL_SERGEANT_PLUGIN_MODE"] = "1"

    # Initialize pytest-cov integration
    _pytest_cov_integration = PytestCovIntegration()
    _pytest_cov_integration.pytest_configure(config)
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

    # pytest-cov integration doesn't need setup


def pytest_runtest_call(item: pytest.Item) -> None:
    """Execute the test with analysis."""
    # Run pytest-cov integration if available
    if _pytest_cov_integration is not None:
        _pytest_cov_integration.pytest_runtest_call(item)


def pytest_runtest_teardown(item: pytest.Item) -> None:
    """Cleanup after each test runs."""
    # pytest-cov integration doesn't need teardown, but we could add it if needed


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Process test report."""
    # Inject persona feedback based on test results
    _inject_persona_feedback(report)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Clean up after test session."""
    global _pytest_cov_integration

    # Clean up pytest-cov integration if it was initialized
    if _pytest_cov_integration is not None:
        _pytest_cov_integration = None


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Generate terminal summary."""
    # Generate persona summary
    _generate_persona_summary(terminalreporter)

    # Run duplicate detection on test files
    _run_duplicate_detection_summary(terminalreporter)

    # Generate coverage summary if pytest-cov integration is enabled
    if _pytest_cov_integration is not None:
        _pytest_cov_integration.pytest_terminal_summary(
            terminalreporter, exitstatus, config
        )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clean up after test session."""
    # Don't clear storage here - let it persist for summary generation


def _initialize_analyzers() -> None:
    """Initialize analyzers for the test session."""
    try:
        storage = get_analysis_storage()

        # Initialize Private Access Detector
        # SUT filtering is now handled by context, not by the detector
        # Initialize config context for pytest plugin mode
        from pytest_drill_sergeant.core.config_context import initialize_config

        initialize_config()  # Use defaults for plugin mode

        # Create centralized analysis pipeline with all default analyzers
        pipeline = create_analysis_pipeline()

        # Add all analyzers from pipeline to storage
        for analyzer in pipeline.analyzers:
            storage.add_analyzer(analyzer)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize analyzers: {e}")


def _analyze_test_file(item: pytest.Item) -> None:
    """Analyze a test file for violations and calculate BIS scores."""
    try:
        test_file_path = Path(item.fspath).resolve()  # Make path absolute
        storage = get_analysis_storage()

        # Check if file should be analyzed using file discovery
        config = get_config()
        file_discovery = create_file_discovery(config)

        should_analyze = file_discovery.should_analyze_file(test_file_path)

        if not should_analyze:
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

            # Store filtered findings back in storage
            test_key = str(test_file_path)
            storage._test_findings[test_key] = filtered_findings

            # Calculate BIS scores for each test in the file
            _calculate_bis_scores_for_file(item, filtered_findings)

            # Store findings in the item for later use
            if not hasattr(item, "ds_findings"):
                item.ds_findings = filtered_findings
            else:
                item.ds_findings = filtered_findings
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to analyze test file {item.fspath}: {e}")


def _calculate_bis_scores_for_file(item: pytest.Item, findings: list[Finding]) -> None:
    """Calculate BIS scores for all tests in a file.

    Args:
        item: Pytest item representing the test file
        findings: List of findings from static analysis
    """
    try:
        bis_calculator = get_bis_calculator()
        test_file_path = Path(item.fspath)

        # Use the improved feature extraction and BIS calculation
        results = bis_calculator.calculate_file_bis(test_file_path, findings)

        # Store results for later retrieval
        for test_name, result in results.items():
            bis_calculator._test_scores[test_name] = result.bis_score
            bis_calculator._test_grades[test_name] = result.bis_grade

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to calculate BIS scores for file {item.fspath}: {e}")


def _inject_persona_feedback(report: pytest.TestReport) -> None:
    """Inject persona feedback into test reports."""
    try:
        # Only inject feedback for test reports (not setup/teardown)
        if report.when != "call":
            return

        persona_manager = get_persona_manager()
        storage = get_analysis_storage()
        bis_calculator = get_bis_calculator()

        # Get findings for this test file
        test_file_path = Path(report.fspath)
        findings = storage.get_test_findings(test_file_path)

        # Get BIS score for this test
        test_name = (
            report.nodeid.split("::")[-1] if "::" in report.nodeid else report.nodeid
        )
        bis_score = bis_calculator.get_test_bis_score(test_name)
        bis_grade = bis_calculator.get_test_bis_grade(test_name)

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
            from pytest_drill_sergeant.core.models import Finding, Severity

            dummy_finding = Finding(
                code="DS999",
                name="unknown_failure",
                severity=Severity.WARNING,
                message="Test failed for unknown reasons",
                file_path=test_file_path,
                line_number=0,
            )
            message = persona_manager.on_test_fail(report.nodeid, dummy_finding)

        # Add BIS score information to the message
        bis_message = persona_manager.on_bis_score(test_name, bis_score)
        if bis_message:
            message = f"{message}\n\n{bis_message}"

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
        bis_calculator = get_bis_calculator()

        # Get summary statistics
        stats = storage.get_summary_stats()

        # Get BIS summary
        bis_summary = bis_calculator.get_bis_summary()

        # Create mock metrics for summary
        from pytest_drill_sergeant.core.models import RunMetrics

        metrics = RunMetrics(
            total_tests=stats["total_tests"],
            total_violations=stats["total_violations"],
            brs_score=max(
                0, 100 - (stats["total_violations"] * 15)
            ),  # Simple BRS calculation
            average_bis=bis_summary["average_score"],
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

        # Add BIS summary
        if bis_summary["total_tests"] > 0:
            terminalreporter.write_sep("-", "BIS (Behavior Integrity Score) Summary")
            terminalreporter.write_line(
                f"Average BIS Score: {bis_summary['average_score']:.1f}"
            )
            terminalreporter.write_line(
                f"Highest Score: {bis_summary['highest_score']:.1f}"
            )
            terminalreporter.write_line(
                f"Lowest Score: {bis_summary['lowest_score']:.1f}"
            )

            # Grade distribution
            terminalreporter.write_line("Grade Distribution:")
            for grade, count in bis_summary["grade_distribution"].items():
                if count > 0:
                    terminalreporter.write_line(f"  {grade}: {count}")

            # Top offenders
            if bis_summary["top_offenders"]:
                terminalreporter.write_line("Top Offenders (Lowest BIS Scores):")
                for test_name, score in bis_summary["top_offenders"]:
                    terminalreporter.write_line(f"  {test_name}: {score:.1f}")

        if stats["rule_counts"]:
            terminalreporter.write_line("Violations by type:")
            for rule_type, count in stats["rule_counts"].items():
                terminalreporter.write_line(f"  {rule_type}: {count}")

        terminalreporter.write_sep("=", "END DRILL SERGEANT SUMMARY")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to generate persona summary: {e}")


def _run_duplicate_detection_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Run duplicate detection and display results in terminal summary."""
    try:
        from pytest_drill_sergeant.core.analyzers.duplicate_test_detector import (
            DuplicateTestDetector,
        )

        # Get test files from the terminal reporter's config
        test_files = set()

        # Try to get test files from the config
        if (
            hasattr(terminalreporter.config, "session")
            and terminalreporter.config.session
        ):
            session = terminalreporter.config.session
            for item in session.items:
                test_files.add(Path(item.fspath))
        else:
            # Fallback: get test files from the current working directory
            import os
            from pathlib import Path

            # Look for test files in common test directories
            test_dirs = ["tests", "test", "tests/unit", "tests/integration"]
            for test_dir in test_dirs:
                if os.path.exists(test_dir):
                    for root, dirs, files in os.walk(test_dir):
                        for file in files:
                            if file.startswith("test_") and file.endswith(".py"):
                                test_files.add(Path(root) / file)

        if not test_files:
            return

        # Run duplicate detection
        detector = DuplicateTestDetector()
        all_findings = []

        for test_file in test_files:
            findings = detector.analyze_file(test_file)
            all_findings.extend(findings)

        # Display duplicate detection results
        if all_findings:
            terminalreporter.write_sep("=", "DUPLICATE TEST DETECTION")

            # Group findings by file
            findings_by_file = {}
            for finding in all_findings:
                file_path = finding.file_path
                if file_path not in findings_by_file:
                    findings_by_file[file_path] = []
                findings_by_file[file_path].append(finding)

            for file_path, findings in findings_by_file.items():
                terminalreporter.write_line(f"📁 {file_path.name}:")
                for finding in findings:
                    terminalreporter.write_line(f"  ⚠️  {finding.message}")
                terminalreporter.write_line("")

            terminalreporter.write_line(
                f"Found {len(all_findings)} duplicate test groups"
            )
            terminalreporter.write_sep("=", "END DUPLICATE TEST DETECTION")
        else:
            terminalreporter.write_sep("=", "DUPLICATE TEST DETECTION")
            terminalreporter.write_line("✅ No duplicate tests found")
            terminalreporter.write_sep("=", "END DUPLICATE TEST DETECTION")

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to run duplicate detection summary: {e}")
