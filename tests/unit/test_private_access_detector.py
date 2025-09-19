"""Tests for the Private Access Detector."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.analyzers.private_access_detector import (
    PrivateAccessDetector,
)
from pytest_drill_sergeant.core.models import Severity


class TestPrivateAccessDetector:
    """Test the Private Access Detector functionality."""

    def test_init(self) -> None:
        """Test detector initialization."""
        detector = PrivateAccessDetector()
        # Should initialize without any parameters and use centralized config
        assert detector is not None
        assert detector.logger is not None

    def test_analyze_file_private_imports(self) -> None:
        """Test detection of private imports."""
        detector = PrivateAccessDetector()

        test_code = """
import pytest
from myapp._internal import secret_function
from _private_module import something
from myapp.public import normal_function
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find 2 private imports
            assert len(findings) == 2

            # Check first finding (myapp._internal)
            finding1 = findings[0]
            assert finding1.code == "DS301"
            assert finding1.name == "private_access"
            assert finding1.severity == Severity.WARNING
            assert "Importing private module: myapp._internal" in finding1.message
            assert finding1.metadata["violation_type"] == "private_import"
            assert finding1.metadata["module_name"] == "myapp._internal"

            # Check second finding (_private_module)
            finding2 = findings[1]
            assert finding2.code == "DS301"
            assert finding2.name == "private_access"
            assert finding2.severity == Severity.WARNING
            assert "Importing private module: _private_module" in finding2.message
            assert finding2.metadata["violation_type"] == "private_import"
            assert finding2.metadata["module_name"] == "_private_module"

    def test_analyze_file_private_attributes(self) -> None:
        """Test detection of private attribute access."""
        detector = PrivateAccessDetector()

        test_code = """
def test_something():
    obj = SomeClass()
    obj._private_attr = "value"
    result = obj._internal_data
    normal_attr = obj.public_attr
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find 2 private attribute accesses
            assert len(findings) == 2

            # Check findings
            for finding in findings:
                assert finding.code == "DS301"
                assert finding.name == "private_access"
                assert finding.severity == Severity.WARNING
                assert finding.metadata["violation_type"] == "private_attribute"
                assert finding.metadata["attribute_name"].startswith("_")

    def test_analyze_file_private_methods(self) -> None:
        """Test detection of private method calls."""
        detector = PrivateAccessDetector()

        test_code = """
def test_something():
    obj = SomeClass()
    obj._private_method()
    result = obj._internal_function()
    obj.public_method()
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find 2 private method calls
            assert len(findings) == 2

            # Check findings
            for finding in findings:
                assert finding.code == "DS301"
                assert finding.name == "private_access"
                assert finding.severity == Severity.WARNING
                assert finding.metadata["violation_type"] == "private_method"
                assert finding.metadata["method_name"].startswith("_")

    def test_analyze_file_sut_package_private_imports(self) -> None:
        """Test detection of private imports from SUT package."""
        detector = PrivateAccessDetector()

        test_code = """
from myapp._internal import secret_function
from myapp.public import normal_function
from other._internal import something
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find 2 private imports (myapp._internal and other._internal)
            assert len(findings) == 2

            # Check that myapp._internal is detected
            myapp_finding = next(f for f in findings if "myapp._internal" in f.message)
            assert myapp_finding.metadata["module_name"] == "myapp._internal"

    def test_analyze_file_no_violations(self) -> None:
        """Test analysis of file with no private access violations."""
        detector = PrivateAccessDetector()

        test_code = """
import pytest
from myapp.public import normal_function

