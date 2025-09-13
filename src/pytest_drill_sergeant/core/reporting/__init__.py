"""Output generation for various formats (terminal, JSON, SARIF).

This module provides comprehensive output formatting capabilities for
pytest-drill-sergeant, including template-based messaging, Rich terminal
output, JSON reports, and SARIF integration.
"""

from pytest_drill_sergeant.core.reporting.json_formatter import (
    JSONFormatter,
    JSONReportBuilder,
    json_formatter,
)
from pytest_drill_sergeant.core.reporting.output_manager import OutputManager
from pytest_drill_sergeant.core.reporting.sarif_formatter import (
    SARIFFormatter,
    SARIFReportBuilder,
    sarif_formatter,
)
from pytest_drill_sergeant.core.reporting.templates import (
    MessageTemplate,
    RichFormatter,
    TemplateContext,
    TemplateRegistry,
    rich_formatter,
    template_registry,
)
from pytest_drill_sergeant.core.reporting.types import JSONDict, JSONValue

__all__: list[str] = [
    "JSONDict",
    "JSONFormatter",
    "JSONReportBuilder",
    "JSONValue",
    "MessageTemplate",
    "OutputManager",
    "RichFormatter",
    "SARIFFormatter",
    "SARIFReportBuilder",
    "TemplateContext",
    "TemplateRegistry",
    "json_formatter",
    "rich_formatter",
    "sarif_formatter",
    "template_registry",
]
