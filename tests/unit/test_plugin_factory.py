"""Tests for the plugin factory system."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pytest_drill_sergeant.core.models import Config
from pytest_drill_sergeant.plugin.base import (
    AnalyzerPlugin,
    DrillSergeantPlugin,
    PluginMetadata,
)
from pytest_drill_sergeant.plugin.factory import (
    PluginConfigError,
    PluginFactory,
    PluginSpec,
    _create_attribute_error,
    _create_import_error,
    _create_invalid_class_error,
    _create_plugin_config_error,
    _extract_bool_field,
    _extract_dependencies_field,
    _extract_int_field,
    _extract_string_field,
    _is_plugin_class,
    _parse_plugin_metadata,
    _to_bool,
    _to_mapping,
    load_plugin_from_module,
)

# Test constants to avoid magic numbers
PRIORITY_5 = 5
FIELD_VALUE_42 = 42
DEFAULT_VALUE_10 = 10
NO_ATTRIBUTE_MSG = "No attribute"


class TestPluginSpec:
    """Test the PluginSpec class."""

    def test_plugin_spec_creation(self) -> None:
        """Test creating a PluginSpec."""
        spec = PluginSpec(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        assert spec.plugin_id == "test_plugin"
        assert spec.name == "Test Plugin"
        assert spec.version == "1.0.0"
        assert spec.description == "A test plugin"
        assert spec.author == "Test Author"
        assert spec.category == "analyzer"


class TestPluginFactory:
    """Test the PluginFactory class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = Config()
        self.factory = PluginFactory(self.config)

    def test_init(self) -> None:
        """Test factory initialization."""
        assert self.factory.config is self.config
        assert hasattr(self.factory, "manager")

    def test_create_analyzer_plugin_basic(self) -> None:
        """Test creating an analyzer plugin with basic functionality."""
        spec = PluginSpec(
            plugin_id="test_analyzer",
            name="Test Analyzer",
            version="1.0.0",
            description="A test analyzer",
            author="Test Author",
            category="analyzer",
        )

        # Mock plugin class that implements required methods
        class MockAnalyzerPlugin(AnalyzerPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)

            def initialize(self) -> None:
                pass

            def cleanup(self) -> None:
                pass

            def analyze_file(self, _file_path, _content):
                return []

            def get_rule_ids(self):
                return ["rule"]

            def get_supported_extensions(self):
                return [".py"]

        with patch.object(
            self.factory.manager.registry, "register_plugin"
        ) as mock_register:
            plugin = self.factory.create_analyzer_plugin(spec, MockAnalyzerPlugin)

            assert isinstance(plugin, MockAnalyzerPlugin)
            assert plugin.config is self.config
            assert plugin.metadata.plugin_id == "test_analyzer"
            mock_register.assert_called_once_with(plugin)

    def test_create_analyzer_plugin_with_kwargs(self) -> None:
        """Test creating an analyzer plugin with additional kwargs."""
        spec = PluginSpec(
            plugin_id="test_analyzer",
            name="Test Analyzer",
            version="1.0.0",
            description="A test analyzer",
            author="Test Author",
            category="analyzer",
        )

        class MockAnalyzerPlugin(AnalyzerPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)

            def initialize(self) -> None:
                pass

            def cleanup(self) -> None:
                pass

            def analyze_file(self, _file_path, _content):
                return []

            def get_rule_ids(self):
                return ["rule"]

            def get_supported_extensions(self):
                return [".py"]

        with patch.object(
            self.factory.manager.registry, "register_plugin"
        ) as mock_register:
            plugin = self.factory.create_analyzer_plugin(
                spec,
                MockAnalyzerPlugin,
                enabled=False,
                priority=5,
                dependencies=["dep1", "dep2"],
            )

            assert isinstance(plugin, MockAnalyzerPlugin)
            assert plugin.metadata.enabled is False
            assert plugin.metadata.priority == PRIORITY_5
            assert plugin.metadata.dependencies == ["dep1", "dep2"]
            mock_register.assert_called_once_with(plugin)


