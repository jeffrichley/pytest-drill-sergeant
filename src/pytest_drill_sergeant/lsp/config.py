"""Configuration management for LSP integration.

This module handles LSP-specific configuration and integrates
with the main drill sergeant configuration system.
"""

from __future__ import annotations

import logging
from typing import Any

from pytest_drill_sergeant.core.config_context import get_config

logger = logging.getLogger(__name__)


class LSPConfig:
    """Configuration for LSP server functionality."""

    def __init__(self) -> None:
        """Initialize LSP configuration."""
        self.logger = logging.getLogger(f"{__name__}.LSPConfig")
        self._config = get_config()

    def get_analysis_enabled(self) -> bool:
        """Check if analysis is enabled for LSP.

        Returns:
            True if analysis should be performed
        """
        # For now, always enable analysis
        # Later we can add LSP-specific configuration
        return True

    def get_analysis_delay(self) -> float:
        """Get the delay before analyzing a file after changes.

        Returns:
            Delay in seconds
        """
        # Default delay to avoid analyzing on every keystroke
        return 0.5

    def get_max_diagnostics(self) -> int:
        """Get the maximum number of diagnostics to show per file.

        Returns:
            Maximum number of diagnostics
        """
        # Limit diagnostics to avoid overwhelming the IDE
        return 100

    def get_enabled_analyzers(self) -> list[str]:
        """Get list of enabled analyzers for LSP.

        Returns:
            List of analyzer names
        """
        # For now, enable all analyzers
        # Later we can add LSP-specific analyzer configuration
        return [
            "private_access",
            "mock_overspecification",
            "structural_equality",
            "aaa_comment",
        ]

    def get_severity_threshold(self) -> str:
        """Get the minimum severity level to show in LSP.

        Returns:
            Minimum severity level
        """
        # Show all severities by default
        return "hint"

    def get_persona_for_lsp(self) -> str:
        """Get the persona to use for LSP messages.

        Returns:
            Persona name
        """
        # Use drill sergeant persona for LSP
        return "drill_sergeant"

    def get_lsp_specific_config(self) -> dict[str, Any]:
        """Get LSP-specific configuration.

        Returns:
            Dictionary of LSP configuration options
        """
        return {
            "analysis_enabled": self.get_analysis_enabled(),
            "analysis_delay": self.get_analysis_delay(),
            "max_diagnostics": self.get_max_diagnostics(),
            "enabled_analyzers": self.get_enabled_analyzers(),
            "severity_threshold": self.get_severity_threshold(),
            "persona": self.get_persona_for_lsp(),
        }


# Global LSP config instance
_lsp_config: LSPConfig | None = None


def get_lsp_config() -> LSPConfig:
    """Get the global LSP configuration instance.

    Returns:
        LSPConfig instance
    """
    global _lsp_config
    if _lsp_config is None:
        _lsp_config = LSPConfig()
    return _lsp_config
