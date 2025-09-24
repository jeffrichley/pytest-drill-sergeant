"""Comprehensive tests for coverage analysis functionality.

This module contains Google-level comprehensive tests for the coverage analysis
methods in CoverageCollector, including import analysis, call analysis, and
result storage functionality.
"""

import ast
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageCollector


class TestCoverageAnalysisStorage:
    """Test coverage analysis result storage functionality."""

    def test_initialization_storage_variables(self):
        """Test that storage variables are properly initialized."""
        collector = CoverageCollector()
        
        # Check that storage variables exist and are empty
        assert hasattr(collector, '_imported_files')
        assert hasattr(collector, '_called_functions')
        assert hasattr(collector, '_analysis_results')
        
        assert isinstance(collector._imported_files, set)
        assert isinstance(collector._called_functions, set)
        assert isinstance(collector._analysis_results, dict)
        
        assert len(collector._imported_files) == 0
        assert len(collector._called_functions) == 0
        assert len(collector._analysis_results) == 0

    def test_get_imported_files_returns_copy(self):
        """Test that get_imported_files returns a copy, not reference."""
        collector = CoverageCollector()
        collector._imported_files.add(Path("/test/file.py"))
        
        result = collector.get_imported_files()
        
        # Should be equal but not the same object
        assert result == collector._imported_files
        assert result is not collector._imported_files
        
        # Modifying the returned set shouldn't affect the original
        result.add(Path("/test/other.py"))
        assert len(collector._imported_files) == 1
        assert len(result) == 2

    def test_get_called_functions_returns_copy(self):
        """Test that get_called_functions returns a copy, not reference."""
        collector = CoverageCollector()
        collector._called_functions.add("test_function")
        
        result = collector.get_called_functions()
        
        # Should be equal but not the same object
        assert result == collector._called_functions
        assert result is not collector._called_functions
        
        # Modifying the returned set shouldn't affect the original
        result.add("other_function")
        assert len(collector._called_functions) == 1
        assert len(result) == 2

    def test_get_analysis_results_existing(self):
        """Test getting analysis results for existing test."""
        collector = CoverageCollector()
        collector._analysis_results["test_function_imports"] = {"import_count": 5}
        
        result = collector.get_analysis_results("test_function_imports")
        
        assert result is not None
        assert result["import_count"] == 5

    def test_get_analysis_results_nonexistent(self):
        """Test getting analysis results for non-existent test."""
        collector = CoverageCollector()
        
        result = collector.get_analysis_results("nonexistent_test")
        
        assert result is None

    def test_get_all_analysis_results_returns_copy(self):
        """Test that get_all_analysis_results returns a copy."""
        collector = CoverageCollector()
        collector._analysis_results["test1"] = {"data": "value1"}
        collector._analysis_results["test2"] = {"data": "value2"}
        
        result = collector.get_all_analysis_results()
        
        # Should be equal but not the same object
        assert result == collector._analysis_results
        assert result is not collector._analysis_results
        
        # Modifying the returned dict shouldn't affect the original
        result["test3"] = {"data": "value3"}
        assert len(collector._analysis_results) == 2
        assert len(result) == 3

    def test_clear_analysis_results(self):
        """Test clearing all analysis results."""
        collector = CoverageCollector()
        
        # Add some data
        collector._imported_files.add(Path("/test/file.py"))
        collector._called_functions.add("test_function")
        collector._analysis_results["test"] = {"data": "value"}
        
        # Clear results
        collector.clear_analysis_results()
        
        # Verify everything is cleared
        assert len(collector._imported_files) == 0
        assert len(collector._called_functions) == 0
        assert len(collector._analysis_results) == 0


