"""Tests for message formatting system."""

from __future__ import annotations

from pathlib import Path

import pytest
from rich.console import Console

from pytest_drill_sergeant.core.config import Config
from pytest_drill_sergeant.core.models import (
    FeaturesData,
    Finding,
    ResultData,
    RuleType,
    Severity,
)
from pytest_drill_sergeant.core.reporting import (
    JSONFormatter,
    MessageTemplate,
    OutputManager,
    RichFormatter,
    SARIFFormatter,
    TemplateContext,
    TemplateRegistry,
)
from tests.constants import (
    TEST_BIS_SCORE,
    TEST_COLUMN_NUMBER,
    TEST_CONFIDENCE,
    TEST_INDENT,
    TEST_LINE_NUMBER,
)


class TestTemplateContext:
    """Test TemplateContext class."""

    def test_template_context_creation(self) -> None:
        """Test creating a template context."""
        context = TemplateContext(
            test_name="test_example",
            file_path="test_file.py",
            line_number=42,
            rule_type="private_access",
            severity="warning",
        )

        assert context.test_name == "test_example"
        assert context.file_path == "test_file.py"
        assert context.line_number == TEST_LINE_NUMBER
        assert context.rule_type == "private_access"
        assert context.severity == "warning"
        assert context.custom == {}

    def test_template_context_custom_vars(self) -> None:
        """Test template context with custom variables."""
        context = TemplateContext(
            test_name="test_example",
            custom={"custom_var": "custom_value", "number": 42},
        )

        assert context.custom is not None
        assert context.custom["custom_var"] == "custom_value"
        assert context.custom["number"] == TEST_LINE_NUMBER


class TestMessageTemplate:
    """Test MessageTemplate class."""

    def test_template_rendering(self) -> None:
        """Test basic template rendering."""
        template = MessageTemplate("Hello {name}, you have {count} issues!")
        result = template.render(name="Developer", count=5)

        assert result == "Hello Developer, you have 5 issues!"

    def test_template_with_context(self) -> None:
        """Test template rendering with context."""
        context = TemplateContext(
            test_name="test_example", file_path="test_file.py", line_number=42
        )
        template = MessageTemplate(
            "Test {test_name} at {file_path}:{line_number}", context
        )

        result = template.render()
        assert result == "Test test_example at test_file.py:42"

    def test_template_missing_variable(self) -> None:
        """Test template with missing variable."""
        template = MessageTemplate("Hello {name}, you have {missing} issues!")
        result = template.render(name="Developer")

        assert result == "Hello Developer, you have <missing:missing> issues!"

    def test_template_override_context(self) -> None:
        """Test template rendering with context override."""
        context = TemplateContext(test_name="original")
        template = MessageTemplate("Test: {test_name}", context)

        result = template.render(test_name="override")
        assert result == "Test: override"


class TestTemplateRegistry:
    """Test TemplateRegistry class."""

    def test_template_registration(self) -> None:
        """Test template registration."""
        registry = TemplateRegistry()
        template = MessageTemplate("Test {name}")

        registry.register("test_template", template)
        retrieved = registry.get("test_template")

        assert retrieved is template

    def test_template_rendering(self) -> None:
        """Test template rendering through registry."""
        registry = TemplateRegistry()
        template = MessageTemplate("Hello {user}!")
        registry.register("greeting", template)

        result = registry.render("greeting", user="World")
        assert result == "Hello World!"

    def test_template_not_found(self) -> None:
        """Test template not found handling."""
        registry = TemplateRegistry()

        result = registry.render("nonexistent")
        assert result == "<template not found: nonexistent>"

    def test_default_templates_loaded(self) -> None:
        """Test that default templates are loaded."""
        registry = TemplateRegistry()

        # Check some default templates exist
        assert registry.get("finding.warning") is not None
        assert registry.get("finding.error") is not None
        assert registry.get("test.result") is not None
        assert registry.get("summary.header") is not None


