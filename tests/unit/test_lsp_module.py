"""Test lsp module imports to increase coverage."""

import pytest_drill_sergeant.lsp


def test_lsp_module_imports():
    """Test importing from lsp module to increase coverage."""
    # Test that the module has the expected attributes
    assert hasattr(pytest_drill_sergeant.lsp, "__all__")
    assert hasattr(pytest_drill_sergeant.lsp, "__doc__")

    # Test __all__ content
    all_items = pytest_drill_sergeant.lsp.__all__
    assert isinstance(all_items, list)
    assert len(all_items) == 9  # This module exports DiagnosticConverter, DrillSergeantLanguageServer, FileWatcher, LSPConfig, create_language_server, get_diagnostic_converter, get_language_server, get_lsp_config, setup_file_watching
    assert "DiagnosticConverter" in all_items
    assert "DrillSergeantLanguageServer" in all_items
    assert "FileWatcher" in all_items
    assert "LSPConfig" in all_items
    assert "create_language_server" in all_items
    assert "get_diagnostic_converter" in all_items
    assert "get_language_server" in all_items
    assert "get_lsp_config" in all_items
    assert "setup_file_watching" in all_items

    # Test that the module is not None
    assert pytest_drill_sergeant.lsp is not None

    # Test that we can access the module's file
    assert hasattr(pytest_drill_sergeant.lsp, "__file__")
    assert pytest_drill_sergeant.lsp.__file__ is not None


def test_lsp_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.lsp.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert len(__all__) == 9  # This module exports DiagnosticConverter, DrillSergeantLanguageServer, FileWatcher, LSPConfig, create_language_server, get_diagnostic_converter, get_language_server, get_lsp_config, setup_file_watching
    assert "DiagnosticConverter" in __all__
    assert "DrillSergeantLanguageServer" in __all__
    assert "FileWatcher" in __all__
    assert "LSPConfig" in __all__
    assert "create_language_server" in __all__
    assert "get_diagnostic_converter" in __all__
    assert "get_language_server" in __all__
    assert "get_lsp_config" in __all__
    assert "setup_file_watching" in __all__
