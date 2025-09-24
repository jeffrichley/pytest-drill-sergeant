"""Tests for the analysis pipeline and registry."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from pytest_drill_sergeant.core.analysis_pipeline import (
    AnalysisPipeline,
    AnalyzerRegistry,
    create_analysis_pipeline,
    get_analyzer_registry,
)
from pytest_drill_sergeant.core.models import Finding, Severity


class MockAnalyzer:
    """Mock analyzer for testing."""
    
    def __init__(self, name: str = "mock", findings: list[Finding] | None = None):
        self.name = name
        self.findings = findings or []
    
    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Mock analyze_file method."""
        return self.findings.copy()


class TestAnalysisPipeline:
    """Test cases for AnalysisPipeline."""

    @pytest.fixture
    def pipeline(self) -> AnalysisPipeline:
        """Create a pipeline instance."""
        return AnalysisPipeline()

    @pytest.fixture
    def sample_finding(self, tmp_path: Path) -> Finding:
        """Create a sample finding."""
        return Finding(
            code="DS999",
            name="test_rule",
            severity=Severity.WARNING,
            message="Test finding",
            file_path=tmp_path / "test.py",
            line_number=1,
        )

    def test_pipeline_initialization(self, pipeline: AnalysisPipeline) -> None:
        """Test pipeline initializes correctly."""
        assert pipeline is not None
        assert len(pipeline.analyzers) == 0
        assert pipeline.get_analyzer_count() == 0
        assert pipeline.get_analyzer_names() == []

    def test_add_analyzer(self, pipeline: AnalysisPipeline) -> None:
        """Test adding analyzers to the pipeline."""
        analyzer1 = MockAnalyzer("analyzer1")
        analyzer2 = MockAnalyzer("analyzer2")
        
        pipeline.add_analyzer(analyzer1)
        assert pipeline.get_analyzer_count() == 1
        assert "MockAnalyzer" in pipeline.get_analyzer_names()
        
        pipeline.add_analyzer(analyzer2)
        assert pipeline.get_analyzer_count() == 2

    def test_remove_analyzer(self, pipeline: AnalysisPipeline) -> None:
        """Test removing analyzers from the pipeline."""
        analyzer1 = MockAnalyzer("analyzer1")
        analyzer2 = MockAnalyzer("analyzer2")
        
        pipeline.add_analyzer(analyzer1)
        pipeline.add_analyzer(analyzer2)
        assert pipeline.get_analyzer_count() == 2
        
        pipeline.remove_analyzer(analyzer1)
        assert pipeline.get_analyzer_count() == 1
        
        pipeline.remove_analyzer(analyzer2)
        assert pipeline.get_analyzer_count() == 0

    def test_clear_analyzers(self, pipeline: AnalysisPipeline) -> None:
        """Test clearing all analyzers."""
        # Arrange
        analyzer1 = MockAnalyzer("analyzer1")
        analyzer2 = MockAnalyzer("analyzer2")
        
        pipeline.add_analyzer(analyzer1)
        pipeline.add_analyzer(analyzer2)
        assert pipeline.get_analyzer_count() == 2
        
        # Act
        pipeline.clear_analyzers()
        
        # Assert
        assert pipeline.get_analyzer_count() == 0

    def test_analyze_file_single_analyzer(self, pipeline: AnalysisPipeline, sample_finding: Finding, tmp_path: Path) -> None:
        """Test analyzing a file with a single analyzer."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_something(): pass")
        
        analyzer = MockAnalyzer("test", [sample_finding])
        pipeline.add_analyzer(analyzer)
        
        findings, errors = pipeline.analyze_file(test_file)
        assert len(findings) == 1
        assert findings[0] == sample_finding

    def test_analyze_file_multiple_analyzers(self, pipeline: AnalysisPipeline, tmp_path: Path) -> None:
        """Test analyzing a file with multiple analyzers."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_something(): pass")
        
        finding1 = Finding(
            code="DS998",
            name="test_rule1",
            severity=Severity.WARNING,
            message="Finding 1",
            file_path=test_file,
            line_number=1,
        )
        
        finding2 = Finding(
            code="DS997",
            name="test_rule2",
            severity=Severity.ERROR,
            message="Finding 2",
            file_path=test_file,
            line_number=2,
        )
        
        analyzer1 = MockAnalyzer("analyzer1", [finding1])
        analyzer2 = MockAnalyzer("analyzer2", [finding2])
        
        pipeline.add_analyzer(analyzer1)
        pipeline.add_analyzer(analyzer2)
        
        findings, errors = pipeline.analyze_file(test_file)
        assert len(findings) == 2
        assert finding1 in findings
        assert finding2 in findings

    def test_analyze_file_error_handling(self, pipeline: AnalysisPipeline, tmp_path: Path) -> None:
        """Test error handling when an analyzer fails."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_something(): pass")
        
        # Create analyzer that raises an exception
        failing_analyzer = Mock()
        failing_analyzer.analyze_file.side_effect = Exception("Test error")
        
        # Create working analyzer
        working_finding = Finding(
            code="DS996",
            name="test_rule",
            severity=Severity.WARNING,
            message="Working finding",
            file_path=test_file,
            line_number=1,
        )
        working_analyzer = MockAnalyzer("working", [working_finding])
        
        pipeline.add_analyzer(failing_analyzer)
        pipeline.add_analyzer(working_analyzer)
        
        # Should continue with working analyzer even if one fails
        findings, errors = pipeline.analyze_file(test_file)
        assert len(findings) == 1
        assert findings[0] == working_finding

    def test_analyze_files_multiple(self, pipeline: AnalysisPipeline, tmp_path: Path) -> None:
        """Test analyzing multiple files."""
        test_file1 = tmp_path / "test1.py"
        test_file2 = tmp_path / "test2.py"
        test_file1.write_text("def test_one(): pass")
        test_file2.write_text("def test_two(): pass")
        
        finding1 = Finding(
            code="DS995",
            name="test_rule",
            severity=Severity.WARNING,
            message="Finding 1",
            file_path=test_file1,
            line_number=1,
        )
        
        finding2 = Finding(
            code="DS994",
            name="test_rule",
            severity=Severity.WARNING,
            message="Finding 2",
            file_path=test_file2,
            line_number=1,
        )
        
        # Analyzer that returns different findings based on file
        def mock_analyze(file_path: Path) -> list[Finding]:
            if file_path.name == "test1.py":
                return [finding1]
            if file_path.name == "test2.py":
                return [finding2]
            return []
        
        analyzer = Mock()
        analyzer.analyze_file.side_effect = mock_analyze
        pipeline.add_analyzer(analyzer)
        
        findings_by_file, errors_by_file = pipeline.analyze_files([test_file1, test_file2])
        
        assert len(findings_by_file) == 2
        assert findings_by_file[test_file1] == [finding1]
        assert findings_by_file[test_file2] == [finding2]


class TestAnalyzerRegistry:
    """Test cases for AnalyzerRegistry."""

    @pytest.fixture
    def registry(self) -> AnalyzerRegistry:
        """Create a registry instance."""
        return AnalyzerRegistry()

    def test_registry_initialization(self, registry: AnalyzerRegistry) -> None:
        """Test registry initializes correctly."""
        assert registry is not None
        assert len(registry.get_available_analyzers()) == 0

    def test_register_analyzer(self, registry: AnalyzerRegistry) -> None:
        """Test registering analyzer classes."""
        registry.register_analyzer("mock_analyzer", MockAnalyzer)
        
        available = registry.get_available_analyzers()
        assert "mock_analyzer" in available
        assert len(available) == 1

    def test_create_analyzer(self, registry: AnalyzerRegistry) -> None:
        """Test creating analyzer instances."""
        registry.register_analyzer("mock_analyzer", MockAnalyzer)
        
        analyzer = registry.create_analyzer("mock_analyzer")
        assert isinstance(analyzer, MockAnalyzer)

    def test_create_unknown_analyzer(self, registry: AnalyzerRegistry) -> None:
        """Test creating unknown analyzer raises error."""
        with pytest.raises(KeyError, match="Unknown analyzer: unknown"):
            registry.create_analyzer("unknown")

    def test_create_default_pipeline(self, registry: AnalyzerRegistry) -> None:
        """Test creating default pipeline with all analyzers."""
        pipeline = registry.create_default_pipeline()
        
        assert isinstance(pipeline, AnalysisPipeline)
        # Should have at least the private access and mock overspec detectors
        assert pipeline.get_analyzer_count() >= 2
        
        analyzer_names = pipeline.get_analyzer_names()
        assert "PrivateAccessDetector" in analyzer_names
        assert "MockOverspecDetector" in analyzer_names


class TestGlobalFunctions:
    """Test global convenience functions."""

    def test_get_analyzer_registry_singleton(self) -> None:
        """Test that get_analyzer_registry returns singleton."""
        registry1 = get_analyzer_registry()
        registry2 = get_analyzer_registry()
        
        assert registry1 is registry2  # Same instance

    def test_create_analysis_pipeline(self) -> None:
        """Test creating analysis pipeline."""
        pipeline = create_analysis_pipeline()
        
        assert isinstance(pipeline, AnalysisPipeline)
        assert pipeline.get_analyzer_count() >= 2  # Should have default analyzers
