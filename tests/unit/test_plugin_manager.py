"""Tests for the plugin manager and registry system."""

from unittest.mock import patch

import pytest

from pytest_drill_sergeant.core.config import DrillSergeantConfig
from pytest_drill_sergeant.plugin.base import (
    AnalyzerPlugin,
    DrillSergeantPlugin,
    PersonaPlugin,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    ReporterPlugin,
)

# Test constants
PLUGIN_CREATION_FAILED_MSG = "Plugin creation failed"


class PluginCreationError(Exception):
    """Custom exception for plugin creation failures."""


class MockPlugin(DrillSergeantPlugin):
    """Mock plugin for testing."""

    def __init__(self, config, metadata):
        super().__init__(config, metadata)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def cleanup(self) -> None:
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def mark_initialized(self) -> None:
        self._initialized = True


class MockAnalyzerPlugin(AnalyzerPlugin):
    """Mock analyzer plugin for testing."""

    def __init__(self, config, metadata):
        super().__init__(config, metadata)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def cleanup(self) -> None:
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def mark_initialized(self) -> None:
        self._initialized = True

    def analyze_file(self, _file_path, _content):
        return []

    def get_rule_ids(self):
        return ["test_rule"]

    def get_supported_extensions(self):
        return [".py"]


class MockPersonaPlugin(PersonaPlugin):
    """Mock persona plugin for testing."""

    def __init__(self, config, metadata):
        super().__init__(config, metadata)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def cleanup(self) -> None:
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def mark_initialized(self) -> None:
        self._initialized = True

    def generate_message(self, _context, _finding):
        return "Test message"

    def get_supported_contexts(self):
        return ["test"]


class MockReporterPlugin(ReporterPlugin):
    """Mock reporter plugin for testing."""

    def __init__(self, config, metadata):
        super().__init__(config, metadata)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def cleanup(self) -> None:
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def mark_initialized(self) -> None:
        self._initialized = True

    def generate_report(self, _findings, _output_path):
        return "Test report"

    def get_supported_formats(self):
        return ["test"]


