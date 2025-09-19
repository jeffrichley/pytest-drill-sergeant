"""Template system for message formatting.

This module provides a template-based message formatting system that supports
variable substitution and different output contexts (terminal, JSON, SARIF).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.console import Console
from rich.text import Text

from pytest_drill_sergeant.core.models import Severity

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import (
        Finding,
        ResultData,
        RuleType,
        RunMetrics,
    )


@dataclass
class TemplateContext:
    """Context for template variable substitution."""

    # Test-specific context
    test_name: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    column_number: int | None = None

    # Finding-specific context
    code: str | None = None
    name: str | None = None
    severity: str | None = None
    message: str | None = None
    suggestion: str | None = None
    confidence: float | None = None

    # Score context
    bis_score: float | None = None
    bis_grade: str | None = None
    brs_score: float | None = None
    brs_grade: str | None = None

    # Run context
    total_tests: int | None = None
    total_findings: int | None = None
    average_bis: float | None = None

    # Custom context
    custom: (
        dict[
            str,
            str | int | float | bool | list[str] | dict[str, str | int | float | bool],
        ]
        | None
    ) = None

    def __post_init__(self) -> None:
        """Initialize custom context if not provided."""
        if self.custom is None:
            self.custom = {}


class MessageTemplate:
    """Template for formatting messages with variable substitution."""

    def __init__(self, template: str, context: TemplateContext | None = None) -> None:
        """Initialize the message template.

        Args:
            template: Template string with {variable} placeholders
            context: Context for variable substitution
        """
        self.template = template
        self.context = context or TemplateContext()

    def render(self, **kwargs: str | int | float | bool) -> str:
        """Render the template with variable substitution.

        Args:
            **kwargs: Additional context variables

        Returns:
            Rendered template string
        """
        # Merge context with additional kwargs
        context_vars = self._get_context_vars()
        context_vars.update(kwargs)

        # Perform variable substitution
        try:
            return self.template.format(**context_vars)
        except KeyError:
            # Handle missing variables gracefully
            # Replace all instances of the missing variable
            result = self.template
            for var_name in context_vars:
                result = result.replace(f"{{{var_name}}}", str(context_vars[var_name]))
            # Replace remaining missing variables
            return re.sub(r"\{([^}]+)\}", r"<missing:\1>", result)

    def _get_context_vars(
        self,
    ) -> dict[
        str, str | int | float | bool | list[str] | dict[str, str | int | float | bool]
    ]:
        """Get all context variables as a dictionary."""
        vars_dict = {}

        # Add all non-None context attributes
        for attr_name in dir(self.context):
            if not attr_name.startswith("_") and not callable(
                getattr(self.context, attr_name)
            ):
                value = getattr(self.context, attr_name)
                if value is not None:
                    vars_dict[attr_name] = value

        # Add custom variables
        if self.context.custom:
            vars_dict.update(self.context.custom)

        return vars_dict


class TemplateRegistry:
    """Registry for message templates."""

    def __init__(self) -> None:
        """Initialize the template registry."""
        self._templates: dict[str, MessageTemplate] = {}
        self._load_default_templates()

    def register(self, name: str, template: MessageTemplate) -> None:
        """Register a template.

        Args:
            name: Template name
            template: Template instance
        """
        self._templates[name] = template

    def get(self, name: str) -> MessageTemplate | None:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            Template instance or None if not found
        """
        return self._templates.get(name)

    def render(
        self,
        name: str,
        context: TemplateContext | None = None,
        **kwargs: str | int | float | bool,
    ) -> str:
        """Render a template by name.

        Args:
            name: Template name
            context: Template context
            **kwargs: Additional context variables

        Returns:
            Rendered template string
        """
        template = self.get(name)
        if template is None:
            return f"<template not found: {name}>"

        if context:
            template.context = context

        return template.render(**kwargs)

    def _load_default_templates(self) -> None:
        """Load default templates."""
        # Finding templates
        self.register(
            "finding.warning",
            MessageTemplate("⚠️  {name}: {message} at {file_path}:{line_number}"),
        )

        self.register(
            "finding.error",
            MessageTemplate("❌ {name}: {message} at {file_path}:{line_number}"),
        )

        self.register(
            "finding.info",
            MessageTemplate("ℹ️  {name}: {message} at {file_path}:{line_number}"),
        )

        self.register(
            "finding.hint",
            MessageTemplate("💡 {name}: {message} at {file_path}:{line_number}"),
        )

        # Test result templates
        self.register(
            "test.result",
            MessageTemplate(
                "Test: {test_name} | BIS: {bis_score:.1f} ({bis_grade}) | Findings: {total_findings}"
            ),
        )

        self.register(
            "test.pass",
            MessageTemplate("✅ {test_name} - BIS: {bis_score:.1f} ({bis_grade})"),
        )

        self.register(
            "test.fail",
            MessageTemplate(
                "❌ {test_name} - BIS: {bis_score:.1f} ({bis_grade}) - {total_findings} issues"
            ),
        )

        # Summary templates
        self.register(
            "summary.header",
            MessageTemplate("🎯 Drill Sergeant Report - {total_tests} tests analyzed"),
        )

        self.register(
            "summary.scores",
            MessageTemplate(
                "📊 Average BIS: {average_bis:.1f} | Total Findings: {total_findings}"
            ),
        )

        self.register(
            "summary.footer",
            MessageTemplate(
                "🏁 Analysis complete - {total_tests} tests, {total_findings} findings"
            ),
        )

        # Suggestion templates
        self.register("suggestion", MessageTemplate("💡 Suggestion: {suggestion}"))

        # Error templates
        self.register(
            "error.analysis",
            MessageTemplate("🔥 Analysis failed for {test_name}: {error_message}"),
        )

        self.register("error.general", MessageTemplate("💥 Error: {error_message}"))


