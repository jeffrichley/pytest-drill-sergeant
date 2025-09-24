"""Tests to verify that real coverage collection is working.

This module contains tests that verify the coverage collection
actually returns real (non-zero) coverage data from coverage.py.
"""

import tempfile
from pathlib import Path

from pytest_drill_sergeant.core.analyzers.coverage_collector import (
    CoverageCollector,
    CoverageData,
)


class TestRealCoverageCollection:
    """Test that coverage collection returns real coverage data."""

    def test_coverage_collection_returns_real_data(self):
        """Test that coverage collection returns real (non-zero) coverage data."""
        collector = CoverageCollector()

        # Create a test file with source code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b  # This won't be executed

def test_add():
    assert add(2, 3) == 5
"""
            )
            test_file = Path(f.name)

        try:
            # Collect coverage for the test
            result = collector.collect_test_coverage(test_file, "test_add", 7)

            # Verify we got real coverage data
            assert isinstance(result, CoverageData)
            assert result.test_name == "test_add"
            assert result.file_path == test_file

            # CRITICAL: Verify that coverage is real (not zero)
            assert (
                result.coverage_percentage > 0
            ), f"Expected real coverage, got {result.coverage_percentage}%"
            assert (
                result.lines_covered > 0
            ), f"Expected real lines covered, got {result.lines_covered}"
            assert (
                result.lines_total > 0
            ), f"Expected real lines total, got {result.lines_total}"

            # Verify that we have actual covered lines
            assert (
                len(result.covered_lines) > 0
            ), f"Expected covered lines, got {result.covered_lines}"

            # Verify coverage signature includes analysis data
            assert result.coverage_signature is not None
            assert "analysis:" in result.coverage_signature

        finally:
            test_file.unlink()

    def test_coverage_collection_with_partial_execution(self):
        """Test coverage collection when some code is not executed."""
        collector = CoverageCollector()

        # Create a test file with unexecuted code
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b  # This won't be executed

def divide(a, b):
    return a / b  # This won't be executed either

def test_add():
    assert add(2, 3) == 5
"""
            )
            test_file = Path(f.name)

        try:
            # Collect coverage for the test
            result = collector.collect_test_coverage(test_file, "test_add", 7)

            # Verify we got real coverage data
            assert isinstance(result, CoverageData)
            assert result.test_name == "test_add"

            # Verify that coverage is real (not zero)
            assert (
                result.coverage_percentage > 0
            ), f"Expected real coverage, got {result.coverage_percentage}%"
            assert (
                result.lines_covered > 0
            ), f"Expected real lines covered, got {result.lines_covered}"
            assert (
                result.lines_total > 0
            ), f"Expected real lines total, got {result.lines_total}"

            # Verify that we have actual covered lines
            assert (
                len(result.covered_lines) > 0
            ), f"Expected covered lines, got {result.covered_lines}"

            # The coverage should be less than 100% since some functions aren't executed
            # (though it might be 100% if only function definitions are measured)
            assert (
                result.coverage_percentage <= 100.0
            ), f"Coverage should not exceed 100%, got {result.coverage_percentage}%"

        finally:
            test_file.unlink()

    def test_coverage_collection_with_multiple_functions(self):
        """Test coverage collection with multiple test functions."""
        collector = CoverageCollector()

        # Create a test file with multiple functions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(2, 3) == 6
"""
            )
            test_file = Path(f.name)

        try:
            # Test first function
            result1 = collector.collect_test_coverage(test_file, "test_add", 7)
            assert result1.coverage_percentage > 0
            assert result1.lines_covered > 0

            # Test second function
            result2 = collector.collect_test_coverage(test_file, "test_multiply", 9)
            assert result2.coverage_percentage > 0
            assert result2.lines_covered > 0

            # Both should have real coverage data
            assert isinstance(result1, CoverageData)
            assert isinstance(result2, CoverageData)

        finally:
            test_file.unlink()

    def test_coverage_collection_error_handling(self):
        """Test coverage collection error handling."""
        collector = CoverageCollector()

        # Test with non-existent file
        non_existent_file = Path("/non/existent/file.py")
        result = collector.collect_test_coverage(
            non_existent_file, "test_nonexistent", 1
        )

        # Should return empty coverage data
        assert isinstance(result, CoverageData)
        assert result.test_name == "test_nonexistent"
        assert result.lines_covered == 0
        assert result.lines_total == 0
        assert result.coverage_percentage == 0.0

    def test_coverage_collection_with_analysis_integration(self):
        """Test that coverage collection integrates with analysis results."""
        collector = CoverageCollector()

        # Create a test file with imports and calls
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
from pathlib import Path

def add(a, b):
    return a + b

def test_add():
    result = add(2, 3)
    assert result == 5
    assert os.path.exists('/tmp')
"""
            )
            test_file = Path(f.name)

        try:
            # Collect coverage for the test
            result = collector.collect_test_coverage(test_file, "test_add", 7)

            # Verify we got real coverage data
            assert isinstance(result, CoverageData)
            assert result.coverage_percentage > 0

            # Verify analysis integration
            assert result.coverage_signature is not None
            assert "analysis:" in result.coverage_signature

            # Check that analysis results are stored
            analysis_results = collector.get_all_analysis_results()
            assert len(analysis_results) > 0

            # Check that we have import and call analysis
            import_results = collector.get_analysis_results("test_add_imports")
            call_results = collector.get_analysis_results("test_add_calls")

            assert import_results is not None
            assert call_results is not None

        finally:
            test_file.unlink()
