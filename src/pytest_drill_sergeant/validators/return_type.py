"""Return type validation for pytest-drill-sergeant."""

import ast

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue


class ReturnTypeValidator:
    """Validator for enforcing return type annotations on test functions."""

    def validate(
        self, item: pytest.Item, config: DrillSergeantConfig
    ) -> list[ValidationIssue]:
        """Validate return type annotations on test functions.

        Args:
            item: The pytest test item to validate
            config: The drill sergeant configuration

        Returns:
            List of validation issues found
        """
        if not self.is_enabled(config) or config.return_type_mode == "disabled":
            return []

        issues: list[ValidationIssue] = []

        # Get the file path from the test item
        file_path = item.fspath
        if not file_path:
            return issues

        try:
            # Parse the file to find test functions
            with open(str(file_path), encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Find the specific test function being validated
            test_function_name = getattr(item, "name", "unknown")
            if hasattr(item, "function") and hasattr(item.function, "__name__"):
                test_function_name = item.function.__name__

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.FunctionDef)
                    and node.name == test_function_name
                ):
                    # Check if this test function has a return type annotation
                    if node.returns is None:
                        if config.return_type_mode == "error":
                            issues.append(
                                ValidationIssue(
                                    issue_type="return_type",
                                    message=f"Test function '{node.name}' is missing return type annotation",
                                    suggestion="Add '-> None' return type annotation to the function signature",
                                )
                            )
                        elif config.return_type_mode == "auto_fix":
                            # Auto-fix by adding -> None to the function signature
                            self._auto_fix_return_type(file_path, node, content)

                    break

        except (OSError, UnicodeDecodeError, SyntaxError) as e:
            # If we can't read or parse the file, create a warning issue
            issues.append(
                ValidationIssue(
                    issue_type="return_type",
                    message=f"Could not parse file '{file_path}' for return type validation",
                    suggestion=f"Check file syntax and encoding. Error: {e}",
                )
            )

        return issues

    def _auto_fix_return_type(
        self, file_path: str, function_node: ast.FunctionDef, content: str
    ) -> None:
        """Auto-fix missing return type by adding -> None to function signature."""
        try:
            # Read the file line by line to find the function definition
            lines = content.split("\n")
            function_line_idx = function_node.lineno - 1  # Convert to 0-based index

            # Find the line with the function definition
            function_line = lines[function_line_idx]

            # Check if it already has a return type annotation
            if "->" in function_line:
                return  # Already has return type annotation

            # Add -> None before the colon
            if ":" in function_line:
                # Split on the colon and add the return type annotation
                before_colon, after_colon = function_line.rsplit(":", 1)
                new_line = f"{before_colon.rstrip()} -> None:{after_colon}"
                lines[function_line_idx] = new_line

                # Write the modified content back to the file
                with open(str(file_path), "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

        except Exception as e:
            # If auto-fix fails, we'll just skip it
            print(f"Warning: Could not auto-fix return type for {file_path}: {e}")

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if return type validation is enabled.

        Args:
            config: The drill sergeant configuration

        Returns:
            True if return type validation should run, False otherwise
        """
        return config.enforce_return_type
