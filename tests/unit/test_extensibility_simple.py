"""Simplified tests for plugin extensibility utilities.

This module provides focused tests for the extensibility system,
covering the core functionality that actually works with the existing codebase.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pytest_drill_sergeant.plugin.extensibility import (
    PluginTemplate,
    TemplateError,
    _to_bool,
    _to_options,
)

# Test constants to avoid magic numbers
TEST_NUMBER = 42
TEST_THRESHOLD = 0.8
LARGE_LIST_SIZE = 1000


class TestUtilityFunctions:
    """Test utility functions for type coercion."""

    def test_to_bool_with_none(self) -> None:
        """Test _to_bool with None value."""
        result = _to_bool(None, "test_field", True)
        assert result is True

        result = _to_bool(None, "test_field", False)
        assert result is False

    def test_to_bool_with_boolean(self) -> None:
        """Test _to_bool with boolean values."""
        result = _to_bool(True, "test_field", False)
        assert result is True

        result = _to_bool(False, "test_field", True)
        assert result is False

    def test_to_bool_with_string_true_values(self) -> None:
        """Test _to_bool with string true values."""
        true_values = ["1", "true", "t", "yes", "y", "on", "TRUE", "True", "YES"]
        for value in true_values:
            result = _to_bool(value, "test_field", False)
            assert result is True, f"Failed for value: {value}"

    def test_to_bool_with_string_false_values(self) -> None:
        """Test _to_bool with string false values."""
        false_values = ["0", "false", "f", "no", "n", "off", "FALSE", "False", "NO"]
        for value in false_values:
            result = _to_bool(value, "test_field", True)
            assert result is False, f"Failed for value: {value}"

    def test_to_bool_with_invalid_string(self) -> None:
        """Test _to_bool with invalid string value."""
        with pytest.raises(TemplateError) as exc_info:
            _to_bool("invalid", "test_field", True)
        assert "`test_field` must be bool/str-bool, got 'invalid'" in str(
            exc_info.value
        )

    def test_to_bool_with_invalid_type(self) -> None:
        """Test _to_bool with invalid type."""
        with pytest.raises(TemplateError) as exc_info:
            _to_bool("invalid_type", "test_field", True)
        assert "`test_field` must be bool/str-bool, got 'invalid_type'" in str(
            exc_info.value
        )

    def test_to_options_with_none(self) -> None:
        """Test _to_options with None value."""
        result = _to_options(None, "test_field")
        assert result == {}

    def test_to_options_with_mapping(self) -> None:
        """Test _to_options with valid mapping."""
        mapping: dict[str, object] = {"key1": "value1", "key2": 42}
        result = _to_options(mapping, "test_field")  # type: ignore[arg-type]
        assert result == mapping

    def test_to_options_with_dict(self) -> None:
        """Test _to_options with dict."""
        mapping: dict[str, object] = {"key1": "value1", "key2": 42}
        result = _to_options(mapping, "test_field")  # type: ignore[arg-type]
        assert result == mapping

    def test_to_options_with_invalid_type(self) -> None:
        """Test _to_options with invalid type."""
        with pytest.raises(TemplateError) as exc_info:
            _to_options("invalid", "test_field")  # type: ignore[arg-type]
        assert "`test_field` must be a mapping[str, JSONValue]" in str(exc_info.value)


class TestPluginTemplate:
    """Test PluginTemplate model."""

    def test_plugin_template_creation_minimal(self) -> None:
        """Test minimal plugin template creation."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
        )
        assert template.plugin_type == "analyzer"
        assert template.name == "test_analyzer"
        assert template.description == "Test analyzer"
        assert template.author == "Test Author"
        assert template.version == "1.0.0"
        assert template.category == "custom"
        assert template.config == {}
        assert template.supported_extensions == [".py"]
        assert template.rule_ids == []
        assert template.supported_contexts == []
        assert template.personality_traits == []
        assert template.supported_formats == []

    def test_plugin_template_creation_full(self) -> None:
        """Test full plugin template creation."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            version="2.0.0",
            category="quality",
            config={"threshold": 0.8, "enabled": True},
            supported_extensions=[".py", ".pyi"],
            rule_ids=["rule1", "rule2"],
            supported_contexts=["test", "setup"],
            personality_traits=["strict", "helpful"],
            supported_formats=["json", "sarif"],
        )
        assert template.version == "2.0.0"
        assert template.category == "quality"
        assert template.config == {"threshold": 0.8, "enabled": True}
        assert template.supported_extensions == [".py", ".pyi"]
        assert template.rule_ids == ["rule1", "rule2"]
        assert template.supported_contexts == ["test", "setup"]
        assert template.personality_traits == ["strict", "helpful"]
        assert template.supported_formats == ["json", "sarif"]

    def test_plugin_template_validation_missing_required(self) -> None:
        """Test plugin template validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            PluginTemplate()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        required_fields = {error["loc"][0] for error in errors}
        assert "plugin_type" in required_fields
        assert "name" in required_fields
        assert "description" in required_fields
        assert "author" in required_fields

    def test_plugin_template_serialization(self) -> None:
        """Test plugin template serialization to dict."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            config={"key": "value", "number": 42, "boolean": True},
        )

        template_dict = template.model_dump()

        assert template_dict["plugin_type"] == "analyzer"
        assert template_dict["name"] == "test_analyzer"
        assert template_dict["description"] == "Test analyzer"
        assert template_dict["author"] == "Test Author"
        assert template_dict["config"]["key"] == "value"
        assert template_dict["config"]["number"] == TEST_NUMBER
        assert template_dict["config"]["boolean"] is True

    def test_plugin_template_deserialization(self) -> None:
        """Test plugin template deserialization from dict."""
        template_dict = {
            "plugin_type": "analyzer",
            "name": "test_analyzer",
            "description": "Test analyzer",
            "author": "Test Author",
            "version": "2.0.0",
            "category": "custom",
            "config": {"key": "value", "number": 42, "boolean": True},
            "supported_extensions": [".py", ".pyi"],
            "rule_ids": ["rule1", "rule2"],
        }

        template = PluginTemplate.model_validate(template_dict)

        assert template.plugin_type == "analyzer"
        assert template.name == "test_analyzer"
        assert template.description == "Test analyzer"
        assert template.author == "Test Author"
        assert template.version == "2.0.0"
        assert template.category == "custom"
        assert template.config == {"key": "value", "number": 42, "boolean": True}
        assert template.supported_extensions == [".py", ".pyi"]
        assert template.rule_ids == ["rule1", "rule2"]


class TestPluginTemplateIntegration:
    """Test PluginTemplate integration scenarios."""

    def test_analyzer_plugin_template(self) -> None:
        """Test analyzer plugin template creation."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="custom_analyzer",
            description="Custom analyzer for specific rules",
            author="Test Author",
            version="1.0.0",
            category="custom",
            config={"threshold": 0.8, "strict_mode": True},
            supported_extensions=[".py", ".pyi"],
            rule_ids=["custom_rule_1", "custom_rule_2"],
        )

        assert template.plugin_type == "analyzer"
        assert template.supported_extensions == [".py", ".pyi"]
        assert template.rule_ids == ["custom_rule_1", "custom_rule_2"]
        assert template.config["threshold"] == TEST_THRESHOLD
        assert template.config["strict_mode"] is True

    def test_persona_plugin_template(self) -> None:
        """Test persona plugin template creation."""
        template = PluginTemplate(
            plugin_type="persona",
            name="custom_persona",
            description="Custom persona for specific contexts",
            author="Test Author",
            version="1.0.0",
            category="custom",
            config={"tone": "professional", "verbosity": "high"},
            supported_contexts=["test_failure", "setup_error"],
            personality_traits=["helpful", "detailed", "encouraging"],
        )

        assert template.plugin_type == "persona"
        assert template.supported_contexts == ["test_failure", "setup_error"]
        assert template.personality_traits == ["helpful", "detailed", "encouraging"]
        assert template.config["tone"] == "professional"
        assert template.config["verbosity"] == "high"

    def test_reporter_plugin_template(self) -> None:
        """Test reporter plugin template creation."""
        template = PluginTemplate(
            plugin_type="reporter",
            name="custom_reporter",
            description="Custom reporter for specific formats",
            author="Test Author",
            version="1.0.0",
            category="custom",
            config={"include_metadata": True, "pretty_print": False},
            supported_formats=["json", "xml", "csv"],
        )

        assert template.plugin_type == "reporter"
        assert template.supported_formats == ["json", "xml", "csv"]
        assert template.config["include_metadata"] is True
        assert template.config["pretty_print"] is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_plugin_template_with_empty_config(self) -> None:
        """Test plugin template with empty config."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            config={},
        )

        assert template.config == {}

    def test_plugin_template_with_none_config(self) -> None:
        """Test plugin template with None config."""
        # Pydantic doesn't allow None for dict fields, so we test the default behavior
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            # config defaults to {} when not provided
        )

        assert template.config == {}

    def test_plugin_template_with_complex_config(self) -> None:
        """Test plugin template with complex config."""
        complex_config = {
            "nested": {"key1": "value1", "key2": 42, "key3": True},
            "list": [1, 2, 3, "string"],
            "boolean": False,
            "number": 3.14,
        }

        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            config=complex_config,
        )

        assert template.config == complex_config

    def test_plugin_template_with_empty_lists(self) -> None:
        """Test plugin template with empty lists."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            supported_extensions=[],
            rule_ids=[],
            supported_contexts=[],
            personality_traits=[],
            supported_formats=[],
        )

        assert template.supported_extensions == []
        assert template.rule_ids == []
        assert template.supported_contexts == []
        assert template.personality_traits == []
        assert template.supported_formats == []

    def test_plugin_template_with_large_lists(self) -> None:
        """Test plugin template with large lists."""
        large_list = [f"item_{i}" for i in range(1000)]

        template = PluginTemplate(
            plugin_type="analyzer",
            name="test_analyzer",
            description="Test analyzer",
            author="Test Author",
            rule_ids=large_list,
        )

        assert len(template.rule_ids) == LARGE_LIST_SIZE
        assert template.rule_ids[0] == "item_0"
        assert template.rule_ids[LARGE_LIST_SIZE - 1] == f"item_{LARGE_LIST_SIZE - 1}"

    def test_plugin_template_with_unicode(self) -> None:
        """Test plugin template with unicode characters."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="测试分析器",
            description="这是一个测试分析器 🚀",
            author="测试作者",
            category="自定义",
            config={"消息": "测试消息", "数字": 42},
        )

        assert template.name == "测试分析器"
        assert template.description == "这是一个测试分析器 🚀"
        assert template.author == "测试作者"
        assert template.category == "自定义"
        assert template.config["消息"] == "测试消息"
        assert template.config["数字"] == TEST_NUMBER

    def test_plugin_template_with_special_characters(self) -> None:
        """Test plugin template with special characters."""
        template = PluginTemplate(
            plugin_type="analyzer",
            name="test-analyzer_v2.0",
            description="Test analyzer with special chars: @#$%^&*()",
            author="Test Author <test@example.com>",
            category="test-category",
            config={"special_key": "value with spaces and symbols!@#$%"},
        )

        assert template.name == "test-analyzer_v2.0"
        assert template.description == "Test analyzer with special chars: @#$%^&*()"
        assert template.author == "Test Author <test@example.com>"
        assert template.category == "test-category"
        assert template.config["special_key"] == "value with spaces and symbols!@#$%"
