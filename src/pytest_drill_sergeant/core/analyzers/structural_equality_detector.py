"""Structural Equality Detector for pytest-drill-sergeant.

This module implements AST-based detection of structural equality violations in test files,
including __dict__ access, vars() calls, dataclasses.asdict() calls, and repr() comparisons.
"""

from __future__ import annotations

import ast
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_drill_sergeant.core.models import Finding
    from pytest_drill_sergeant.core.rulespec import RuleSpec

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.rulespec import (
    RuleCategory,
    RuleRegistry,
    RuleSpec,
)
from pytest_drill_sergeant.core.rulespec import (
    Severity as RuleSeverity,
)


class StructuralEqualityDetector:
    """Detects structural equality violations in test files using AST analysis."""

    # Constants for getattr argument positions
    GETATTR_MIN_ARGS = 2
    GETATTR_ATTR_NAME_INDEX = 1

    def __init__(self) -> None:
        """Initialize the structural equality detector."""
        self.logger = logging.getLogger("drill_sergeant.structural_equality_detector")

    def _get_rule_spec(self) -> RuleSpec:
        """Get the rule specification for structural equality detection.

        Returns:
            RuleSpec: The rule specification for this detector
        """
        try:
            return RuleRegistry.get_rule("DS306")
        except KeyError:
            # Fallback if rule not found
            return RuleSpec(
                code="DS306",
                name="structural_equality",
                default_level=RuleSeverity.WARNING,
                short_desc="Check for proper equality testing",
                long_desc="Validates that tests use appropriate equality assertions and don't rely on object identity when value equality is intended.",
                tags=["assertions", "quality", "correctness"],
                fixable=False,
                category=RuleCategory.CODE_QUALITY,
            )

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for structural equality violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for structural equality violations
        """
        findings: list[Finding] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))

            # Analyze each test function individually
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    findings.extend(self._analyze_test_function(node, file_path))

        except SyntaxError as e:
            # Create a finding for syntax errors
            rule_spec = self._get_rule_spec()
            finding = Finding(
                code=rule_spec.code,
                name=rule_spec.name,
                severity=Severity.ERROR,
                message=f"Syntax error in test file: {e}",
                file_path=file_path,
                line_number=e.lineno or 0,
                column_number=e.offset or 0,
                code_snippet=None,
                suggestion="Fix syntax error before analysis",
                confidence=1.0,
                fixable=False,
                tags=rule_spec.tags,
                metadata={"error_type": "syntax_error", "error_msg": str(e)},
            )
            findings.append(finding)
        except (OSError, UnicodeDecodeError) as e:
            self.logger.exception("Error analyzing %s", file_path)
            # Create a finding for analysis errors
            rule_spec = self._get_rule_spec()
            finding = Finding(
                code=rule_spec.code,
                name=rule_spec.name,
                severity=Severity.ERROR,
                message=f"Analysis error: {e}",
                file_path=file_path,
                line_number=0,
                column_number=0,
                code_snippet=None,
                suggestion="Check file format and try again",
                confidence=0.0,
                fixable=False,
                tags=rule_spec.tags,
                metadata={"error_type": "analysis_error", "error_msg": str(e)},
            )
            findings.append(finding)

        return findings

    def _analyze_test_function(
        self, func_node: ast.FunctionDef, file_path: Path
    ) -> list[Finding]:  # noqa: C901
        """Analyze a single test function for structural equality violations.

        Args:
            func_node: The test function AST node
            file_path: Path to the file being analyzed

        Returns:
            List of findings for structural equality violations
        """
        findings: list[Finding] = []

        # Use a visitor to find violations within the test function
        class StructuralEqualityVisitor(ast.NodeVisitor):
            def __init__(self, detector, file_path, findings):
                self.detector = detector
                self.file_path = file_path
                self.findings = findings

            def visit_Attribute(self, node):
                # Check for __dict__ access
                if node.attr == "__dict__":
                    self._add_dict_access_finding(node)
                self.generic_visit(node)

            def visit_Call(self, node):
                # Check for vars() calls
                if isinstance(node.func, ast.Name) and node.func.id == "vars":
                    self._add_vars_call_finding(node)
                # Check for dataclasses.asdict() calls
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "dataclasses"
                    and node.func.attr == "asdict"
                ):
                    self._add_asdict_call_finding(node)
                # Check for repr() calls
                elif isinstance(node.func, ast.Name) and node.func.id == "repr":
                    self._add_repr_call_finding(node)
                # Check for str() calls
                elif isinstance(node.func, ast.Name) and node.func.id == "str":
                    self._add_str_call_finding(node)
                # Check for getattr() calls with private attributes
                elif (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "getattr"
                    and len(node.args) >= self.detector.GETATTR_MIN_ARGS
                    and isinstance(
                        node.args[self.detector.GETATTR_ATTR_NAME_INDEX], ast.Constant
                    )
                    and isinstance(
                        node.args[self.detector.GETATTR_ATTR_NAME_INDEX].value, str
                    )
                    and node.args[
                        self.detector.GETATTR_ATTR_NAME_INDEX
                    ].value.startswith("_")
                ):
                    self._add_getattr_private_finding(node)
                self.generic_visit(node)

            def _add_dict_access_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message="Comparing internal structure: __dict__",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of internal structure. Use public API methods or properties.",
                    confidence=0.9,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "dict_access",
                        "method_name": "__dict__",
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

            def _add_vars_call_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message="Comparing internal structure: vars()",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of internal structure. Use public API methods or properties.",
                    confidence=0.9,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "vars_call",
                        "method_name": "vars",
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

            def _add_asdict_call_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message="Comparing internal structure: dataclasses.asdict()",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of internal structure. Use public API methods or properties.",
                    confidence=0.9,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "asdict_call",
                        "method_name": "asdict",
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

            def _add_repr_call_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message="Comparing string representation: repr()",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of string representation. Use public API methods or properties.",
                    confidence=0.8,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "repr_comparison",
                        "method_name": "repr",
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

            def _add_str_call_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message="Comparing string representation: str()",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of string representation. Use public API methods or properties.",
                    confidence=0.7,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "str_comparison",
                        "method_name": "str",
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

            def _add_getattr_private_finding(self, node):
                rule_spec = self.detector._get_rule_spec()  # noqa: SLF001
                finding = Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.WARNING,
                    message=f"Accessing private attribute: {node.args[self.detector.GETATTR_ATTR_NAME_INDEX].value}",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    code_snippet=self.detector._get_code_snippet(node),  # noqa: SLF001
                    suggestion="Test behavior instead of private attributes. Use public API methods or properties.",
                    confidence=0.9,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={
                        "violation_type": "getattr_private",
                        "method_name": "getattr",
                        "attribute_name": node.args[
                            self.detector.GETATTR_ATTR_NAME_INDEX
                        ].value,
                        "object_name": self.detector._get_object_name(
                            node
                        ),  # noqa: SLF001
                    },
                )
                self.findings.append(finding)

        # Use the visitor to analyze the test function
        visitor = StructuralEqualityVisitor(self, file_path, findings)
        visitor.visit(func_node)

        return findings

    def _get_code_snippet(self, node: ast.AST) -> str | None:
        """Get code snippet around the violation."""
        try:
            # For now, return a simple representation
            # In a full implementation, you might want to read the file content
            # and extract the actual line
            if hasattr(node, "lineno") and node.lineno:
                return f"Line {node.lineno}"
            return None  # noqa: TRY300
        except (AttributeError, TypeError):
            return None

    def _get_object_name(self, node: ast.AST) -> str:
        """Get object name from AST node."""
        try:
            if isinstance(node, ast.Attribute):
                return self._get_object_name(node.value)
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Call):
                return self._get_object_name(node.func)
            return "unknown"  # noqa: TRY300
        except (AttributeError, TypeError):
            return "unknown"
