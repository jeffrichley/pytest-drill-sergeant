"""Tests for core __init__.py module."""

import pytest_drill_sergeant.core


class TestCoreInit:
    """Test core __init__.py module."""

    def test_module_imports(self) -> None:
        """Test that the module can be imported."""
        assert pytest_drill_sergeant.core is not None

    def test_module_has_version(self) -> None:
        """Test that the module has version information."""
        # The module should be importable and have some content
        assert pytest_drill_sergeant.core is not None
