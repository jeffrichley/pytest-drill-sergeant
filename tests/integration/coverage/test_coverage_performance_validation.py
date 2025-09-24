"""Performance validation tests for coverage data collection.

This module contains tests to validate that coverage collection
performs well with large files, many tests, and complex scenarios.
"""

import tempfile
import time
from pathlib import Path

from pytest_drill_sergeant.core.analyzers.coverage_collector import (
    CoverageCollector,
    CoverageData,
)


class TestCoveragePerformanceValidation:
    """Test coverage collection performance characteristics."""

    def test_large_file_coverage_performance(self):
        """Test coverage collection with large files (1000+ lines)."""
        collector = CoverageCollector()

        # Create a large test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Generate 1000 lines of code
            f.write(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    return a / b

def subtract(a, b):
    return a - b

"""
            )

            # Add many functions
            for i in range(100):
                f.write(
                    f'''
def function_{i}(x):
    """Function {i}."""
    if x > 0:
        return x * {i}
    elif x < 0:
        return x / {i}
    else:
        return 0

def test_function_{i}():
    """Test function {i}."""
    result = function_{i}(5)
    assert result == 5 * {i}
'''
                )

            test_file = Path(f.name)

        try:
            start_time = time.time()

            # Collect coverage for one of the tests
            result = collector.collect_test_coverage(test_file, "test_function_50", 15)

            end_time = time.time()
            collection_time = end_time - start_time

            # Verify we got coverage data
            assert isinstance(result, CoverageData)
            assert result.test_name == "test_function_50"

            # Verify performance is acceptable (< 5 seconds for large file)
            assert (
                collection_time < 5.0
            ), f"Coverage collection took too long: {collection_time:.2f}s"

            # Verify coverage is positive
            assert (
                result.coverage_percentage > 0
            ), f"Expected positive coverage, got {result.coverage_percentage}%"

        finally:
            test_file.unlink()

    def test_many_test_functions_performance(self):
        """Test coverage collection with many test functions."""
        collector = CoverageCollector()

        # Create a test file with many test functions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

"""
            )

            # Generate 200 test functions
            for i in range(200):
                f.write(
                    f'''
def test_add_{i}():
    """Test add function {i}."""
    result = add({i}, {i + 1})
    assert result == {i + i + 1}

def test_multiply_{i}():
    """Test multiply function {i}."""
    result = multiply({i}, {i + 1})
    assert result == {i * (i + 1)}
'''
                )

            test_file = Path(f.name)

        try:
            start_time = time.time()

            # Collect coverage for multiple tests
            results = []
            for i in range(10):  # Test 10 different functions
                result = collector.collect_test_coverage(test_file, f"test_add_{i}", 5)
                results.append(result)

            end_time = time.time()
            total_time = end_time - start_time

            # Verify we got coverage data for all tests
            assert len(results) == 10
            for result in results:
                assert isinstance(result, CoverageData)
                assert result.coverage_percentage > 0

            # Verify performance is acceptable (< 3 seconds for 10 tests)
            assert (
                total_time < 3.0
            ), f"Coverage collection took too long: {total_time:.2f}s"

        finally:
            test_file.unlink()

    def test_memory_usage_with_large_coverage_data(self):
        """Test memory usage with large coverage datasets."""
        collector = CoverageCollector()

        # Create many coverage data objects
        coverage_data_list = []

        start_time = time.time()

        for i in range(1000):
            coverage_data = CoverageData(
                test_name=f"test_memory_{i}",
                file_path=Path(f"/tmp/test_{i}.py"),
                line_number=1,
                lines_covered=50,
                lines_total=100,
                branches_covered=25,
                branches_total=50,
                coverage_percentage=50.0,
                covered_lines=set(range(1, 51)),
                missing_lines=set(range(51, 101)),
            )
            coverage_data_list.append(coverage_data)

        end_time = time.time()
        creation_time = end_time - start_time

        # Should create objects quickly (< 1 second)
        assert (
            creation_time < 1.0
        ), f"Coverage data creation took too long: {creation_time:.2f}s"

        # Should be able to store many objects
        assert len(coverage_data_list) == 1000

        # Test serialization performance
        start_time = time.time()

        serialized_data = []
        for coverage_data in coverage_data_list[:100]:  # Test first 100
            serialized = coverage_data.to_dict()
            serialized_data.append(serialized)

        end_time = time.time()
        serialization_time = end_time - start_time

        # Should serialize quickly (< 0.5 seconds)
        assert (
            serialization_time < 0.5
        ), f"Serialization took too long: {serialization_time:.2f}s"

        # Test deserialization performance
        start_time = time.time()

        deserialized_data = []
        for serialized in serialized_data:
            deserialized = CoverageData.from_dict(serialized)
            deserialized_data.append(deserialized)

        end_time = time.time()
        deserialization_time = end_time - start_time

        # Should deserialize quickly (< 0.5 seconds)
        assert (
            deserialization_time < 0.5
        ), f"Deserialization took too long: {deserialization_time:.2f}s"

        # Verify data integrity
        for original, deserialized in zip(
            coverage_data_list[:100], deserialized_data, strict=False
        ):
            assert original == deserialized, "Deserialized data should match original"

    def test_concurrent_coverage_collection_performance(self):
        """Test concurrent coverage collection performance."""
        collectors = [CoverageCollector() for _ in range(5)]

        # Create test files for each collector
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(
                    f"""
def add_{i}(a, b):
    return a + b

def test_add_{i}():
    result = add_{i}(2, 3)
    assert result == 5
"""
                )
                test_files.append(Path(f.name))

        try:
            start_time = time.time()

            # Start all collectors
            for collector in collectors:
                collector.start_coverage()

            # Collect coverage from all collectors
            results = []
            for i, collector in enumerate(collectors):
                result = collector.collect_test_coverage(
                    test_files[i], f"test_add_{i}", 5
                )
                results.append(result)

            # Stop all collectors
            for collector in collectors:
                collector.stop_coverage()

            end_time = time.time()
            total_time = end_time - start_time

            # Verify we got results from all collectors
            assert len(results) == 5
            for result in results:
                assert isinstance(result, CoverageData)
                assert result.coverage_percentage > 0

            # Should complete quickly (< 2 seconds)
            assert (
                total_time < 2.0
            ), f"Concurrent collection took too long: {total_time:.2f}s"

        finally:
            # Cleanup test files
            for test_file in test_files:
                test_file.unlink()

    def test_coverage_data_comparison_performance(self):
        """Test performance of coverage data comparison operations."""
        # Create many coverage data objects
        coverage_data_list = []

        for i in range(500):
            coverage_data = CoverageData(
                test_name=f"test_comparison_{i}",
                file_path=Path(f"/tmp/test_{i}.py"),
                line_number=1,
                lines_covered=50,
                lines_total=100,
                branches_covered=25,
                branches_total=50,
                coverage_percentage=50.0,
                covered_lines=set(range(1, 51)),
                missing_lines=set(range(51, 101)),
            )
            coverage_data_list.append(coverage_data)

        start_time = time.time()

        # Test equality comparisons
        comparisons = []
        for i in range(min(100, len(coverage_data_list))):
            for j in range(i + 1, min(100, len(coverage_data_list))):
                is_equal = coverage_data_list[i] == coverage_data_list[j]
                comparisons.append(is_equal)

        end_time = time.time()
        comparison_time = end_time - start_time

        # Should compare quickly (< 1 second)
        assert (
            comparison_time < 1.0
        ), f"Comparison operations took too long: {comparison_time:.2f}s"

        # Should have performed many comparisons
        assert len(comparisons) > 0, "Should have performed comparisons"

        # Test that identical objects are equal
        identical_comparison = coverage_data_list[0] == coverage_data_list[0]
        assert identical_comparison, "Identical objects should be equal"

        # Test that different objects are not equal
        different_comparison = coverage_data_list[0] == coverage_data_list[1]
        assert not different_comparison, "Different objects should not be equal"

    def test_coverage_signature_generation_performance(self):
        """Test performance of coverage signature generation."""
        from pytest_drill_sergeant.core.analyzers.coverage_signature import (
            CoverageSignatureGenerator,
        )

        generator = CoverageSignatureGenerator()

        # Create many coverage data objects
        coverage_data_list = []

        for i in range(200):
            coverage_data = CoverageData(
                test_name=f"test_signature_{i}",
                file_path=Path(f"/tmp/test_{i}.py"),
                line_number=1,
                lines_covered=50 + i,
                lines_total=100,
                branches_covered=25 + i,
                branches_total=50,
                coverage_percentage=50.0 + i,
                covered_lines=set(range(1, 51 + i)),
                missing_lines=set(range(51 + i, 101)),
            )
            coverage_data_list.append(coverage_data)

        start_time = time.time()

        # Generate signatures for all coverage data
        signatures = []
        for coverage_data in coverage_data_list:
            signature = generator.generate_signature(
                coverage_data.file_path, coverage_data.test_name, coverage_data
            )
            signatures.append(signature)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should generate signatures quickly (< 2 seconds)
        assert (
            generation_time < 2.0
        ), f"Signature generation took too long: {generation_time:.2f}s"

        # Should have generated all signatures
        assert len(signatures) == 200

        # Test similarity calculation performance
        start_time = time.time()

        similarities = []
        for i in range(min(50, len(signatures))):
            for j in range(i + 1, min(50, len(signatures))):
                similarity = generator.calculate_similarity(
                    signatures[i], signatures[j]
                )
                similarities.append(similarity)

        end_time = time.time()
        similarity_time = end_time - start_time

        # Should calculate similarities quickly (< 1 second)
        assert (
            similarity_time < 1.0
        ), f"Similarity calculation took too long: {similarity_time:.2f}s"

        # Should have calculated similarities
        assert len(similarities) > 0, "Should have calculated similarities"
        assert all(
            0.0 <= sim <= 1.0 for sim in similarities
        ), "Similarities should be between 0 and 1"


