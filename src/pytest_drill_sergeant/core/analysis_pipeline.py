"""Analysis pipeline for pytest-drill-sergeant.

This module implements the centralized analysis pipeline that coordinates
all analyzers and provides a single interface for both CLI and plugin.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.error_handler import AnalysisError
    from pytest_drill_sergeant.core.models import Finding

from pytest_drill_sergeant.core.error_handler import (
    ErrorHandler,
    ErrorRecoveryManager,
    create_error_context,
    get_error_handler,
)
from pytest_drill_sergeant.core.models import Finding


class Analyzer(Protocol):
    """Protocol for all analyzers in the system."""

    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a test file for violations.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            List of findings for violations
        """
        ...


class AnalysisPipeline:
    """Central analysis pipeline that coordinates all analyzers.

    This implements the Observer pattern from the architecture design,
    providing a single interface for running multiple analyzers.
    """

    def __init__(self, error_handler: ErrorHandler | None = None) -> None:
        """Initialize the analysis pipeline.

        Args:
            error_handler: Error handler instance for error recovery
        """
        self.analyzers: list[Analyzer] = []
        self.logger = logging.getLogger("drill_sergeant.analysis_pipeline")
        self.error_handler = error_handler or get_error_handler()
        self.recovery_manager = ErrorRecoveryManager(self.error_handler)
        self.analysis_errors: list[AnalysisError] = []

    def add_analyzer(self, analyzer: Analyzer) -> None:
        """Add an analyzer to the pipeline.

        Args:
            analyzer: The analyzer to add
        """
        self.analyzers.append(analyzer)
        self.logger.debug("Added analyzer: %s", type(analyzer).__name__)

    def remove_analyzer(self, analyzer: Analyzer) -> None:
        """Remove an analyzer from the pipeline.

        Args:
            analyzer: The analyzer to remove
        """
        if analyzer in self.analyzers:
            self.analyzers.remove(analyzer)
            self.logger.debug("Removed analyzer: %s", type(analyzer).__name__)

    def clear_analyzers(self) -> None:
        """Clear all analyzers from the pipeline."""
        self.analyzers.clear()
        self.logger.debug("Cleared all analyzers")

    def analyze_file(
        self, file_path: Path
    ) -> tuple[list[Finding], list[AnalysisError]]:
        """Analyze a single test file using all registered analyzers.

        Args:
            file_path: Path to the test file to analyze

        Returns:
            Tuple of (findings, errors) from all analyzers
        """
        findings: list[Finding] = []
        file_errors: list[AnalysisError] = []

        self.logger.debug("Analyzing file: %s", file_path)

        for analyzer in self.analyzers:
            analyzer_name = type(analyzer).__name__

            # Execute analyzer with error recovery
            result, error = self.recovery_manager.execute_with_recovery(
                analyzer.analyze_file, file_path
            )

            if error:
                # Handle the error
                error.context = create_error_context(
                    file_path=file_path,
                    analyzer_name=analyzer_name,
                    function_name="analyze_file",
                )
                file_errors.append(error)
                self.analysis_errors.append(error)

                self.logger.warning(
                    "Analyzer %s failed for %s: %s",
                    analyzer_name,
                    file_path,
                    error.message,
                )
            else:
                # Add successful findings
                findings.extend(result)
                self.logger.debug(
                    "%s found %d violations in %s",
                    analyzer_name,
                    len(result),
                    file_path,
                )

        return findings, file_errors

    def analyze_files(
        self, file_paths: list[Path]
    ) -> tuple[dict[Path, list[Finding]], dict[Path, list[AnalysisError]]]:
        """Analyze multiple test files.

        Args:
            file_paths: List of paths to test files

        Returns:
            Tuple of (findings_by_file, errors_by_file) dictionaries
        """
        findings_by_file: dict[Path, list[Finding]] = {}
        errors_by_file: dict[Path, list[AnalysisError]] = {}

        for file_path in file_paths:
            findings, errors = self.analyze_file(file_path)
            findings_by_file[file_path] = findings
            if errors:
                errors_by_file[file_path] = errors

        return findings_by_file, errors_by_file

    def get_analyzer_count(self) -> int:
        """Get the number of registered analyzers.

        Returns:
            Number of analyzers in the pipeline
        """
        return len(self.analyzers)

    def get_analyzer_names(self) -> list[str]:
        """Get the names of all registered analyzers.

        Returns:
            List of analyzer class names
        """
        return [type(analyzer).__name__ for analyzer in self.analyzers]

    def get_analysis_errors(self) -> list[AnalysisError]:
        """Get all analysis errors that occurred.

        Returns:
            List of analysis errors
        """
        return self.analysis_errors.copy()

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all analysis errors.

        Returns:
            Dictionary with error statistics
        """
        return self.error_handler.get_error_summary()

    def clear_errors(self) -> None:
        """Clear all recorded errors."""
        self.analysis_errors.clear()
        self.error_handler.clear_errors()


class AnalyzerRegistry:
    """Registry for discovering and creating analyzers.

    This implements the Registry pattern from the architecture design.
    """

    def __init__(self) -> None:
        """Initialize the analyzer registry."""
        self._analyzer_classes: dict[str, type[Analyzer]] = {}
        self.logger = logging.getLogger("drill_sergeant.analyzer_registry")

    def register_analyzer(self, name: str, analyzer_class: type[Analyzer]) -> None:
        """Register an analyzer class.

        Args:
            name: Name of the analyzer
            analyzer_class: The analyzer class to register
        """
        self._analyzer_classes[name] = analyzer_class
        self.logger.debug("Registered analyzer: %s", name)

    def create_analyzer(self, name: str) -> Analyzer:
        """Create an analyzer instance by name.

        Args:
            name: Name of the analyzer to create

        Returns:
            Analyzer instance

        Raises:
            KeyError: If analyzer name is not registered
        """
        if name not in self._analyzer_classes:
            raise KeyError(f"Unknown analyzer: {name}")

        analyzer_class = self._analyzer_classes[name]
        return analyzer_class()

    def get_available_analyzers(self) -> list[str]:
        """Get list of available analyzer names.

        Returns:
            List of registered analyzer names
        """
        return list(self._analyzer_classes.keys())

    def create_default_pipeline(self) -> AnalysisPipeline:
        """Create a pipeline with all default analyzers.

        Returns:
            AnalysisPipeline with default analyzers
        """
        pipeline = AnalysisPipeline()

        # Register and add default analyzers
        self._register_default_analyzers()

        for name in self.get_available_analyzers():
            try:
                analyzer = self.create_analyzer(name)
                pipeline.add_analyzer(analyzer)
            except Exception as e:
                self.logger.error("Failed to create analyzer %s: %s", name, e)

        return pipeline

    def _register_default_analyzers(self) -> None:
        """Register all default analyzers."""
        try:
            from pytest_drill_sergeant.core.analyzers.aaa_comment_detector import (
                AAACommentDetector,
            )
            from pytest_drill_sergeant.core.analyzers.duplicate_test_detector import (
                DuplicateTestDetector,
            )
            from pytest_drill_sergeant.core.analyzers.mock_overspec_detector import (
                MockOverspecDetector,
            )
            from pytest_drill_sergeant.core.analyzers.private_access_detector import (
                PrivateAccessDetector,
            )
            from pytest_drill_sergeant.core.analyzers.structural_equality_detector import (
                StructuralEqualityDetector,
            )

            self.register_analyzer("aaa_comments", AAACommentDetector)
            self.register_analyzer("duplicate_tests", DuplicateTestDetector)
            self.register_analyzer("mock_overspec", MockOverspecDetector)
            self.register_analyzer("private_access", PrivateAccessDetector)
            self.register_analyzer("structural_equality", StructuralEqualityDetector)

        except ImportError as e:
            self.logger.warning("Failed to import analyzer: %s", e)


# Global registry instance
_global_registry: AnalyzerRegistry | None = None


def get_analyzer_registry() -> AnalyzerRegistry:
    """Get the global analyzer registry.

    Returns:
        Global analyzer registry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AnalyzerRegistry()
    return _global_registry


def create_analysis_pipeline() -> AnalysisPipeline:
    """Create a new analysis pipeline with default analyzers.

    Returns:
        AnalysisPipeline with all default analyzers
    """
    registry = get_analyzer_registry()
    return registry.create_default_pipeline()
