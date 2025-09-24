"""Tests for persona integration with pytest hooks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pytest_drill_sergeant.core.models import Finding, RunMetrics, Severity
from pytest_drill_sergeant.plugin.analysis_storage import AnalysisStorage
from pytest_drill_sergeant.plugin.personas.manager import PersonaManager


class TestPersonaManager:
    """Test the PersonaManager functionality."""

    def test_init(self) -> None:
        """Test persona manager initialization."""
        manager = PersonaManager()
        assert "drill_sergeant" in manager.list_personas()

    def test_get_persona_default(self) -> None:
        """Test getting default persona."""
        manager = PersonaManager()
        persona = manager.get_persona()
        assert persona.name == "drill_sergeant"

    def test_get_persona_by_name(self) -> None:
        """Test getting persona by name."""
        manager = PersonaManager()
        persona = manager.get_persona("drill_sergeant")
        assert persona.name == "drill_sergeant"

    def test_get_persona_not_found(self) -> None:
        """Test getting non-existent persona."""
        manager = PersonaManager()
        with pytest.raises(ValueError, match="Persona 'nonexistent' not found"):
            manager.get_persona("nonexistent", fallback_on_missing=False)

    def test_list_personas(self) -> None:
        """Test listing available personas."""
        manager = PersonaManager()
        personas = manager.list_personas()
        assert "drill_sergeant" in personas

    def test_get_persona_info(self) -> None:
        """Test getting persona information."""
        manager = PersonaManager()
        info = manager.get_persona_info("drill_sergeant")
        assert info["name"] == "drill_sergeant"
        assert "military" in info["description"].lower()
        assert "config" in info

    def test_on_test_pass(self) -> None:
        """Test test pass message generation."""
        manager = PersonaManager()
        message = manager.on_test_pass("test_something")
        assert "test_something" in message
        assert len(message) > 0

    def test_on_test_fail(self) -> None:
        """Test test fail message generation."""
        manager = PersonaManager()
        finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Some violation",
            file_path=Path("test.py"),
            line_number=1,
        )
        message = manager.on_test_fail("test_something", finding)
        assert "test_something" in message
        assert len(message) > 0

    def test_on_summary(self) -> None:
        """Test summary message generation."""
        manager = PersonaManager()
        metrics = RunMetrics(total_tests=10, total_violations=2, brs_score=70.0)
        message = manager.on_summary(metrics)
        assert len(message) > 0

    def test_on_bis_score(self) -> None:
        """Test BIS score message generation."""
        manager = PersonaManager()
        message = manager.on_bis_score("test_something", 75.0)
        assert "test_something" in message
        assert "75.0" in message

    def test_on_brs_score(self) -> None:
        """Test BRS score message generation."""
        manager = PersonaManager()
        message = manager.on_brs_score(85.0)
        assert "85.0" in message


class TestAnalysisStorage:
    """Test the AnalysisStorage functionality."""

    def test_init(self) -> None:
        """Test analysis storage initialization."""
        storage = AnalysisStorage()
        assert storage._test_findings == {}
        assert storage._test_metrics == {}
        assert storage._session_metrics is None
        assert storage._analyzers == []

    def test_add_analyzer(self) -> None:
        """Test adding an analyzer."""
        storage = AnalysisStorage()
        mock_analyzer = Mock()
        storage.add_analyzer(mock_analyzer)
        assert mock_analyzer in storage._analyzers

    def test_analyze_test_file(self) -> None:
        """Test analyzing a test file."""
        storage = AnalysisStorage()

        # Mock analyzer
        mock_analyzer = Mock()
        mock_finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Test violation",
            file_path=Path("test.py"),
            line_number=1,
        )
        mock_analyzer.analyze_file.return_value = [mock_finding]
        storage.add_analyzer(mock_analyzer)

        # Analyze test file
        test_file = Path("test_example.py")
        findings = storage.analyze_test_file(test_file)

        assert len(findings) == 1
        assert findings[0] == mock_finding
        assert str(test_file) in storage._test_findings

    def test_get_test_findings(self) -> None:
        """Test getting test findings."""
        storage = AnalysisStorage()
        test_file = Path("test_example.py")
        mock_finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Test violation",
            file_path=test_file,
            line_number=1,
        )
        storage._test_findings[str(test_file)] = [mock_finding]

        findings = storage.get_test_findings(test_file)
        assert len(findings) == 1
        assert findings[0] == mock_finding

    def test_set_get_test_metrics(self) -> None:
        """Test setting and getting test metrics."""
        storage = AnalysisStorage()
        metrics = {"score": 85.0, "violations": 2}
        storage.set_test_metrics("test_something", metrics)

        retrieved_metrics = storage.get_test_metrics("test_something")
        assert retrieved_metrics == metrics

    def test_set_get_session_metrics(self) -> None:
        """Test setting and getting session metrics."""
        storage = AnalysisStorage()
        metrics = RunMetrics(total_tests=10, total_violations=3, brs_score=70.0)
        storage.set_session_metrics(metrics)

        retrieved_metrics = storage.get_session_metrics()
        assert retrieved_metrics == metrics

    def test_get_all_findings(self) -> None:
        """Test getting all findings."""
        storage = AnalysisStorage()
        mock_finding1 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Violation 1",
            file_path=Path("test1.py"),
            line_number=1,
        )
        mock_finding2 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.ERROR,
            message="Violation 2",
            file_path=Path("test2.py"),
            line_number=2,
        )
        storage._test_findings["test1.py"] = [mock_finding1]
        storage._test_findings["test2.py"] = [mock_finding2]

        all_findings = storage.get_all_findings()
        assert len(all_findings) == 2
        assert mock_finding1 in all_findings
        assert mock_finding2 in all_findings

    def test_get_total_violations(self) -> None:
        """Test getting total violations count."""
        storage = AnalysisStorage()
        mock_finding1 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Violation 1",
            file_path=Path("test1.py"),
            line_number=1,
        )
        mock_finding2 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.ERROR,
            message="Violation 2",
            file_path=Path("test2.py"),
            line_number=2,
        )
        storage._test_findings["test1.py"] = [mock_finding1]
        storage._test_findings["test2.py"] = [mock_finding2]

        total = storage.get_total_violations()
        assert total == 2

    def test_clear(self) -> None:
        """Test clearing storage."""
        storage = AnalysisStorage()
        storage._test_findings["test.py"] = [Mock()]
        storage._test_metrics["test"] = {"score": 85.0}
        storage._session_metrics = Mock()

        storage.clear()

        assert storage._test_findings == {}
        assert storage._test_metrics == {}
        assert storage._session_metrics is None

    def test_get_summary_stats(self) -> None:
        """Test getting summary statistics."""
        storage = AnalysisStorage()
        mock_finding1 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Violation 1",
            file_path=Path("test1.py"),
            line_number=1,
        )
        mock_finding2 = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.ERROR,
            message="Violation 2",
            file_path=Path("test2.py"),
            line_number=2,
        )
        storage._test_findings["test1.py"] = [mock_finding1]
        storage._test_findings["test2.py"] = [mock_finding2]
        storage._test_metrics["test1"] = {"score": 85.0}
        storage._test_metrics["test2"] = {"score": 70.0}

        stats = storage.get_summary_stats()

        assert stats["total_violations"] == 2
        assert stats["total_test_files"] == 2
        assert stats["total_tests"] == 2
        assert "DS201" in stats["rule_counts"]
        assert stats["rule_counts"]["DS201"] == 2


class TestHookIntegration:
    """Test the integration between hooks and persona system."""

    @patch("pytest_drill_sergeant.plugin.hooks.get_config")
    @patch("pytest_drill_sergeant.plugin.hooks.get_analysis_storage")
    def test_initialize_analyzers(self, mock_storage, mock_config) -> None:
        """Test analyzer initialization in hooks."""
        from pytest_drill_sergeant.plugin.hooks import _initialize_analyzers

        # Mock config
        mock_config.return_value.sut_package = "myapp"

        # Mock storage
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance

        # Call the function
        _initialize_analyzers()

        # Verify analyzers were added (now we have 5 analyzers: private access, mock overspec, AAA comment, structural equality, duplicate tests)
        assert mock_storage_instance.add_analyzer.call_count == 5

    @patch("pytest_drill_sergeant.plugin.hooks.create_file_discovery")
    @patch("pytest_drill_sergeant.plugin.hooks.get_config")
    @patch("pytest_drill_sergeant.plugin.hooks.get_analysis_storage")
    def test_analyze_test_file(
        self, mock_storage, mock_config, mock_create_file_discovery
    ) -> None:
        """Test test file analysis in hooks."""
        from pytest_drill_sergeant.plugin.hooks import _analyze_test_file

        # Mock file discovery to return True for should_analyze_file
        mock_file_discovery = Mock()
        mock_file_discovery.should_analyze_file.return_value = True
        mock_file_discovery.get_file_config.return_value = {"ignored_rules": []}
        mock_create_file_discovery.return_value = mock_file_discovery

        # Mock config
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance

        # Mock storage
        mock_storage_instance = Mock()
        mock_storage_instance._test_findings = {}
        mock_storage_instance.analyze_test_file.return_value = []
        mock_storage.return_value = mock_storage_instance

        # Mock test item
        mock_item = Mock()
        mock_item.fspath = "/path/test_example.py"

        # Call the function
        _analyze_test_file(mock_item)

        # Verify analysis was called
        mock_storage_instance.analyze_test_file.assert_called_once()

    @patch("pytest_drill_sergeant.plugin.hooks.get_persona_manager")
    @patch("pytest_drill_sergeant.plugin.hooks.get_analysis_storage")
    def test_inject_persona_feedback_passed(
        self, mock_storage, mock_persona_manager
    ) -> None:
        """Test persona feedback injection for passed tests."""
        from pytest_drill_sergeant.plugin.hooks import _inject_persona_feedback

        # Mock storage
        mock_storage_instance = Mock()
        mock_storage_instance.get_test_findings.return_value = []
        mock_storage.return_value = mock_storage_instance

        # Mock persona manager
        mock_persona_manager_instance = Mock()
        mock_persona_manager_instance.on_test_pass.return_value = "Test passed!"
        mock_persona_manager.return_value = mock_persona_manager_instance

        # Mock test report
        mock_report = Mock()
        mock_report.when = "call"
        mock_report.outcome = "passed"
        mock_report.nodeid = "test_something"
        mock_report.fspath = "/path/to/test.py"
        mock_report.longrepr = None

        # Call the function
        _inject_persona_feedback(mock_report)

        # Verify persona message was generated
        mock_persona_manager_instance.on_test_pass.assert_called_once_with(
            "test_something"
        )
        # BIS integration adds extra content, so we check it contains the original message
        assert "Test passed!" in str(mock_report.longrepr)

    @patch("pytest_drill_sergeant.plugin.hooks.get_persona_manager")
    @patch("pytest_drill_sergeant.plugin.hooks.get_analysis_storage")
    def test_inject_persona_feedback_failed(
        self, mock_storage, mock_persona_manager
    ) -> None:
        """Test persona feedback injection for failed tests."""
        from pytest_drill_sergeant.plugin.hooks import _inject_persona_feedback

        # Mock storage
        mock_storage_instance = Mock()
        mock_finding = Finding(
            code="DS201",
            name="private_access",
            severity=Severity.WARNING,
            message="Test violation",
            file_path=Path("test.py"),
            line_number=1,
        )
        mock_storage_instance.get_test_findings.return_value = [mock_finding]
        mock_storage.return_value = mock_storage_instance

        # Mock persona manager
        mock_persona_manager_instance = Mock()
        mock_persona_manager_instance.on_test_fail.return_value = "Test failed!"
        mock_persona_manager.return_value = mock_persona_manager_instance

        # Mock test report
        mock_report = Mock()
        mock_report.when = "call"
        mock_report.outcome = "failed"
        mock_report.nodeid = "test_something"
        mock_report.fspath = "/path/to/test.py"
        mock_report.longrepr = None

        # Call the function
        _inject_persona_feedback(mock_report)

        # Verify persona message was generated
        mock_persona_manager_instance.on_test_fail.assert_called_once_with(
            "test_something", mock_finding
        )
        # BIS integration adds extra content, so we check it contains the original message
        assert "Test failed!" in str(mock_report.longrepr)

    @patch("pytest_drill_sergeant.plugin.hooks.get_persona_manager")
    @patch("pytest_drill_sergeant.plugin.hooks.get_analysis_storage")
    def test_generate_persona_summary(self, mock_storage, mock_persona_manager) -> None:
        """Test persona summary generation."""
        from pytest_drill_sergeant.plugin.hooks import _generate_persona_summary

        # Mock storage
        mock_storage_instance = Mock()
        mock_storage_instance.get_summary_stats.return_value = {
            "total_violations": 2,
            "total_test_files": 1,
            "total_tests": 5,
            "rule_counts": {"PRIVATE_ACCESS": 2},
        }
        mock_storage.return_value = mock_storage_instance

        # Mock persona manager
        mock_persona_manager_instance = Mock()
        mock_persona_manager_instance.on_summary.return_value = "Summary message!"
        mock_persona_manager.return_value = mock_persona_manager_instance

        # Mock terminal reporter
        mock_terminal_reporter = Mock()

        # Call the function
        _generate_persona_summary(mock_terminal_reporter)

        # Verify summary was generated
        mock_persona_manager_instance.on_summary.assert_called_once()
        mock_terminal_reporter.write_sep.assert_called()
        mock_terminal_reporter.write_line.assert_called()
