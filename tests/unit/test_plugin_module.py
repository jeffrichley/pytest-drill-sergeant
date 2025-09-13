"""Test plugin module imports to increase coverage."""

import pytest_drill_sergeant.plugin
from pytest_drill_sergeant.plugin import (
    AnalyzerPlugin,
    DrillSergeantPlugin,
    PersonaPlugin,
    PluginBuilder,
    PluginDiscovery,
    PluginDiscoveryConfig,
    PluginFactory,
    PluginManager,
    PluginMetadata,
    PluginRegistry,
    PluginTemplate,
    ReporterPlugin,
    create_analyzer_plugin_class,
    create_persona_plugin_class,
    create_reporter_plugin_class,
)


def test_plugin_module_imports():
    """Test importing from plugin module to increase coverage."""
    # Test that the imports work
    assert AnalyzerPlugin is not None
    assert DrillSergeantPlugin is not None
    assert PersonaPlugin is not None
    assert PluginBuilder is not None
    assert PluginDiscovery is not None
    assert PluginDiscoveryConfig is not None
    assert PluginFactory is not None
    assert PluginManager is not None
    assert PluginMetadata is not None
    assert PluginRegistry is not None
    assert PluginTemplate is not None
    assert ReporterPlugin is not None
    assert create_analyzer_plugin_class is not None
    assert create_persona_plugin_class is not None
    assert create_reporter_plugin_class is not None


def test_plugin_module_all():
    """Test that __all__ is properly defined."""
    __all__ = pytest_drill_sergeant.plugin.__all__

    # Test that __all__ is a list
    assert isinstance(__all__, list)
    assert len(__all__) > 0

    # Test that it contains expected items
    expected_items = [
        "AnalyzerPlugin",
        "DrillSergeantPlugin",
        "PersonaPlugin",
        "PluginBuilder",
        "PluginDiscovery",
        "PluginDiscoveryConfig",
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

    for item in expected_items:
        assert item in __all__