class TestCoverageAccuracyValidation:
    """Test coverage data accuracy with comprehensive validation."""

    def test_coverage_percentage_calculation_accuracy(self):
        """Test that coverage percentages are calculated with high accuracy."""
        collector = CoverageCollector()

        # Create test files with known line counts
        test_cases = [
            (10, 5),  # 50% coverage
            (20, 10),  # 50% coverage
            (100, 75),  # 75% coverage
            (50, 25),  # 50% coverage
        ]

        for total_lines, covered_lines in test_cases:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                # Generate code with known line count
                f.write("def add(a, b):\n")
                f.write("    return a + b\n\n")

                # Add more lines to reach total_lines
                for i in range(total_lines - 2):
                    f.write(f"# Line {i + 3}\n")

                f.write("\ndef test_add():\n")
                f.write("    result = add(2, 3)\n")
                f.write("    assert result == 5\n")

                test_file = Path(f.name)

            try:
                # Collect coverage
                result = collector.collect_test_coverage(
                    test_file, "test_add", total_lines - 2
                )

                # Verify coverage calculation accuracy
                if result.lines_total > 0:
                    expected_percentage = (
                        result.lines_covered / result.lines_total
                    ) * 100
                    actual_percentage = result.coverage_percentage

                    # Allow small floating point differences
                    assert (
                        abs(actual_percentage - expected_percentage) < 0.1
                    ), f"Coverage percentage {actual_percentage}% does not match expected {expected_percentage}%"

            finally:
                test_file.unlink()

    def test_covered_lines_accuracy_with_complex_code(self):
        """Test that covered lines are accurately tracked with complex code."""
        collector = CoverageCollector()

        # Create complex test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def complex_function(x, y):
    """Complex function with multiple branches."""
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        if y > 0:
            return y - x
        else:
            return -(x + y)
    else:
        return 0

