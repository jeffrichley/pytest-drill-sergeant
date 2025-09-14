"""Base plugin architecture for pytest-drill-sergeant.

This module provides the foundation for the plugin system, including
base classes, registry management, and lifecycle hooks.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_drill_sergeant.core.config import DrillSergeantConfig as Config
    from pytest_drill_sergeant.core.models import Finding

logger = logging.getLogger(__name__)


class PluginMetadata(BaseModel):
    """Metadata for a registered plugin."""

    plugin_id: str = Field(..., description="Unique identifier for the plugin")
    name: str = Field(..., description="Human-readable name")
    version: str = Field(..., description="Plugin version")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    category: str = Field(
        ..., description="Plugin category (analyzer, persona, reporter, etc.)"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Required dependencies"
    )
    enabled: bool = Field(True, description="Whether the plugin is enabled")
    priority: int = Field(0, description="Plugin priority (higher = more important)")


class DrillSergeantPlugin(ABC):
    """Base class for all drill sergeant plugins."""

    def __init__(self, config: Config, metadata: PluginMetadata):
        """Initialize the plugin.

        Args:
            config: Global configuration
            metadata: Plugin metadata
        """
        self.config = config
        self.metadata = metadata
        self._initialized = False
        self._logger = logging.getLogger(f"drill_sergeant.plugin.{metadata.plugin_id}")

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the plugin.

        Called when the plugin is first loaded. Use this for any
        setup that needs to happen before the plugin can be used.
        """

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources.

        Called when the plugin is being unloaded. Use this to
        clean up any resources or connections.
        """

    @property
    def is_initialized(self) -> bool:
        """Whether the plugin has been initialized."""
        return self._initialized

    def mark_initialized(self) -> None:
        """Mark the plugin as initialized."""
        self._initialized = True
        self._logger.debug("Plugin %s initialized", self.metadata.plugin_id)


class AnalyzerPlugin(DrillSergeantPlugin):
    """Base class for analyzer plugins."""

    @abstractmethod
    def analyze_file(self, file_path: Path) -> list[Finding]:
        """Analyze a file and return findings.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of findings from the analysis
        """

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Get file extensions supported by this analyzer.

        Returns:
            Set of file extensions (e.g., {'.py', '.pyi'})
        """

    @abstractmethod
    def get_rule_ids(self) -> set[str]:
        """Get rule IDs that this analyzer can generate.

        Returns:
            Set of rule IDs that this analyzer can produce
        """


class PersonaPlugin(DrillSergeantPlugin):
    """Base class for persona plugins."""

    @abstractmethod
    def generate_message(self, context: str, **kwargs: str) -> str:
        """Generate a message for the given context.

        Args:
            context: Context for the message (e.g., 'test_fail', 'summary')
            **kwargs: String substitution variables (test_name, error_message, etc.)

        Returns:
            Generated message
        """

    @abstractmethod
    def get_supported_contexts(self) -> set[str]:
        """Get contexts supported by this persona.

        Returns:
            Set of supported context strings
        """


class ReporterPlugin(DrillSergeantPlugin):
    """Base class for reporter plugins."""

    @abstractmethod
    def generate_report(
        self, findings: list[Finding], output_path: Path | None = None
    ) -> str:
        """Generate a report from findings.

        Args:
            findings: List of findings to include in the report
            output_path: Optional path to write the report to

        Returns:
            Generated report content
        """

    @abstractmethod
    def get_supported_formats(self) -> set[str]:
        """Get output formats supported by this reporter.

        Returns:
            Set of supported format strings (e.g., {'json', 'sarif'})
        """


