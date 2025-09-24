"""Main entry point for the drill sergeant LSP server.

This module provides the main entry point for running the language server
as a standalone process that can be used by IDEs.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from pygls.server import LanguageServer
from lsprotocol.types import (
    InitializeParams,
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind,
)

from pytest_drill_sergeant import __version__
from pytest_drill_sergeant.lsp import (
    DrillSergeantLanguageServer,
    setup_file_watching,
)

logger = logging.getLogger(__name__)


def create_server() -> DrillSergeantLanguageServer:
    """Create and configure the drill sergeant language server.
    
    Returns:
        Configured DrillSergeantLanguageServer instance
    """
    # Create server
    server = DrillSergeantLanguageServer()
    
    # Set up file watching
    setup_file_watching(server)
    
    # Configure server capabilities
    @server.feature("initialize")
    def initialize(ls: DrillSergeantLanguageServer, params: InitializeParams) -> InitializeResult:
        """Initialize the language server."""
        logger.info("Initializing drill sergeant language server")
        
        # Configure server capabilities
        capabilities = ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Full,
            diagnostic_provider=True,
        )
        
        return InitializeResult(
            capabilities=capabilities,
            server_info={
                "name": "drill-sergeant-lsp",
                "version": __version__,
            },
        )
    
    @server.feature("initialized")
    def initialized(ls: DrillSergeantLanguageServer, params: Any) -> None:
        """Handle initialized notification."""
        logger.info("Drill sergeant language server initialized")
    
    return server


async def main() -> None:
    """Main entry point for the LSP server."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        logger.info("Starting drill sergeant language server")
        
        # Create and run server
        server = create_server()
        
        # Run the server
        await server.start_io()
        
    except Exception as e:
        logger.error(f"Failed to start language server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_server() -> None:
    """Run the LSP server, handling existing event loops."""
    try:
        # Set up logging first
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        
        logger.info("Starting drill sergeant language server")
        
        # Create server
        server = create_server()
        
        # Use pygls's built-in event loop handling
        # This should handle existing event loops properly
        server.start_io()
        
    except Exception as e:
        logger.error(f"Failed to start language server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the server with proper event loop handling
    run_server()