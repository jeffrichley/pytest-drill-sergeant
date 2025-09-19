"""Analysis result storage for per-test findings and metrics."""

from __future__ import annotations

import logging
from pathlib import Path

from pytest_drill_sergeant.core.analyzers.private_access_detector import Detector
from pytest_drill_sergeant.core.models import Finding, RunMetrics


logger = logging.getLogger(__name__)


class AnalysisStorage:
    """Stores analysis results for the current test session."""

    def __init__(self) -> None:
        """Initialize the analysis storage."""
        self._test_findings: dict[str, list[Finding]] = {}
        self._test_metrics: dict[str, dict[str, float]] = {}
        self._session_metrics: RunMetrics | None = None
        self._analyzers: list[Detector] = []

    def add_analyzer(self, analyzer: Detector) -> None:
        """Add an analyzer to the storage.
        
        Args:
            analyzer: Analyzer instance to add
        """
        self._analyzers.append(analyzer)
        logger.debug(f"Added analyzer: {analyzer.__class__.__name__}")

    def analyze_test_file(self, test_file_path: Path) -> list[Finding]:
        """Analyze a test file and store results.
        
        Args:
            test_file_path: Path to the test file
            
        Returns:
            List of findings from all analyzers
        """
        all_findings: list[Finding] = []
        
        for analyzer in self._analyzers:
            try:
                findings = analyzer.analyze_file(test_file_path)
                all_findings.extend(findings)
                logger.debug(f"Analyzer {analyzer.__class__.__name__} found {len(findings)} violations in {test_file_path}")
            except Exception as e:
                logger.warning(f"Analyzer {analyzer.__class__.__name__} failed on {test_file_path}: {e}")
        
        # Store findings for this test file
        test_key = str(test_file_path)
        self._test_findings[test_key] = all_findings
        
        return all_findings

    def get_test_findings(self, test_file_path: Path) -> list[Finding]:
        """Get findings for a specific test file.
        
        Args:
            test_file_path: Path to the test file
            
        Returns:
            List of findings for the test file
        """
        test_key = str(test_file_path)
        return self._test_findings.get(test_key, [])

    def set_test_metrics(self, test_name: str, metrics: dict[str, float]) -> None:
        """Set metrics for a specific test.
        
        Args:
            test_name: Name of the test
            metrics: Dictionary of metric names to values
        """
        self._test_metrics[test_name] = metrics
        logger.debug(f"Set metrics for test {test_name}: {metrics}")

    def get_test_metrics(self, test_name: str) -> dict[str, float]:
        """Get metrics for a specific test.
        
        Args:
            test_name: Name of the test
            
        Returns:
            Dictionary of metric names to values
        """
        return self._test_metrics.get(test_name, {})

    def set_session_metrics(self, metrics: RunMetrics) -> None:
        """Set session-level metrics.
        
        Args:
            metrics: Session metrics
        """
        self._session_metrics = metrics
        logger.debug(f"Set session metrics: {metrics}")

    def get_session_metrics(self) -> RunMetrics | None:
        """Get session-level metrics.
        
        Returns:
            Session metrics or None if not set
        """
        return self._session_metrics

    def get_all_findings(self) -> list[Finding]:
        """Get all findings from all test files.
        
        Returns:
            List of all findings
        """
        all_findings: list[Finding] = []
        for findings in self._test_findings.values():
            all_findings.extend(findings)
        return all_findings

    def get_total_violations(self) -> int:
        """Get total number of violations found.
        
        Returns:
            Total number of violations
        """
        return len(self.get_all_findings())

    def clear(self) -> None:
        """Clear all stored data."""
        self._test_findings.clear()
        self._test_metrics.clear()
        self._session_metrics = None
        logger.debug("Cleared analysis storage")

    def get_summary_stats(self) -> dict[str, int]:
        """Get summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        all_findings = self.get_all_findings()
        
        # Count by rule code
        rule_counts: dict[str, int] = {}
        for finding in all_findings:
            rule_code = finding.code
            rule_counts[rule_code] = rule_counts.get(rule_code, 0) + 1
        
        return {
            "total_violations": len(all_findings),
            "total_test_files": len(self._test_findings),
            "total_tests": len(self._test_metrics),
            "rule_counts": rule_counts
        }


# Global analysis storage instance
_analysis_storage: AnalysisStorage | None = None


def get_analysis_storage() -> AnalysisStorage:
    """Get the global analysis storage instance.
    
    Returns:
        AnalysisStorage instance
    """
    global _analysis_storage
    if _analysis_storage is None:
        _analysis_storage = AnalysisStorage()
    return _analysis_storage