class TestRichFormatter:
    """Test RichFormatter class."""

    def test_rich_formatter_creation(self) -> None:
        """Test creating a Rich formatter."""
        formatter = RichFormatter()

        assert formatter.console is not None
        assert formatter.registry is not None

    def test_rich_formatter_with_console(self) -> None:
        """Test creating a Rich formatter with custom console."""
        console = Console()
        formatter = RichFormatter(console)

        assert formatter.console is console

    def test_format_finding(self) -> None:
        """Test formatting a finding."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Private access detected",
            file_path=Path("test_file.py"),
            line_number=42,
            column_number=10,
            code_snippet="def test_example():\n    obj._private_method()",
            suggestion="Use public methods instead of private ones",
            confidence=0.8,
        )

        formatter = RichFormatter()
        result = formatter.format_finding(finding)

        # Rich formatter returns Rich Text objects, not strings
        assert hasattr(result, "plain")  # Rich Text object
        result_str = str(result)
        assert "private_access" in result_str
        assert "Private access detected" in result_str
        assert "test_file.py:42" in result_str

    def test_format_test_result(self) -> None:
        """Test formatting a test result."""
        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            has_aaa_comments=False,
            aaa_comment_order=None,
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=0,
            complexity_score=0.0,
            coverage_percentage=0.0,
            coverage_signature=None,
            assertion_count=0,
            setup_lines=0,
            teardown_lines=0,
            execution_time=0.0,
            memory_usage=0.0,
            exception_count=0,
        )

        result = ResultData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            bis_score=85.5,
            bis_grade="B",
            analyzed=True,
            error_message=None,
            analysis_time=0.0,
        )

        formatter = RichFormatter()
        formatted = formatter.format_test_result(result)

        # Rich formatter returns Rich Text objects, not strings
        assert hasattr(formatted, "plain")  # Rich Text object
        formatted_str = str(formatted)
        assert "test_example" in formatted_str
        assert "85.5" in formatted_str
        assert "B" in formatted_str


class TestJSONFormatter:
    """Test JSONFormatter class."""

    def test_json_formatter_creation(self) -> None:
        """Test creating a JSON formatter."""
        formatter = JSONFormatter()

        assert formatter.indent == TEST_INDENT
        assert formatter.ensure_ascii is False

    def test_format_finding(self) -> None:
        """Test formatting a finding as JSON."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Private access detected",
            file_path=Path("test_file.py"),
            line_number=42,
            column_number=10,
            code_snippet="def test_example():\n    obj._private_method()",
            suggestion="Use public methods instead of private ones",
            confidence=0.8,
        )

        formatter = JSONFormatter()
        result = formatter.format_finding(finding)

        assert isinstance(result, dict)
        assert result["rule_type"] == "private_access"
        assert result["severity"] == "warning"
        assert result["message"] == "Private access detected"
        assert result["file_path"] == "test_file.py"
        assert result["line_number"] == TEST_LINE_NUMBER
        assert result["column_number"] == TEST_COLUMN_NUMBER
        assert result["confidence"] == TEST_CONFIDENCE

    def test_format_test_result(self) -> None:
        """Test formatting a test result as JSON."""
        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            has_aaa_comments=False,
            aaa_comment_order=None,
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=0,
            complexity_score=0.0,
            coverage_percentage=0.0,
            coverage_signature=None,
            assertion_count=0,
            setup_lines=0,
            teardown_lines=0,
            execution_time=0.0,
            memory_usage=0.0,
            exception_count=0,
        )

        result = ResultData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            bis_score=85.5,
            bis_grade="B",
            analyzed=True,
            error_message=None,
            analysis_time=0.0,
        )

        formatter = JSONFormatter()
        formatted = formatter.format_test_result(result)

        assert isinstance(formatted, dict)
        assert formatted["test_name"] == "test_example"
        assert formatted["bis_score"] == TEST_BIS_SCORE
        assert formatted["bis_grade"] == "B"
        assert "features" in formatted
        assert "findings" in formatted


class TestSARIFFormatter:
    """Test SARIFFormatter class."""

    def test_sarif_formatter_creation(self) -> None:
        """Test creating a SARIF formatter."""
        formatter = SARIFFormatter()

        assert formatter.tool_name == "pytest-drill-sergeant"
        assert formatter.tool_version == "1.0.0-dev"
        assert formatter.base_uri == "file://"

    def test_format_finding(self) -> None:
        """Test formatting a finding as SARIF."""
        finding = Finding(
            rule_type=RuleType.PRIVATE_ACCESS,
            severity=Severity.WARNING,
            message="Private access detected",
            file_path=Path("test_file.py"),
            line_number=42,
            column_number=10,
            code_snippet="def test_example():\n    obj._private_method()",
            suggestion="Use public methods instead of private ones",
            confidence=0.8,
        )

        formatter = SARIFFormatter()
        result = formatter.format_finding(finding)

        # Test the SARIF Result object properties
        assert result.rule_id == "drill-sergeant/private_access"
        assert result.level == "warning"
        assert result.message.text == "Private access detected"
        assert result.locations is not None
        assert len(result.locations) == 1

        location = result.locations[0]
        assert location.artifact_location is not None
        assert location.artifact_location.uri == "file:///test_file.py"
        assert location.region is not None
        assert location.region.start_line == TEST_LINE_NUMBER
        assert location.region.start_column == TEST_COLUMN_NUMBER