class TestPluginRegistry:
    """Test the PluginRegistry class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.registry = PluginRegistry()

    def test_init(self) -> None:
        """Test registry initialization."""
        assert self.registry._plugins == {}
        assert self.registry._metadata == {}
        assert self.registry._by_category == {}

    def test_register_plugin(self) -> None:
        """Test registering a plugin."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        with patch.object(self.registry._logger, "info") as mock_info:
            self.registry.register_plugin(plugin)

            assert "test_plugin" in self.registry._plugins
            assert self.registry._plugins["test_plugin"] is plugin
            assert "test_plugin" in self.registry._metadata
            assert self.registry._metadata["test_plugin"] is metadata
            assert "analyzer" in self.registry._by_category
            assert "test_plugin" in self.registry._by_category["analyzer"]
            mock_info.assert_called_once_with(
                "Registered plugin: %s (%s)", "test_plugin", "Test Plugin"
            )

    def test_register_plugin_duplicate(self) -> None:
        """Test registering a duplicate plugin."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin1 = MockPlugin(config, metadata)
        plugin2 = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin1)

        with pytest.raises(
            ValueError, match="Plugin test_plugin is already registered"
        ):
            self.registry.register_plugin(plugin2)

    def test_unregister_plugin(self) -> None:
        """Test unregistering a plugin."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        with patch.object(self.registry._logger, "info") as mock_info:
            self.registry.unregister_plugin("test_plugin")

            assert "test_plugin" not in self.registry._plugins
            assert "test_plugin" not in self.registry._metadata
            assert "test_plugin" not in self.registry._by_category["analyzer"]
            mock_info.assert_called_once_with("Unregistered plugin: %s", "test_plugin")

    def test_unregister_plugin_not_found(self) -> None:
        """Test unregistering a non-existent plugin."""
        with patch.object(self.registry._logger, "warning") as mock_warning:
            self.registry.unregister_plugin("nonexistent")

            mock_warning.assert_called_once_with(
                "Plugin %s not found for unregistration", "nonexistent"
            )

    def test_get_plugin(self) -> None:
        """Test getting a plugin by ID."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        result = self.registry.get_plugin("test_plugin")
        assert result is plugin

        result = self.registry.get_plugin("nonexistent")
        assert result is None

    def test_get_plugins_by_category(self) -> None:
        """Test getting plugins by category."""
        config = DrillSergeantConfig()

        # Register analyzer plugin
        analyzer_metadata = PluginMetadata(
            plugin_id="analyzer_plugin",
            name="Analyzer Plugin",
            version="1.0.0",
            description="An analyzer plugin",
            author="Test Author",
            category="analyzer",
        )
        analyzer_plugin = MockPlugin(config, analyzer_metadata)
        self.registry.register_plugin(analyzer_plugin)

        # Register persona plugin
        persona_metadata = PluginMetadata(
            plugin_id="persona_plugin",
            name="Persona Plugin",
            version="1.0.0",
            description="A persona plugin",
            author="Test Author",
            category="persona",
        )
        persona_plugin = MockPlugin(config, persona_metadata)
        self.registry.register_plugin(persona_plugin)

        # Test getting analyzers
        analyzers = self.registry.get_plugins_by_category("analyzer")
        assert len(analyzers) == 1
        assert analyzers[0] is analyzer_plugin

        # Test getting personas
        personas = self.registry.get_plugins_by_category("persona")
        assert len(personas) == 1
        assert personas[0] is persona_plugin

        # Test getting non-existent category
        empty = self.registry.get_plugins_by_category("nonexistent")
        assert empty == []

    def test_get_enabled_plugins(self) -> None:
        """Test getting enabled plugins."""
        config = DrillSergeantConfig()

        # Register enabled plugin
        enabled_metadata = PluginMetadata(
            plugin_id="enabled_plugin",
            name="Enabled Plugin",
            version="1.0.0",
            description="An enabled plugin",
            author="Test Author",
            category="analyzer",
            enabled=True,
        )
        enabled_plugin = MockPlugin(config, enabled_metadata)
        self.registry.register_plugin(enabled_plugin)

        # Register disabled plugin
        disabled_metadata = PluginMetadata(
            plugin_id="disabled_plugin",
            name="Disabled Plugin",
            version="1.0.0",
            description="A disabled plugin",
            author="Test Author",
            category="analyzer",
            enabled=False,
        )
        disabled_plugin = MockPlugin(config, disabled_metadata)
        self.registry.register_plugin(disabled_plugin)

        enabled_plugins = self.registry.get_enabled_plugins()
        assert len(enabled_plugins) == 1
        assert enabled_plugins[0] is enabled_plugin

    def test_initialize_all(self) -> None:
        """Test initializing all plugins."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        with (
            patch.object(plugin, "initialize") as mock_initialize,
            patch.object(plugin, "mark_initialized") as mock_mark,
        ):
            self.registry.initialize_all()

            mock_initialize.assert_called_once()
            mock_mark.assert_called_once()

    def test_initialize_all_with_exception(self) -> None:
        """Test initializing all plugins with exception."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        with (
            patch.object(plugin, "initialize", side_effect=Exception("Init failed")),
            patch.object(self.registry._logger, "exception") as mock_exception,
        ):
            self.registry.initialize_all()

            mock_exception.assert_called_once()

    def test_cleanup_all(self) -> None:
        """Test cleaning up all plugins."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        with patch.object(plugin, "cleanup") as mock_cleanup:
            self.registry.cleanup_all()

            mock_cleanup.assert_called_once()

    def test_cleanup_all_with_exception(self) -> None:
        """Test cleaning up all plugins with exception."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        with (
            patch.object(plugin, "cleanup", side_effect=Exception("Cleanup failed")),
            patch.object(self.registry._logger, "exception") as mock_exception,
        ):
            self.registry.cleanup_all()

            mock_exception.assert_called_once()

    def test_list_plugins(self) -> None:
        """Test listing all plugins."""
        config = DrillSergeantConfig()
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )
        plugin = MockPlugin(config, metadata)

        self.registry.register_plugin(plugin)

        plugins = self.registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0] is metadata


class TestPluginManager:
    """Test the PluginManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = DrillSergeantConfig()
        self.manager = PluginManager(self.config)

    def test_init(self) -> None:
        """Test manager initialization."""
        assert self.manager.config is self.config
        assert isinstance(self.manager.registry, PluginRegistry)

    def test_load_plugin(self) -> None:
        """Test loading a plugin."""
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        with (
            patch.object(self.manager.registry, "register_plugin") as mock_register,
            patch.object(self.manager._logger, "info") as mock_info,
        ):
            self.manager.load_plugin(MockPlugin, metadata)

            mock_register.assert_called_once()
            mock_info.assert_called_once_with("Loaded plugin: %s", "test_plugin")

    def test_load_plugin_with_exception(self) -> None:
        """Test loading a plugin with exception."""
        metadata = PluginMetadata(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="analyzer",
        )

        class FailingPlugin(DrillSergeantPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)
                raise PluginCreationError(PLUGIN_CREATION_FAILED_MSG)

            def initialize(self) -> None:
                pass

            def cleanup(self) -> None:
                pass

        with patch.object(self.manager._logger, "exception") as mock_exception:
            with pytest.raises(Exception, match="Plugin creation failed"):
                self.manager.load_plugin(FailingPlugin, metadata)

            mock_exception.assert_called_once()

    def test_get_analyzers(self) -> None:
        """Test getting analyzer plugins."""
        metadata = PluginMetadata(
            plugin_id="analyzer_plugin",
            name="Analyzer Plugin",
            version="1.0.0",
            description="An analyzer plugin",
            author="Test Author",
            category="analyzer",
        )
        analyzer_plugin = MockAnalyzerPlugin(self.config, metadata)

        with patch.object(self.manager.registry, "get_plugins_by_category") as mock_get:
            mock_get.return_value = [analyzer_plugin]

            analyzers = self.manager.get_analyzers()

            assert len(analyzers) == 1
            assert analyzers[0] is analyzer_plugin
            mock_get.assert_called_once_with("analyzer")

    def test_get_personas(self) -> None:
        """Test getting persona plugins."""
        metadata = PluginMetadata(
            plugin_id="persona_plugin",
            name="Persona Plugin",
            version="1.0.0",
            description="A persona plugin",
            author="Test Author",
            category="persona",
        )
        persona_plugin = MockPersonaPlugin(self.config, metadata)

        with patch.object(self.manager.registry, "get_plugins_by_category") as mock_get:
            mock_get.return_value = [persona_plugin]

            personas = self.manager.get_personas()

            assert len(personas) == 1
            assert personas[0] is persona_plugin
            mock_get.assert_called_once_with("persona")

    def test_get_reporters(self) -> None:
        """Test getting reporter plugins."""
        metadata = PluginMetadata(
            plugin_id="reporter_plugin",
            name="Reporter Plugin",
            version="1.0.0",
            description="A reporter plugin",
            author="Test Author",
            category="reporter",
        )
        reporter_plugin = MockReporterPlugin(self.config, metadata)

        with patch.object(self.manager.registry, "get_plugins_by_category") as mock_get:
            mock_get.return_value = [reporter_plugin]

            reporters = self.manager.get_reporters()

            assert len(reporters) == 1
            assert reporters[0] is reporter_plugin
            mock_get.assert_called_once_with("reporter")

    def test_initialize_all(self) -> None:
        """Test initializing all plugins."""
        with patch.object(self.manager.registry, "initialize_all") as mock_init:
            self.manager.initialize_all()
            mock_init.assert_called_once()

    def test_cleanup_all(self) -> None:
        """Test cleaning up all plugins."""
        with patch.object(self.manager.registry, "cleanup_all") as mock_cleanup:
            self.manager.cleanup_all()
            mock_cleanup.assert_called_once()
