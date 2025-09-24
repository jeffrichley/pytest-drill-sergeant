"""Tests for the LSP server implementation."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from lsprotocol.types import DiagnosticSeverity
from pygls.workspace import Document

from pytest_drill_sergeant.core.models import Finding, Severity
from pytest_drill_sergeant.lsp.diagnostics import DiagnosticConverter
from pytest_drill_sergeant.lsp.server import DrillSergeantLanguageServer


class TestDrillSergeantLanguageServer:
    """Test the Drill Sergeant Language Server."""

    def test_init(self) -> None:
        """Test server initialization."""
        with patch("pytest_drill_sergeant.lsp.server.create_analysis_pipeline"):
            with patch("pytest_drill_sergeant.core.config_context.initialize_config"):
                with patch("pytest_drill_sergeant.lsp.server.setup_standard_logging"):
                    server = DrillSergeantLanguageServer()
                    assert server is not None
                    assert server.analyzers is not None
                    assert server.config is not None

    def test_analyze_document_test_file(self) -> None:
        """Test analyzing a test file."""
        # Create a test file with violations
        test_code = """
import pytest
from myapp._internal import secret_function

def test_something():
    obj = SomeClass()
    obj._private_method()
    assert True
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_test.py", delete=False
        ) as f:
            f.write(test_code)
            f.flush()

            # Create mock document
            document = Mock(spec=Document)
            document.uri = f"file://{f.name}"

            # Mock analyzers to return findings
            mock_findings = [
                Finding(
                    code="DS301",
                    name="private_access",
                    severity=Severity.WARNING,
                    message="Importing private module: myapp._internal",
                    file_path=Path(f.name),
                    line_number=2,
                    column_number=0,
                    confidence=0.9,
                    fixable=False,
                    tags=["encapsulation"],
                    metadata={"violation_type": "private_import"},
                ),
                Finding(
                    code="DS301",
                    name="private_access",
                    severity=Severity.WARNING,
                    message="Calling private method: _private_method",
                    file_path=Path(f.name),
                    line_number=6,
                    column_number=4,
                    confidence=0.8,
                    fixable=False,
                    tags=["encapsulation"],
                    metadata={"violation_type": "private_method"},
                ),
            ]

            with patch(
                "pytest_drill_sergeant.lsp.server.create_analysis_pipeline"
            ) as mock_pipeline:
                mock_analyzers = Mock()
                mock_analyzers.analyzers = [Mock()]
                mock_analyzers.analyzers[0].analyze_file.return_value = mock_findings
                mock_pipeline.return_value = mock_analyzers

                with patch(
                    "pytest_drill_sergeant.core.config_context.initialize_config"
                ):
                    with patch(
                        "pytest_drill_sergeant.lsp.server.setup_standard_logging"
                    ):
                        server = DrillSergeantLanguageServer()
                        diagnostics = server.analyze_document(document)

                    # Should find 2 diagnostics
                    assert len(diagnostics) == 2

                    # Check first diagnostic
                    diag1 = diagnostics[0]
                    assert diag1.code == "DS301"
                    assert diag1.severity == DiagnosticSeverity.Warning
                    assert "Importing private module" in diag1.message
                    assert diag1.source == "drill-sergeant"

                    # Check second diagnostic
                    diag2 = diagnostics[1]
                    assert diag2.code == "DS301"
                    assert diag2.severity == DiagnosticSeverity.Warning
                    assert "Calling private method" in diag2.message

    def test_analyze_document_non_test_file(self) -> None:
        """Test analyzing a non-test file (should return empty)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello world')")
            f.flush()

            # Create mock document
            document = Mock(spec=Document)
            document.uri = f"file://{f.name}"

            with patch("pytest_drill_sergeant.lsp.server.create_analysis_pipeline"):
                with patch(
                    "pytest_drill_sergeant.core.config_context.initialize_config"
                ):
                    with patch(
                        "pytest_drill_sergeant.lsp.server.setup_standard_logging"
                    ):
                        server = DrillSergeantLanguageServer()
                        diagnostics = server.analyze_document(document)

                        # Should return empty for non-test files
                        assert len(diagnostics) == 0

    def test_convert_severity(self) -> None:
        """Test severity conversion."""
        with patch("pytest_drill_sergeant.lsp.server.create_analysis_pipeline"):
            with patch("pytest_drill_sergeant.core.config_context.initialize_config"):
                with patch("pytest_drill_sergeant.lsp.server.setup_standard_logging"):
                    server = DrillSergeantLanguageServer()

                    assert server._convert_severity("error") == DiagnosticSeverity.Error
                    assert (
                        server._convert_severity("warning")
                        == DiagnosticSeverity.Warning
                    )
                    assert (
                        server._convert_severity("info")
                        == DiagnosticSeverity.Information
                    )
                    assert server._convert_severity("hint") == DiagnosticSeverity.Hint
                    assert (
                        server._convert_severity("unknown")
                        == DiagnosticSeverity.Warning
                    )

    def test_is_test_file(self) -> None:
        """Test test file detection."""
        with patch("pytest_drill_sergeant.lsp.server.create_analysis_pipeline"):
            with patch("pytest_drill_sergeant.core.config_context.initialize_config"):
                with patch("pytest_drill_sergeant.lsp.server.setup_standard_logging"):
                    server = DrillSergeantLanguageServer()

                    # Test files
                    assert server._is_test_file(Path("test_something.py"))
                    assert server._is_test_file(Path("something_test.py"))
                    assert server._is_test_file(Path("tests/test_file.py"))
                    assert server._is_test_file(Path("test/test_file.py"))

                    # Non-test files
                    assert not server._is_test_file(Path("regular_file.py"))
                    assert not server._is_test_file(Path("src/module.py"))


class TestDiagnosticConverter:
    """Test the diagnostic converter."""

    def test_init(self) -> None:
        """Test converter initialization."""
        converter = DiagnosticConverter()
        assert converter is not None
        assert converter.SEVERITY_MAP is not None

    def test_convert_findings(self) -> None:
        """Test converting findings to diagnostics."""
        findings = [
            Finding(
                code="DS301",
                name="private_access",
                severity=Severity.WARNING,
                message="Test finding",
                file_path=Path("test.py"),
                line_number=5,
                column_number=10,
                confidence=0.9,
                fixable=False,
                tags=["test"],
                metadata={},
            ),
        ]

        converter = DiagnosticConverter()
        diagnostics = converter.convert_findings(findings)

        assert len(diagnostics) == 1
        diag = diagnostics[0]
        assert diag.code == "DS301"
        assert diag.severity == DiagnosticSeverity.Warning
        assert diag.message == "Test finding"
        assert diag.source == "drill-sergeant"
        assert diag.range.start.line == 4  # 0-indexed
        assert diag.range.start.character == 10

    def test_convert_severity(self) -> None:
        """Test severity conversion."""
        converter = DiagnosticConverter()

        assert converter._convert_severity("error") == DiagnosticSeverity.Error
        assert converter._convert_severity("warning") == DiagnosticSeverity.Warning
        assert converter._convert_severity("info") == DiagnosticSeverity.Information
        assert converter._convert_severity("hint") == DiagnosticSeverity.Hint
        assert converter._convert_severity("unknown") == DiagnosticSeverity.Warning

    def test_format_message_with_suggestion(self) -> None:
        """Test message formatting with suggestion."""
        finding = Finding(
            code="DS301",
            name="private_access",
            severity=Severity.WARNING,
            message="Test finding",
            file_path=Path("test.py"),
            line_number=1,
            suggestion="Use public API",
            confidence=0.7,
            fixable=False,
            tags=["test"],
            metadata={},
        )

        converter = DiagnosticConverter()
        message = converter._format_message(finding)

        assert "Test finding" in message
        assert "💡 Suggestion: Use public API" in message
        assert "⚠️ Confidence: 70%" in message
