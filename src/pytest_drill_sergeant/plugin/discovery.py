"""Plugin discovery system for automatic plugin loading."""

from __future__ import annotations

import importlib
import logging
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

# Import modules at top level to avoid runtime imports
import pytest_drill_sergeant.core.analyzers
import pytest_drill_sergeant.plugin.personas

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.config import DrillSergeantConfig as Config
from pytest_drill_sergeant.plugin.base import DrillSergeantPlugin, PluginMetadata
from pytest_drill_sergeant.plugin.factory import PluginFactory, PluginSpec
from pytest_drill_sergeant.util.paths import normalize_module_path

logger = logging.getLogger(__name__)


class PluginDiscoveryConfig(BaseModel):
    """Configuration for plugin discovery."""

    enabled: bool = True
    search_paths: list[str] = []
    entry_point_groups: list[str] = [
        "pytest_drill_sergeant.analyzers",
        "pytest_drill_sergeant.personas",
        "pytest_drill_sergeant.reporters",
    ]
    auto_discover: bool = True
    load_builtin: bool = True


class PluginDiscovery:
    """Discovers and loads plugins automatically."""

    def __init__(
        self, config: Config, discovery_config: PluginDiscoveryConfig | None = None
    ):
        """Initialize plugin discovery.

        Args:
            config: Global configuration
            discovery_config: Discovery configuration
        """
        self.config = config
        self.discovery_config = discovery_config or PluginDiscoveryConfig()
        self.factory = PluginFactory(config)
        self._logger = logging.getLogger("drill_sergeant.discovery")
        self._discovered_plugins: set[str] = set()

    def discover_plugins(self) -> list[DrillSergeantPlugin]:
        """Discover and load all available plugins.

        Returns:
            List of discovered plugins
        """
        if not self.discovery_config.enabled:
            self._logger.info("Plugin discovery is disabled")
            return []

        discovered_plugins = []

        # Load built-in plugins
        if self.discovery_config.load_builtin:
            builtin_plugins = self._discover_builtin_plugins()
            discovered_plugins.extend(builtin_plugins)

        # Discover plugins from entry points
        if self.discovery_config.auto_discover:
            entry_point_plugins = self._discover_entry_point_plugins()
            discovered_plugins.extend(entry_point_plugins)

        # Discover plugins from search paths
        if self.discovery_config.search_paths:
            path_plugins = self._discover_path_plugins()
            discovered_plugins.extend(path_plugins)

        self._logger.info("Discovered %d plugins", len(discovered_plugins))
        return discovered_plugins

    def _discover_builtin_plugins(self) -> list[DrillSergeantPlugin]:
        """Discover built-in plugins.

        Returns:
            List of built-in plugins
        """
        builtin_plugins: list[DrillSergeantPlugin] = []

        try:
            # Use pre-imported analyzers module

            # Register built-in analyzers
            analyzers = [
                (
                    "private_access",
                    "Private Access Analyzer",
                    "1.0.0",
                    "Detects private attribute and method access",
                    "Drill Sergeant Team",
                ),
                (
                    "mock_overspecification",
                    "Mock Over-Specification Analyzer",
                    "1.0.0",
                    "Detects over-specified mock assertions",
                    "Drill Sergeant Team",
                ),
                (
                    "structural_equality",
                    "Structural Equality Analyzer",
                    "1.0.0",
                    "Detects structural equality comparisons",
                    "Drill Sergeant Team",
                ),
                (
                    "aaa_comment",
                    "AAA Comment Analyzer",
                    "1.0.0",
                    "Validates AAA comment structure",
                    "Drill Sergeant Team",
                ),
            ]

            for plugin_id, name, version, description, author in analyzers:
                try:
                    spec = PluginSpec(
                        plugin_id=plugin_id,
                        name=name,
                        version=version,
                        description=description,
                        author=author,
                        category="analyzer",
                    )
                    plugin = self.factory.create_analyzer_plugin(
                        spec=spec,
                        plugin_class=getattr(
                            getattr(
                                pytest_drill_sergeant.core.analyzers,
                                f"{plugin_id}_analyzer",
                            ),
                            f"{plugin_id.title().replace('_', '')}Plugin",
                        ),
                    )
                    builtin_plugins.append(plugin)
                    self._discovered_plugins.add(plugin_id)
                except (AttributeError, ImportError, TypeError, ValueError) as e:
                    self._logger.warning(
                        "Failed to load built-in analyzer %s: %s", plugin_id, e
                    )

            # Use pre-imported personas module

            # Register built-in personas
            personas = [
                (
                    "drill_sergeant",
                    "Drill Sergeant Hartman",
                    "1.0.0",
                    "Military-themed feedback persona",
                    "Drill Sergeant Team",
                ),
                (
                    "snoop_dogg",
                    "Snoop Dogg",
                    "1.0.0",
                    "Hip-hop themed feedback persona",
                    "Drill Sergeant Team",
                ),
                (
                    "motivational_coach",
                    "Motivational Coach",
                    "1.0.0",
                    "Encouraging and supportive persona",
                    "Drill Sergeant Team",
                ),
                (
                    "sarcastic_butler",
                    "Sarcastic Butler",
                    "1.0.0",
                    "Witty and sarcastic persona",
                    "Drill Sergeant Team",
                ),
                (
                    "pirate",
                    "Pirate",
                    "1.0.0",
                    "Pirate-themed feedback persona",
                    "Drill Sergeant Team",
                ),
            ]

            for plugin_id, name, version, description, author in personas:
                try:
                    spec = PluginSpec(
                        plugin_id=plugin_id,
                        name=name,
                        version=version,
                        description=description,
                        author=author,
                        category="persona",
                    )
                    persona_plugin: DrillSergeantPlugin = (
                        self.factory.create_persona_plugin(
                            spec=spec,
                            plugin_class=getattr(
                                getattr(
                                    pytest_drill_sergeant.plugin.personas,
                                    f"{plugin_id}_persona",
                                ),
                                f"{plugin_id.title().replace('_', '')}Plugin",
                            ),
                        )
                    )
                    builtin_plugins.append(persona_plugin)
                    self._discovered_plugins.add(plugin_id)
                except (AttributeError, ImportError, TypeError, ValueError) as e:
                    self._logger.warning(
                        "Failed to load built-in persona %s: %s", plugin_id, e
                    )

        except ImportError as e:
            self._logger.warning("Failed to import built-in plugins: %s", e)

        return builtin_plugins

    def _discover_entry_point_plugins(self) -> list[DrillSergeantPlugin]:
        """Discover plugins from entry points.

        Returns:
            List of discovered plugins
        """
        discovered_plugins = []

        for entry_point_group in self.discovery_config.entry_point_groups:
            try:
                entry_points_iter = entry_points().select(group=entry_point_group)

                for entry_point in entry_points_iter:
                    try:
                        plugin_class = entry_point.load()

                        # Create metadata from entry point
                        metadata = PluginMetadata(
                            plugin_id=entry_point.name,
                            name=entry_point.name.replace("_", " ").title(),
                            version=getattr(entry_point.dist, "version", "1.0.0"),
                            description=getattr(entry_point, "description", ""),
                            author=getattr(entry_point.dist, "author", "Unknown"),
                            category=entry_point_group.split(".")[-1],
                            enabled=True,
                            priority=0,
                        )

                        plugin = plugin_class(self.config, metadata)
                        self.factory.manager.registry.register_plugin(plugin)
                        discovered_plugins.append(plugin)
                        self._discovered_plugins.add(entry_point.name)

                        self._logger.info(
                            "Discovered plugin from entry point: %s", entry_point.name
                        )

                    except (AttributeError, ImportError, TypeError, ValueError) as e:
                        self._logger.warning(
                            "Failed to load entry point plugin %s: %s",
                            entry_point.name,
                            e,
                        )

            except (ImportError, AttributeError) as e:
                self._logger.warning(
                    "Failed to discover entry point plugins for %s: %s",
                    entry_point_group,
                    e,
                )

        return discovered_plugins

    def _discover_path_plugins(self) -> list[DrillSergeantPlugin]:
        """Discover plugins from search paths.

        Returns:
            List of discovered plugins
        """
        discovered_plugins = []

        for search_path in self.discovery_config.search_paths:
            path = Path(search_path)

            if not path.exists():
                self._logger.warning("Search path does not exist: %s", search_path)
                continue

            discovered_plugins.extend(self._discover_plugins_from_path(path))

        return discovered_plugins

    def _discover_plugins_from_path(self, path: Path) -> list[DrillSergeantPlugin]:
        """Discover plugins from a specific path."""
        discovered_plugins = []

        for py_file in path.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue

            plugin = self._load_plugin_from_file(py_file, path)
            if plugin:
                discovered_plugins.append(plugin)

        return discovered_plugins

    def _load_plugin_from_file(
        self, py_file: Path, search_path: Path
    ) -> DrillSergeantPlugin | None:
        """Load a plugin from a Python file."""
        try:
            module_path = self._get_module_path(py_file, search_path)
            module = importlib.import_module(module_path)
            return self._extract_plugin_from_module(module, module_path)
        except (ImportError, AttributeError, SyntaxError, ValueError) as e:
            self._logger.debug("Failed to load plugin from %s: %s", py_file, e)
            return None

    def _get_module_path(self, py_file: Path, search_path: Path) -> str:
        """Convert file path to module path."""
        return normalize_module_path(py_file, search_path.parent)

    def _extract_plugin_from_module(
        self, module: object, module_path: str
    ) -> DrillSergeantPlugin | None:
        """Extract plugin from module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if self._is_valid_plugin_class(attr):
                return self._create_plugin_instance(attr, module_path, attr_name)

        return None

    def _is_valid_plugin_class(self, attr: object) -> bool:
        """Check if attribute is a valid plugin class."""
        try:
            return (
                isinstance(attr, type)
                and issubclass(attr, DrillSergeantPlugin)
                and attr != DrillSergeantPlugin
            )
        except TypeError as e:
            # Handle case where attr is not a class or DrillSergeantPlugin is not a class
            self._logger.debug(f"Invalid plugin class check: {e}")
            return False

    def _create_plugin_instance(
        self, plugin_class: type[DrillSergeantPlugin], module_path: str, attr_name: str
    ) -> DrillSergeantPlugin:
        """Create and register plugin instance."""
        metadata = PluginMetadata(
            plugin_id=f"{module_path}.{attr_name}",
            name=attr_name.replace("_", " ").title(),
            version="1.0.0",
            description=getattr(plugin_class, "__doc__", "") or "",
            author="Unknown",
            category="custom",
            enabled=True,
            priority=0,
        )

        plugin = plugin_class(self.config, metadata)
        self.factory.manager.registry.register_plugin(plugin)
        self._discovered_plugins.add(metadata.plugin_id)

        self._logger.info("Discovered plugin from path: %s", metadata.plugin_id)
        return plugin

    def get_discovered_plugins(self) -> set[str]:
        """Get set of discovered plugin IDs.

        Returns:
            Set of discovered plugin IDs
        """
        return self._discovered_plugins.copy()

    def reload_plugin(self, plugin_id: str) -> bool:
        """Reload a specific plugin.

        Args:
            plugin_id: ID of the plugin to reload

        Returns:
            True if reloaded successfully, False otherwise
        """
        try:
            # Unregister the plugin
            self.factory.manager.registry.unregister_plugin(plugin_id)

            # Re-discover plugins
            self.discover_plugins()

            self._logger.info("Reloaded plugin: %s", plugin_id)
        except (ImportError, AttributeError, ValueError, RuntimeError):
            self._logger.exception("Failed to reload plugin %s", plugin_id)
            return False
        else:
            return True
