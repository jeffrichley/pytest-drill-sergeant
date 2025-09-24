"""Integration with pytest-cov for coverage data access.

This module provides a way to hook into pytest-cov's existing coverage
collection instead of implementing our own coverage system.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.nodes import Item

from pytest_drill_sergeant.core.analyzers.car_calculator import CARCalculator
from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
from pytest_drill_sergeant.core.analyzers.coverage_signature import (
    CoverageSignatureGenerator,
)


class PytestCovIntegration:
    """Integration with pytest-cov for accessing coverage data."""

    def __init__(self) -> None:
        """Initialize the pytest-cov integration."""
        self.logger = logging.getLogger("drill_sergeant.pytest_cov_integration")
        self._coverage_data: dict[str, CoverageData] = {}
        self._car_calculator = CARCalculator()
        self._signature_generator = CoverageSignatureGenerator()
        self._coverage_enabled = False

    def pytest_configure(self, config) -> None:
        """Configure the integration when pytest starts."""
        # Check if pytest-cov is enabled
        if hasattr(config, "option") and hasattr(config.option, "cov"):
            self._coverage_enabled = config.option.cov is not None
            self.logger.info(
                f"pytest-cov integration {'enabled' if self._coverage_enabled else 'disabled'}"
            )
        else:
            self._coverage_enabled = False
            self.logger.info("pytest-cov not detected, integration disabled")

    def pytest_runtest_call(self, item: Item) -> None:
        """Extract coverage data after each test runs."""
        try:
            if not self._coverage_enabled:
                return

            # Get test information
            test_file_path = Path(item.fspath)
            test_name = item.name.split("::")[-1] if "::" in item.name else item.name
            test_line_number = item.location[1] if item.location else 0

            # Extract coverage data from pytest-cov
            coverage_data = self._extract_coverage_from_pytest_cov(
                test_file_path, test_name, test_line_number
            )

            if coverage_data:
                # Calculate CAR for this test
                car_result = self._car_calculator.calculate_car(
                    test_file_path, test_name, test_line_number, coverage_data
                )

                # Generate coverage signature
                signature = self._signature_generator.generate_signature(
                    test_file_path, test_name, coverage_data
                )

                # Store results in the test item
                item.ds_coverage_data = coverage_data
                item.ds_car_result = car_result
                item.ds_coverage_signature = signature

                self.logger.debug(f"Coverage analysis completed for {test_name}")

        except Exception as e:
            self.logger.error(f"Failed to extract coverage data: {e}")

    def _extract_coverage_from_pytest_cov(
        self, test_file_path: Path, test_name: str, test_line_number: int
    ) -> CoverageData | None:
        """Extract coverage data from pytest-cov's coverage collection.

        Args:
            test_file_path: Path to the test file
            test_name: Name of the test function
            test_line_number: Line number where test starts

        Returns:
            CoverageData object with coverage information, or None if not available
        """
        try:
            import coverage

            # Get the current coverage instance
            # pytest-cov should have started coverage collection
            cov = coverage.Coverage.current()
            if cov is None:
                self.logger.warning("No active coverage collection found")
                return None

            # Get coverage data
            data = cov.get_data()

            # Find source files that were covered
            measured_files = data.measured_files()
            if not measured_files:
                self.logger.warning("No files were measured for coverage")
                return None

            # Calculate coverage for each measured file
            total_lines = 0
            covered_lines = 0
            total_branches = 0
            covered_branches = 0
            all_covered_lines = set()
            all_missing_lines = set()

            for file_path in measured_files:
                file_path_obj = Path(file_path)

                # Skip test files themselves
                if self._is_test_file(file_path_obj):
                    continue

                # Get line coverage for this file
                lines = data.lines(file_path)
                if lines:
                    total_lines += len(lines)

                    # Get executed lines (this is a simplified approach)
                    # In practice, we'd need to track which lines were executed
                    # during this specific test, which is complex with pytest-cov
                    executed_lines = set(
                        lines
                    )  # Simplified - assume all measured lines were executed
                    covered_lines += len(executed_lines)

                    # Track covered and missing lines
                    all_covered_lines.update(executed_lines)
                    all_missing_lines.update(set(lines) - executed_lines)

                # Get branch coverage
                arcs = data.arcs(file_path)
                if arcs:
                    total_branches += len(arcs)
                    # Simplified branch coverage calculation
                    covered_branches += len(arcs)

            # Calculate coverage percentage
            coverage_percentage = (
                (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            )

            # Generate coverage signature
            coverage_signature = self._generate_coverage_signature(
                all_covered_lines, measured_files
            )

            return CoverageData(
                test_name=test_name,
                file_path=test_file_path,
                line_number=test_line_number,
                lines_covered=covered_lines,
                lines_total=total_lines,
                branches_covered=covered_branches,
                branches_total=total_branches,
                coverage_percentage=coverage_percentage,
                covered_lines=all_covered_lines,
                missing_lines=all_missing_lines,
                coverage_signature=coverage_signature,
            )

        except Exception as e:
            self.logger.error(f"Failed to extract coverage data from pytest-cov: {e}")
            return None

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file."""
        name = file_path.name.lower()
        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or name.startswith("test")
            or "test" in file_path.parts
        )

    def _generate_coverage_signature(
        self, covered_lines: set[int], measured_files: list[str]
    ) -> str:
        """Generate a signature for coverage similarity detection."""
        try:
            import hashlib

            signature_parts = []

            # Add file information
            for file_path in measured_files:
                file_name = Path(file_path).name
                signature_parts.append(f"{file_name}:{len(covered_lines)}")

            # Add coverage pattern
            if covered_lines:
                coverage_str = ",".join(sorted(str(line) for line in covered_lines))
                coverage_hash = hashlib.md5(coverage_str.encode()).hexdigest()[:8]
                signature_parts.append(f"coverage:{coverage_hash}")

            return "|".join(signature_parts)

        except Exception as e:
            self.logger.error(f"Failed to generate coverage signature: {e}")
            return ""

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config) -> None:
        """Generate coverage analysis summary."""
        try:
            if not self._coverage_enabled:
                return

            # Collect all coverage data from test items
            coverage_data_list = []
            car_results = []

            for item in terminalreporter.config.hook.pytest_collection_modifyitems(
                session=terminalreporter.config.session,
                config=terminalreporter.config,
                items=terminalreporter.config.session.items,
            ):
                if hasattr(item, "ds_coverage_data") and item.ds_coverage_data:
                    coverage_data_list.append(item.ds_coverage_data)
                if hasattr(item, "ds_car_result") and item.ds_car_result:
                    car_results.append(item.ds_car_result)

            if not coverage_data_list:
                return

            # Calculate summary statistics
            total_tests = len(coverage_data_list)
            avg_coverage = (
                sum(cd.coverage_percentage for cd in coverage_data_list) / total_tests
            )
            avg_car = (
                sum(cr.car_score for cr in car_results) / len(car_results)
                if car_results
                else 0.0
            )

            # Generate summary
            terminalreporter.write_sep("=", "COVERAGE ANALYSIS SUMMARY")
            terminalreporter.write_line(f"Total tests analyzed: {total_tests}")
            terminalreporter.write_line(f"Average coverage: {avg_coverage:.1f}%")
            terminalreporter.write_line(f"Average CAR score: {avg_car:.1f}")

        except Exception as e:
            self.logger.error(f"Failed to generate coverage summary: {e}")
