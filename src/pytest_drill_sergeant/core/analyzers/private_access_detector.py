"""Private Access Detector for pytest-drill-sergeant.

This module implements AST-based detection of private access violations in test files,
including private imports, private attribute access, and private method calls.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.rulespec import RuleRegistry, RuleSpec


class Detector(Protocol):
    """Protocol for all detectors in the system."""

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for violations
        """
        ...


class PrivateAccessDetector:
    """Detects private access violations in test files using AST analysis."""

    def __init__(self) -> None:
        """Initialize the private access detector.

        The detector will use the centralized configuration registry
        to get rule severities and settings.
        """
        self.logger = logging.getLogger("drill_sergeant.private_access_detector")

    def _get_rule_spec(self) -> RuleSpec:
        """Get the rule specification for private access detection.

        Returns:
            Rule specification for private access
        """
        try:
            return RuleRegistry.get_rule("DS301")  # Private access rule code
        except KeyError:
            # Fallback if rule not found
            from pytest_drill_sergeant.core.rulespec import RuleCategory, RuleSpec
            from pytest_drill_sergeant.core.rulespec import Severity as RuleSeverity

            return RuleSpec(
                code="DS301",
                name="private_access",
                default_level=RuleSeverity.WARNING,
                short_desc="Detect access to private members in tests",
                long_desc="Flags tests that access private methods, attributes, or modules.",
                tags=["encapsulation", "quality", "brittleness"],
                fixable=False,
                category=RuleCategory.CODE_QUALITY,
            )

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for private access violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for private access violations
        """
        findings = []

        # Only analyze test files - skip source code files
        if not self._is_test_file(file_path):
            return findings

        try:
            # Parse the file
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Analyze the AST for private access violations
            findings.extend(self._detect_private_imports(tree, file_path))

            # Collect method call nodes to avoid double detection
            method_call_nodes = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    method_call_nodes.add(node.func)

            findings.extend(
                self._detect_private_attributes(tree, file_path, method_call_nodes)
            )
            findings.extend(self._detect_private_methods(tree, file_path))

            self.logger.debug(
                "Analyzed %s: found %d private access violations",
                file_path,
                len(findings),
            )

        except SyntaxError as e:
            self.logger.warning("Failed to parse %s: %s", file_path, e)
            # Create a finding for syntax errors
            rule_spec = self._get_rule_spec()
            findings.append(
                Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.ERROR,
                    message=f"Syntax error in test file: {e}",
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    column_number=e.offset,
                    confidence=1.0,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={"error_type": "syntax_error", "error_message": str(e)},
                )
            )
        except Exception as e:
            self.logger.error("Unexpected error analyzing %s: %s", file_path, e)
            # Create a finding for unexpected errors
            rule_spec = self._get_rule_spec()
            findings.append(
                Finding(
                    code=rule_spec.code,
                    name=rule_spec.name,
                    severity=Severity.ERROR,
                    message=f"Analysis error: {e}",
                    file_path=file_path,
                    line_number=1,
                    confidence=1.0,
                    fixable=rule_spec.fixable,
                    tags=rule_spec.tags,
                    metadata={"error_type": "analysis_error", "error_message": str(e)},
                )
            )

        return findings

    def _detect_private_imports(self, tree: ast.AST, file_path: Path) -> list[Finding]:
        """Detect private imports (from pkg._internal import ...).

        Args:
            tree: AST tree to analyze
            file_path: Path to the file being analyzed

        Returns:
            List of findings for private imports
        """
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and self._is_private_module(node.module):
                    rule_spec = self._get_rule_spec()
                    finding = Finding(
                        code=rule_spec.code,
                        name=rule_spec.name,
                        severity=Severity.WARNING,
                        message=f"Importing private module: {node.module}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=self._get_code_snippet(node),
                        suggestion="Use public API instead of private modules",
                        confidence=0.9,
                        fixable=rule_spec.fixable,
                        tags=rule_spec.tags,
                        metadata={
                            "violation_type": "private_import",
                            "module_name": node.module,
                            "imported_names": ", ".join(
                                [alias.name for alias in node.names]
                            ),
                        },
                    )
                    findings.append(finding)

        return findings

    def _detect_private_attributes(
        self, tree: ast.AST, file_path: Path, method_call_nodes: set[ast.Attribute]
    ) -> list[Finding]:
        """Detect private attribute access (obj._private).

        Args:
            tree: AST tree to analyze
            file_path: Path to the file being analyzed
            method_call_nodes: Set of attribute nodes that are part of method calls

        Returns:
            List of findings for private attribute access
        """
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Skip if this is part of a method call (handled separately)
                if node in method_call_nodes:
                    continue

                if self._is_private_attribute(node.attr):
                    rule_spec = self._get_rule_spec()
                    finding = Finding(
                        code=rule_spec.code,
                        name=rule_spec.name,
                        severity=Severity.WARNING,
                        message=f"Accessing private attribute: {node.attr}",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        code_snippet=self._get_code_snippet(node),
                        suggestion="Use public API instead of private attributes",
                        confidence=0.8,
                        fixable=rule_spec.fixable,
                        tags=rule_spec.tags,
                        metadata={
                            "violation_type": "private_attribute",
                            "attribute_name": node.attr,
                            "object_name": self._get_object_name(node.value),
                        },
                    )
                    findings.append(finding)

        return findings

    def _detect_private_methods(self, tree: ast.AST, file_path: Path) -> list[Finding]:
        """Detect private method calls (obj._private_method()).

        Args:
            tree: AST tree to analyze
            file_path: Path to the file being analyzed

        Returns:
            List of findings for private method calls
        """
        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if self._is_private_method(node.func.attr):
                        # Check if this is a self-call (class calling its own method)
                        if self._is_self_call(node.func):
                            continue  # Skip self-calls - they're allowed

                        rule_spec = self._get_rule_spec()
                        finding = Finding(
                            code=rule_spec.code,
                            name=rule_spec.name,
                            severity=Severity.WARNING,
                            message=f"Calling private method: {node.func.attr}",
                            file_path=file_path,
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            code_snippet=self._get_code_snippet(node),
                            suggestion="Use public API instead of private methods",
                            confidence=0.8,
                            fixable=rule_spec.fixable,
                            tags=rule_spec.tags,
                            metadata={
                                "violation_type": "private_method",
                                "method_name": node.func.attr,
                                "object_name": self._get_object_name(node.func.value),
                            },
                        )
                        findings.append(finding)

        return findings

    def _is_private_module(self, module_name: str) -> bool:
        """Check if a module name indicates private access.

        Args:
            module_name: Name of the module to check

        Returns:
            True if the module is private
        """
        # Skip standard Python modules that start with underscore
        if module_name in ["__future__", "__main__", "__builtin__", "__builtins__"]:
            return False

        # Check for private modules (starting with underscore)
        if module_name.startswith("_"):
            return True

        # Check for common private module patterns
        private_patterns = ["_internal", "_private", "_impl", "_utils"]
        for pattern in private_patterns:
            if f".{pattern}" in module_name or module_name.endswith(f".{pattern}"):
                return True

        return False

    def _is_private_attribute(self, attr_name: str) -> bool:
        """Check if an attribute name indicates private access.

        Args:
            attr_name: Name of the attribute to check

        Returns:
            True if the attribute is private
        """
        return attr_name.startswith("_")

    def _is_private_method(self, method_name: str) -> bool:
        """Check if a method name indicates private access.

        Args:
            method_name: Name of the method to check

        Returns:
            True if the method is private
        """
        return method_name.startswith("_")

    def _is_self_call(self, func_attr: ast.Attribute) -> bool:
        """Check if this is a self-call (class calling its own method).

        Args:
            func_attr: The function attribute node

        Returns:
            True if this is a self-call
        """
        # Check if the function is called on 'self'
        if isinstance(func_attr.value, ast.Name) and func_attr.value.id == "self":
            return True

        # Check if it's a chained call like self.something._private_method()
        if isinstance(func_attr.value, ast.Attribute):
            # Walk up the chain to see if it starts with 'self'
            current = func_attr.value
            while isinstance(current, ast.Attribute):
                current = current.value
            if isinstance(current, ast.Name) and current.id == "self":
                return True

        return False

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file is a test file
        """
        # Check if the file is in a test directory
        if "test" in file_path.parts:
            return True

        # Check if the filename starts with test_
        if file_path.name.startswith("test_"):
            return True

        # Check if the filename ends with _test.py
        if file_path.name.endswith("_test.py"):
            return True

        return False

    def _get_code_snippet(self, node: ast.AST) -> str | None:
        """Get a code snippet around the given AST node.

        Args:
            node: AST node to get snippet for

        Returns:
            Code snippet or None if not available
        """
        # For now, return None - this could be enhanced to extract actual code
        # from the source file around the node's line number
        return None

    def _get_object_name(self, node: ast.AST) -> str:
        """Get the name of an object from an AST node.

        Args:
            node: AST node representing an object

        Returns:
            String representation of the object name
        """
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_object_name(node.value)}.{node.attr}"
        if isinstance(node, ast.Call):
            return self._get_object_name(node.func)
        return "<unknown>"
