"""Coverage hooks for pytest-drill-sergeant.

This module implements pytest hooks for coverage collection
and integration with the coverage analysis system.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest
    from _pytest.nodes import Item

from pytest_drill_sergeant.core.analyzers.car_calculator import CARCalculator
from pytest_drill_sergeant.core.analyzers.clone_detector import DynamicCloneDetector
from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageCollector
from pytest_drill_sergeant.core.analyzers.coverage_signature import (
    CoverageSignatureGenerator,
)


class CoverageHooks:
    """Pytest hooks for coverage collection and analysis."""

    def __init__(self) -> None:
        """Initialize coverage hooks."""
        self.logger = logging.getLogger("drill_sergeant.coverage_hooks")
        self.coverage_collector = CoverageCollector()
        self.car_calculator = CARCalculator()
        self.signature_generator = CoverageSignatureGenerator()
        self.clone_detector = DynamicCloneDetector()
        self._coverage_enabled = False
        self._duplicate_clusters = []

    def pytest_configure(self, config: pytest.Config) -> None:
        """Configure coverage collection."""
        try:
            # Check if coverage is enabled
            self._coverage_enabled = config.getoption("--ds-coverage", default=False)

            if self._coverage_enabled:
                self.logger.info("Coverage collection enabled")
                self.coverage_collector.start_coverage()
            else:
                self.logger.debug("Coverage collection disabled")

        except Exception as e:
            self.logger.error(f"Failed to configure coverage: {e}")

    def pytest_unconfigure(self, config: pytest.Config) -> None:
        """Clean up coverage collection."""
        try:
            if self._coverage_enabled:
                self.coverage_collector.stop_coverage()
                self.logger.info("Coverage collection stopped")

        except Exception as e:
            self.logger.error(f"Failed to cleanup coverage: {e}")

    def pytest_runtest_setup(self, item: Item) -> None:
        """Setup before each test runs."""
        try:
            if not self._coverage_enabled:
                return

            # Get test information
            test_file_path = Path(item.fspath)
            # Extract just the function name from the full test name
            # For "TestClass::test_function", we want "test_function"
            test_name = item.name.split("::")[-1] if "::" in item.name else item.name
            test_line_number = item.location[1] if item.location else 0

            # Start coverage collection for this test
            self.logger.debug(f"Starting coverage collection for {test_name}")

        except Exception as e:
            self.logger.error(f"Failed to setup coverage for test: {e}")

    def pytest_runtest_call(self, item: Item) -> None:
        """Execute the test with coverage collection."""
        try:
            if not self._coverage_enabled:
                return

            # Get test information
            test_file_path = Path(item.fspath)
            # Extract just the function name from the full test name
            # For "TestClass::test_function", we want "test_function"
            test_name = item.name.split("::")[-1] if "::" in item.name else item.name
            test_line_number = item.location[1] if item.location else 0

            # Collect coverage data for this test
            coverage_data = self.coverage_collector.collect_test_coverage(
                test_file_path, test_name, test_line_number
            )

            # Calculate CAR for this test
            car_result = self.car_calculator.calculate_car(
                test_file_path, test_name, test_line_number, coverage_data
            )

            # Generate coverage signature
            signature = self.signature_generator.generate_signature(
                test_file_path, test_name, coverage_data
            )

            # Store results in the test item
            item.ds_coverage_data = coverage_data
            item.ds_car_result = car_result
            item.ds_coverage_signature = signature

            self.logger.debug(f"Coverage analysis completed for {test_name}")

        except Exception as e:
            self.logger.error(f"Failed to collect coverage for test: {e}")

    def pytest_runtest_teardown(self, item: Item) -> None:
        """Cleanup after each test runs."""
        try:
            if not self._coverage_enabled:
                return

            # Cleanup any test-specific coverage data
            self.logger.debug(f"Cleaning up coverage data for {item.name}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup coverage for test: {e}")

    def pytest_terminal_summary(
        self,
        terminalreporter: pytest.TerminalReporter,
        exitstatus: int,
        config: pytest.Config,
    ) -> None:
        """Generate coverage summary in terminal output."""
        try:
            if not self._coverage_enabled:
                return

            # Run duplicate detection analysis
            self._run_duplicate_detection()

            # Generate coverage summary
            self._generate_coverage_summary(terminalreporter)

        except Exception as e:
            self.logger.error(f"Failed to generate coverage summary: {e}")

    def _generate_coverage_summary(
        self, terminalreporter: pytest.TerminalReporter
    ) -> None:
        """Generate coverage summary for terminal output."""
        try:
            terminalreporter.write_sep("=", "COVERAGE ANALYSIS SUMMARY")

            # Get all coverage data
            coverage_data = self.coverage_collector._coverage_data
            car_results = []
            signatures = self.signature_generator._signatures

            # Collect CAR results
            for key, coverage_data_item in coverage_data.items():
                test_file_path = coverage_data_item.file_path
                test_name = coverage_data_item.test_name
                test_line_number = coverage_data_item.line_number

                car_result = self.car_calculator.calculate_car(
                    test_file_path, test_name, test_line_number, coverage_data_item
                )
                car_results.append(car_result)

            # Display summary statistics
            if coverage_data:
                total_tests = len(coverage_data)
                avg_coverage = (
                    sum(data.coverage_percentage for data in coverage_data.values())
                    / total_tests
                )
                avg_car = sum(result.car_score for result in car_results) / len(
                    car_results
                )

                terminalreporter.write_line(f"Total tests analyzed: {total_tests}")
                terminalreporter.write_line(f"Average coverage: {avg_coverage:.1f}%")
                terminalreporter.write_line(f"Average CAR score: {avg_car:.1f}")

                # Display CAR grade distribution
                grade_counts = {}
                for result in car_results:
                    grade_counts[result.car_grade] = (
                        grade_counts.get(result.car_grade, 0) + 1
                    )

                terminalreporter.write_line("CAR Grade Distribution:")
                for grade in sorted(grade_counts.keys()):
                    count = grade_counts[grade]
                    percentage = (count / len(car_results)) * 100
                    terminalreporter.write_line(
                        f"  Grade {grade}: {count} tests ({percentage:.1f}%)"
                    )

                # Display efficiency level distribution
                efficiency_counts = {}
                for result in car_results:
                    efficiency_counts[result.efficiency_level] = (
                        efficiency_counts.get(result.efficiency_level, 0) + 1
                    )

                terminalreporter.write_line("Efficiency Level Distribution:")
                for level in sorted(efficiency_counts.keys()):
                    count = efficiency_counts[level]
                    percentage = (count / len(car_results)) * 100
                    terminalreporter.write_line(
                        f"  {level}: {count} tests ({percentage:.1f}%)"
                    )

                # Display similar tests
                if signatures:
                    terminalreporter.write_line("Similar Tests (coverage signatures):")
                    similar_pairs = []

                    for key1, sig1 in signatures.items():
                        for key2, sig2 in signatures.items():
                            if key1 < key2:  # Avoid duplicates
                                similarity = (
                                    self.signature_generator.calculate_similarity(
                                        sig1, sig2
                                    )
                                )
                                if similarity >= 0.8:  # High similarity threshold
                                    similar_pairs.append((sig1, sig2, similarity))

                    if similar_pairs:
                        for sig1, sig2, similarity in similar_pairs[:5]:  # Show top 5
                            terminalreporter.write_line(
                                f"  {sig1.test_name} <-> {sig2.test_name}: {similarity:.2f} similarity"
                            )
                    else:
                        terminalreporter.write_line("  No highly similar tests found")

                # Display duplicate clusters
                if self._duplicate_clusters:
                    terminalreporter.write_line("Duplicate Test Clusters:")
                    for cluster in self._duplicate_clusters:
                        terminalreporter.write_line(
                            f"  Cluster {cluster.cluster_id} ({cluster.cluster_type}):"
                        )
                        terminalreporter.write_line(
                            f"    Similarity: {cluster.similarity_score:.2f}"
                        )
                        terminalreporter.write_line(f"    Tests: {len(cluster.tests)}")
                        for test_name, test_file in cluster.tests:
                            terminalreporter.write_line(
                                f"      - {test_name} ({test_file.name})"
                            )
                        if cluster.consolidation_suggestion:
                            terminalreporter.write_line(
                                f"    Suggestion: {cluster.consolidation_suggestion}"
                            )
                        terminalreporter.write_line("")
                else:
                    terminalreporter.write_line("No duplicate test clusters found")
            else:
                terminalreporter.write_line("No coverage data collected")

            terminalreporter.write_sep("=", "END COVERAGE ANALYSIS SUMMARY")

        except Exception as e:
            self.logger.error(f"Failed to generate coverage summary: {e}")

    def _run_duplicate_detection(self) -> None:
        """Run duplicate detection analysis on collected coverage data."""
        try:
            if not self.coverage_collector._coverage_data:
                self.logger.debug("No coverage data available for duplicate detection")
                return

            # Get test files from coverage data
            test_files = set()
            for coverage_data in self.coverage_collector._coverage_data.values():
                test_files.add(coverage_data.file_path)

            # Run duplicate detection
            self._duplicate_clusters = self.clone_detector.analyze_test_suite(
                list(test_files), self.coverage_collector._coverage_data
            )

            self.logger.info(
                f"Duplicate detection found {len(self._duplicate_clusters)} clusters"
            )

        except Exception as e:
            self.logger.error(f"Failed to run duplicate detection: {e}")
            self._duplicate_clusters = []


# Global instance for use by pytest hooks
_coverage_hooks = CoverageHooks()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add coverage-related command line options."""
    group = parser.getgroup("drill-sergeant-coverage")
    group.addoption(
        "--ds-coverage",
        action="store_true",
        default=False,
        help="Enable drill sergeant coverage collection and analysis",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure coverage collection."""
    _coverage_hooks.pytest_configure(config)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Clean up coverage collection."""
    _coverage_hooks.pytest_unconfigure(config)


def pytest_runtest_setup(item: Item) -> None:
    """Setup before each test runs."""
    _coverage_hooks.pytest_runtest_setup(item)


def pytest_runtest_call(item: Item) -> None:
    """Execute the test with coverage collection."""
    _coverage_hooks.pytest_runtest_call(item)


def pytest_runtest_teardown(item: Item) -> None:
    """Cleanup after each test runs."""
    _coverage_hooks.pytest_runtest_teardown(item)


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    """Generate coverage summary in terminal output."""
    _coverage_hooks.pytest_terminal_summary(terminalreporter, exitstatus, config)
