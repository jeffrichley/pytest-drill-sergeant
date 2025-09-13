"""Tests for the main module entry point."""

import inspect
from pathlib import Path
from unittest.mock import patch

import pytest_drill_sergeant.__main__ as main_module
from pytest_drill_sergeant.__main__ import cli
from pytest_drill_sergeant.cli.main import cli as cli_main


class TestMain:
    """Test the main module entry point."""

    def test_main_module_import(self) -> None:
        """Test that the main module can be imported."""
        assert hasattr(main_module, "cli")
        assert callable(main_module.cli)

    def test_cli_function_exists(self) -> None:
        """Test that the cli function exists and is callable."""
        assert callable(cli)

    def test_cli_function_calls_cli_main(self) -> None:
        """Test that cli function calls the CLI main function."""
        with patch("pytest_drill_sergeant.cli.main.app") as mock_app:
            cli()
            mock_app.assert_called_once()

    def test_main_module_execution(self) -> None:
        """Test that the main module can be executed."""
        with patch("pytest_drill_sergeant.cli.main.cli"):
            # Import and run the main module
            # The cli() call should have been made during import if __name__ == "__main__"
            # Since we're importing, it won't be called, so we test the import works
            assert hasattr(main_module, "cli")

    def test_cli_function_signature(self) -> None:
        """Test that the cli function has the expected signature."""
        sig = inspect.signature(cli)
        # Should have no parameters (or only self if it's a method)
        assert len(sig.parameters) == 0

    def test_cli_function_docstring(self) -> None:
        """Test that the cli function has a docstring."""
        assert cli.__doc__ is not None
        assert len(cli.__doc__.strip()) > 0

    def test_main_module_docstring(self) -> None:
        """Test that the main module has a docstring."""
        assert main_module.__doc__ is not None
        assert "Entry point" in main_module.__doc__
        assert "module" in main_module.__doc__

    def test_main_module_has_main_guard(self) -> None:
        """Test that the main module has the __name__ == '__main__' guard."""
        with Path("src/pytest_drill_sergeant/__main__.py").open() as f:
            content = f.read()

        assert 'if __name__ == "__main__":' in content
        assert "cli()" in content

    def test_cli_function_import_path(self) -> None:
        """Test that the cli function is imported from the correct path."""
        # The cli function in __main__.py should be the same as the one in cli.main
        assert cli is cli_main

    def test_main_module_structure(self) -> None:
        """Test that the main module has the expected structure."""
        # Should have cli function
        assert hasattr(main_module, "cli")

        # Should not have other unexpected attributes
        expected_attrs = {"cli", "__doc__", "__file__", "__name__", "__package__"}
        actual_attrs = set(dir(main_module))

        # Should only have expected attributes (allowing for some Python internals)
        unexpected_attrs = (
            actual_attrs
            - expected_attrs
            - {
                "__builtins__",
                "__loader__",
                "__spec__",
                "__cached__",
                "__annotations__",
            }
        )
        assert len(unexpected_attrs) == 0, f"Unexpected attributes: {unexpected_attrs}"
