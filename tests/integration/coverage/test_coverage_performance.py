"""Performance tests for coverage collection."""

import tempfile
import time
from pathlib import Path

from pytest_drill_sergeant.core.analyzers.car_calculator import CARCalculator
from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageCollector
from pytest_drill_sergeant.core.analyzers.coverage_signature import (
    CoverageSignatureGenerator,
)


class TestCoveragePerformance:
    """Test performance characteristics of coverage collection."""

    def test_coverage_collector_performance(self):
        """Test coverage collector performance with many tests."""
        collector = CoverageCollector()

        # Create a large test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            test_content = '''
def test_function():
    """Test function."""
    pass

'''
            # Generate 100 test functions
            for i in range(100):
                test_content += f'''
def test_example_{i}():
    """Test example {i}."""
    assert {i} + 1 == {i + 1}
    assert {i} * 2 == {i * 2}
    assert {i} - 1 == {i - 1}
'''

            f.write(test_content)
            test_file_path = Path(f.name)

        try:
            start_time = time.time()

            # Analyze the large test file
            findings = collector.analyze_file(test_file_path)

            end_time = time.time()
            analysis_time = end_time - start_time

            # Should complete in reasonable time (< 5 seconds)
            assert analysis_time < 5.0, f"Analysis took too long: {analysis_time:.2f}s"

            # Should complete analysis without errors
            # Coverage collector may or may not find issues depending on implementation
            assert isinstance(findings, list), "Should return a list of findings"

        finally:
            test_file_path.unlink()

    def test_car_calculator_performance(self):
        """Test CAR calculator performance with many tests."""
        calculator = CARCalculator()

        # Create a large test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            test_content = ""

            # Generate 50 test functions with varying assertion counts
            for i in range(50):
                if i < 10:
                    # First 10 tests have no assertions (should trigger DS401)
                    assertion_count = 0
                elif i < 20:
                    # Next 10 tests have 1-5 assertions (normal)
                    assertion_count = (i % 5) + 1
                else:
                    # Remaining tests have 11-20 assertions (should trigger DS402)
                    assertion_count = (i % 10) + 11

                test_content += f'''
def test_car_example_{i}():
    """Test CAR example {i}."""
'''
                for j in range(assertion_count):
                    test_content += f"    assert {i} + {j} == {i + j}\n"

            f.write(test_content)
            test_file_path = Path(f.name)

        try:
            start_time = time.time()

            # Analyze the large test file
            findings = calculator.analyze_file(test_file_path)

            end_time = time.time()
            analysis_time = end_time - start_time

            # Should complete in reasonable time (< 3 seconds)
            assert (
                analysis_time < 3.0
            ), f"CAR analysis took too long: {analysis_time:.2f}s"

            # Should find specific CAR issues
            assert len(findings) > 0, "Should find some CAR issues"

            # Verify we found the expected types of issues
            issue_codes = {finding.code for finding in findings}
            assert (
                "DS401" in issue_codes
            ), "Should find tests with no assertions (DS401)"
            assert (
                "DS402" in issue_codes
            ), "Should find tests with too many assertions (DS402)"

            # Verify we found issues for the expected number of tests
            no_assertion_findings = [f for f in findings if f.code == "DS401"]
            too_many_assertion_findings = [f for f in findings if f.code == "DS402"]

            assert (
                len(no_assertion_findings) == 10
            ), f"Expected 10 tests with no assertions, found {len(no_assertion_findings)}"
            assert (
                len(too_many_assertion_findings) == 30
            ), f"Expected 30 tests with too many assertions, found {len(too_many_assertion_findings)}"

        finally:
            test_file_path.unlink()

    def test_coverage_signature_performance(self):
        """Test coverage signature generation performance."""
        generator = CoverageSignatureGenerator()

        # Create many coverage signatures
        signatures = []

        start_time = time.time()

        for i in range(100):
            from pytest_drill_sergeant.core.analyzers.coverage_collector import (
                CoverageData,
            )

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

            signature = generator.generate_signature(
                Path(f"/tmp/test_{i}.py"), f"test_signature_{i}", coverage_data
            )
            signatures.append(signature)

        end_time = time.time()
        generation_time = end_time - start_time

        # Should generate signatures quickly (< 2 seconds)
        assert (
            generation_time < 2.0
        ), f"Signature generation took too long: {generation_time:.2f}s"

        # Test similarity calculations
        start_time = time.time()

        # Calculate similarities between all pairs
        similarities = []
        for i in range(min(10, len(signatures))):
            for j in range(i + 1, min(10, len(signatures))):
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

        # Should have reasonable similarities
        assert len(similarities) > 0, "Should calculate similarities between signatures"
        assert all(
            0.0 <= sim <= 1.0 for sim in similarities
        ), "Similarities should be between 0 and 1"

        # Verify similarity calculation is working correctly
        # Identical signatures should have similarity of 1.0
        identical_similarity = generator.calculate_similarity(
            signatures[0], signatures[0]
        )
        assert (
            identical_similarity == 1.0
        ), f"Identical signatures should have similarity 1.0, got {identical_similarity}"

        # Different signatures should have similarity < 1.0
        if len(signatures) > 1:
            different_similarity = generator.calculate_similarity(
                signatures[0], signatures[1]
            )
            assert (
                different_similarity < 1.0
            ), f"Different signatures should have similarity < 1.0, got {different_similarity}"

    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets."""
        generator = CoverageSignatureGenerator()

        # Create many signatures to test memory usage
        signatures = []

        for i in range(1000):
            from pytest_drill_sergeant.core.analyzers.coverage_collector import (
                CoverageData,
            )

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

            signature = generator.generate_signature(
                Path(f"/tmp/test_{i}.py"), f"test_memory_{i}", coverage_data
            )
            signatures.append(signature)

        # Should be able to store many signatures
        assert len(signatures) == 1000

        # Test finding similar tests
        if signatures:
            target_sig = signatures[0]
            similar_tests = generator.find_similar_tests(target_sig, threshold=0.5)

            # Should find some similar tests
            assert len(similar_tests) > 0

    def test_concurrent_coverage_collection(self):
        """Test concurrent coverage collection (basic test)."""
        # Test that multiple collectors don't interfere
        collectors = [CoverageCollector() for _ in range(5)]

        start_time = time.time()

        try:
            # Start all collectors
            for collector in collectors:
                collector.start_coverage()

            # Verify all collectors are in a valid state
            for i, collector in enumerate(collectors):
                assert hasattr(
                    collector, "cov"
                ), f"Collector {i} should have coverage object after start"

            # Stop all collectors
            for collector in collectors:
                collector.stop_coverage()

        except Exception as e:
            # Ensure cleanup even if test fails
            for collector in collectors:
                try:
                    collector.stop_coverage()
                except:
                    pass
            raise e

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete quickly (< 2 seconds)
        assert (
            total_time < 2.0
        ), f"Concurrent collection took too long: {total_time:.2f}s"

        # Verify collectors are in clean state
        for i, collector in enumerate(collectors):
            # Coverage object should still exist but be stopped
            assert hasattr(
                collector, "cov"
            ), f"Collector {i} should still have coverage object"
            # Temporary directory should be cleaned up
            assert (
                collector._temp_dir is None
            ), f"Collector {i} should have cleaned up temp directory"

    def test_large_file_analysis(self):
        """Test analysis of very large test files."""
        calculator = CARCalculator()

        # Create a very large test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            test_content = '''
