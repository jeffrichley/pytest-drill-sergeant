"""Language Server Protocol integration for pytest-drill-sergeant.

This module provides LSP server functionality for real-time IDE integration,
allowing drill sergeant findings to appear as error squiggles and diagnostics
in supported editors like VS Code.
"""

from pytest_drill_sergeant.lsp.config import LSPConfig, get_lsp_config
from pytest_drill_sergeant.lsp.diagnostics import (
    DiagnosticConverter,
    get_diagnostic_converter,
)
from pytest_drill_sergeant.lsp.file_watcher import FileWatcher, setup_file_watching
from pytest_drill_sergeant.lsp.server import (
    DrillSergeantLanguageServer,
    create_language_server,
    get_language_server,
)

__all__: list[str] = [
    "DiagnosticConverter",
    "DrillSergeantLanguageServer",
    "FileWatcher",
    "LSPConfig",
    "create_language_server",
    "get_diagnostic_converter",
    "get_language_server",
    "get_lsp_config",
    "setup_file_watching",
]