class TestOutputManager:
    """Test OutputManager class."""

    def test_output_manager_creation(self) -> None:
        """Test creating an output manager."""
        config = Config(
            mode="advisory",
            persona="drill_sergeant",
            sut_package=None,
            fail_on_how=False,
            output_format="terminal",
            json_report_path=None,
            sarif_report_path=None,
            verbose=False,
            bis_threshold=70.0,
            brs_threshold=60.0,
            similarity_threshold=0.8,
            parallel_analysis=True,
            max_workers=4,
            cache_ast=True,
            lsp_enabled=False,
            lsp_port=8080,
        )
        manager = OutputManager(config)

        assert manager.config is config
        assert manager.rich_formatter is not None
        assert manager.json_builder is not None
        assert manager.sarif_builder is not None
        assert len(manager._test_results) == 0
        assert manager._metrics is None

    def test_add_test_result(self) -> None:
        """Test adding a test result."""
        config = Config(
            mode="advisory",
            persona="drill_sergeant",
            sut_package=None,
            fail_on_how=False,
            output_format="terminal",
            json_report_path=None,
            sarif_report_path=None,
            verbose=False,
            bis_threshold=70.0,
            brs_threshold=60.0,
            similarity_threshold=0.8,
            parallel_analysis=True,
            max_workers=4,
            cache_ast=True,
            lsp_enabled=False,
            lsp_port=8080,
        )
        manager = OutputManager(config)

        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            has_aaa_comments=False,
            aaa_comment_order=None,
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=0,
            complexity_score=0.0,
            coverage_percentage=0.0,
            coverage_signature=None,
            assertion_count=0,
            setup_lines=0,
            teardown_lines=0,
            execution_time=0.0,
            memory_usage=0.0,
            exception_count=0,
        )

        result = ResultData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            bis_score=85.5,
            bis_grade="B",
            analyzed=True,
            error_message=None,
            analysis_time=0.0,
        )

        manager.add_test_result(result)

        assert len(manager._test_results) == 1
        assert manager._test_results[0] is result

    def test_get_summary_stats_without_metrics(self) -> None:
        """Test getting summary stats without metrics raises error."""
        config = Config(
            mode="advisory",
            persona="drill_sergeant",
            sut_package=None,
            fail_on_how=False,
            output_format="terminal",
            json_report_path=None,
            sarif_report_path=None,
            verbose=False,
            bis_threshold=70.0,
            brs_threshold=60.0,
            similarity_threshold=0.8,
            parallel_analysis=True,
            max_workers=4,
            cache_ast=True,
            lsp_enabled=False,
            lsp_port=8080,
        )
        manager = OutputManager(config)

        with pytest.raises(ValueError, match="Metrics must be set"):
            manager.get_summary_stats()

    def test_clear_results(self) -> None:
        """Test clearing results."""
        config = Config(
            mode="advisory",
            persona="drill_sergeant",
            sut_package=None,
            fail_on_how=False,
            output_format="terminal",
            json_report_path=None,
            sarif_report_path=None,
            verbose=False,
            bis_threshold=70.0,
            brs_threshold=60.0,
            similarity_threshold=0.8,
            parallel_analysis=True,
            max_workers=4,
            cache_ast=True,
            lsp_enabled=False,
            lsp_port=8080,
        )
        manager = OutputManager(config)

        # Add some results
        features = FeaturesData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            has_aaa_comments=False,
            aaa_comment_order=None,
            private_access_count=0,
            mock_assertion_count=0,
            structural_equality_count=0,
            test_length=0,
            complexity_score=0.0,
            coverage_percentage=0.0,
            coverage_signature=None,
            assertion_count=0,
            setup_lines=0,
            teardown_lines=0,
            execution_time=0.0,
            memory_usage=0.0,
            exception_count=0,
        )

        result = ResultData(
            test_name="test_example",
            file_path=Path("test_file.py"),
            line_number=10,
            features=features,
            bis_score=85.5,
            bis_grade="B",
            analyzed=True,
            error_message=None,
            analysis_time=0.0,
        )

        manager.add_test_result(result)
        assert len(manager._test_results) == 1

        # Clear results
        manager.clear_results()
        assert len(manager._test_results) == 0
        assert manager._metrics is None
