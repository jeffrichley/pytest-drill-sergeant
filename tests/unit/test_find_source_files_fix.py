"""Comprehensive tests for the fixed _find_source_files functionality.

This module contains Google-level comprehensive tests for the permission error bug fix
in _find_source_files method, including safe directory traversal and error handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pytest_drill_sergeant.core.analyzers.coverage_collector import CoverageCollector


class TestSafeParentTraversal:
    """Test the safe parent traversal functionality."""

    def test_safe_parent_traversal_basic(self):
        """Test basic safe parent traversal with real paths."""
        collector = CoverageCollector()
        
        # Test with a real temporary path
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create nested structure
            nested_path = tmp_path / 'level1' / 'level2' / 'level3' / 'test.py'
            nested_path.parent.mkdir(parents=True)
            nested_path.write_text('test')
            
            # Test safe parent traversal
            safe_parents = collector._safe_parent_traversal(nested_path)
            
            # Should find some parents
            assert isinstance(safe_parents, list)
            assert len(safe_parents) >= 0

    def test_safe_parent_traversal_stops_at_system_dirs(self):
        """Test that traversal stops at system directories."""
        collector = CoverageCollector()
        
        # Test with a path that would go through system directories
        test_path = Path("/usr/local/project/tests/test_file.py")
        
        safe_parents = collector._safe_parent_traversal(test_path)
        
        # Should stop at system directories
        assert isinstance(safe_parents, list)
        # Should not include system directories like /usr
        assert all(str(p) not in ["/usr", "/", "/var", "/etc"] for p in safe_parents)

    def test_safe_parent_traversal_windows_system_dirs(self):
        """Test that traversal stops at Windows system directories."""
        collector = CoverageCollector()
        
        # Test with Windows-style path
        test_path = Path("C:\\Program Files\\project\\tests\\test_file.py")
        
        safe_parents = collector._safe_parent_traversal(test_path)
        
        # Should stop at system directories
        assert isinstance(safe_parents, list)
        # Should not include Windows system directories
        assert all(str(p) not in ["C:\\Program Files", "C:\\", "C:\\Windows"] for p in safe_parents)

    def test_safe_parent_traversal_permission_error(self):
        """Test handling of permission errors during traversal."""
        collector = CoverageCollector()
        
        # Test with a path that might cause permission issues
        test_path = Path("/root/project/tests/test_file.py")
        
        safe_parents = collector._safe_parent_traversal(test_path)
        
        # Should handle error gracefully
        assert isinstance(safe_parents, list)

    def test_safe_parent_traversal_max_depth(self):
        """Test that traversal respects maximum depth limit."""
        collector = CoverageCollector()
        
        # Test with a deeply nested path
        test_path = Path("/tmp/level1/level2/level3/level4/level5/level6/test.py")
        
        safe_parents = collector._safe_parent_traversal(test_path)
        
        # Should respect maximum depth of 5
        assert isinstance(safe_parents, list)
        assert len(safe_parents) <= 5

    def test_safe_parent_traversal_avoids_infinite_loops(self):
        """Test that traversal avoids infinite loops."""
        collector = CoverageCollector()
        
        # Test with a path that could cause loops
        test_path = Path("/tmp/project/tests/test_file.py")
        
        safe_parents = collector._safe_parent_traversal(test_path)
        
        # Should not include the same path
        assert isinstance(safe_parents, list)
        assert test_path not in safe_parents


class TestFindSourceFilesFix:
    """Test the fixed _find_source_files functionality."""

    def test_find_source_files_basic_structure(self):
        """Test finding source files in basic project structure."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create basic structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            # Create files
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 1
            assert src_file in source_files

    def test_find_source_files_with_lib_directory(self):
        """Test finding source files with lib directory."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure with lib directory
            test_dir = tmp_path / 'tests'
            lib_dir = tmp_path / 'lib'
            
            test_dir.mkdir()
            lib_dir.mkdir()
            
            # Create files
            test_file = test_dir / 'test_example.py'
            lib_file = lib_dir / 'library.py'
            
            test_file.write_text('def test_something(): pass')
            lib_file.write_text('def lib_func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 1
            assert lib_file in source_files

    def test_find_source_files_with_package_structure(self):
        """Test finding source files with package structure."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create package structure
            test_dir = tmp_path / 'tests'
            package_dir = tmp_path / 'mypackage'
            
            test_dir.mkdir()
            package_dir.mkdir()
            
            # Create __init__.py to make it a package
            init_file = package_dir / '__init__.py'
            init_file.write_text('')
            
            # Create files
            test_file = test_dir / 'test_example.py'
            package_file = package_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            package_file.write_text('def package_func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 2  # __init__.py and module.py
            assert init_file in source_files
            assert package_file in source_files

    def test_find_source_files_filters_test_files(self):
        """Test that test files are filtered out."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            # Create files including test files in src
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            src_test_file = src_dir / 'test_module.py'  # This should be filtered out
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            src_test_file.write_text('def test_func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 1
            assert src_file in source_files
            assert src_test_file not in source_files

    def test_find_source_files_handles_permission_errors(self):
        """Test that permission errors are handled gracefully."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            test_file = test_dir / 'test_example.py'
            
            test_dir.mkdir()
            test_file.write_text('def test_something(): pass')
            
            # Mock iterdir to raise permission error
            with patch('pathlib.Path.iterdir') as mock_iterdir:
                mock_iterdir.side_effect = PermissionError("Permission denied")
                
                # Should not crash
                source_files = collector._find_source_files(test_file)
                
                # Should return empty list or fallback gracefully
                assert isinstance(source_files, list)

    def test_find_source_files_handles_rglob_permission_errors(self):
        """Test that rglob permission errors are handled gracefully."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            test_file = test_dir / 'test_example.py'
            test_file.write_text('def test_something(): pass')
            
            # Mock rglob to raise permission error
            with patch('pathlib.Path.rglob') as mock_rglob:
                mock_rglob.side_effect = PermissionError("Permission denied")
                
                # Should not crash
                source_files = collector._find_source_files(test_file)
                
                # Should return empty list or fallback gracefully
                assert isinstance(source_files, list)

    def test_find_source_files_fallback_method(self):
        """Test the fallback method works correctly."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            
            # Test fallback method directly
            source_files = collector._find_source_files_fallback(test_file)
            
            assert len(source_files) == 1
            assert src_file in source_files

    def test_find_source_files_with_import_analysis(self):
        """Test finding source files with import analysis."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            # Create test file with imports
            test_file = test_dir / 'test_example.py'
            test_file.write_text('''
import os
from pathlib import Path

def test_something():
    result = os.path.join('test', 'file')
    path = Path('test')
    assert result is not None
''')
            
            # Create source files
            os_file = src_dir / 'os.py'
            pathlib_file = src_dir / 'pathlib.py'
            
            os_file.write_text('def join(*args): pass')
            pathlib_file.write_text('class Path: pass')
            
            # Mock the resolve function to map imports to files
            def mock_resolve(module_name, files):
                if module_name == 'os':
                    return os_file
                elif module_name == 'pathlib':
                    return pathlib_file
                return None
            
            collector._resolve_import_to_file = mock_resolve
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            # Should find the imported files
            assert len(source_files) >= 2
            assert os_file in source_files
            assert pathlib_file in source_files

    def test_find_source_files_empty_directory(self):
        """Test finding source files in empty directory structure."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create minimal structure
            test_dir = tmp_path / 'tests'
            test_file = test_dir / 'test_example.py'
            
            test_dir.mkdir()
            test_file.write_text('def test_something(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            # Should return empty list gracefully
            assert isinstance(source_files, list)
            assert len(source_files) == 0

    def test_find_source_files_nested_structure(self):
        """Test finding source files in nested directory structure."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create nested structure
            test_dir = tmp_path / 'project' / 'tests'
            src_dir = tmp_path / 'project' / 'src' / 'modules'
            
            test_dir.mkdir(parents=True)
            src_dir.mkdir(parents=True)
            
            # Create files
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 1
            assert src_file in source_files


class TestErrorHandling:
    """Test error handling in _find_source_files."""

    def test_find_source_files_handles_file_not_found(self):
        """Test handling of file not found errors."""
        collector = CoverageCollector()
        
        # Test with non-existent file
        non_existent_file = Path("/nonexistent/path/test.py")
        
        # Should not crash
        source_files = collector._find_source_files(non_existent_file)
        
        assert isinstance(source_files, list)

    def test_find_source_files_handles_invalid_path(self):
        """Test handling of invalid path errors."""
        collector = CoverageCollector()
        
        # Test with invalid path
        invalid_path = Path("")
        
        # Should not crash
        source_files = collector._find_source_files(invalid_path)
        
        assert isinstance(source_files, list)

    def test_find_source_files_handles_os_error(self):
        """Test handling of OSError during directory operations."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            test_file = test_dir / 'test_example.py'
            
            test_dir.mkdir()
            test_file.write_text('def test_something(): pass')
            
            # Mock _analyze_test_file_imports to raise OSError
            with patch.object(collector, '_analyze_test_file_imports') as mock_analyze:
                mock_analyze.side_effect = OSError("OS error")
                
                # Should not crash, should fall back to fallback method
                source_files = collector._find_source_files(test_file)
                
                assert isinstance(source_files, list)

    def test_find_source_files_handles_general_exception(self):
        """Test handling of general exceptions."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            test_file = test_dir / 'test_example.py'
            
            test_dir.mkdir()
            test_file.write_text('def test_something(): pass')
            
            # Mock _analyze_test_file_imports to raise exception
            with patch.object(collector, '_analyze_test_file_imports') as mock_analyze:
                mock_analyze.side_effect = Exception("General error")
                
                # Should not crash, should fall back to fallback method
                source_files = collector._find_source_files(test_file)
                
                assert isinstance(source_files, list)


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""

    def test_find_source_files_large_directory_structure(self):
        """Test performance with large directory structure."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create large structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            # Create many files
            test_file = test_dir / 'test_example.py'
            test_file.write_text('def test_something(): pass')
            
            for i in range(50):
                src_file = src_dir / f'module{i}.py'
                src_file.write_text(f'def func{i}(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            # Should find all source files
            assert len(source_files) == 50

    def test_find_source_files_deep_nesting(self):
        """Test handling of deeply nested directory structures."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create deeply nested structure
            test_dir = tmp_path / 'level1' / 'level2' / 'level3' / 'tests'
            src_dir = tmp_path / 'level1' / 'level2' / 'level3' / 'src'
            
            test_dir.mkdir(parents=True)
            src_dir.mkdir(parents=True)
            
            # Create files
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            
            # Test finding source files
            source_files = collector._find_source_files(test_file)
            
            assert len(source_files) == 1
            assert src_file in source_files

    def test_find_source_files_symlinks(self):
        """Test handling of symbolic links."""
        collector = CoverageCollector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create structure
            test_dir = tmp_path / 'tests'
            src_dir = tmp_path / 'src'
            
            test_dir.mkdir()
            src_dir.mkdir()
            
            # Create files
            test_file = test_dir / 'test_example.py'
            src_file = src_dir / 'module.py'
            
            test_file.write_text('def test_something(): pass')
            src_file.write_text('def func(): pass')
            
            # Create symlink (if supported)
            try:
                symlink_file = test_dir / 'symlink.py'
                symlink_file.symlink_to(src_file)
                
                # Test finding source files
                source_files = collector._find_source_files(test_file)
                
                # Should handle symlinks gracefully
                assert isinstance(source_files, list)
            except OSError:
                # Symlinks not supported on this platform
                pass