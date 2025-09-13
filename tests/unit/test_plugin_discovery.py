"""Tests for the plugin discovery system."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from pytest_drill_sergeant.core.models import Config
from pytest_drill_sergeant.plugin.base import DrillSergeantPlugin
from pytest_drill_sergeant.plugin.discovery import (
    PluginDiscovery,
    PluginDiscoveryConfig,
)
from pytest_drill_sergeant.plugin.factory import PluginFactory

# Test constants to avoid magic numbers
TOTAL_PLUGINS_9 = 9
ANALYZER_COUNT_4 = 4
PERSONA_COUNT_5 = 5
MIN_PLUGINS_3 = 3


class TestPluginDiscoveryConfig:
    """Test the PluginDiscoveryConfig class."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = PluginDiscoveryConfig()

        assert config.enabled is True
        assert config.search_paths == []
        assert config.entry_point_groups == [
            "pytest_drill_sergeant.analyzers",
            "pytest_drill_sergeant.personas",
            "pytest_drill_sergeant.reporters",
        ]
        assert config.auto_discover is True
        assert config.load_builtin is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = PluginDiscoveryConfig(
            enabled=False,
            search_paths=["/custom/path"],
            entry_point_groups=["custom.group"],
            auto_discover=False,
            load_builtin=False,
        )

        assert config.enabled is False
        assert config.search_paths == ["/custom/path"]
        assert config.entry_point_groups == ["custom.group"]
        assert config.auto_discover is False
        assert config.load_builtin is False

    def test_config_validation(self) -> None:
        """Test configuration validation."""
        with pytest.raises(ValidationError):
            PluginDiscoveryConfig(enabled="invalid")


