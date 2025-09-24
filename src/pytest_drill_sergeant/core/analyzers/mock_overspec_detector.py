"""Mock Over-Specification Detector for pytest-drill-sergeant.

This module implements AST-based detection of excessive mock assertions in test files,
focusing on tests that assert too many implementation details about mock calls.
"""

from __future__ import annotations

import ast
import logging
import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.core.rulespec import RuleCategory, RuleRegistry, RuleSpec
from pytest_drill_sergeant.core.rulespec import Severity as RuleSeverity


class MockOverspecDetector:
    """Detects excessive mock assertions that focus on HOW instead of WHAT."""

    # Mock assertion methods to detect
    MOCK_ASSERTS: ClassVar[set[str]] = {
        "assert_called_once",
        "assert_called_with",
        "assert_has_calls",
        "assert_any_call",
        "assert_called",
        "assert_not_called",
    }

    def __init__(self) -> None:
        """Initialize the mock over-specification detector."""
        self.logger = logging.getLogger("drill_sergeant.mock_overspec_detector")

    def _get_rule_spec(self) -> RuleSpec:
        """Get the rule specification for mock over-specification detection.

        Returns:
            RuleSpec: The rule specification for this detector
        """
        try:
            return RuleRegistry.get_rule("DS102")  # Mock overspec rule code
        except KeyError:
            # Fallback if rule not found
            return RuleSpec(
                code="DS102",
                name="mock_overspec",
                default_level=RuleSeverity.WARNING,
                short_desc="Detect excessive mock assertions in tests",
                long_desc="Flags tests that have too many mock assertions, focusing on implementation details rather than behavior.",
                tags=["mock", "overspecification", "behavior", "testing"],
                fixable=False,
                category=RuleCategory.CODE_QUALITY,
            )

    def _is_mock_target_allowed(self, mock_target: str, allowlist: list[str]) -> bool:
        """Check if a mock target is in the allowlist.

        Args:
            mock_target: The mock target to check
            allowlist: List of allowed mock patterns

        Returns:
            bool: True if the mock target is allowed
        """
        for pattern in allowlist:
            # Convert glob pattern to regex
            # Escape special regex characters except * and ?
            escaped_pattern = re.escape(pattern)
            # Convert back * and ? to regex equivalents
            regex_pattern = escaped_pattern.replace(r"\*", ".*").replace(r"\?", ".")
            if re.match(f"^{regex_pattern}$", mock_target):
                return True
        return False

    def _extract_mock_target(self, node: ast.Attribute) -> str | None:
        """Extract the mock target from an attribute access.

        Args:
            node: The AST attribute node

        Returns:
            str | None: The mock target name or None if not extractable
        """
        try:
            # For mock assertions, we want to get the base mock object name
            # node.value is the object being accessed for the assertion
            current = node.value
            parts = []

            # Walk up the attribute chain to get the full path
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value

            # The final node should be a Name (the base variable)
            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))
            return None
        except Exception:
            return None

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for mock over-specification violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for mock over-specification violations
        """
        findings: list[Finding] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception as e:
            self.logger.warning("Failed to parse %s: %s", file_path, e)
            return findings

        # Get configuration
        rule_spec = self._get_rule_spec()

        # Get threshold from config (default: 3)
        # TODO: Integrate with configuration system properly
        threshold = 3

        # Get allowlist from config
        # TODO: Integrate with configuration system properly
        allowlist = [
            "requests.*",
            "boto3.*",
            "time.*",
            "random.*",
            "os.*",
            "subprocess.*",
        ]

        # Analyze each top-level test function (not nested functions)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                mock_assertions = self._count_mock_assertions(node, allowlist)

                if mock_assertions > threshold:
                    finding = Finding(
                        code=rule_spec.code,
                        name=rule_spec.name,
                        severity=Severity.WARNING,  # Use the imported Severity enum
                        message=f"Test '{node.name}' has {mock_assertions} mock assertions (threshold: {threshold}). "
                        f"Consider focusing on behavior outcomes instead of implementation details.",
                        file_path=file_path,
                        line_number=node.lineno,
                        column_number=getattr(node, "col_offset", 0),
                        suggestion="Reduce mock assertions by focusing on the behavior being tested rather than "
                        "specific call sequences. Consider asserting on the final state or return value instead.",
                    )
                    findings.append(finding)

        return findings

    def _count_mock_assertions(
        self, func_node: ast.FunctionDef, allowlist: list[str]
    ) -> int:
        """Count mock assertions in a test function.

        Args:
            func_node: The test function AST node
            allowlist: List of allowed mock patterns

        Returns:
            int: Number of mock assertions found
        """

        class MockAssertionVisitor(ast.NodeVisitor):
            def __init__(self, detector, allowlist):
                self.detector = detector
                self.allowlist = allowlist
                self.count = 0
                self.in_nested_function = False

            def visit_FunctionDef(self, node):
                # If we encounter a function definition while already in a function,
                # it's a nested function - don't visit it
                if self.in_nested_function:
                    return
                # This is the main function, visit its body but mark nested functions
                old_nested = self.in_nested_function
                self.in_nested_function = True
                self.generic_visit(node)
                self.in_nested_function = old_nested

            def visit_AsyncFunctionDef(self, node):
                # Same logic for async functions
                if self.in_nested_function:
                    return
                old_nested = self.in_nested_function
                self.in_nested_function = True
                self.generic_visit(node)
                self.in_nested_function = old_nested

            def visit_Call(self, node):
                # Look for method calls where the method name is a mock assertion
                if isinstance(node.func, ast.Attribute) and node.func.attr in self.detector.MOCK_ASSERTS:
                        # Extract the mock target
                        mock_target = self.detector._extract_mock_target(node.func)

                        # Skip if target is in allowlist
                        if mock_target and self.detector._is_mock_target_allowed(
                            mock_target, self.allowlist
                        ):
                            pass
                        else:
                            self.count += 1

                # Continue visiting child nodes
                self.generic_visit(node)

        visitor = MockAssertionVisitor(self, allowlist)
        visitor.visit(func_node)
        return visitor.count


# Register the detector
def register_mock_overspec_detector() -> None:
    """Register the mock over-specification detector with the rule registry."""
    detector = MockOverspecDetector()
    rule_spec = detector._get_rule_spec()

    rule_registry = RuleRegistry()
    rule_registry.register_rule(rule_spec)
