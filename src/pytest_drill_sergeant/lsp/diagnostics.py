"""Diagnostic conversion utilities for LSP integration.

This module handles converting drill sergeant findings into LSP-compatible
diagnostics with proper formatting and metadata.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Finding

logger = logging.getLogger(__name__)


class DiagnosticConverter:
    """Converts drill sergeant findings to LSP diagnostics."""
    
    # Severity mapping from drill sergeant to LSP
    SEVERITY_MAP = {
        "error": DiagnosticSeverity.Error,
        "warning": DiagnosticSeverity.Warning,
        "info": DiagnosticSeverity.Information,
        "hint": DiagnosticSeverity.Hint,
    }
    
    def __init__(self) -> None:
        """Initialize the diagnostic converter."""
        self.logger = logging.getLogger(f"{__name__}.DiagnosticConverter")
    
    def convert_findings(
        self, findings: list[Finding], document_lines: list[str] | None = None
    ) -> list[Diagnostic]:
        """Convert drill sergeant findings to LSP diagnostics.
        
        Args:
            findings: List of findings from analyzers
            document_lines: Optional list of document lines for better positioning
            
        Returns:
            List of LSP diagnostics
        """
        diagnostics = []
        
        for finding in findings:
            try:
                diagnostic = self._convert_single_finding(finding, document_lines)
                if diagnostic:
                    diagnostics.append(diagnostic)
            except Exception as e:
                self.logger.warning(f"Failed to convert finding {finding.code}: {e}")
                continue
        
        return diagnostics
    
    def _convert_single_finding(
        self, finding: Finding, document_lines: list[str] | None = None
    ) -> Diagnostic | None:
        """Convert a single finding to an LSP diagnostic.
        
        Args:
            finding: The finding to convert
            document_lines: Optional document lines for better positioning
            
        Returns:
            LSP diagnostic or None if conversion fails
        """
        # Convert severity
        severity = self._convert_severity(finding.severity)
        
        # Create range
        range_obj = self._create_range(finding, document_lines)
        
        # Create diagnostic
        diagnostic = Diagnostic(
            range=range_obj,
            message=self._format_message(finding),
            severity=severity,
            source="drill-sergeant",
            code=finding.code,
            related_information=[],
        )
        
        return diagnostic
    
    def _convert_severity(self, severity: str) -> DiagnosticSeverity:
        """Convert drill sergeant severity to LSP severity.
        
        Args:
            severity: Drill sergeant severity level
            
        Returns:
            LSP diagnostic severity
        """
        return self.SEVERITY_MAP.get(severity, DiagnosticSeverity.Warning)
    
    def _create_range(
        self, finding: Finding, document_lines: list[str] | None = None
    ) -> Range:
        """Create LSP range for a finding.
        
        Args:
            finding: The finding
            document_lines: Optional document lines for better positioning
            
        Returns:
            LSP range
        """
        # LSP uses 0-indexed line numbers
        line = max(0, finding.line_number - 1)
        
        # Default column positions
        start_col = finding.column_number or 0
        end_col = start_col
        
        # Try to get better column positioning from document lines
        if document_lines and line < len(document_lines):
            line_content = document_lines[line]
            
            # If we have a code snippet, try to find it in the line
            if finding.code_snippet:
                snippet_start = line_content.find(finding.code_snippet.strip())
                if snippet_start >= 0:
                    start_col = snippet_start
                    end_col = snippet_start + len(finding.code_snippet.strip())
            else:
                # Default to start of line for now
                start_col = 0
                end_col = len(line_content)
        
        # Handle multi-line findings
        end_line = line
        if finding.end_line_number:
            end_line = max(0, finding.end_line_number - 1)
        
        return Range(
            start=Position(line, start_col),
            end=Position(end_line, end_col),
        )
    
    def _format_message(self, finding: Finding) -> str:
        """Format finding message for LSP display.
        
        Args:
            finding: The finding
            
        Returns:
            Formatted message
        """
        message = finding.message
        
        # Add suggestion if available
        if finding.suggestion:
            message += f"\n💡 Suggestion: {finding.suggestion}"
        
        # Add confidence if low
        if finding.confidence < 0.8:
            confidence_pct = int(finding.confidence * 100)
            message += f"\n⚠️ Confidence: {confidence_pct}%"
        
        return message


# Global converter instance
_converter: DiagnosticConverter | None = None


def get_diagnostic_converter() -> DiagnosticConverter:
    """Get the global diagnostic converter instance.
    
    Returns:
        DiagnosticConverter instance
    """
    global _converter
    if _converter is None:
        _converter = DiagnosticConverter()
    return _converter