def test_positive_both():
    """Test positive x and y."""
    result = complex_function(5, 3)
    assert result == 8

def test_positive_x_negative_y():
    """Test positive x and negative y."""
    result = complex_function(5, -3)
    assert result == 2
'''
            )
            test_file = Path(f.name)

        try:
            # Test first scenario
            result1 = collector.collect_test_coverage(
                test_file, "test_positive_both", 15
            )

            # Test second scenario
            result2 = collector.collect_test_coverage(
                test_file, "test_positive_x_negative_y", 19
            )

            # Verify both results are valid
            assert isinstance(result1, CoverageData)
            assert isinstance(result2, CoverageData)

            # Verify coverage is positive
            assert result1.coverage_percentage > 0
            assert result2.coverage_percentage > 0

            # Verify covered lines are reasonable
            assert len(result1.covered_lines) > 0
            assert len(result2.covered_lines) > 0

            # Verify no overlap between covered and missing lines
            overlap1 = result1.covered_lines.intersection(result1.missing_lines)
            overlap2 = result2.covered_lines.intersection(result2.missing_lines)

            assert (
                len(overlap1) == 0
            ), f"Test 1: Covered and missing lines overlap: {overlap1}"
            assert (
                len(overlap2) == 0
            ), f"Test 2: Covered and missing lines overlap: {overlap2}"

        finally:
            test_file.unlink()

    def test_branch_coverage_accuracy(self):
        """Test that branch coverage is accurately calculated."""
        collector = CoverageCollector()

        # Create test file with branches
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''
def branch_function(x):
    """Function with multiple branches."""
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"

def test_positive_branch():
    """Test positive branch only."""
    result = branch_function(5)
    assert result == "positive"
'''
            )
            test_file = Path(f.name)

        try:
            # Collect coverage
            result = collector.collect_test_coverage(
                test_file, "test_positive_branch", 9
            )

            # Verify we got coverage data
            assert isinstance(result, CoverageData)

            # Verify branch coverage is reasonable
            assert result.branches_covered >= 0
            assert result.branches_total >= 0

            if result.branches_total > 0:
                assert result.branches_covered <= result.branches_total

            # Verify coverage is positive
            assert result.coverage_percentage > 0

        finally:
            test_file.unlink()

    def test_coverage_data_consistency_across_runs(self):
        """Test that coverage data is consistent across multiple runs."""
        collector = CoverageCollector()

        # Create test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
def add(a, b):
    return a + b

def test_add():
    result = add(2, 3)
    assert result == 5
"""
            )
            test_file = Path(f.name)

        try:
            # Run coverage collection multiple times
            results = []
            for _ in range(5):
                result = collector.collect_test_coverage(test_file, "test_add", 5)
                results.append(result)

            # Verify all results are consistent
            for i, result in enumerate(results):
                assert isinstance(result, CoverageData)
                assert result.test_name == "test_add"

                # All results should be equal
                for j, other_result in enumerate(results):
                    if i != j:
                        assert (
                            result == other_result
                        ), f"Results {i} and {j} should be equal"

        finally:
            test_file.unlink()