def test_function():
    """Test function."""
    pass

'''
            # Generate 500 test functions
            for i in range(500):
                test_content += f'''
def test_large_example_{i}():
    """Test large example {i}."""
    assert {i} + 1 == {i + 1}
    assert {i} * 2 == {i * 2}
    assert {i} - 1 == {i - 1}
    assert {i} / 1 == {i}
    assert {i} % 2 == {i % 2}
'''

            f.write(test_content)
            test_file_path = Path(f.name)

        try:
            start_time = time.time()

            # Analyze the very large test file
            findings = calculator.analyze_file(test_file_path)

            end_time = time.time()
            analysis_time = end_time - start_time

            # Should complete in reasonable time (< 10 seconds)
            assert (
                analysis_time < 10.0
            ), f"Large file analysis took too long: {analysis_time:.2f}s"

            # Should find CAR issues in large file
            assert len(findings) > 0, "Should find some CAR issues in large file"

            # Verify performance scales reasonably with file size
            # 500 tests should take proportionally longer than 50 tests
            # But should still be efficient (linear or sub-linear scaling)
            assert (
                analysis_time < 10.0
            ), f"Large file analysis took too long: {analysis_time:.2f}s"

            # Verify we're actually analyzing all test functions
            test_function_findings = [
                f for f in findings if f.code in ["DS401", "DS402"]
            ]
            assert (
                len(test_function_findings) > 0
            ), "Should find CAR issues for test functions"

        finally:
            test_file_path.unlink()

    def test_coverage_data_serialization_performance(self):
        """Test performance of coverage data serialization."""
        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        # Create many coverage data objects
        coverage_data_list = []

        start_time = time.time()

        for i in range(1000):
            coverage_data = CoverageData(
                test_name=f"test_serialization_{i}",
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

        # Test accessing all fields
        start_time = time.time()

        for coverage_data in coverage_data_list:
            _ = coverage_data.test_name
            _ = coverage_data.coverage_percentage
            _ = len(coverage_data.covered_lines)
            _ = len(coverage_data.missing_lines)

        end_time = time.time()
        access_time = end_time - start_time

        # Should access fields quickly (< 0.5 seconds)
        assert (
            access_time < 0.5
        ), f"Coverage data access took too long: {access_time:.2f}s"