class TestImportAnalysis:
    """Test import analysis functionality."""

    def test_analyze_test_imports_basic_import(self):
        """Test analysis of basic import statements."""
        collector = CoverageCollector()
        
        # Create test function with basic import
        test_code = '''
def test_example():
    import os
    import sys
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock source files
        source_files = [Path("/test/os.py"), Path("/test/sys.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py") if name in ["os", "sys"] else None
            
            collector._analyze_test_imports(test_func, source_files)
        
        # Check that results are stored
        assert len(collector._imported_files) == 2
        assert Path("/test/os.py") in collector._imported_files
        assert Path("/test/sys.py") in collector._imported_files
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_imports")
        assert results is not None
        assert results["import_count"] == 2
        assert results["source_files_available"] == 2
        assert results["coverage_ratio"] == 1.0
        assert len(results["imported_files"]) == 2

    def test_analyze_test_imports_from_import(self):
        """Test analysis of from...import statements."""
        collector = CoverageCollector()
        
        # Create test function with from...import
        test_code = '''
def test_example():
    from pathlib import Path
    from collections import defaultdict
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock source files
        source_files = [Path("/test/pathlib.py"), Path("/test/collections.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py") if name in ["pathlib", "collections"] else None
            
            collector._analyze_test_imports(test_func, source_files)
        
        # Check that results are stored
        assert len(collector._imported_files) == 2
        assert Path("/test/pathlib.py") in collector._imported_files
        assert Path("/test/collections.py") in collector._imported_files

    def test_analyze_test_imports_dynamic_import(self):
        """Test analysis of dynamic import statements."""
        collector = CoverageCollector()
        
        # Create test function with dynamic import
        test_code = '''
def test_example():
    module = __import__('json')
    data = __import__('pickle')
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock source files
        source_files = [Path("/test/json.py"), Path("/test/pickle.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py") if name in ["json", "pickle"] else None
            
            collector._analyze_test_imports(test_func, source_files)
        
        # Check that results are stored
        assert len(collector._imported_files) == 2
        assert Path("/test/json.py") in collector._imported_files
        assert Path("/test/pickle.py") in collector._imported_files

    def test_analyze_test_imports_no_matching_files(self):
        """Test analysis when no source files match imports."""
        collector = CoverageCollector()
        
        # Create test function with imports
        test_code = '''
def test_example():
    import nonexistent_module
    from another_module import something
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock source files that don't match
        source_files = [Path("/test/other.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.return_value = None
            
            collector._analyze_test_imports(test_func, source_files)
        
        # Check that no files are stored
        assert len(collector._imported_files) == 0
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_imports")
        assert results is not None
        assert results["import_count"] == 0
        assert results["coverage_ratio"] == 0.0

    def test_analyze_test_imports_empty_source_files(self):
        """Test analysis with empty source files list."""
        collector = CoverageCollector()
        
        # Create test function with imports
        test_code = '''
def test_example():
    import os
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_imports(test_func, [])
        
        # Check that no files are stored
        assert len(collector._imported_files) == 0
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_imports")
        assert results is not None
        assert results["import_count"] == 0
        assert results["source_files_available"] == 0
        assert results["coverage_ratio"] == 0.0

    def test_analyze_test_imports_error_handling(self):
        """Test error handling in import analysis."""
        collector = CoverageCollector()
        
        # Create test function
        test_code = '''
def test_example():
    import os
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock _resolve_import_to_file to raise an exception
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = Exception("Test error")
            
            collector._analyze_test_imports(test_func, [])
        
        # Check that error is stored
        results = collector.get_analysis_results("test_example_imports")
        assert results is not None
        assert "error" in results
        assert results["error"] == "Test error"
        assert results["import_count"] == 0


class TestCallAnalysis:
    """Test function call analysis functionality."""

    def test_analyze_test_calls_direct_calls(self):
        """Test analysis of direct function calls."""
        collector = CoverageCollector()
        
        # Create test function with direct calls
        test_code = '''
def test_example():
    result = func1()
    data = func2()
    assert result is not None
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_calls(test_func, [])
        
        # Check that results are stored
        assert len(collector._called_functions) == 3
        assert "func1" in collector._called_functions
        assert "func2" in collector._called_functions
        assert "assert" in collector._called_functions
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_calls")
        assert results is not None
        assert results["call_count"] == 3
        assert results["unique_calls"] == 3
        assert "func1" in results["called_functions"]
        assert "func2" in results["called_functions"]
        assert "assert" in results["called_functions"]

    def test_analyze_test_calls_method_calls(self):
        """Test analysis of method calls."""
        collector = CoverageCollector()
        
        # Create test function with method calls
        test_code = '''
def test_example():
    obj = SomeClass()
    result = obj.method1()
    data = obj.method2()
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_calls(test_func, [])
        
        # Check that results are stored
        assert len(collector._called_functions) == 3
        assert "SomeClass" in collector._called_functions
        assert "obj.method1" in collector._called_functions
        assert "obj.method2" in collector._called_functions

    def test_analyze_test_calls_nested_calls(self):
        """Test analysis of nested method calls."""
        collector = CoverageCollector()
        
        # Create test function with nested calls
        test_code = '''
def test_example():
    result = obj.attr.method()
    data = obj.attr.other.method()
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_calls(test_func, [])
        
        # Check that results are stored
        assert len(collector._called_functions) == 2
        assert "obj.attr.method" in collector._called_functions
        assert "obj.attr.other.method" in collector._called_functions

    def test_analyze_test_calls_complex_patterns(self):
        """Test analysis of complex call patterns."""
        collector = CoverageCollector()
        
        # Create test function with complex calls
        test_code = '''
def test_example():
    result = func()()
    data = obj[key]()
    obj.method()
    assert result is not None
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_calls(test_func, [])
        
        # Check that results are stored
        assert len(collector._called_functions) == 5  # func, callable_result, subscript_call, obj.method, assert
        assert "func" in collector._called_functions
        assert "callable_result" in collector._called_functions
        assert "subscript_call" in collector._called_functions
        assert "obj.method" in collector._called_functions
        assert "assert" in collector._called_functions

    def test_categorize_calls(self):
        """Test call categorization functionality."""
        collector = CoverageCollector()
        
        called_functions = {
            "func1",           # direct call
            "obj.method",      # method call
            "obj.attr.method", # nested call
            "assert_equal",    # assertion
            "subscript_call",  # dynamic call
            "callable_result"  # dynamic call
        }
        
        categories = collector._categorize_calls(called_functions)
        
        assert categories["direct_calls"] == 1
        assert categories["method_calls"] == 1
        assert categories["nested_calls"] == 1
        assert categories["assertions"] == 1
        assert categories["dynamic_calls"] == 2

    def test_analyze_test_calls_error_handling(self):
        """Test error handling in call analysis."""
        collector = CoverageCollector()
        
        # Create test function
        test_code = '''
def test_example():
    func()
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock ast.walk to raise an exception
        with patch('ast.walk') as mock_walk:
            mock_walk.side_effect = Exception("Test error")
            
            collector._analyze_test_calls(test_func, [])
        
        # Check that error is stored
        results = collector.get_analysis_results("test_example_calls")
        assert results is not None
        assert "error" in results
        assert results["error"] == "Test error"
        assert results["call_count"] == 0


class TestIntegrationAnalysis:
    """Test integration between import and call analysis."""

    def test_multiple_test_functions_analysis(self):
        """Test analysis of multiple test functions."""
        collector = CoverageCollector()
        
        # Create multiple test functions
        test_code = '''
def test_function1():
    import os
    result = os.path.join('test', 'file')

def test_function2():
    from pathlib import Path
    path = Path('test')
    assert path.exists()
'''
        tree = ast.parse(test_code)
        
        source_files = [Path("/test/os.py"), Path("/test/pathlib.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py") if name in ["os", "pathlib"] else None
            
            # Analyze both functions
            collector._analyze_test_imports(tree.body[0], source_files)
            collector._analyze_test_calls(tree.body[0], source_files)
            collector._analyze_test_imports(tree.body[1], source_files)
            collector._analyze_test_calls(tree.body[1], source_files)
        
        # Check that results from both functions are stored
        assert len(collector._imported_files) == 2
        assert Path("/test/os.py") in collector._imported_files
        assert Path("/test/pathlib.py") in collector._imported_files
        
        assert len(collector._called_functions) >= 3  # At least os.path.join, Path, assert
        
        # Check detailed results for both functions
        results1_imports = collector.get_analysis_results("test_function1_imports")
        results1_calls = collector.get_analysis_results("test_function1_calls")
        results2_imports = collector.get_analysis_results("test_function2_imports")
        results2_calls = collector.get_analysis_results("test_function2_calls")
        
        assert results1_imports is not None
        assert results1_calls is not None
        assert results2_imports is not None
        assert results2_calls is not None
        
        assert results1_imports["import_count"] == 1
        assert results2_imports["import_count"] == 1

    def test_analysis_results_persistence(self):
        """Test that analysis results persist across multiple calls."""
        collector = CoverageCollector()
        
        # Create test function
        test_code = '''
def test_example():
    import os
    result = os.path.join('test', 'file')
    assert result is not None
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        source_files = [Path("/test/os.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.return_value = Path("/test/os.py")
            
            # First analysis
            collector._analyze_test_imports(test_func, source_files)
            collector._analyze_test_calls(test_func, source_files)
            
            # Check results
            assert len(collector._imported_files) == 1
            assert len(collector._called_functions) >= 2
            
            # Second analysis (should accumulate)
            collector._analyze_test_imports(test_func, source_files)
            collector._analyze_test_calls(test_func, source_files)
            
            # Results should still be there (sets don't duplicate)
            assert len(collector._imported_files) == 1
            assert len(collector._called_functions) >= 2

    def test_clear_and_reanalyze(self):
        """Test clearing results and re-analyzing."""
        collector = CoverageCollector()
        
        # Create test function
        test_code = '''
def test_example():
    import os
    result = os.path.join('test', 'file')
    assert result is not None
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        source_files = [Path("/test/os.py")]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.return_value = Path("/test/os.py")
            
            # First analysis
            collector._analyze_test_imports(test_func, source_files)
            collector._analyze_test_calls(test_func, source_files)
            
            # Check results exist
            assert len(collector._imported_files) == 1
            assert len(collector._called_functions) >= 2
            
            # Clear results
            collector.clear_analysis_results()
            
            # Check results are cleared
            assert len(collector._imported_files) == 0
            assert len(collector._called_functions) == 0
            assert len(collector._analysis_results) == 0
            
            # Re-analyze
            collector._analyze_test_imports(test_func, source_files)
            collector._analyze_test_calls(test_func, source_files)
            
            # Check results are back
            assert len(collector._imported_files) == 1
            assert len(collector._called_functions) >= 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_test_function(self):
        """Test analysis of empty test function."""
        collector = CoverageCollector()
        
        # Create empty test function
        test_code = '''
def test_example():
    pass
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_imports(test_func, [])
        collector._analyze_test_calls(test_func, [])
        
        # Check that no results are stored
        assert len(collector._imported_files) == 0
        assert len(collector._called_functions) == 0
        
        # Check detailed results
        import_results = collector.get_analysis_results("test_example_imports")
        call_results = collector.get_analysis_results("test_example_calls")
        
        assert import_results is not None
        assert call_results is not None
        assert import_results["import_count"] == 0
        assert call_results["call_count"] == 0

    def test_test_function_with_comments_only(self):
        """Test analysis of test function with only comments."""
        collector = CoverageCollector()
        
        # Create test function with only comments
        test_code = '''
def test_example():
    # This is a comment
    # Another comment
    pass
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_imports(test_func, [])
        collector._analyze_test_calls(test_func, [])
        
        # Check that no results are stored
        assert len(collector._imported_files) == 0
        assert len(collector._called_functions) == 0

    def test_test_function_with_strings_only(self):
        """Test analysis of test function with only string literals."""
        collector = CoverageCollector()
        
        # Create test function with only strings
        test_code = '''
def test_example():
    "This is a string"
    'Another string'
    """Docstring"""
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_imports(test_func, [])
        collector._analyze_test_calls(test_func, [])
        
        # Check that no results are stored
        assert len(collector._imported_files) == 0
        assert len(collector._called_functions) == 0

    def test_malformed_ast_node(self):
        """Test handling of malformed AST nodes."""
        collector = CoverageCollector()
        
        # Create test function
        test_code = '''
def test_example():
    import os
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        # Mock ast.walk to return malformed nodes
        with patch('ast.walk') as mock_walk:
            mock_walk.return_value = [None, "invalid_node", test_func]
            
            collector._analyze_test_imports(test_func, [])
            collector._analyze_test_calls(test_func, [])
        
        # Should handle gracefully without crashing
        assert isinstance(collector._imported_files, set)
        assert isinstance(collector._called_functions, set)
        assert isinstance(collector._analysis_results, dict)


class TestPerformanceAndMemory:
    """Test performance and memory usage characteristics."""

    def test_large_number_of_imports(self):
        """Test analysis with large number of imports."""
        collector = CoverageCollector()
        
        # Create test function with many imports - use proper indentation
        imports = [f"    import module{i}" for i in range(100)]
        test_code = f'''def test_example():
{chr(10).join(imports)}
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        source_files = [Path(f"/test/module{i}.py") for i in range(100)]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py")
            
            collector._analyze_test_imports(test_func, source_files)
        
        # Check that all imports are stored
        assert len(collector._imported_files) == 100
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_imports")
        assert results is not None
        assert results["import_count"] == 100
        assert results["coverage_ratio"] == 1.0

    def test_large_number_of_calls(self):
        """Test analysis with large number of function calls."""
        collector = CoverageCollector()
        
        # Create test function with many calls - use proper indentation
        calls = [f"    func{i}()" for i in range(100)]
        test_code = f'''def test_example():
{chr(10).join(calls)}
'''
        tree = ast.parse(test_code)
        test_func = tree.body[0]
        
        collector._analyze_test_calls(test_func, [])
        
        # Check that all calls are stored
        assert len(collector._called_functions) == 100
        
        # Check detailed results
        results = collector.get_analysis_results("test_example_calls")
        assert results is not None
        assert results["call_count"] == 100
        assert results["unique_calls"] == 100

    def test_memory_usage_with_multiple_analyses(self):
        """Test memory usage with multiple analyses."""
        collector = CoverageCollector()
        
        # Create multiple test functions
        test_functions = []
        for i in range(50):
            test_code = f'''
def test_function{i}():
    import module{i}
    result = func{i}()
'''
            tree = ast.parse(test_code)
            test_functions.append(tree.body[0])
        
        source_files = [Path(f"/test/module{i}.py") for i in range(50)]
        
        with patch.object(collector, '_resolve_import_to_file') as mock_resolve:
            mock_resolve.side_effect = lambda name, files: Path(f"/test/{name}.py")
            
            # Analyze all functions
            for i, test_func in enumerate(test_functions):
                collector._analyze_test_imports(test_func, source_files)
                collector._analyze_test_calls(test_func, source_files)
        
        # Check that results are stored efficiently
        assert len(collector._imported_files) == 50
        assert len(collector._called_functions) == 50
        assert len(collector._analysis_results) == 100  # 50 imports + 50 calls
        
        # Check that we can retrieve all results
        all_results = collector.get_all_analysis_results()
        assert len(all_results) == 100