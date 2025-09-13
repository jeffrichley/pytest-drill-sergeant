"""Logging utilities for pytest-drill-sergeant."""

import logging
import os
import sys

try:
    import rich.logging
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
    )

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def is_cli_mode() -> bool:
    """Detect if we're running as a CLI tool vs library/plugin."""
    # Check if we're in pytest context
    if "pytest" in sys.modules:
        return False

    # Check environment variables
    if os.getenv("PYTEST_DRILL_SERGEANT_PLUGIN_MODE"):
        return False

    # Check command line args
    if any(arg in sys.argv for arg in ["--pytest-plugin", "--library-mode"]):
        return False

    # Check if we're running as a CLI (either direct script or module)
    if len(sys.argv) > 0:
        script_name = sys.argv[0]
        # Check if we're running the CLI by looking at the script path
        # When running with -m, sys.argv[0] will be the __main__.py path
        return script_name.endswith(("drill-sergeant", "main.py", "__main__.py")) or (
            "-m" in sys.argv and "pytest_drill_sergeant" in sys.argv
        )

    return False


def setup_logging(use_rich: bool = True, level: int = logging.INFO) -> None:
    """Set up logging based on context.

    Args:
        use_rich: Whether to attempt to use rich logging
        level: Logging level to use
    """
    if use_rich and is_cli_mode():
        setup_rich_logging(level=level)
    else:
        setup_standard_logging(level=level)


def setup_rich_logging(level: int = logging.INFO) -> None:
    """Set up rich logging for CLI mode."""
    if not RICH_AVAILABLE:
        # Rich not available, fall back to standard logging
        setup_standard_logging(level=level)
        return

    # Create rich handler
    rich_handler = rich.logging.RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(message)s",  # Rich handles formatting
        handlers=[rich_handler],
        force=True,  # Override any existing configuration
    )


def setup_standard_logging(level: int = logging.INFO) -> None:
    """Set up standard logging for library/plugin mode."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,  # Override any existing configuration
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    This is a convenience function that ensures logging is set up
    and returns a logger with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def create_progress_logger(_logger: logging.Logger) -> object | None:
    """Create a progress logger if rich is available.

    Args:
        _logger: Base logger instance (unused but kept for API consistency)

    Returns:
        Rich Progress instance if available, None otherwise
    """
    if not RICH_AVAILABLE:
        return None

    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=None,  # Use default console
        transient=False,
    )
