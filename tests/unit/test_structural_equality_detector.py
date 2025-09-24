"""Tests for the Structural Equality Detector."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.analyzers.structural_equality_detector import (
    StructuralEqualityDetector,
)
from pytest_drill_sergeant.core.models import Finding, Severity


class TestStructuralEqualityDetector:
    """Test cases for StructuralEqualityDetector."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = StructuralEqualityDetector()

    def _analyze_test_code(self, code: str, file_path: Path) -> list[Finding]:
        """Helper method to analyze test code and return findings."""
        tree = ast.parse(code)
        # Find the test function and analyze it
        test_func = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                test_func = node
                break

        if test_func is None:
            return []

        return self.detector._analyze_test_function(test_func, file_path)

    def test_init(self) -> None:
        """Test detector initialization."""
        detector = StructuralEqualityDetector()
        assert detector is not None
        assert detector.logger.name == "drill_sergeant.structural_equality_detector"

    def test_get_rule_spec(self) -> None:
        """Test rule spec retrieval."""
        rule_spec = self.detector._get_rule_spec()
        assert rule_spec.code == "DS306"
        assert rule_spec.name == "structural_equality"
        assert rule_spec.default_level == Severity.WARNING

    def test_detect_dict_access(self) -> None:
        """Test detection of __dict__ access patterns."""
        code = """
def test_dict_access():
    user = User("John", "john@example.com")
    assert user.__dict__ == {"name": "John", "email": "john@example.com"}
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Comparing internal structure: __dict__" in finding.message
        assert finding.metadata["violation_type"] == "dict_access"
        assert finding.metadata["method_name"] == "__dict__"

    def test_detect_vars_calls(self) -> None:
        """Test detection of vars() function calls."""
        code = """
def test_vars_call():
    user = User("Jane", "jane@example.com")
    assert vars(user) == {"name": "Jane", "email": "jane@example.com"}
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Comparing internal structure: vars()" in finding.message
        assert finding.metadata["violation_type"] == "vars_call"
        assert finding.metadata["method_name"] == "vars"

    def test_detect_dataclass_asdict(self) -> None:
        """Test detection of dataclasses.asdict() calls."""
        code = """
def test_asdict_call():
    user = User("Bob", "bob@example.com")
    assert dataclasses.asdict(user) == {"name": "Bob", "email": "bob@example.com"}
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Comparing internal structure: dataclasses.asdict()" in finding.message
        assert finding.metadata["violation_type"] == "asdict_call"
        assert finding.metadata["method_name"] == "asdict"

    def test_detect_repr_comparisons(self) -> None:
        """Test detection of repr() comparisons."""
        code = """
def test_repr_comparison():
    user = User("Alice", "alice@example.com")
    assert repr(user) == "User(name='Alice', email='alice@example.com')"
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Comparing string representation: repr()" in finding.message
        assert finding.metadata["violation_type"] == "repr_comparison"
        assert finding.metadata["method_name"] == "repr"

    def test_detect_str_comparisons(self) -> None:
        """Test detection of str() comparisons."""
        code = """
def test_str_comparison():
    user = User("Charlie", "charlie@example.com")
    assert str(user) == "User(name='Charlie', email='charlie@example.com')"
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Comparing string representation: str()" in finding.message
        assert finding.metadata["violation_type"] == "str_comparison"
        assert finding.metadata["method_name"] == "str"

    def test_detect_getattr_private(self) -> None:
        """Test detection of getattr() calls with private attributes."""
        code = """
def test_getattr_private():
    user = User("David", "david@example.com")
    assert getattr(user, "_private_attr", None) == "expected_value"
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.code == "DS306"
        assert finding.severity == Severity.WARNING
        assert "Accessing private attribute: _private_attr" in finding.message
        assert finding.metadata["violation_type"] == "getattr_private"
        assert finding.metadata["method_name"] == "getattr"
        assert finding.metadata["attribute_name"] == "_private_attr"

    def test_ignore_non_assert_context(self) -> None:
        """Test that violations outside assert statements are detected."""
        code = """
def test_non_assert_context():
    user = User("Eve", "eve@example.com")
    user_dict = user.__dict__  # This should be flagged
    result = vars(user)  # This should be flagged
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        # Should find both violations
        assert len(findings) == 2
        violation_types = {f.metadata["violation_type"] for f in findings}
        assert "dict_access" in violation_types
        assert "vars_call" in violation_types

    def test_ignore_non_test_functions(self) -> None:
        """Test that violations in non-test functions are ignored."""
        code = """