class RichFormatter:
    """Rich-based terminal formatter for beautiful output."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the Rich formatter.

        Args:
            console: Rich console instance (creates default if None)
        """
        self.console = console or Console()
        self.registry = TemplateRegistry()

    def format_finding(self, finding: Finding) -> Text:
        """Format a finding with Rich styling.

        Args:
            finding: Finding to format

        Returns:
            Rich Text object
        """
        text = self._render_finding_template(finding)
        return self._apply_severity_styling(Text(text), finding.severity)

    def _render_finding_template(self, finding: Finding) -> str:
        """Render the template for a finding.

        Args:
            finding: Finding to render

        Returns:
            Rendered template string
        """
        template = self._get_finding_template(finding.severity)

        if template is not None:
            return template.render(
                code=finding.code,
                name=finding.name,
                message=finding.message,
                file_path=str(finding.file_path),
                line_number=finding.line_number,
                column_number=finding.column_number or 0,
                suggestion=finding.suggestion or "",
                confidence=finding.confidence,
            )
        return (
            f"Finding: {finding.message} at {finding.file_path}:{finding.line_number}"
        )

    def _get_finding_template(self, severity: Severity) -> MessageTemplate | None:
        """Get the appropriate template for a finding severity.

        Args:
            severity: Finding severity

        Returns:
            Template or None if not found
        """
        severity_value = severity.value if hasattr(severity, "value") else str(severity)
        template_name = f"finding.{severity_value}"
        template = self.registry.get(template_name)

        if template is None:
            template = self.registry.get("finding.warning")

        return template


    def _apply_severity_styling(self, text: Text, severity: Severity) -> Text:
        """Apply Rich styling based on severity.

        Args:
            text: Text to style
            severity: Severity level

        Returns:
            Styled text
        """
        severity_styles = {
            Severity.ERROR: "red bold",
            Severity.WARNING: "yellow bold",
            Severity.INFO: "blue",
            Severity.HINT: "cyan",
        }

        style = severity_styles.get(severity)
        if style:
            text.stylize(style)

        return text

    def format_test_result(self, result: ResultData) -> Text:
        """Format a test result with Rich styling.

        Args:
            result: Test result to format

        Returns:
            Rich Text object
        """
        # Determine template based on findings
        template_name = "test.fail" if result.findings else "test.pass"

        # Create context
        TemplateContext(
            test_name=result.test_name,
            file_path=str(result.file_path),
            line_number=result.line_number,
            bis_score=result.bis_score,
            bis_grade=result.bis_grade,
            total_findings=len(result.findings),
        )

        # Render template
        template = self.registry.get(template_name)
        if template is None:
            template = self.registry.get("test.result")

        if template is not None:
            text = template.render(
                test_name=result.test_name,
                file_path=str(result.file_path),
                line_number=result.line_number,
                bis_score=result.bis_score,
                bis_grade=result.bis_grade,
                total_findings=len(result.findings),
            )
        else:
            text = f"Test: {result.test_name} | BIS: {result.bis_score:.1f} ({result.bis_grade}) | Findings: {len(result.findings)}"

        # Apply Rich styling
        styled_text = Text(text)

        # Color by BIS grade
        if result.bis_grade in ["A", "B"]:
            styled_text.stylize("green")
        elif result.bis_grade in ["C", "D"]:
            styled_text.stylize("yellow")
        else:  # F grade
            styled_text.stylize("red")

        return styled_text

    def format_summary(self, metrics: RunMetrics) -> Text:
        """Format run summary with Rich styling.

        Args:
            metrics: Run metrics to format

        Returns:
            Rich Text object
        """
        # Create context
        TemplateContext(
            total_tests=metrics.total_tests,
            total_findings=metrics.total_findings,
            average_bis=metrics.average_bis,
            brs_score=metrics.brs_score,
            brs_grade=metrics.brs_grade,
        )

        # Render header
        header_template = self.registry.get("summary.header")
        header_text = header_template.render() if header_template else ""

        # Render scores
        scores_template = self.registry.get("summary.scores")
        scores_text = scores_template.render() if scores_template else ""

        # Combine and style
        full_text = f"{header_text}\n{scores_text}"
        styled_text = Text(full_text)
        styled_text.stylize("bold blue")

        return styled_text

    def print_finding(self, finding: Finding) -> None:
        """Print a finding to the console.

        Args:
            finding: Finding to print
        """
        self.console.print(self.format_finding(finding))

    def print_test_result(self, result: ResultData) -> None:
        """Print a test result to the console.

        Args:
            result: Test result to print
        """
        self.console.print(self.format_test_result(result))

    def print_summary(self, metrics: RunMetrics) -> None:
        """Print run summary to the console.

        Args:
            metrics: Run metrics to print
        """
        self.console.print(self.format_summary(metrics))


# Global template registry instance
template_registry = TemplateRegistry()

# Global Rich formatter instance
rich_formatter = RichFormatter()