class TestHelperFunctions:
    """Test helper functions in the factory module."""

    def test_to_bool_true_values(self) -> None:
        """Test _to_bool with true values."""
        assert _to_bool(True, "test") is True
        assert _to_bool("true", "test") is True
        assert _to_bool("1", "test") is True
        assert _to_bool("yes", "test") is True
        assert _to_bool("on", "test") is True

    def test_to_bool_false_values(self) -> None:
        """Test _to_bool with false values."""
        assert _to_bool(False, "test") is False
        assert _to_bool("false", "test") is False
        assert _to_bool("0", "test") is False
        assert _to_bool("no", "test") is False
        assert _to_bool("off", "test") is False

    def test_to_bool_default(self) -> None:
        """Test _to_bool with default values."""
        assert _to_bool(None, "test", default=True) is True
        assert _to_bool(None, "test", default=False) is False

    def test_to_bool_invalid(self) -> None:
        """Test _to_bool with invalid values."""
        with pytest.raises(PluginConfigError):
            _to_bool("invalid", "test")

    def test_to_mapping_valid(self) -> None:
        """Test _to_mapping with valid mapping."""
        mapping = {"key": "value"}
        result = _to_mapping(mapping, "test")
        assert result == mapping

    def test_to_mapping_none(self) -> None:
        """Test _to_mapping with None."""
        result = _to_mapping(None, "test")
        assert result == {}

    def test_to_mapping_invalid(self) -> None:
        """Test _to_mapping with invalid type."""
        with pytest.raises(PluginConfigError):
            _to_mapping("not_a_mapping", "test")  # type: ignore[arg-type]

    def test_create_plugin_config_error(self) -> None:
        """Test _create_plugin_config_error."""
        error = _create_plugin_config_error(1, "field", "string")
        assert isinstance(error, PluginConfigError)
        assert "Plugin #1" in str(error)
        assert "field" in str(error)
        assert "string" in str(error)

    def test_create_import_error(self) -> None:
        """Test _create_import_error."""
        error = _create_import_error("test.module")
        assert isinstance(error, PluginConfigError)
        assert "Cannot import module" in str(error)
        assert "test.module" in str(error)

    def test_create_attribute_error(self) -> None:
        """Test _create_attribute_error."""
        error = _create_attribute_error("test.module", "TestClass")
        assert isinstance(error, PluginConfigError)
        assert "test.module" in str(error)
        assert "TestClass" in str(error)

    def test_create_invalid_class_error(self) -> None:
        """Test _create_invalid_class_error."""
        error = _create_invalid_class_error("test.module", "TestClass")
        assert isinstance(error, PluginConfigError)
        assert "test.module.TestClass" in str(error)

    def test_extract_string_field(self) -> None:
        """Test _extract_string_field."""
        metadata = {"field": "value"}
        result = _extract_string_field(metadata, 1, "field")
        assert result == "value"

    def test_extract_string_field_default(self) -> None:
        """Test _extract_string_field with default."""
        metadata: dict[str, object] = {}
        result = _extract_string_field(metadata, 1, "field", "default")  # type: ignore[arg-type]
        assert result == "default"

    def test_extract_string_field_invalid(self) -> None:
        """Test _extract_string_field with invalid type."""
        metadata = {"field": 123}
        with pytest.raises(PluginConfigError):
            _extract_string_field(metadata, 1, "field")

    def test_extract_dependencies_field_valid(self) -> None:
        """Test _extract_dependencies_field with valid list."""
        metadata = {"dependencies": ["dep1", "dep2"]}
        result = _extract_dependencies_field(metadata)  # type: ignore[arg-type]
        assert result == ["dep1", "dep2"]

    def test_extract_dependencies_field_invalid(self) -> None:
        """Test _extract_dependencies_field with invalid type."""
        metadata = {"dependencies": "not_a_list"}
        result = _extract_dependencies_field(metadata)
        assert result == []

    def test_extract_bool_field(self) -> None:
        """Test _extract_bool_field."""
        metadata = {"field": True}
        result = _extract_bool_field(metadata, "field")
        assert result is True

    def test_extract_bool_field_default(self) -> None:
        """Test _extract_bool_field with default."""
        metadata = {"field": "invalid"}
        result = _extract_bool_field(metadata, "field", False)
        assert result is False

    def test_extract_int_field(self) -> None:
        """Test _extract_int_field."""
        metadata = {"field": 42}
        result = _extract_int_field(metadata, "field")
        assert result == FIELD_VALUE_42

    def test_extract_int_field_default(self) -> None:
        """Test _extract_int_field with default."""
        metadata = {"field": "invalid"}
        result = _extract_int_field(metadata, "field", 10)
        assert result == DEFAULT_VALUE_10

    def test_parse_plugin_metadata(self) -> None:
        """Test _parse_plugin_metadata."""
        metadata_dict: dict[str, object] = {
            "plugin_id": "test_plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "A test plugin",
            "author": "Test Author",
            "category": "analyzer",
            "enabled": True,
            "priority": 5,
            "dependencies": ["dep1", "dep2"],
        }

        metadata = _parse_plugin_metadata(1, metadata_dict)  # type: ignore[arg-type]

        assert isinstance(metadata, PluginMetadata)
        assert metadata.plugin_id == "test_plugin"
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test plugin"
        assert metadata.author == "Test Author"
        assert metadata.category == "analyzer"
        assert metadata.enabled is True
        assert metadata.priority == PRIORITY_5
        assert metadata.dependencies == ["dep1", "dep2"]

    def test_is_plugin_class_valid(self) -> None:
        """Test _is_plugin_class with valid plugin class."""

        class ValidPlugin(DrillSergeantPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)

        assert _is_plugin_class(ValidPlugin) is True

    def test_is_plugin_class_invalid(self) -> None:
        """Test _is_plugin_class with invalid class."""

        class InvalidPlugin:
            pass

        assert _is_plugin_class(InvalidPlugin) is False
        assert _is_plugin_class("not_a_class") is False
        assert _is_plugin_class(None) is False

    def test_load_plugin_from_module_success(self) -> None:
        """Test load_plugin_from_module with successful load."""
        config = Config()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        class MockPlugin(DrillSergeantPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)

            def initialize(self) -> None:
                pass

            def cleanup(self) -> None:
                pass

        with patch(
            "pytest_drill_sergeant.plugin.factory.importlib.import_module"
        ) as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = MockPlugin
            mock_import.return_value = mock_module

            plugin = load_plugin_from_module(
                "test.module", "TestPlugin", config, metadata
            )

            assert isinstance(plugin, MockPlugin)
            assert plugin.config is config
            assert plugin.metadata is metadata

    def test_load_plugin_from_module_import_error(self) -> None:
        """Test load_plugin_from_module with import error."""
        config = Config()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        with patch(
            "pytest_drill_sergeant.plugin.factory.importlib.import_module"
        ) as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(PluginConfigError, match="Cannot import module"):
                load_plugin_from_module("test.module", "TestPlugin", config, metadata)

    def test_load_plugin_from_module_attribute_error(self) -> None:
        """Test load_plugin_from_module with attribute error."""
        config = Config()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        with patch(
            "pytest_drill_sergeant.plugin.factory.importlib.import_module"
        ) as mock_import:
            mock_module = SimpleNamespace()
            mock_import.return_value = mock_module

            with pytest.raises(PluginConfigError, match="has no class"):
                load_plugin_from_module("test.module", "TestPlugin", config, metadata)

    def test_load_plugin_from_module_invalid_class(self) -> None:
        """Test load_plugin_from_module with invalid class."""
        config = Config()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        class InvalidPlugin:
            pass

        with patch(
            "pytest_drill_sergeant.plugin.factory.importlib.import_module"
        ) as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = InvalidPlugin
            mock_import.return_value = mock_module

            with pytest.raises(PluginConfigError, match="not a valid plugin class"):
                load_plugin_from_module("test.module", "TestPlugin", config, metadata)
