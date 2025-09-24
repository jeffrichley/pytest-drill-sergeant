"""Demo script to test the LSP server functionality.

This script creates a test file with violations and demonstrates
how the LSP server would analyze it.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from pytest_drill_sergeant.lsp import DrillSergeantLanguageServer


def create_test_file_with_violations() -> Path:
    """Create a test file with various violations."""
    test_code = '''
"""Test file with drill sergeant violations."""

import pytest
from myapp._internal import secret_function  # Private import violation
from _private_module import something        # Private import violation

def test_something():
    """Test function with violations."""
    obj = SomeClass()
    
    # Private attribute access
    obj._private_attr = "value"
    result = obj._internal_data
    
    # Private method call
    obj._private_method()
    
    # Mock over-specification (if we had mocks)
    # mock_obj.assert_called_once()
    # mock_obj.assert_called_with("arg1", "arg2")
    # mock_obj.assert_has_calls([call("arg1"), call("arg2")])
    
    # Structural equality violation
    assert obj.__dict__ == expected_dict
    assert vars(obj) == expected_vars
    
    # Missing AAA comments
    assert result == "expected"


def test_another_function():
    """Another test with violations."""
    from other._internal import more_secrets  # Another private import
    
    data = SomeData()
    data._private_field = "test"
    data._private_method()
    
    assert data.__dict__ == {"_private_field": "test"}
'''
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix="_test.py", delete=False) as f:
        f.write(test_code)
        f.flush()
        return Path(f.name)


def main():
    """Main demo function."""
    print("🔍 Drill Sergeant LSP Server Demo")
    print("=" * 50)
    
    # Create test file
    test_file = create_test_file_with_violations()
    print(f"📁 Created test file: {test_file}")
    
    try:
        # Create LSP server
        print("\n🚀 Initializing LSP server...")
        server = DrillSergeantLanguageServer()
        
        # Create mock document
        from pygls.workspace import Document
        document = Document("file://" + str(test_file), "python")
        
        # Analyze the document
        print("\n🔍 Analyzing test file...")
        diagnostics = server.analyze_document(document)
        
        print(f"\n📊 Found {len(diagnostics)} diagnostics:")
        print("-" * 30)
        
        for i, diag in enumerate(diagnostics, 1):
            print(f"{i}. {diag.code}: {diag.message}")
            print(f"   Severity: {diag.severity}")
            print(f"   Line: {diag.range.start.line + 1}")
            print(f"   Source: {diag.source}")
            print()
        
        print("✅ LSP server analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        test_file.unlink()
        print(f"🧹 Cleaned up test file: {test_file}")


if __name__ == "__main__":
    main()