class PluginRegistry:
    """Registry for managing drill sergeant plugins."""

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, DrillSergeantPlugin] = {}
        self._metadata: dict[str, PluginMetadata] = {}
        self._by_category: dict[str, set[str]] = {}
        self._logger = logging.getLogger("drill_sergeant.registry")

    def register_plugin(self, plugin: DrillSergeantPlugin) -> None:
        """Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin ID is already registered
        """
        plugin_id = plugin.metadata.plugin_id

        if plugin_id in self._plugins:
            msg = f"Plugin {plugin_id} is already registered"
            raise ValueError(msg)

        self._plugins[plugin_id] = plugin
        self._metadata[plugin_id] = plugin.metadata

        # Add to category index
        category = plugin.metadata.category
        if category not in self._by_category:
            self._by_category[category] = set()
        self._by_category[category].add(plugin_id)

        self._logger.info("Registered plugin: %s (%s)", plugin_id, plugin.metadata.name)

    def unregister_plugin(self, plugin_id: str) -> None:
        """Unregister a plugin.

        Args:
            plugin_id: ID of the plugin to unregister
        """
        if plugin_id not in self._plugins:
            self._logger.warning("Plugin %s not found for unregistration", plugin_id)
            return

        plugin = self._plugins[plugin_id]
        plugin.cleanup()

        # Remove from category index
        category = plugin.metadata.category
        if category in self._by_category:
            self._by_category[category].discard(plugin_id)

        del self._plugins[plugin_id]
        del self._metadata[plugin_id]

        self._logger.info("Unregistered plugin: %s", plugin_id)

    def get_plugin(self, plugin_id: str) -> DrillSergeantPlugin | None:
        """Get a plugin by ID.

        Args:
            plugin_id: ID of the plugin to get

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_id)

    def get_plugins_by_category(self, category: str) -> list[DrillSergeantPlugin]:
        """Get all plugins in a category.

        Args:
            category: Category to filter by

        Returns:
            List of plugins in the category
        """
        plugin_ids = self._by_category.get(category, set())
        return [self._plugins[pid] for pid in plugin_ids if pid in self._plugins]

    def get_enabled_plugins(self) -> list[DrillSergeantPlugin]:
        """Get all enabled plugins.

        Returns:
            List of enabled plugins
        """
        return [plugin for plugin in self._plugins.values() if plugin.metadata.enabled]

    def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        for plugin in self._plugins.values():
            if plugin.metadata.enabled and not plugin.is_initialized:
                try:
                    plugin.initialize()
                    plugin.mark_initialized()
                except Exception:
                    self._logger.exception(
                        "Failed to initialize plugin %s", plugin.metadata.plugin_id
                    )

    def cleanup_all(self) -> None:
        """Clean up all registered plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.cleanup()
            except Exception:
                self._logger.exception(
                    "Failed to cleanup plugin %s", plugin.metadata.plugin_id
                )

    def list_plugins(self) -> list[PluginMetadata]:
        """List all registered plugins.

        Returns:
            List of plugin metadata
        """
        return list(self._metadata.values())


class PluginManager:
    """High-level plugin manager for the drill sergeant system."""

    def __init__(self, config: Config):
        """Initialize the plugin manager.

        Args:
            config: Global configuration
        """
        self.config = config
        self.registry = PluginRegistry()
        self._logger = logging.getLogger("drill_sergeant.plugin_manager")

    def load_plugin(
        self, plugin_class: type[DrillSergeantPlugin], metadata: PluginMetadata
    ) -> None:
        """Load a plugin class.

        Args:
            plugin_class: Plugin class to load
            metadata: Plugin metadata
        """
        try:
            plugin = plugin_class(self.config, metadata)
            self.registry.register_plugin(plugin)
            self._logger.info("Loaded plugin: %s", metadata.plugin_id)
        except Exception:
            self._logger.exception("Failed to load plugin %s", metadata.plugin_id)
            raise

    def get_analyzers(self) -> list[AnalyzerPlugin]:
        """Get all analyzer plugins.

        Returns:
            List of analyzer plugins
        """
        return [
            plugin
            for plugin in self.registry.get_plugins_by_category("analyzer")
            if isinstance(plugin, AnalyzerPlugin)
        ]

    def get_personas(self) -> list[PersonaPlugin]:
        """Get all persona plugins.

        Returns:
            List of persona plugins
        """
        return [
            plugin
            for plugin in self.registry.get_plugins_by_category("persona")
            if isinstance(plugin, PersonaPlugin)
        ]

    def get_reporters(self) -> list[ReporterPlugin]:
        """Get all reporter plugins.

        Returns:
            List of reporter plugins
        """
        return [
            plugin
            for plugin in self.registry.get_plugins_by_category("reporter")
            if isinstance(plugin, ReporterPlugin)
        ]

    def initialize_all(self) -> None:
        """Initialize all loaded plugins."""
        self.registry.initialize_all()

    def cleanup_all(self) -> None:
        """Clean up all loaded plugins."""
        self.registry.cleanup_all()
