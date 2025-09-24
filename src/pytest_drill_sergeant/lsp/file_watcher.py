"""File watching and analysis hooks for LSP integration.

This module handles file system events and triggers analysis
when test files are opened, saved, or modified.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from lsprotocol.types import TextDocumentSyncKind
from pygls.workspace import Document

if TYPE_CHECKING:
    from pytest_drill_sergeant.lsp.server import DrillSergeantLanguageServer

logger = logging.getLogger(__name__)


class FileWatcher:
    """Handles file watching and analysis triggers for the LSP server."""

    def __init__(self, server: DrillSergeantLanguageServer) -> None:
        """Initialize the file watcher.

        Args:
            server: The language server instance
        """
        self.server = server
        self.logger = logging.getLogger(f"{__name__}.FileWatcher")

        # Track which files we're analyzing to avoid duplicates
        self._analyzing_files: set[str] = set()

    def on_document_open(self, document: Document) -> None:
        """Handle document open event.

        Args:
            document: The opened document
        """
        self.logger.debug("Document opened: %s", document.uri)
        self._analyze_document_if_needed(document)

    def on_document_save(self, document: Document) -> None:
        """Handle document save event.

        Args:
            document: The saved document
        """
        self.logger.debug("Document saved: %s", document.uri)
        self._analyze_document_if_needed(document)

    def on_document_change(self, document: Document) -> None:
        """Handle document change event.

        Args:
            document: The changed document
        """
        # For now, we'll analyze on save rather than on every change
        # to avoid performance issues with large files

    def _analyze_document_if_needed(self, document: Document) -> None:
        """Analyze a document if it's a test file and not already being analyzed.

        Args:
            document: The document to potentially analyze
        """
        try:
            # Check if we should analyze this file
            if not self._should_analyze_document(document):
                return

            # Avoid duplicate analysis
            if document.uri in self._analyzing_files:
                return

            # Mark as analyzing
            self._analyzing_files.add(document.uri)

            try:
                # Analyze the document
                diagnostics = self.server.analyze_document(document)

                # Publish diagnostics to the client
                self.server.publish_diagnostics(document.uri, diagnostics)

                self.logger.debug(
                    "Published %d diagnostics for %s", len(diagnostics), document.uri
                )

            finally:
                # Remove from analyzing set
                self._analyzing_files.discard(document.uri)

        except Exception as e:
            self.logger.error("Failed to analyze document %s: %s", document.uri, e)
            # Clean up on error
            self._analyzing_files.discard(document.uri)

    def _should_analyze_document(self, document: Document) -> bool:
        """Check if a document should be analyzed.

        Args:
            document: The document to check

        Returns:
            True if the document should be analyzed
        """
        try:
            # Convert URI to file path
            file_path = Path(document.uri.replace("file://", ""))

            # Only analyze Python files
            if file_path.suffix != ".py":
                return False

            # Check if it's a test file
            return self._is_test_file(file_path)

        except Exception as e:
            self.logger.warning("Failed to check if document should be analyzed: %s", e)
            return False

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to the file

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


def setup_file_watching(server: DrillSergeantLanguageServer) -> FileWatcher:
    """Set up file watching for the language server.

    Args:
        server: The language server instance

    Returns:
        Configured FileWatcher instance
    """
    file_watcher = FileWatcher(server)

    # Set up LSP event handlers
    @server.feature("textDocument/didOpen")
    def did_open(ls: DrillSergeantLanguageServer, params):
        """Handle document open event."""
        document = ls.workspace.get_document(params.text_document.uri)
        file_watcher.on_document_open(document)

    @server.feature("textDocument/didSave")
    def did_save(ls: DrillSergeantLanguageServer, params):
        """Handle document save event."""
        document = ls.workspace.get_document(params.text_document.uri)
        file_watcher.on_document_save(document)

    @server.feature("textDocument/didChange")
    def did_change(ls: DrillSergeantLanguageServer, params):
        """Handle document change event."""
        document = ls.workspace.get_document(params.text_document.uri)
        file_watcher.on_document_change(document)

    # Configure text document sync
    server.text_document_sync_kind = TextDocumentSyncKind.Full

    logger.info("File watching configured for drill sergeant LSP server")

    return file_watcher
