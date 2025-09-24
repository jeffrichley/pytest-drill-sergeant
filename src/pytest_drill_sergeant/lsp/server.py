"""Language Server Protocol implementation for pytest-drill-sergeant.

This module provides a Language Server Protocol (LSP) server that integrates
with IDEs to provide real-time diagnostics and feedback for test quality issues.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range
from pygls.server import LanguageServer
from pygls.workspace import Document

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant import __version__
from pytest_drill_sergeant.core.analysis_pipeline import create_analysis_pipeline
from pytest_drill_sergeant.core.config_context import initialize_config
from pytest_drill_sergeant.core.logging_utils import setup_standard_logging

logger = logging.getLogger(__name__)


class DrillSergeantLanguageServer(LanguageServer):
    """Language Server Protocol server for pytest-drill-sergeant.

    This server provides real-time diagnostics for test quality issues,
    integrating with IDEs to show drill sergeant findings as error squiggles.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the drill sergeant language server."""
        super().__init__("drill-sergeant-lsp", __version__, *args, **kwargs)

        # Initialize logging for LSP mode
        setup_standard_logging()

        # Initialize configuration from project files
        self.config = initialize_config()

        # Initialize analyzers
        self.analyzers = create_analysis_pipeline()

        logger.info("Drill Sergeant Language Server initialized")

    def analyze_document(self, document: Document) -> list[Diagnostic]:
        """Analyze a document and return LSP diagnostics.

        Args:
            document: The LSP document to analyze

        Returns:
            List of LSP diagnostics for the document
        """
        try:
            # Convert LSP document URI to file path
            file_path = Path(document.uri.replace("file://", ""))

            # Only analyze test files
            if not self._is_test_file(file_path):
                return []

            # Run our analyzers on the file
            findings = []
            for analyzer in self.analyzers.analyzers:
                try:
                    analyzer_findings = analyzer.analyze_file(file_path)
                    findings.extend(analyzer_findings)
                except Exception as e:
                    logger.warning(
                        "Analyzer %s failed: %s", analyzer.__class__.__name__, e
                    )
                    continue

            # Convert findings to LSP diagnostics
            diagnostics = self._convert_findings_to_diagnostics(findings, document)

            logger.debug(
                "Analyzed %s: found %d diagnostics", file_path, len(diagnostics)
            )
            return diagnostics

        except Exception as e:
            logger.error("Failed to analyze document %s: %s", document.uri, e)
            return []

    def _convert_findings_to_diagnostics(
        self, findings: list[Finding], document: Document
    ) -> list[Diagnostic]:
        """Convert drill sergeant findings to LSP diagnostics.

        Args:
            findings: List of findings from analyzers
            document: The LSP document

        Returns:
            List of LSP diagnostics
        """
        diagnostics = []

        for finding in findings:
            try:
                # Convert severity
                severity = self._convert_severity(finding.severity)

                # Create range (line-based for now)
                line = max(0, finding.line_number - 1)  # LSP is 0-indexed
                start_pos = Position(line, finding.column_number or 0)
                end_pos = Position(line, finding.column_number or 0)

                # Handle multi-line findings
                if finding.end_line_number:
                    end_pos = Position(finding.end_line_number - 1, 0)

                diagnostic = Diagnostic(
                    range=Range(start=start_pos, end=end_pos),
                    message=finding.message,
                    severity=severity,
                    source="drill-sergeant",
                    code=finding.code,
                    # Add suggestion if available
                    related_information=[],
                )

                diagnostics.append(diagnostic)

            except Exception as e:
                logger.warning("Failed to convert finding to diagnostic: %s", e)
                continue

        return diagnostics

    def _convert_severity(self, severity: str) -> DiagnosticSeverity:
        """Convert drill sergeant severity to LSP severity.

        Args:
            severity: Drill sergeant severity level

        Returns:
            LSP diagnostic severity
        """
        severity_map = {
            "error": DiagnosticSeverity.Error,
            "warning": DiagnosticSeverity.Warning,
            "info": DiagnosticSeverity.Information,
            "hint": DiagnosticSeverity.Hint,
        }

        return severity_map.get(severity, DiagnosticSeverity.Warning)

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed as a test file.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be analyzed
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


# Global server instance
_server: DrillSergeantLanguageServer | None = None


def get_language_server() -> DrillSergeantLanguageServer:
    """Get the global language server instance.

    Returns:
        DrillSergeantLanguageServer instance
    """
    global _server
    if _server is None:
        _server = DrillSergeantLanguageServer()
    return _server


def create_language_server() -> DrillSergeantLanguageServer:
    """Create a new language server instance.

    Returns:
        New DrillSergeantLanguageServer instance
    """
    return DrillSergeantLanguageServer()