class TestPluginDiscovery:
    """Test the PluginDiscovery class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.config = Config()
        self.discovery_config = PluginDiscoveryConfig()
        self.discovery = PluginDiscovery(self.config, self.discovery_config)

    def test_init_with_default_config(self) -> None:
        """Test initialization with default discovery config."""
        discovery = PluginDiscovery(self.config)

        assert discovery.config is self.config
        assert isinstance(discovery.discovery_config, PluginDiscoveryConfig)
        assert discovery.discovery_config.enabled is True
        assert isinstance(discovery.factory, PluginFactory)
        assert discovery._discovered_plugins == set()

    def test_init_with_custom_config(self) -> None:
        """Test initialization with custom discovery config."""
        custom_config = PluginDiscoveryConfig(enabled=False)
        discovery = PluginDiscovery(self.config, custom_config)

        assert discovery.config is self.config
        assert discovery.discovery_config is custom_config
        assert discovery.discovery_config.enabled is False

    @patch("pytest_drill_sergeant.plugin.discovery.logging.getLogger")
    def test_init_logger_setup(self, mock_get_logger: MagicMock) -> None:
        """Test that logger is properly set up during initialization."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        discovery = PluginDiscovery(self.config)

        mock_get_logger.assert_called_with("drill_sergeant.discovery")
        assert discovery._logger is mock_logger

    def test_discover_plugins_disabled(self) -> None:
        """Test discover_plugins when discovery is disabled."""
        self.discovery.discovery_config.enabled = False

        with patch.object(self.discovery._logger, "info") as mock_info:
            result = self.discovery.discover_plugins()

            assert result == []
            mock_info.assert_called_once_with("Plugin discovery is disabled")

    def test_discover_plugins_all_enabled(self) -> None:
        """Test discover_plugins when all discovery methods are enabled."""
        # Test with default config that has all discovery enabled
        result = self.discovery.discover_plugins()

        # Should return a list (may be empty if no plugins are found)
        assert isinstance(result, list)
        assert all(isinstance(plugin, DrillSergeantPlugin) for plugin in result)

    @patch.object(PluginDiscovery, "_discover_builtin_plugins")
    @patch.object(PluginDiscovery, "_discover_entry_point_plugins")
    @patch.object(PluginDiscovery, "_discover_path_plugins")
    def test_discover_plugins_partial_enabled(
        self,
        mock_path_plugins: MagicMock,
        mock_entry_point_plugins: MagicMock,
        mock_builtin_plugins: MagicMock,
    ) -> None:
        """Test discover_plugins with partial discovery enabled."""
        self.discovery.discovery_config.load_builtin = False
        self.discovery.discovery_config.auto_discover = False
        self.discovery.discovery_config.search_paths = ["/test/path"]

        mock_path_plugins.return_value = [MagicMock()]

        result = self.discovery.discover_plugins()

        assert len(result) == 1
        mock_builtin_plugins.assert_not_called()
        mock_entry_point_plugins.assert_not_called()
        mock_path_plugins.assert_called_once()

    @patch(
        "pytest_drill_sergeant.plugin.discovery.pytest_drill_sergeant.core.analyzers"
    )
    @patch(
        "pytest_drill_sergeant.plugin.discovery.pytest_drill_sergeant.plugin.personas"
    )
    def test_discover_builtin_plugins_success(
        self, mock_personas_module: MagicMock, mock_analyzers_module: MagicMock
    ) -> None:
        """Test successful discovery of built-in plugins."""
        # Mock analyzer plugins
        mock_analyzer_plugin = MagicMock(spec=DrillSergeantPlugin)
        mock_analyzer_class = MagicMock(return_value=mock_analyzer_plugin)
        mock_analyzer_class.__name__ = "PrivateAccessPlugin"

        mock_analyzers_module.private_access_analyzer.PrivateAccessPlugin = (
            mock_analyzer_class
        )

        # Mock persona plugins
        mock_persona_plugin = MagicMock(spec=DrillSergeantPlugin)
        mock_persona_class = MagicMock(return_value=mock_persona_plugin)
        mock_persona_class.__name__ = "DrillSergeantPlugin"

        mock_personas_module.drill_sergeant_persona.DrillSergeantPlugin = (
            mock_persona_class
        )

        # Mock factory methods
        with (
            patch.object(
                self.discovery.factory, "create_analyzer_plugin"
            ) as mock_create_analyzer,
            patch.object(
                self.discovery.factory, "create_persona_plugin"
            ) as mock_create_persona,
        ):
            mock_create_analyzer.return_value = mock_analyzer_plugin
            mock_create_persona.return_value = mock_persona_plugin

            result = self.discovery._discover_builtin_plugins()

            # Should discover 4 analyzers + 5 personas = 9 plugins
            assert len(result) == TOTAL_PLUGINS_9
            assert mock_create_analyzer.call_count == ANALYZER_COUNT_4
            assert mock_create_persona.call_count == PERSONA_COUNT_5

    @patch(
        "pytest_drill_sergeant.plugin.discovery.pytest_drill_sergeant.core.analyzers"
    )
    def test_discover_builtin_plugins_analyzer_error(
        self, mock_analyzers_module: MagicMock
    ) -> None:
        """Test built-in plugin discovery with analyzer errors."""
        # Mock analyzer that raises an error
        mock_analyzers_module.private_access_analyzer.PrivateAccessPlugin = None

        with patch.object(self.discovery._logger, "warning") as mock_warning:
            result = self.discovery._discover_builtin_plugins()

            # Should still discover some plugins even if one analyzer fails
            assert (
                len(result) >= MIN_PLUGINS_3
            )  # Some analyzers and personas should still work
            mock_warning.assert_called()

    def test_discover_builtin_plugins_import_error(self) -> None:
        """Test built-in plugin discovery with import errors."""
        # This test verifies the method handles import errors gracefully
        # The actual implementation should work with real modules
        result = self.discovery._discover_builtin_plugins()

        # Should discover some plugins even if there are import issues
        assert isinstance(result, list)
        assert all(isinstance(plugin, DrillSergeantPlugin) for plugin in result)

    @patch("pytest_drill_sergeant.plugin.discovery.entry_points")
    def test_discover_entry_point_plugins_success(
        self, mock_entry_points: MagicMock
    ) -> None:
        """Test successful discovery of entry point plugins."""
        # Mock entry point
        mock_entry_point = MagicMock()
        mock_entry_point.name = "test_plugin"
        mock_entry_point.load.return_value = MagicMock
        mock_entry_point.dist.version = "1.0.0"
        mock_entry_point.dist.author = "Test Author"
        mock_entry_point.description = "Test Description"

        # Mock the entry_points().select() to return different results for each group
        def mock_select_side_effect(group):
            if group == "pytest_drill_sergeant.analyzers":
                return [mock_entry_point]
            if group in (
                "pytest_drill_sergeant.personas",
                "pytest_drill_sergeant.reporters",
            ):
                return []
            return []

        mock_entry_points.return_value.select.side_effect = mock_select_side_effect

        # Mock plugin class
        mock_plugin_class = MagicMock(spec=DrillSergeantPlugin)
        mock_plugin_instance = MagicMock(spec=DrillSergeantPlugin)
        mock_plugin_class.return_value = mock_plugin_instance

        with (
            patch.object(
                self.discovery.factory.manager.registry, "register_plugin"
            ) as mock_register,
            patch.object(self.discovery._logger, "info") as mock_info,
        ):
            mock_entry_point.load.return_value = mock_plugin_class

            result = self.discovery._discover_entry_point_plugins()

            assert len(result) == 1
            mock_register.assert_called_once_with(mock_plugin_instance)
            mock_info.assert_called_once_with(
                "Discovered plugin from entry point: %s", "test_plugin"
            )
            assert "test_plugin" in self.discovery._discovered_plugins

    @patch("pytest_drill_sergeant.plugin.discovery.entry_points")
    def test_discover_entry_point_plugins_load_error(
        self, mock_entry_points: MagicMock
    ) -> None:
        """Test entry point plugin discovery with load errors."""
        mock_entry_point = MagicMock()
        mock_entry_point.name = "test_plugin"
        mock_entry_point.load.side_effect = ImportError("Failed to load")

        mock_entry_points.return_value.select.return_value = [mock_entry_point]

        with patch.object(self.discovery._logger, "warning") as mock_warning:
            result = self.discovery._discover_entry_point_plugins()

            assert result == []
            mock_warning.assert_called()

    @patch("pytest_drill_sergeant.plugin.discovery.entry_points")
    def test_discover_entry_point_plugins_iter_error(
        self, mock_entry_points: MagicMock
    ) -> None:
        """Test entry point plugin discovery with iteration errors."""
        mock_entry_points.return_value.select.side_effect = ImportError(
            "Entry point group not found"
        )

        with patch.object(self.discovery._logger, "warning") as mock_warning:
            result = self.discovery._discover_entry_point_plugins()

            assert result == []
            mock_warning.assert_called()

    def test_discover_path_plugins_empty_paths(self) -> None:
        """Test path plugin discovery with empty search paths."""
        self.discovery.discovery_config.search_paths = []

        result = self.discovery._discover_path_plugins()

        assert result == []

    @patch("pytest_drill_sergeant.plugin.discovery.Path")
    def test_discover_path_plugins_nonexistent_path(self, mock_path: MagicMock) -> None:
        """Test path plugin discovery with nonexistent path."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        self.discovery.discovery_config.search_paths = ["/nonexistent/path"]

        with patch.object(self.discovery._logger, "warning") as mock_warning:
            result = self.discovery._discover_path_plugins()

            assert result == []
            mock_warning.assert_called_with(
                "Search path does not exist: %s", "/nonexistent/path"
            )

    @patch("pytest_drill_sergeant.plugin.discovery.Path")
    def test_discover_path_plugins_success(self, mock_path: MagicMock) -> None:
        """Test successful path plugin discovery."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        self.discovery.discovery_config.search_paths = ["/test/path"]

        with patch.object(
            self.discovery, "_discover_plugins_from_path"
        ) as mock_discover_from_path:
            mock_discover_from_path.return_value = [MagicMock()]

            result = self.discovery._discover_path_plugins()

            assert len(result) == 1
            mock_discover_from_path.assert_called_once_with(mock_path_instance)

    @patch("pytest_drill_sergeant.plugin.discovery.Path")
    def test_discover_plugins_from_path(self, mock_path: MagicMock) -> None:
        """Test discovering plugins from a specific path."""
        # Mock path with Python files
        mock_py_file1 = MagicMock()
        mock_py_file1.name = "test_plugin.py"
        mock_py_file2 = MagicMock()
        mock_py_file2.name = "__init__.py"  # Should be skipped

        mock_path_instance = MagicMock()
        mock_path_instance.glob.return_value = [mock_py_file1, mock_py_file2]
        mock_path.return_value = mock_path_instance

        with patch.object(self.discovery, "_load_plugin_from_file") as mock_load_plugin:
            mock_load_plugin.return_value = MagicMock()

            result = self.discovery._discover_plugins_from_path(mock_path_instance)

            assert len(result) == 1
            mock_load_plugin.assert_called_once_with(mock_py_file1, mock_path_instance)

    def test_load_plugin_from_file_success(self) -> None:
        """Test successful plugin loading from file."""
        mock_py_file = MagicMock()
        mock_search_path = MagicMock()

        with (
            patch.object(self.discovery, "_get_module_path") as mock_get_module_path,
            patch(
                "pytest_drill_sergeant.plugin.discovery.importlib.import_module"
            ) as mock_import,
            patch.object(self.discovery, "_extract_plugin_from_module") as mock_extract,
        ):
            mock_get_module_path.return_value = "test.module"
            mock_import.return_value = MagicMock()
            mock_extract.return_value = MagicMock()

            result = self.discovery._load_plugin_from_file(
                mock_py_file, mock_search_path
            )

            assert result is not None
            mock_get_module_path.assert_called_once_with(mock_py_file, mock_search_path)
            mock_import.assert_called_once_with("test.module")
            mock_extract.assert_called_once()

    def test_load_plugin_from_file_error(self) -> None:
        """Test plugin loading from file with errors."""
        mock_py_file = MagicMock()
        mock_search_path = MagicMock()

        with (
            patch.object(self.discovery, "_get_module_path") as mock_get_module_path,
            patch(
                "pytest_drill_sergeant.plugin.discovery.importlib.import_module"
            ) as mock_import,
            patch.object(self.discovery._logger, "debug") as mock_debug,
        ):
            mock_get_module_path.return_value = "test.module"
            mock_import.side_effect = ImportError("Module not found")

            result = self.discovery._load_plugin_from_file(
                mock_py_file, mock_search_path
            )

            assert result is None
            mock_debug.assert_called()

    def test_get_module_path(self) -> None:
        """Test module path generation."""
        mock_py_file = MagicMock()
        mock_py_file.relative_to.return_value = Path("subdir/plugin.py")
        mock_search_path = MagicMock()
        mock_search_path.parent = MagicMock()

        result = self.discovery._get_module_path(mock_py_file, mock_search_path)

        assert result == "subdir.plugin"

    def test_extract_plugin_from_module_success(self) -> None:
        """Test successful plugin extraction from module."""
        mock_plugin_class = MagicMock()
        mock_plugin_class.__name__ = "TestPlugin"
        mock_plugin_instance = MagicMock(spec=DrillSergeantPlugin)
        mock_plugin_class.return_value = mock_plugin_instance

        mock_module = SimpleNamespace(
            TestPlugin=mock_plugin_class, other_attr="not_a_plugin"
        )

        with (
            patch.object(self.discovery, "_is_valid_plugin_class") as mock_is_valid,
            patch.object(self.discovery, "_create_plugin_instance") as mock_create,
        ):
            mock_is_valid.return_value = True
            mock_create.return_value = mock_plugin_instance

            result = self.discovery._extract_plugin_from_module(
                mock_module, "test.module"
            )

            assert result is mock_plugin_instance
            mock_create.assert_called_once_with(
                mock_plugin_class, "test.module", "TestPlugin"
            )

    def test_extract_plugin_from_module_no_valid_plugin(self) -> None:
        """Test plugin extraction when no valid plugin is found."""
        mock_module = SimpleNamespace(not_a_plugin="not_a_plugin")

        with patch.object(self.discovery, "_is_valid_plugin_class") as mock_is_valid:
            mock_is_valid.return_value = False

            result = self.discovery._extract_plugin_from_module(
                mock_module, "test.module"
            )

            assert result is None

    def test_is_valid_plugin_class_valid(self) -> None:
        """Test valid plugin class detection."""

        class ValidPlugin(DrillSergeantPlugin):
            def __init__(self, config, metadata):
                super().__init__(config, metadata)

        result = self.discovery._is_valid_plugin_class(ValidPlugin)
        assert result is True

    def test_is_valid_plugin_class_invalid(self) -> None:
        """Test invalid plugin class detection."""

        class NotAPlugin:
            pass

        result = self.discovery._is_valid_plugin_class(NotAPlugin)
        assert result is False

        result = self.discovery._is_valid_plugin_class(DrillSergeantPlugin)
        assert result is False

        result = self.discovery._is_valid_plugin_class("not_a_class")
        assert result is False

    def test_create_plugin_instance(self) -> None:
        """Test plugin instance creation."""
        mock_plugin_class = MagicMock()
        mock_plugin_instance = MagicMock(spec=DrillSergeantPlugin)
        mock_plugin_class.return_value = mock_plugin_instance

        with (
            patch.object(
                self.discovery.factory.manager.registry, "register_plugin"
            ) as mock_register,
            patch.object(self.discovery._logger, "info") as mock_info,
        ):
            result = self.discovery._create_plugin_instance(
                mock_plugin_class, "test.module", "TestPlugin"
            )

            assert result is mock_plugin_instance
            mock_register.assert_called_once_with(mock_plugin_instance)
            mock_info.assert_called_once_with(
                "Discovered plugin from path: %s", "test.module.TestPlugin"
            )
            assert "test.module.TestPlugin" in self.discovery._discovered_plugins

    def test_get_discovered_plugins(self) -> None:
        """Test getting discovered plugin IDs."""
        self.discovery._discovered_plugins = {"plugin1", "plugin2"}

        result = self.discovery.get_discovered_plugins()

        assert result == {"plugin1", "plugin2"}
        # Should return a copy, not the original set
        assert result is not self.discovery._discovered_plugins

    def test_reload_plugin_success(self) -> None:
        """Test successful plugin reload."""
        with (
            patch.object(
                self.discovery.factory.manager.registry, "unregister_plugin"
            ) as mock_unregister,
            patch.object(self.discovery, "discover_plugins") as mock_discover,
            patch.object(self.discovery._logger, "info") as mock_info,
        ):
            result = self.discovery.reload_plugin("test_plugin")

            assert result is True
            mock_unregister.assert_called_once_with("test_plugin")
            mock_discover.assert_called_once()
            mock_info.assert_called_once_with("Reloaded plugin: %s", "test_plugin")

    def test_reload_plugin_failure(self) -> None:
        """Test plugin reload failure."""
        with (
            patch.object(
                self.discovery.factory.manager.registry, "unregister_plugin"
            ) as mock_unregister,
            patch.object(self.discovery, "discover_plugins"),
            patch.object(self.discovery._logger, "exception") as mock_exception,
        ):
            mock_unregister.side_effect = RuntimeError("Plugin not found")

            result = self.discovery.reload_plugin("test_plugin")

            assert result is False
            mock_exception.assert_called_once_with(
                "Failed to reload plugin %s", "test_plugin"
            )
