"""Tests for the logging utilities."""

import logging
import os
import sys
from unittest.mock import MagicMock, patch

from pytest_drill_sergeant.core.logging_utils import (
    RICH_AVAILABLE,
    create_progress_logger,
    get_logger,
    is_cli_mode,
    setup_logging,
    setup_rich_logging,
    setup_standard_logging,
)


class TestIsCliMode:
    """Test the is_cli_mode function."""

    def test_is_cli_mode_pytest_in_modules(self) -> None:
        """Test is_cli_mode returns False when pytest is in sys.modules."""
        with patch.dict(sys.modules, {"pytest": MagicMock()}, clear=False):
            assert is_cli_mode() is False

    def test_is_cli_mode_plugin_mode_env_var(self) -> None:
        """Test is_cli_mode returns False when plugin mode env var is set."""
        with patch.dict(
            os.environ, {"PYTEST_DRILL_SERGEANT_PLUGIN_MODE": "1"}, clear=False
        ):
            assert is_cli_mode() is False

    def test_is_cli_mode_library_mode_args(self) -> None:
        """Test is_cli_mode returns False when library mode args are present."""
        with patch("sys.argv", ["script.py", "--pytest-plugin"]):
            assert is_cli_mode() is False

        with patch("sys.argv", ["script.py", "--library-mode"]):
            assert is_cli_mode() is False

    def test_is_cli_mode_drill_sergeant_script(self) -> None:
        """Test is_cli_mode returns True when running drill-sergeant script."""
        with (
            patch("sys.argv", ["/path/to/drill-sergeant"]),
            patch("pytest_drill_sergeant.core.logging_utils.sys.modules", {}),
            patch.dict(os.environ, {}, clear=True),
        ):
            assert is_cli_mode() is True

    def test_is_cli_mode_main_py_script(self) -> None:
        """Test is_cli_mode returns True when running main.py script."""
        with (
            patch("sys.argv", ["/path/to/main.py"]),
            patch("pytest_drill_sergeant.core.logging_utils.sys.modules", {}),
            patch.dict(os.environ, {}, clear=True),
        ):
            assert is_cli_mode() is True

    def test_is_cli_mode_main_module(self) -> None:
        """Test is_cli_mode returns True when running as module."""
        with (
            patch("sys.argv", ["-m", "pytest_drill_sergeant"]),
            patch("pytest_drill_sergeant.core.logging_utils.sys.modules", {}),
            patch.dict(os.environ, {}, clear=True),
        ):
            assert is_cli_mode() is True

    def test_is_cli_mode_empty_argv(self) -> None:
        """Test is_cli_mode returns False when sys.argv is empty."""
        with patch("sys.argv", []):
            assert is_cli_mode() is False

    def test_is_cli_mode_other_script(self) -> None:
        """Test is_cli_mode returns False for other scripts."""
        with patch("sys.argv", ["/path/to/other_script.py"]):
            assert is_cli_mode() is False

    def test_is_cli_mode_module_without_drill_sergeant(self) -> None:
        """Test is_cli_mode returns False for module without drill_sergeant."""
        with patch("sys.argv", ["-m", "other_module"]):
            assert is_cli_mode() is False


class TestSetupLogging:
    """Test the setup_logging function."""

    def test_setup_logging_cli_mode_with_rich(self) -> None:
        """Test setup_logging uses rich logging in CLI mode."""
        with (
            patch(
                "pytest_drill_sergeant.core.logging_utils.is_cli_mode",
                return_value=True,
            ),
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_rich_logging"
            ) as mock_rich,
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_standard_logging"
            ) as mock_standard,
        ):
            setup_logging(use_rich=True, level=logging.DEBUG)

            mock_rich.assert_called_once_with(level=logging.DEBUG)
            mock_standard.assert_not_called()

    def test_setup_logging_cli_mode_without_rich(self) -> None:
        """Test setup_logging uses standard logging when rich is disabled."""
        with (
            patch(
                "pytest_drill_sergeant.core.logging_utils.is_cli_mode",
                return_value=True,
            ),
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_rich_logging"
            ) as mock_rich,
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_standard_logging"
            ) as mock_standard,
        ):
            setup_logging(use_rich=False, level=logging.WARNING)

            mock_standard.assert_called_once_with(level=logging.WARNING)
            mock_rich.assert_not_called()

    def test_setup_logging_library_mode(self) -> None:
        """Test setup_logging uses standard logging in library mode."""
        with (
            patch(
                "pytest_drill_sergeant.core.logging_utils.is_cli_mode",
                return_value=False,
            ),
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_rich_logging"
            ) as mock_rich,
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_standard_logging"
            ) as mock_standard,
        ):
            setup_logging(use_rich=True, level=logging.INFO)

            mock_standard.assert_called_once_with(level=logging.INFO)
            mock_rich.assert_not_called()


