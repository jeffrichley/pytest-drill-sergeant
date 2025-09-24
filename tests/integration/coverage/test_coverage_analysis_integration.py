"""Comprehensive tests for coverage analysis integration.

This module contains Google-level comprehensive tests for the integration between
analysis results and coverage collection, including enhanced coverage data and
intelligent source file selection.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageCollector


class TestCoverageAnalysisIntegration:
    """Test integration between analysis results and coverage collection."""

    def test_collect_test_coverage_with_analysis_integration(self):
        """Test that coverage collection integrates analysis results."""
        collector = CoverageCollector()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create structure
            test_dir = tmp_path / "tests"
            src_dir = tmp_path / "src"

            test_dir.mkdir()
            src_dir.mkdir()

            # Create test file
            test_file = test_dir / "test_example.py"
            test_file.write_text(
                """
import os
from pathlib import Path

def test_example():
    result = os.path.join('test', 'file')
    path = Path('test')
    assert result is not None
"""
            )

            # Create source files
            os_file = src_dir / "os.py"
            pathlib_file = src_dir / "pathlib.py"

            os_file.write_text("def join(*args): pass")
            pathlib_file.write_text("class Path: pass")

            # Mock resolve function
            def mock_resolve(module_name, files):
                if module_name == "os":
                    return os_file
                if module_name == "pathlib":
                    return pathlib_file
                return None

            collector._resolve_import_to_file = mock_resolve

            # Collect coverage
            coverage_data = collector.collect_test_coverage(
                test_file, "test_example", 10
            )

            # Verify coverage data
            assert coverage_data.test_name == "test_example"
            assert coverage_data.file_path == test_file
            assert coverage_data.line_number == 10

            # Verify analysis insights are in signature
            assert "analysis:" in coverage_data.coverage_signature
            assert "imports:" in coverage_data.coverage_signature
            assert "calls:" in coverage_data.coverage_signature

    def test_extract_coverage_data_with_analysis(self):
        """Test the enhanced coverage data extraction."""
        collector = CoverageCollector()

        # Create mock coverage data
        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        base_coverage = CoverageData(
            test_name="test_example",
            file_path=Path("/test/test.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="base_signature",
        )

        # Add analysis results
        collector._analysis_results["test_example_imports"] = {
            "import_count": 3,
            "coverage_ratio": 0.75,
            "imported_files": ["file1.py", "file2.py"],
        }

        collector._analysis_results["test_example_calls"] = {
            "call_count": 5,
            "call_types": {"direct_calls": 2, "method_calls": 2, "assertions": 1},
        }

        # Mock the base coverage extraction to return our test data
        with patch.object(
            collector, "_extract_coverage_data", return_value=base_coverage
        ):
            # Test enhanced extraction
            enhanced_coverage = collector._extract_coverage_data_with_analysis(
                Path("/test/test.py"),
                "test_example",
                10,
                [Path("file1.py"), Path("file2.py")],
            )

            # Verify enhancement
            assert enhanced_coverage.test_name == "test_example"
            assert enhanced_coverage.coverage_percentage == 80.0
            assert "analysis:" in enhanced_coverage.coverage_signature
            assert "imports:3" in enhanced_coverage.coverage_signature
            assert "calls:5" in enhanced_coverage.coverage_signature

    def test_enhance_coverage_with_analysis(self):
        """Test coverage enhancement with analysis insights."""
        collector = CoverageCollector()

        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        base_coverage = CoverageData(
            test_name="test_example",
            file_path=Path("/test/test.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="base_signature",
        )

        import_results = {
            "import_count": 2,
            "coverage_ratio": 0.5,
            "imported_files": ["file1.py"],
        }

        call_results = {
            "call_count": 3,
            "call_types": {"direct_calls": 1, "method_calls": 1, "assertions": 1},
        }

        source_files = [Path("file1.py"), Path("file2.py")]

        # Test enhancement
        enhanced_coverage = collector._enhance_coverage_with_analysis(
            base_coverage, import_results, call_results, source_files
        )

        # Verify enhancement
        assert enhanced_coverage.test_name == "test_example"
        assert enhanced_coverage.coverage_percentage == 80.0
        assert "analysis:" in enhanced_coverage.coverage_signature
        assert "imports:2" in enhanced_coverage.coverage_signature
        assert "calls:3" in enhanced_coverage.coverage_signature
        assert "assertions:1" in enhanced_coverage.coverage_signature

    def test_generate_analysis_insights(self):
        """Test analysis insights generation."""
        collector = CoverageCollector()

        import_results = {
            "import_count": 3,
            "coverage_ratio": 0.75,
            "imported_files": ["file1.py", "file2.py"],
        }

        call_results = {
            "call_count": 4,
            "call_types": {"direct_calls": 1, "method_calls": 2, "assertions": 1},
        }

        source_files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]

        # Test insights generation
        insights = collector._generate_analysis_insights(
            import_results, call_results, source_files
        )

        # Verify insights
        assert "imports:3" in insights
        assert "import_coverage:0.75" in insights
        assert "calls:4" in insights
        assert "assertions:1" in insights
        assert "direct_calls:1" in insights
        assert "method_calls:2" in insights
        assert "source_files:3" in insights

    def test_generate_analysis_insights_with_errors(self):
        """Test analysis insights generation with error results."""
        collector = CoverageCollector()

        import_results = {"error": "Import analysis failed"}
        call_results = {"error": "Call analysis failed"}
        source_files = [Path("file1.py")]

        # Test insights generation
        insights = collector._generate_analysis_insights(
            import_results, call_results, source_files
        )

        # Should only include source files count
        assert insights == "source_files:1"

    def test_select_source_files_with_analysis(self):
        """Test intelligent source file selection based on analysis."""
        collector = CoverageCollector()

        all_files = [
            Path("file1.py"),
            Path("file2.py"),
            Path("file3.py"),
            Path("file4.py"),
            Path("file5.py"),
        ]

        imported_files = [Path("file1.py"), Path("file2.py")]
        imported_modules = ["module1", "module2"]

        # Test selection
        selected_files = collector._select_source_files_with_analysis(
            all_files, imported_files, imported_modules
        )

        # Should prioritize imported files
        assert Path("file1.py") in selected_files
        assert Path("file2.py") in selected_files
        assert len(selected_files) <= 20  # Should respect limit

    def test_select_source_files_without_imports(self):
        """Test source file selection when no imports are found."""
        collector = CoverageCollector()

        all_files = [Path(f"file{i}.py") for i in range(60)]  # More than limit
        imported_files = []
        imported_modules = []

        # Test selection
        selected_files = collector._select_source_files_with_analysis(
            all_files, imported_files, imported_modules
        )

        # Should limit to reasonable number
        assert len(selected_files) <= 50
        assert len(selected_files) > 0

    def test_get_analysis_enhanced_coverage_data(self):
        """Test getting analysis-enhanced coverage data."""
        collector = CoverageCollector()

        # Create mock coverage data with analysis
        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        enhanced_coverage = CoverageData(
            test_name="test_example",
            file_path=Path("/test/test.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="base_signature|analysis:imports:2|calls:3",
        )

        # Store in coverage data
        collector._coverage_data["/test/test.py:test_example"] = enhanced_coverage

        # Test retrieval
        result = collector.get_analysis_enhanced_coverage_data(
            Path("/test/test.py"), "test_example"
        )

        assert result is not None
        assert result.test_name == "test_example"
        assert "analysis:" in result.coverage_signature

    def test_get_analysis_enhanced_coverage_data_not_found(self):
        """Test getting analysis-enhanced coverage data when not found."""
        collector = CoverageCollector()

        # Test retrieval of non-existent data
        result = collector.get_analysis_enhanced_coverage_data(
            Path("/test/test.py"), "nonexistent_test"
        )

        assert result is None

    def test_get_coverage_analysis_summary(self):
        """Test getting coverage analysis summary."""
        collector = CoverageCollector()

        # Create mock data
        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        coverage_data = CoverageData(
            test_name="test_example",
            file_path=Path("/test/test.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="base_signature",
        )

        # Store data
        collector._coverage_data["/test/test.py:test_example"] = coverage_data
        collector._analysis_results["test_example_imports"] = {
            "import_count": 2,
            "coverage_ratio": 0.5,
        }
        collector._analysis_results["test_example_calls"] = {
            "call_count": 3,
            "call_types": {"assertions": 1},
        }

        # Test summary generation
        summary = collector.get_coverage_analysis_summary(
            Path("/test/test.py"), "test_example"
        )

        # Verify summary
        assert summary is not None
        assert summary["test_name"] == "test_example"
        assert summary["coverage"]["percentage"] == 80.0
        assert summary["analysis"]["imports"]["import_count"] == 2
        assert summary["analysis"]["calls"]["call_count"] == 3

    def test_get_coverage_analysis_summary_not_found(self):
        """Test getting coverage analysis summary when not found."""
        collector = CoverageCollector()

        # Test summary generation for non-existent data
        summary = collector.get_coverage_analysis_summary(
            Path("/test/test.py"), "nonexistent_test"
        )

        assert summary is None

    def test_integration_error_handling(self):
        """Test error handling in integration."""
        collector = CoverageCollector()

        # Test with invalid data
        with patch.object(collector, "_extract_coverage_data") as mock_extract:
            mock_extract.side_effect = Exception("Coverage extraction failed")

            # Should fallback gracefully
            result = collector._extract_coverage_data_with_analysis(
                Path("/test/test.py"), "test_example", 10, []
            )

            # Should return basic coverage data
            assert result is not None
            assert result.test_name == "test_example"

    def test_integration_with_empty_analysis_results(self):
        """Test integration when analysis results are empty."""
        collector = CoverageCollector()

        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData

        base_coverage = CoverageData(
            test_name="test_example",
            file_path=Path("/test/test.py"),
            line_number=10,
            lines_covered=80,
            lines_total=100,
            branches_covered=40,
            branches_total=50,
            coverage_percentage=80.0,
            covered_lines={1, 2, 3},
            missing_lines={4, 5},
            coverage_signature="base_signature",
        )

        # Test with None analysis results
        enhanced_coverage = collector._enhance_coverage_with_analysis(
            base_coverage, None, None, [Path("file1.py")]
        )

        # Should still work
        assert enhanced_coverage.test_name == "test_example"
        assert enhanced_coverage.coverage_percentage == 80.0
        assert "source_files:1" in enhanced_coverage.coverage_signature


class TestAnalysisIntegrationPerformance:
    """Test performance characteristics of analysis integration."""

    def test_integration_with_large_analysis_results(self):
        """Test integration with large analysis results."""
        collector = CoverageCollector()

        # Create large analysis results
        large_import_results = {
            "import_count": 50,
            "coverage_ratio": 0.8,
            "imported_files": [f"file{i}.py" for i in range(50)],
        }

        large_call_results = {
            "call_count": 100,
            "call_types": {
                "direct_calls": 30,
                "method_calls": 40,
                "nested_calls": 20,
                "assertions": 10,
            },
        }

        large_source_files = [Path(f"file{i}.py") for i in range(100)]

        # Test insights generation
        insights = collector._generate_analysis_insights(
            large_import_results, large_call_results, large_source_files
        )

        # Should handle large data gracefully
        assert "imports:50" in insights
        assert "calls:100" in insights
        assert "source_files:100" in insights

    def test_integration_with_complex_call_types(self):
        """Test integration with complex call type analysis."""
        collector = CoverageCollector()

        complex_call_results = {
            "call_count": 20,
            "call_types": {
                "direct_calls": 5,
                "method_calls": 8,
                "nested_calls": 4,
                "dynamic_calls": 2,
                "assertions": 1,
            },
        }

        # Test insights generation
        insights = collector._generate_analysis_insights(
            None, complex_call_results, [Path("file1.py")]
        )

        # Should include all call types
        assert "calls:20" in insights
        assert "direct_calls:5" in insights
        assert "method_calls:8" in insights
        assert "nested_calls:4" in insights
        assert "dynamic_calls:2" in insights
        assert "assertions:1" in insights


class TestAnalysisIntegrationEdgeCases:
    """Test edge cases in analysis integration."""

    def test_integration_with_malformed_analysis_results(self):
        """Test integration with malformed analysis results."""
        collector = CoverageCollector()

        malformed_results = {
            "import_count": "invalid",  # Should be int
            "coverage_ratio": "invalid",  # Should be float
            "call_types": "invalid",  # Should be dict
        }

        # Test insights generation
        insights = collector._generate_analysis_insights(
            malformed_results, malformed_results, [Path("file1.py")]
        )

        # Should handle gracefully
        assert "source_files:1" in insights

    def test_integration_with_missing_analysis_fields(self):
        """Test integration with missing analysis fields."""
        collector = CoverageCollector()

        incomplete_results = {
            "import_count": 2,
            # Missing coverage_ratio
            "call_count": 3,
            # Missing call_types
        }

        # Test insights generation
        insights = collector._generate_analysis_insights(
            incomplete_results, incomplete_results, [Path("file1.py")]
        )

        # Should handle missing fields gracefully
        assert "imports:2" in insights
        assert "calls:3" in insights
        assert "source_files:1" in insights

    def test_integration_with_empty_source_files(self):
        """Test integration with empty source files list."""
        collector = CoverageCollector()

        import_results = {"import_count": 2}
        call_results = {"call_count": 3}
        source_files = []

        # Test insights generation
        insights = collector._generate_analysis_insights(
            import_results, call_results, source_files
        )

        # Should handle empty source files
        assert "source_files:0" in insights
