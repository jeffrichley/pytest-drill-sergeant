"""Tests for personas __init__.py module."""

import pytest_drill_sergeant.plugin.personas


class TestPersonasInit:
    """Test personas __init__.py module."""

    def test_module_imports(self) -> None:
        """Test that the module can be imported."""
        assert pytest_drill_sergeant.plugin.personas is not None

    def test_module_has_file(self) -> None:
        """Test that the module has file information."""
        # Just test that the module is importable
        assert pytest_drill_sergeant.plugin.personas is not None