def test_something():
    obj = SomeClass()
    result = obj.public_method()
    assert result == "expected"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find no violations
            assert len(findings) == 0

    def test_analyze_file_syntax_error(self) -> None:
        """Test handling of syntax errors in test files."""
        detector = PrivateAccessDetector()

        test_code = """
def test_something(
    # Missing closing parenthesis
    assert True
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find 1 syntax error
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS301"
            assert finding.name == "private_access"
            assert finding.severity == Severity.ERROR
            assert "Syntax error" in finding.message
            assert finding.metadata["error_type"] == "syntax_error"

    def test_analyze_file_analysis_error(self) -> None:
        """Test handling of analysis errors."""
        detector = PrivateAccessDetector()

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            findings = detector.analyze_file(Path("nonexistent.py"))

            # Should find 1 analysis error
            assert len(findings) == 1

            finding = findings[0]
            assert finding.code == "DS301"
            assert finding.name == "private_access"
            assert finding.severity == Severity.ERROR
            assert "Analysis error" in finding.message
            assert finding.metadata["error_type"] == "analysis_error"

    def test_is_private_module(self) -> None:
        """Test private module detection logic."""
        detector = PrivateAccessDetector()

        # Test private modules
        assert detector._is_private_module("_internal")
        assert detector._is_private_module("_private")
        assert detector._is_private_module("_impl")
        assert detector._is_private_module("_utils")

        # Test private modules with dots
        assert detector._is_private_module("myapp._internal")
        assert detector._is_private_module("myapp._private.utils")

        # Test public modules
        assert not detector._is_private_module("public")
        assert not detector._is_private_module("myapp.public")
        assert not detector._is_private_module("normal_module")

    def test_is_private_module_with_sut_package(self) -> None:
        """Test private module detection with SUT package."""
        detector = PrivateAccessDetector()

        # Test SUT package private modules
        assert detector._is_private_module("myapp._internal")
        assert detector._is_private_module("myapp._private.utils")

        # Test other package private modules (should still be detected)
        assert detector._is_private_module("other._internal")

        # Test public modules
        assert not detector._is_private_module("myapp.public")
        assert not detector._is_private_module("other.public")

    def test_is_private_attribute(self) -> None:
        """Test private attribute detection logic."""
        detector = PrivateAccessDetector()

        # Test private attributes
        assert detector._is_private_attribute("_private")
        assert detector._is_private_attribute("_internal_data")
        assert detector._is_private_attribute("__dunder__")

        # Test public attributes
        assert not detector._is_private_attribute("public")
        assert not detector._is_private_attribute("normal_attr")
        assert not detector._is_private_attribute("data")

    def test_is_private_method(self) -> None:
        """Test private method detection logic."""
        detector = PrivateAccessDetector()

        # Test private methods
        assert detector._is_private_method("_private_method")
        assert detector._is_private_method("_internal_function")
        assert detector._is_private_method("__dunder__")

        # Test public methods
        assert not detector._is_private_method("public_method")
        assert not detector._is_private_method("normal_function")
        assert not detector._is_private_method("test_something")

    def test_get_object_name(self) -> None:
        """Test object name extraction from AST nodes."""
        detector = PrivateAccessDetector()

        # Test with simple name
        import ast

        name_node = ast.Name(id="obj", ctx=ast.Load())
        assert detector._get_object_name(name_node) == "obj"

        # Test with attribute
        attr_node = ast.Attribute(
            value=ast.Name(id="obj", ctx=ast.Load()), attr="attr", ctx=ast.Load()
        )
        assert detector._get_object_name(attr_node) == "obj.attr"

        # Test with nested attribute
        nested_attr = ast.Attribute(
            value=ast.Attribute(
                value=ast.Name(id="obj", ctx=ast.Load()), attr="nested", ctx=ast.Load()
            ),
            attr="attr",
            ctx=ast.Load(),
        )
        assert detector._get_object_name(nested_attr) == "obj.nested.attr"

    def test_comprehensive_analysis(self) -> None:
        """Test comprehensive analysis with multiple violation types."""
        detector = PrivateAccessDetector()

        test_code = """
import pytest
from myapp._internal import secret_function
from _private_module import something

def test_something():
    obj = SomeClass()
    obj._private_attr = "value"
    result = obj._internal_method()
    obj.public_method()

    # Test with nested access
    data = obj.nested._private_data
    obj.nested._private_method()
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            f.flush()

            findings = detector.analyze_file(Path(f.name))

            # Should find multiple violations
            assert len(findings) >= 4  # At least 2 imports + 2 attributes + 2 methods

            # Group findings by type
            import_findings = [
                f for f in findings if f.metadata["violation_type"] == "private_import"
            ]
            attr_findings = [
                f
                for f in findings
                if f.metadata["violation_type"] == "private_attribute"
            ]
            method_findings = [
                f for f in findings if f.metadata["violation_type"] == "private_method"
            ]

            assert len(import_findings) >= 2
            assert len(attr_findings) >= 2
            assert len(method_findings) >= 2

            # Verify all findings have correct metadata
            for finding in findings:
                assert finding.code == "DS301"
                assert finding.name == "private_access"
                assert finding.severity == Severity.WARNING
                assert finding.confidence > 0.0
                assert "violation_type" in finding.metadata
