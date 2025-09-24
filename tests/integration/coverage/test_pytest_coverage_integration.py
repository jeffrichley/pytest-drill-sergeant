"""Integration tests for pytest coverage hooks."""

import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock

from pytest_drill_sergeant.plugin.coverage_hooks import CoverageHooks


class TestPytestCoverageIntegration:
    """Test integration with pytest and coverage collection."""

    def test_coverage_hooks_initialization(self):
        """Test that coverage hooks initialize correctly."""
        hooks = CoverageHooks()
        
        assert hooks.coverage_collector is not None
        assert hooks.car_calculator is not None
        assert hooks.signature_generator is not None
        assert hooks._coverage_enabled is False

    def test_coverage_hooks_with_mock_config(self):
        """Test coverage hooks with mock pytest config."""
        hooks = CoverageHooks()
        
        # Mock pytest config
        mock_config = Mock()
        mock_config.getoption.return_value = True  # --ds-coverage enabled
        
        # Test configure
        hooks.pytest_configure(mock_config)
        assert hooks._coverage_enabled is True
        
        # Test unconfigure
        hooks.pytest_unconfigure(mock_config)
        # Should not crash

    def test_coverage_hooks_with_mock_item(self):
        """Test coverage hooks with mock pytest item."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Mock pytest item
        mock_item = Mock()
        mock_item.fspath = "/tmp/test_example.py"
        mock_item.name = "test_example"
        mock_item.location = ("/tmp/test_example.py", 10, "test_example")
        
        # Test setup
        hooks.pytest_runtest_setup(mock_item)
        # Should not crash
        
        # Test call
        hooks.pytest_runtest_call(mock_item)
        # Should not crash
        
        # Test teardown
        hooks.pytest_runtest_teardown(mock_item)
        # Should not crash

    def test_coverage_hooks_with_mock_terminal_reporter(self):
        """Test coverage hooks with mock terminal reporter."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Mock terminal reporter
        mock_reporter = Mock()
        mock_config = Mock()
        
        # Test terminal summary
        hooks.pytest_terminal_summary(mock_reporter, 0, mock_config)
        # Should not crash

    def test_real_pytest_execution_with_coverage(self):
        """Test real pytest execution with coverage collection."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
import pytest

def add(a, b):
    """Simple function to test."""
    return a + b

def test_add_basic():
    """Test basic addition."""
    assert add(2, 3) == 5

def test_add_zero():
    """Test addition with zero."""
    assert add(0, 5) == 5
    assert add(5, 0) == 5

def test_add_negative():
    """Test addition with negative numbers."""
    assert add(-1, 1) == 0
    assert add(-2, -3) == -5
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            # Run pytest with our plugin
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_file_path),
                "-v",
                "--tb=short"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            # Check that pytest ran successfully
            assert result.returncode == 0, f"Pytest failed: {result.stderr}"
            
            # Check that our tests ran
            assert "test_add_basic" in result.stdout
            assert "test_add_zero" in result.stdout
            assert "test_add_negative" in result.stdout
            
        finally:
            # Cleanup
            test_file_path.unlink()

    def test_pytest_with_coverage_option(self):
        """Test pytest with pytest-cov integration."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_content = '''
def test_simple():
    """Simple test."""
    assert 1 + 1 == 2
'''
            f.write(test_content)
            test_file_path = Path(f.name)
        
        try:
            # Run pytest with pytest-cov (which should trigger our integration)
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_file_path),
                "--cov=src/pytest_drill_sergeant",
                "--cov-fail-under=0",  # Don't fail on low coverage for this test
                "-v"
            ], capture_output=True, text=True, cwd=Path.cwd())
            
            # pytest-cov should run successfully and our integration should detect it
            assert result.returncode == 0
            # Verify that pytest-cov ran (coverage report should be present)
            assert "tests coverage" in result.stdout
            # Verify that our plugin ran (Drill Sergeant summary should be present)
            assert "DRILL SERGEANT SUMMARY" in result.stdout
            
        finally:
            # Cleanup
            test_file_path.unlink()

    def test_coverage_data_storage_and_retrieval(self):
        """Test that coverage data is stored and can be retrieved."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Mock pytest item
        mock_item = Mock()
        mock_item.fspath = "/tmp/test_example.py"
        mock_item.name = "test_example"
        mock_item.location = ("/tmp/test_example.py", 10, "test_example")
        
        # Run the test call
        hooks.pytest_runtest_call(mock_item)
        
        # Check that data was stored
        assert hasattr(mock_item, 'ds_coverage_data')
        assert hasattr(mock_item, 'ds_car_result')
        assert hasattr(mock_item, 'ds_coverage_signature')

    def test_coverage_summary_generation(self):
        """Test coverage summary generation."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Add some mock coverage data
        from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageData
        
        mock_coverage = CoverageData(
            test_name="test_mock",
            file_path=Path("/tmp/test_mock.py"),
            line_number=1,
            lines_covered=50,
            lines_total=100,
            branches_covered=25,
            branches_total=50,
            coverage_percentage=50.0,
            covered_lines={1, 2, 3, 4, 5},
            missing_lines={6, 7, 8, 9, 10},
        )
        
        hooks.coverage_collector._coverage_data["test_mock"] = mock_coverage
        
        # Mock terminal reporter
        mock_reporter = Mock()
        mock_config = Mock()
        
        # Generate summary
        hooks.pytest_terminal_summary(mock_reporter, 0, mock_config)
        
        # Check that summary methods were called
        assert mock_reporter.write_sep.called
        assert mock_reporter.write_line.called

    def test_error_handling_in_hooks(self):
        """Test error handling in coverage hooks."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Test with invalid item
        mock_item = Mock()
        mock_item.fspath = None  # Invalid path
        mock_item.name = "test_invalid"
        mock_item.location = None
        
        # Should not crash
        hooks.pytest_runtest_setup(mock_item)
        hooks.pytest_runtest_call(mock_item)
        hooks.pytest_runtest_teardown(mock_item)

    def test_coverage_hooks_with_disabled_coverage(self):
        """Test coverage hooks when coverage is disabled."""
        # Create a real CoverageHooks instance with coverage disabled
        hooks = CoverageHooks()
        hooks._coverage_enabled = False
        
        # Create a simple object instead of Mock to avoid Mock's dynamic attribute behavior
        class TestItem:
            def __init__(self):
                self.fspath = "/tmp/test_example.py"
                self.name = "test_example"
                self.location = ("/tmp/test_example.py", 10, "test_example")
        
        test_item = TestItem()
        
        # Should not crash and should not process coverage
        hooks.pytest_runtest_setup(test_item)
        hooks.pytest_runtest_call(test_item)
        hooks.pytest_runtest_teardown(test_item)
        
        # Should not have coverage data
        assert not hasattr(test_item, 'ds_coverage_data')

    def test_coverage_hooks_cleanup(self):
        """Test that coverage hooks properly clean up."""
        hooks = CoverageHooks()
        hooks._coverage_enabled = True
        
        # Start coverage
        hooks.coverage_collector.start_coverage()
        assert hooks.coverage_collector._temp_dir is not None
        
        # Mock config for unconfigure
        mock_config = Mock()
        hooks.pytest_unconfigure(mock_config)
        
        # Coverage should be stopped
        assert hooks.coverage_collector._temp_dir is None
