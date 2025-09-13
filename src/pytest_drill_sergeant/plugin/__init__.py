"""Pytest plugin integration."""

from pytest_drill_sergeant.plugin.base import (
    AnalyzerPlugin,
    DrillSergeantPlugin,
    PersonaPlugin,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    ReporterPlugin,
)
from pytest_drill_sergeant.plugin.discovery import (
    PluginDiscovery,
    PluginDiscoveryConfig,
)
from pytest_drill_sergeant.plugin.extensibility import (
    PluginBuilder,
    PluginTemplate,
    create_analyzer_plugin_class,
    create_persona_plugin_class,
    create_reporter_plugin_class,
)
from pytest_drill_sergeant.plugin.factory import PluginFactory

__all__ = [
    "AnalyzerPlugin",
    # Base classes
    "DrillSergeantPlugin",
    "PersonaPlugin",
    # Extensibility
    "PluginBuilder",
    "PluginDiscovery",
    "PluginDiscoveryConfig",
    # Factory and discovery
    "PluginFactory",
    "PluginManager",
    "PluginMetadata",
    "PluginRegistry",
    "PluginTemplate",
    "ReporterPlugin",
    "create_analyzer_plugin_class",
    "create_persona_plugin_class",
    "create_reporter_plugin_class",
]