def regular_function():
    user = User("Frank", "frank@example.com")
    assert user.__dict__ == {"name": "Frank", "email": "frank@example.com"}
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        # Should find no violations since it's not a test function
        assert len(findings) == 0

    def test_handle_nested_calls(self) -> None:
        """Test handling of nested structural equality calls."""
        code = """
def test_nested_calls():
    user = User("Grace", "grace@example.com")
    expected_dict = {"name": "Grace", "email": "grace@example.com"}
    assert vars(user) == expected_dict
    assert dataclasses.asdict(user) == expected_dict
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        # Should find both violations
        assert len(findings) == 2
        violation_types = {f.metadata["violation_type"] for f in findings}
        assert "vars_call" in violation_types
        assert "asdict_call" in violation_types

    def test_syntax_error_handling(self) -> None:
        """Test graceful handling of syntax errors."""
        file_path = Path("syntax_error.py")

        # Create a file with syntax error
        with patch(
            "pathlib.Path.read_text",
            return_value="def test_invalid_syntax:\n    assert True",
        ):
            findings = self.detector.analyze_file(file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.severity == Severity.ERROR
        assert "Syntax error in test file" in finding.message

    def test_analysis_error_handling(self) -> None:
        """Test graceful handling of analysis errors."""
        file_path = Path("analysis_error.py")

        with patch("pathlib.Path.read_text", side_effect=OSError("File not found")):
            findings = self.detector.analyze_file(file_path)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.severity == Severity.ERROR
        assert "Analysis error" in finding.message

    def test_get_object_name(self) -> None:
        """Test object name extraction from AST nodes."""
        # Test with Name node
        name_node = ast.Name(id="user", ctx=ast.Load())
        assert self.detector._get_object_name(name_node) == "user"

        # Test with Attribute node
        attr_node = ast.Attribute(
            value=ast.Name(id="user", ctx=ast.Load()), attr="name", ctx=ast.Load()
        )
        assert self.detector._get_object_name(attr_node) == "user"

        # Test with Call node
        call_node = ast.Call(
            func=ast.Name(id="vars", ctx=ast.Load()),
            args=[ast.Name(id="user", ctx=ast.Load())],
            keywords=[],
        )
        assert self.detector._get_object_name(call_node) == "vars"

    def test_get_code_snippet(self) -> None:
        """Test code snippet extraction."""
        node = ast.Name(id="test", ctx=ast.Load())
        node.lineno = 10

        snippet = self.detector._get_code_snippet(node)
        assert snippet == "Line 10"

    def test_analyze_file_integration(self) -> None:
        """Test full file analysis integration."""
        code = """
import dataclasses
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str

def test_dict_access():
    user = User("John", "john@example.com")
    assert user.__dict__ == {"name": "John", "email": "john@example.com"}

def test_vars_call():
    user = User("Jane", "jane@example.com")
    assert vars(user) == {"name": "Jane", "email": "jane@example.com"}

def test_clean_test():
    user = User("Bob", "bob@example.com")
    assert user.name == "Bob"
    assert user.email == "bob@example.com"
"""

        file_path = Path("integration_test.py")
        with patch("pathlib.Path.read_text", return_value=code):
            findings = self.detector.analyze_file(file_path)

        # Should find 2 violations (dict access and vars call)
        assert len(findings) >= 2

        # Check that violations are properly categorized
        violation_types = {f.metadata.get("violation_type") for f in findings}
        assert "dict_access" in violation_types
        assert "vars_call" in violation_types

    def test_confidence_scoring(self) -> None:
        """Test confidence scoring for different violation types."""
        code = """
def test_confidence_levels():
    user = User("Test", "test@example.com")
    assert user.__dict__ == {}  # High confidence
    assert vars(user) == {}     # High confidence
    assert repr(user) == ""     # Medium confidence
    assert str(user) == ""      # Lower confidence
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        # Should find 4 violations
        assert len(findings) == 4

        # Check confidence levels
        confidence_levels = {f.confidence for f in findings}
        assert 0.9 in confidence_levels  # dict and vars
        assert 0.8 in confidence_levels  # repr
        assert 0.7 in confidence_levels  # str

    def test_finding_metadata(self) -> None:
        """Test finding metadata structure."""
        code = """
def test_metadata():
    user = User("Test", "test@example.com")
    assert user.__dict__ == {}
"""
        file_path = Path("test_file.py")
        findings = self._analyze_test_code(code, file_path)

        assert len(findings) == 1
        finding = findings[0]
        metadata = finding.metadata

        assert "violation_type" in metadata
        assert "method_name" in metadata
        assert "object_name" in metadata
        assert metadata["violation_type"] == "dict_access"
        assert metadata["method_name"] == "__dict__"

    def test_rule_spec_integration(self) -> None:
        """Test integration with rule specification system."""
        rule_spec = self.detector._get_rule_spec()

        assert rule_spec.code == "DS306"
        assert rule_spec.name == "structural_equality"
        assert rule_spec.tags == ["assertions", "quality", "correctness"]
        assert rule_spec.category.value == "code_quality"
        assert not rule_spec.fixable  # Should be False as per spec
