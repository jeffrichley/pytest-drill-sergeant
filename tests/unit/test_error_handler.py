"""Tests for the error handling system."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pytest_drill_sergeant.core.error_handler import (
    AnalysisError,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorRecoveryManager,
    ErrorSeverity,
    ErrorRecoveryStrategy,
    create_error_context,
    get_error_handler,
)


class TestErrorContext:
    """Test ErrorContext functionality."""

    def test_create_error_context_basic(self):
        """Test creating basic error context."""
        context = create_error_context()
        assert context.file_path is None
        assert context.line_number is None
        assert context.analyzer_name is None
        assert context.function_name is None
        assert context.user_data == {}

    def test_create_error_context_with_data(self):
        """Test creating error context with data."""
        context = create_error_context(
            file_path=Path("test.py"),
            line_number=42,
            analyzer_name="test_analyzer",
            function_name="test_function",
            custom_data="value"
        )
        assert context.file_path == Path("test.py")
        assert context.line_number == 42
        assert context.analyzer_name == "test_analyzer"
        assert context.function_name == "test_function"
        assert context.user_data["custom_data"] == "value"


class TestAnalysisError:
    """Test AnalysisError functionality."""

    def test_analysis_error_creation(self):
        """Test creating an analysis error."""
        context = create_error_context(analyzer_name="test_analyzer")
        error = AnalysisError(
            error_id="TEST_001",
            category=ErrorCategory.ANALYSIS_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            context=context,
            suggestion="Test suggestion",
            recoverable=True
        )
        
        assert error.error_id == "TEST_001"
        assert error.category == ErrorCategory.ANALYSIS_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.message == "Test error message"
        assert error.context == context
        assert error.suggestion == "Test suggestion"
        assert error.recoverable is True
        assert error.retry_count == 0
        assert error.max_retries == 3

    def test_analysis_error_auto_id_generation(self):
        """Test automatic error ID generation."""
        error = AnalysisError(
            error_id="",  # Empty ID should trigger auto-generation
            category=ErrorCategory.SYNTAX_ERROR,
            severity=ErrorSeverity.HIGH,
            message="Test error"
        )
        
        assert error.error_id.startswith("ERR_syntax_error_")
        assert len(error.error_id) > 20  # Should be reasonably long


class TestErrorHandler:
    """Test ErrorHandler functionality."""

    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler()
        assert handler.errors == []
        assert len(handler.error_patterns) > 0
        assert len(handler.recovery_strategies) > 0

    def test_handle_error_basic(self):
        """Test basic error handling."""
        handler = ErrorHandler()
        exception = ValueError("Test error")
        
        error = handler.handle_error(exception)
        
        assert isinstance(error, AnalysisError)
        assert error.message == "Test error"
        assert error.category == ErrorCategory.VALIDATION_ERROR
        assert error.severity == ErrorSeverity.MEDIUM
        assert len(handler.errors) == 1

    def test_handle_error_with_context(self):
        """Test error handling with context."""
        handler = ErrorHandler()
        exception = FileNotFoundError("File not found")
        context = create_error_context(
            file_path=Path("test.py"),
            analyzer_name="test_analyzer"
        )
        
        error = handler.handle_error(exception, context, "test_analyzer")
        
        assert error.category == ErrorCategory.FILE_ACCESS_ERROR
        assert error.context.file_path == Path("test.py")
        assert error.context.analyzer_name == "test_analyzer"

    def test_error_classification(self):
        """Test error classification."""
        handler = ErrorHandler()
        
        # Test various exception types
        test_cases = [
            (SyntaxError("syntax error"), ErrorCategory.SYNTAX_ERROR),
            (FileNotFoundError("file not found"), ErrorCategory.FILE_ACCESS_ERROR),
            (PermissionError("permission denied"), ErrorCategory.PERMISSION_ERROR),
            (MemoryError("out of memory"), ErrorCategory.MEMORY_ERROR),
            (TimeoutError("timeout"), ErrorCategory.TIMEOUT_ERROR),
            (ImportError("import failed"), ErrorCategory.IMPORT_ERROR),
            (ValueError("invalid value"), ErrorCategory.VALIDATION_ERROR),
            (RuntimeError("unknown error"), ErrorCategory.UNKNOWN_ERROR),
        ]
        
        for exception, expected_category in test_cases:
            error = handler.handle_error(exception)
            assert error.category == expected_category

    def test_error_severity_determination(self):
        """Test error severity determination."""
        handler = ErrorHandler()
        
        # Test critical errors
        memory_error = handler.handle_error(MemoryError("out of memory"))
        assert memory_error.severity == ErrorSeverity.CRITICAL
        
        # Test high severity errors
        syntax_error = handler.handle_error(SyntaxError("syntax error"))
        assert syntax_error.severity == ErrorSeverity.HIGH
        
        # Test medium severity errors
        value_error = handler.handle_error(ValueError("invalid value"))
        assert value_error.severity == ErrorSeverity.MEDIUM

    def test_suggestion_generation(self):
        """Test suggestion generation."""
        handler = ErrorHandler()
        
        # Test syntax error suggestion
        syntax_error = handler.handle_error(SyntaxError("syntax error"))
        assert "syntax errors" in syntax_error.suggestion.lower()
        
        # Test file access error suggestion
        file_error = handler.handle_error(FileNotFoundError("file not found"))
        assert "file exists" in file_error.suggestion.lower()

    def test_recovery_strategy_determination(self):
        """Test recovery strategy determination."""
        handler = ErrorHandler()
        
        # Test skip strategy
        syntax_error = handler.handle_error(SyntaxError("syntax error"))
        strategy = handler.get_recovery_strategy(syntax_error)
        assert strategy == ErrorRecoveryStrategy.SKIP
        
        # Test retry strategy
        analysis_error = handler.handle_error(RuntimeError("analysis failed"))
        strategy = handler.get_recovery_strategy(analysis_error)
        assert strategy == ErrorRecoveryStrategy.RETRY
        
        # Test abort strategy
        memory_error = handler.handle_error(MemoryError("out of memory"))
        strategy = handler.get_recovery_strategy(memory_error)
        assert strategy == ErrorRecoveryStrategy.ABORT

    def test_retry_logic(self):
        """Test retry logic."""
        handler = ErrorHandler()
        
        # Test retryable error
        analysis_error = handler.handle_error(RuntimeError("analysis failed"))
        assert handler.should_retry(analysis_error) is True
        
        # Test non-retryable error
        memory_error = handler.handle_error(MemoryError("out of memory"))
        assert handler.should_retry(memory_error) is False
        
        # Test retry count limit
        analysis_error.retry_count = 3
        assert handler.should_retry(analysis_error) is False

    def test_error_summary(self):
        """Test error summary generation."""
        handler = ErrorHandler()
        
        # Add some test errors
        handler.handle_error(SyntaxError("syntax error"))
        handler.handle_error(ValueError("value error"))
        handler.handle_error(MemoryError("memory error"))
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert "by_category" in summary
        assert "by_severity" in summary
        assert summary["critical_errors"] == 1
        assert summary["recoverable_errors"] == 2

    def test_error_filtering(self):
        """Test error filtering by category and severity."""
        handler = ErrorHandler()
        
        # Add test errors
        handler.handle_error(SyntaxError("syntax error"))
        handler.handle_error(ValueError("value error"))
        handler.handle_error(MemoryError("memory error"))
        
        # Test filtering by category
        syntax_errors = handler.get_errors_by_category(ErrorCategory.SYNTAX_ERROR)
        assert len(syntax_errors) == 1
        assert syntax_errors[0].category == ErrorCategory.SYNTAX_ERROR
        
        # Test filtering by severity
        critical_errors = handler.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical_errors) == 1
        assert critical_errors[0].severity == ErrorSeverity.CRITICAL

    def test_clear_errors(self):
        """Test clearing errors."""
        handler = ErrorHandler()
        
        # Add some errors
        handler.handle_error(SyntaxError("syntax error"))
        handler.handle_error(ValueError("value error"))
        assert len(handler.errors) == 2
        
        # Clear errors
        handler.clear_errors()
        assert len(handler.errors) == 0


class TestErrorRecoveryManager:
    """Test ErrorRecoveryManager functionality."""

    def test_recovery_manager_initialization(self):
        """Test recovery manager initialization."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        assert manager.error_handler == handler
        assert manager.retry_delays == [1, 2, 5]

    def test_successful_execution(self):
        """Test successful function execution."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        def success_func():
            return "success"
        
        result, error = manager.execute_with_recovery(success_func)
        
        assert result == "success"
        assert error is None

    def test_failed_execution_with_retry(self):
        """Test failed execution with retry."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("temporary failure")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result, error = manager.execute_with_recovery(failing_func)
        
        assert result == "success"
        assert error is None
        assert call_count == 3

    def test_failed_execution_no_retry(self):
        """Test failed execution with no retry."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        def failing_func():
            raise MemoryError("out of memory")
        
        result, error = manager.execute_with_recovery(failing_func)
        
        assert result is None
        assert error is not None
        assert error.category == ErrorCategory.MEMORY_ERROR

    def test_failed_execution_max_retries(self):
        """Test failed execution that exceeds max retries."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        def always_failing_func():
            raise RuntimeError("always fails")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result, error = manager.execute_with_recovery(always_failing_func)
        
        assert result is None
        assert error is not None
        assert error.retry_count == 3  # Should have tried 3 times