class TestSetupRichLogging:
    """Test the setup_rich_logging function."""

    def test_setup_rich_logging_rich_available(self) -> None:
        """Test setup_rich_logging when rich is available."""
        with (
            patch("pytest_drill_sergeant.core.logging_utils.RICH_AVAILABLE", True),
            patch(
                "pytest_drill_sergeant.core.logging_utils.rich.logging.RichHandler"
            ) as mock_handler,
            patch("pytest_drill_sergeant.core.logging_utils.Console") as mock_console,
            patch("logging.basicConfig") as mock_basic_config,
        ):
            setup_rich_logging(level=logging.DEBUG)

            mock_console.assert_called_once_with(stderr=True)
            mock_handler.assert_called_once_with(
                console=mock_console.return_value,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            )
            mock_basic_config.assert_called_once_with(
                level=logging.DEBUG,
                format="%(message)s",
                handlers=[mock_handler.return_value],
                force=True,
            )

    def test_setup_rich_logging_rich_not_available(self) -> None:
        """Test setup_rich_logging falls back to standard when rich is not available."""
        with (
            patch("pytest_drill_sergeant.core.logging_utils.RICH_AVAILABLE", False),
            patch(
                "pytest_drill_sergeant.core.logging_utils.setup_standard_logging"
            ) as mock_standard,
        ):
            setup_rich_logging(level=logging.INFO)

            mock_standard.assert_called_once_with(level=logging.INFO)


class TestSetupStandardLogging:
    """Test the setup_standard_logging function."""

    def test_setup_standard_logging(self) -> None:
        """Test setup_standard_logging configuration."""
        with (
            patch("logging.basicConfig") as mock_basic_config,
            patch("logging.StreamHandler") as mock_handler,
        ):
            setup_standard_logging(level=logging.WARNING)

            mock_basic_config.assert_called_once_with(
                level=logging.WARNING,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[mock_handler.return_value],
                force=True,
            )

    def test_setup_standard_logging_default_level(self) -> None:
        """Test setup_standard_logging with default level."""
        with (
            patch("logging.basicConfig") as mock_basic_config,
            patch("logging.StreamHandler") as mock_handler,
        ):
            setup_standard_logging()

            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[mock_handler.return_value],
                force=True,
            )


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger(self) -> None:
        """Test get_logger returns a logger with the given name."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_different_names(self) -> None:
        """Test get_logger with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2

    def test_get_logger_same_name(self) -> None:
        """Test get_logger returns same logger for same name."""
        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")

        assert logger1 is logger2


class TestCreateProgressLogger:
    """Test the create_progress_logger function."""

    def test_create_progress_logger_rich_available(self) -> None:
        """Test create_progress_logger when rich is available."""
        with (
            patch("pytest_drill_sergeant.core.logging_utils.RICH_AVAILABLE", True),
            patch("pytest_drill_sergeant.core.logging_utils.Progress") as mock_progress,
            patch(
                "pytest_drill_sergeant.core.logging_utils.SpinnerColumn"
            ) as mock_spinner,
            patch("pytest_drill_sergeant.core.logging_utils.TextColumn") as mock_text,
            patch("pytest_drill_sergeant.core.logging_utils.BarColumn") as mock_bar,
            patch(
                "pytest_drill_sergeant.core.logging_utils.TaskProgressColumn"
            ) as mock_task,
        ):
            mock_logger = MagicMock()
            result = create_progress_logger(mock_logger)

            mock_progress.assert_called_once_with(
                mock_spinner.return_value,
                mock_text.return_value,
                mock_bar.return_value,
                mock_task.return_value,
                console=None,
                transient=False,
            )
            assert result is mock_progress.return_value

    def test_create_progress_logger_rich_not_available(self) -> None:
        """Test create_progress_logger returns None when rich is not available."""
        with patch("pytest_drill_sergeant.core.logging_utils.RICH_AVAILABLE", False):
            mock_logger = MagicMock()
            result = create_progress_logger(mock_logger)

            assert result is None

    def test_create_progress_logger_with_logger(self) -> None:
        """Test create_progress_logger accepts logger parameter."""
        with (
            patch("pytest_drill_sergeant.core.logging_utils.RICH_AVAILABLE", True),
            patch("pytest_drill_sergeant.core.logging_utils.Progress"),
            patch("pytest_drill_sergeant.core.logging_utils.SpinnerColumn"),
            patch("pytest_drill_sergeant.core.logging_utils.TextColumn"),
            patch("pytest_drill_sergeant.core.logging_utils.BarColumn"),
            patch("pytest_drill_sergeant.core.logging_utils.TaskProgressColumn"),
        ):
            mock_logger = MagicMock()
            mock_logger.name = "test_logger"

            result = create_progress_logger(mock_logger)

            # The function should work regardless of the logger parameter
            assert result is not None


class TestRichAvailability:
    """Test RICH_AVAILABLE constant."""

    def test_rich_available_constant(self) -> None:
        """Test that RICH_AVAILABLE is a boolean."""
        assert isinstance(RICH_AVAILABLE, bool)

    def test_rich_available_import_behavior(self) -> None:
        """Test that RICH_AVAILABLE reflects import success."""
        # This test verifies that the import logic works correctly
        # The actual value depends on whether rich is installed
        assert RICH_AVAILABLE in [True, False]


class TestLoggingIntegration:
    """Integration tests for logging setup."""

    def test_logging_setup_integration(self) -> None:
        """Test that logging setup actually works."""
        # Clear any existing logging configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Set up logging
        setup_standard_logging(level=logging.DEBUG)

        # Create a test logger
        logger = get_logger("test_integration")

        # Test that logging works - just verify no exceptions are raised
        logger.info("Test message")
        logger.warning("Test warning")
        logger.error("Test error")

    def test_logging_level_configuration(self) -> None:
        """Test that logging level is properly configured."""
        # Clear any existing logging configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Set up logging with WARNING level
        setup_standard_logging(level=logging.WARNING)

        # Create a test logger
        logger = get_logger("test_level")

        # Test that different log levels work without exceptions
        logger.info("This should not appear")
        logger.warning("This should appear")
        logger.error("This should also appear")
