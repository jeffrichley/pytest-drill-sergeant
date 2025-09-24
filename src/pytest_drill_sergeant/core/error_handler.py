"""Error handling and reporting system for pytest-drill-sergeant.

This module provides comprehensive error handling, classification, and recovery
strategies for the analysis pipeline.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class ErrorCategory(str, Enum):
    """Categories of errors that can occur during analysis."""

    SYNTAX_ERROR = "syntax_error"
    ANALYSIS_ERROR = "analysis_error"
    CONFIGURATION_ERROR = "configuration_error"
    FILE_ACCESS_ERROR = "file_access_error"
    PERMISSION_ERROR = "permission_error"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    IMPORT_ERROR = "import_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ErrorContext:
    """Context information for an error."""

    file_path: Path | None = None
    line_number: int | None = None
    analyzer_name: str | None = None
    function_name: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    user_data: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass
class AnalysisError:
    """Represents an error that occurred during analysis."""

    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Exception | None = None
    context: ErrorContext | None = None
    suggestion: str | None = None
    recoverable: bool = True
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self) -> None:
        """Generate error ID if not provided."""
        if not self.error_id:
            self.error_id = (
                f"ERR_{self.category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )


class ErrorRecoveryStrategy(str, Enum):
    """Strategies for handling errors."""

    SKIP = "skip"
    RETRY = "retry"
    FALLBACK = "fallback"
    ABORT = "abort"


class ErrorHandler:
    """Centralized error handling and recovery system."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize the error handler.

        Args:
            logger: Logger instance for error reporting
        """
        self.logger = logger or logging.getLogger("drill_sergeant.error_handler")
        self.errors: list[AnalysisError] = []
        self.error_patterns: dict[str, ErrorCategory] = {}
        self.recovery_strategies: dict[ErrorCategory, ErrorRecoveryStrategy] = {}
        self._setup_default_patterns()
        self._setup_default_strategies()

    def _setup_default_patterns(self) -> None:
        """Set up default error pattern recognition."""
        self.error_patterns = {
            "SyntaxError": ErrorCategory.SYNTAX_ERROR,
            "IndentationError": ErrorCategory.SYNTAX_ERROR,
            "FileNotFoundError": ErrorCategory.FILE_ACCESS_ERROR,
            "PermissionError": ErrorCategory.PERMISSION_ERROR,
            "IsADirectoryError": ErrorCategory.FILE_ACCESS_ERROR,
            "NotADirectoryError": ErrorCategory.FILE_ACCESS_ERROR,
            "MemoryError": ErrorCategory.MEMORY_ERROR,
            "TimeoutError": ErrorCategory.TIMEOUT_ERROR,
            "ImportError": ErrorCategory.IMPORT_ERROR,
            "ModuleNotFoundError": ErrorCategory.IMPORT_ERROR,
            "ValueError": ErrorCategory.VALIDATION_ERROR,
            "TypeError": ErrorCategory.VALIDATION_ERROR,
            "KeyError": ErrorCategory.VALIDATION_ERROR,
            "RuntimeError": ErrorCategory.UNKNOWN_ERROR,
        }

    def _setup_default_strategies(self) -> None:
        """Set up default recovery strategies."""
        self.recovery_strategies = {
            ErrorCategory.SYNTAX_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.ANALYSIS_ERROR: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.CONFIGURATION_ERROR: ErrorRecoveryStrategy.ABORT,
            ErrorCategory.FILE_ACCESS_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.PERMISSION_ERROR: ErrorRecoveryStrategy.ABORT,
            ErrorCategory.MEMORY_ERROR: ErrorRecoveryStrategy.ABORT,
            ErrorCategory.TIMEOUT_ERROR: ErrorRecoveryStrategy.RETRY,
            ErrorCategory.IMPORT_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.VALIDATION_ERROR: ErrorRecoveryStrategy.SKIP,
            ErrorCategory.UNKNOWN_ERROR: ErrorRecoveryStrategy.RETRY,  # Changed from SKIP to RETRY
        }

    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext | None = None,
        analyzer_name: str | None = None,
    ) -> AnalysisError:
        """Handle an error and create an AnalysisError instance.

        Args:
            exception: The exception that occurred
            context: Additional context about the error
            analyzer_name: Name of the analyzer that failed

        Returns:
            AnalysisError instance with classification and recovery info
        """
        # Classify the error
        category = self._classify_error(exception)
        severity = self._determine_severity(category)

        # Create error context
        if context is None:
            context = ErrorContext()
        if analyzer_name:
            context.analyzer_name = analyzer_name

        # Generate suggestion
        suggestion = self._generate_suggestion(exception, category, context)

        # Create error instance
        error = AnalysisError(
            error_id="",  # Will be auto-generated
            category=category,
            severity=severity,
            message=str(exception),
            original_exception=exception,
            context=context,
            suggestion=suggestion,
            recoverable=self._is_recoverable(category),
        )

        # Add to error log
        self.errors.append(error)

        # Log the error
        self._log_error(error)

        return error

    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify an error based on its type.

        Args:
            exception: The exception to classify

        Returns:
            Error category
        """
        exception_type = type(exception).__name__
        return self.error_patterns.get(exception_type, ErrorCategory.UNKNOWN_ERROR)

    def _determine_severity(self, category: ErrorCategory) -> ErrorSeverity:
        """Determine the severity of an error.

        Args:
            category: Error category

        Returns:
            Error severity level
        """
        severity_mapping = {
            ErrorCategory.SYNTAX_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.ANALYSIS_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.CONFIGURATION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.FILE_ACCESS_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.PERMISSION_ERROR: ErrorSeverity.HIGH,
            ErrorCategory.MEMORY_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.IMPORT_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.UNKNOWN_ERROR: ErrorSeverity.HIGH,
        }
        return severity_mapping.get(category, ErrorSeverity.MEDIUM)

    def _generate_suggestion(
        self, exception: Exception, category: ErrorCategory, context: ErrorContext
    ) -> str | None:
        """Generate a helpful suggestion for fixing the error.

        Args:
            exception: The exception that occurred
            category: Error category
            context: Error context

        Returns:
            Suggestion string or None
        """
        suggestions = {
            ErrorCategory.SYNTAX_ERROR: "Check the file for syntax errors and fix them before running analysis.",
            ErrorCategory.ANALYSIS_ERROR: "The analyzer encountered an issue. Try running with verbose output for more details.",
            ErrorCategory.CONFIGURATION_ERROR: "Check your configuration file for invalid settings. Use --validate-config to verify.",
            ErrorCategory.FILE_ACCESS_ERROR: f"Check if the file exists and is readable: {context.file_path}",
            ErrorCategory.PERMISSION_ERROR: "Check file permissions and ensure you have read access to the file.",
            ErrorCategory.MEMORY_ERROR: "The analysis requires too much memory. Try analyzing fewer files at once.",
            ErrorCategory.TIMEOUT_ERROR: "The analysis timed out. Try increasing the timeout or analyzing smaller files.",
            ErrorCategory.IMPORT_ERROR: "A required module is missing. Check your Python environment and dependencies.",
            ErrorCategory.VALIDATION_ERROR: "The input data is invalid. Check the configuration format and try again.",
        }
        return suggestions.get(category)

    def _is_recoverable(self, category: ErrorCategory) -> bool:
        """Determine if an error is recoverable.

        Args:
            category: Error category

        Returns:
            True if the error is recoverable
        """
        non_recoverable = {
            ErrorCategory.CONFIGURATION_ERROR,
            ErrorCategory.PERMISSION_ERROR,
            ErrorCategory.MEMORY_ERROR,
        }
        return category not in non_recoverable

    def _log_error(self, error: AnalysisError) -> None:
        """Log an error with appropriate level.

        Args:
            error: The error to log
        """
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.DEBUG,
        }.get(error.severity, logging.ERROR)

        message = f"Error {error.error_id}: {error.message}"
        if error.context and error.context.file_path:
            message += f" in {error.context.file_path}"
        if error.suggestion:
            message += f" Suggestion: {error.suggestion}"

        self.logger.log(log_level, message, exc_info=error.original_exception)

    def get_recovery_strategy(self, error: AnalysisError) -> ErrorRecoveryStrategy:
        """Get the recovery strategy for an error.

        Args:
            error: The error to get strategy for

        Returns:
            Recovery strategy
        """
        return self.recovery_strategies.get(error.category, ErrorRecoveryStrategy.SKIP)

    def should_retry(self, error: AnalysisError) -> bool:
        """Determine if an error should be retried.

        Args:
            error: The error to check

        Returns:
            True if the error should be retried
        """
        if not error.recoverable:
            return False

        strategy = self.get_recovery_strategy(error)
        if strategy != ErrorRecoveryStrategy.RETRY:
            return False

        return error.retry_count < error.max_retries

    def increment_retry_count(self, error: AnalysisError) -> None:
        """Increment the retry count for an error.

        Args:
            error: The error to increment retry count for
        """
        error.retry_count += 1

    def get_error_summary(self) -> dict[str, str | int | float | bool]:
        """Get a summary of all errors.

        Returns:
            Dictionary with error statistics
        """
        if not self.errors:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}

        by_category = {}
        by_severity = {}

        for error in self.errors:
            # Count by category
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1

            # Count by severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_errors": len(self.errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "recoverable_errors": sum(1 for e in self.errors if e.recoverable),
            "critical_errors": sum(
                1 for e in self.errors if e.severity == ErrorSeverity.CRITICAL
            ),
        }

    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self.errors.clear()

    def get_errors_by_category(self, category: ErrorCategory) -> list[AnalysisError]:
        """Get all errors of a specific category.

        Args:
            category: Error category to filter by

        Returns:
            List of errors in the category
        """
        return [error for error in self.errors if error.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> list[AnalysisError]:
        """Get all errors of a specific severity.

        Args:
            severity: Error severity to filter by

        Returns:
            List of errors with the severity
        """
        return [error for error in self.errors if error.severity == severity]


class ErrorRecoveryManager:
    """Manages error recovery strategies and retry logic."""

    def __init__(self, error_handler: ErrorHandler) -> None:
        """Initialize the recovery manager.

        Args:
            error_handler: Error handler instance
        """
        self.error_handler = error_handler
        self.retry_delays = [1, 2, 5]  # seconds

    def execute_with_recovery(
        self,
        func: Callable[..., str | int | float | bool],
        *args: str | int | float | bool,
        **kwargs: str | int | float | bool,
    ) -> tuple[str | int | float | bool | None, AnalysisError | None]:
        """Execute a function with error recovery.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (result, error) where result is the function output or None
        """
        last_error = None

        for attempt in range(3):  # Max 3 attempts
            try:
                result = func(*args, **kwargs)
                return result, None
            except Exception as e:
                # Create error context
                context = ErrorContext()
                if len(args) > 0 and isinstance(args[0], Path):
                    context.file_path = args[0]

                # Handle the error (only create once)
                if last_error is None:
                    error = self.error_handler.handle_error(e, context)
                    last_error = error

                # Increment retry count for each attempt (including first)
                self.error_handler.increment_retry_count(last_error)

                # Check if we should retry
                if not self.error_handler.should_retry(last_error):
                    break

                # Wait before retry (except on last attempt)
                if attempt < 2:  # Don't wait after the last attempt
                    import time

                    time.sleep(self.retry_delays[attempt])

        return None, last_error


# Global error handler instance
_global_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance.

    Returns:
        Global error handler instance
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def create_error_context(
    file_path: Path | None = None,
    line_number: int | None = None,
    analyzer_name: str | None = None,
    function_name: str | None = None,
    **user_data: str | int | float | bool,
) -> ErrorContext:
    """Create an error context with the provided information.

    Args:
        file_path: Path to the file where error occurred
        line_number: Line number where error occurred
        analyzer_name: Name of the analyzer that failed
        function_name: Name of the function that failed
        **user_data: Additional user data

    Returns:
        ErrorContext instance
    """
    return ErrorContext(
        file_path=file_path,
        line_number=line_number,
        analyzer_name=analyzer_name,
        function_name=function_name,
        user_data=user_data,
    )