class TestGlobalErrorHandler:
    """Test global error handler functionality."""

    def test_get_error_handler_singleton(self):
        """Test that get_error_handler returns a singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2

    def test_global_error_handler_functionality(self):
        """Test that global error handler works correctly."""
        handler = get_error_handler()
        
        # Clear any existing errors
        handler.clear_errors()
        
        # Add an error
        error = handler.handle_error(ValueError("test error"))
        
        assert len(handler.errors) == 1
        assert error.message == "test error"


class TestErrorHandlingIntegration:
    """Test error handling integration scenarios."""

    def test_analyzer_failure_recovery(self):
        """Test recovery from analyzer failures."""
        handler = ErrorHandler()
        manager = ErrorRecoveryManager(handler)
        
        # Mock analyzer that fails then succeeds
        call_count = 0
        
        def mock_analyzer(file_path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("analyzer failed")
            return []  # Empty findings
        
        result, error = manager.execute_with_recovery(mock_analyzer, Path("test.py"))
        
        assert result == []
        assert error is None
        assert call_count == 2

    def test_multiple_error_types(self):
        """Test handling multiple types of errors."""
        handler = ErrorHandler()
        
        # Add various error types
        handler.handle_error(SyntaxError("syntax error"))
        handler.handle_error(FileNotFoundError("file not found"))
        handler.handle_error(ValueError("value error"))
        handler.handle_error(MemoryError("memory error"))
        
        summary = handler.get_error_summary()
        
        assert summary["total_errors"] == 4
        assert summary["by_category"]["syntax_error"] == 1
        assert summary["by_category"]["file_access_error"] == 1
        assert summary["by_category"]["validation_error"] == 1
        assert summary["by_category"]["memory_error"] == 1

    def test_error_context_preservation(self):
        """Test that error context is preserved correctly."""
        handler = ErrorHandler()
        
        context = create_error_context(
            file_path=Path("test.py"),
            line_number=42,
            analyzer_name="test_analyzer",
            function_name="analyze_file"
        )
        
        error = handler.handle_error(ValueError("test error"), context)
        
        assert error.context.file_path == Path("test.py")
        assert error.context.line_number == 42
        assert error.context.analyzer_name == "test_analyzer"
        assert error.context.function_name == "analyze_file"

    def test_error_suggestion_quality(self):
        """Test that error suggestions are helpful."""
        handler = ErrorHandler()
        
        # Test syntax error suggestion
        syntax_error = handler.handle_error(SyntaxError("invalid syntax"))
        assert "syntax" in syntax_error.suggestion.lower()
        assert "fix" in syntax_error.suggestion.lower()
        
        # Test file access error suggestion
        file_error = handler.handle_error(FileNotFoundError("No such file"))
        assert "file" in file_error.suggestion.lower()
        assert "exists" in file_error.suggestion.lower()
        
        # Test configuration error suggestion
        config_error = handler.handle_error(ValueError("invalid config"))
        assert "config" in config_error.suggestion.lower()
        assert "valid" in config_error.suggestion.lower()
