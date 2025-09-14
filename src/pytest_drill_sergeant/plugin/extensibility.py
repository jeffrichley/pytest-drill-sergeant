"""Extensibility utilities for creating custom plugins."""

from __future__ import annotations

import logging
import types
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    runtime_checkable,
)

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.models import Config, Finding
from pytest_drill_sergeant.plugin.base import (
    AnalyzerPlugin,
    PersonaPlugin,
    PluginMetadata,
    ReporterPlugin,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# JSON types for plugin configuration
JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


@runtime_checkable
class BasePlugin(Protocol):
    """Base protocol for all plugins."""

    name: str

    def configure(self, options: Mapping[str, JSONValue]) -> None:
        """Configure the plugin with options."""
        ...


# TypeVar bound to the actual plugin base classes
P = TypeVar("P", bound=AnalyzerPlugin | PersonaPlugin | ReporterPlugin)


class TemplateError(ValueError):
    """Raised when plugin template configuration is invalid."""


def _create_invalid_name_error() -> ValueError:
    """Create an error for invalid plugin class name."""
    msg = "Plugin class name must be a non-empty string"
    return ValueError(msg)


def _create_invalid_base_error(base_type: type) -> TypeError:
    """Create an error for invalid base class."""
    msg = f"base must be a class, got {base_type!r}"
    return TypeError(msg)


def _create_invalid_interface_error(base: type) -> TypeError:
    """Create an error for invalid plugin interface."""
    msg = f"base {base!r} does not implement BasePlugin interface"
    return TypeError(msg)


def _create_invalid_attrs_error() -> TypeError:
    """Create an error for invalid attrs."""
    msg = "attrs must be a mapping[str, object]"
    return TypeError(msg)


def _create_invalid_subclass_error() -> TypeError:
    """Create an error for invalid subclass."""
    msg = "constructed class does not subclass base"
    return TypeError(msg)


def create_plugin_class(
    name: str, base: type[P], attrs: Mapping[str, object] | None = None,
) -> type[P]:
    """Create a plugin subclass with proper typing and runtime checks.

    Args:
        name: Name for the new class
        base: Base class to inherit from
        attrs: Additional attributes to add to the class

    Returns:
        New plugin class

    Raises:
        ValueError: If name is invalid
        TypeError: If base is not a valid class
        TypeError: If constructed class doesn't subclass base
    """
    if not isinstance(name, str) or not name:
        raise _create_invalid_name_error()

    if not isinstance(base, type):
        raise _create_invalid_base_error(type(base))

    # Runtime check that base implements BasePlugin protocol
    if not hasattr(base, "name") or not callable(getattr(base, "configure", None)):
        raise _create_invalid_interface_error(base)

    ns: dict[str, object] = {}
    if attrs:
        if not isinstance(attrs, Mapping):
            raise _create_invalid_attrs_error()
        ns.update(attrs)

    # Use types.new_class for proper metaclass and MRO handling
    cls = types.new_class(name, (base,), exec_body=lambda d: d.update(ns))

    # Runtime verification that the constructed class subclasses base
    if not issubclass(cls, base):
        raise _create_invalid_subclass_error()

    return cls


def _to_bool(v: bool | str | None, field: str, default: bool) -> bool:
    """Coerce a value to bool with proper error handling."""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = v.strip().lower()
    if s in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "f", "no", "n", "off"}:
        return False
    msg = f"`{field}` must be bool/str-bool, got {v!r}"
    raise TemplateError(msg)


def _to_options(
    v: Mapping[str, JSONValue] | dict[str, JSONValue] | None, field: str
) -> Mapping[str, JSONValue]:
    """Coerce a value to options mapping with proper error handling."""
    if v is None:
        return {}
    if isinstance(v, Mapping):
        return v
    msg = f"`{field}` must be a mapping[str, JSONValue]"
    raise TemplateError(msg)


logger = logging.getLogger(__name__)


class PluginTemplate(BaseModel):
    """Template for creating new plugins."""

    plugin_type: str = Field(
        ..., description="Type of plugin (analyzer, persona, reporter)"
    )
    name: str = Field(..., description="Plugin name")
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    version: str = Field("1.0.0", description="Plugin version")
    category: str = Field("custom", description="Plugin category")

    # Plugin-specific configuration
    config: dict[str, object] = Field(
        default_factory=dict, description="Plugin configuration"
    )

    # For analyzer plugins
    supported_extensions: list[str] = Field(
        default_factory=lambda: [".py"], description="Supported file extensions"
    )
    rule_ids: list[str] = Field(
        default_factory=list, description="Rule IDs this analyzer can generate"
    )

    # For persona plugins
    supported_contexts: list[str] = Field(
        default_factory=list, description="Supported message contexts"
    )
    personality_traits: list[str] = Field(
        default_factory=list, description="Personality traits"
    )

    # For reporter plugins
    supported_formats: list[str] = Field(
        default_factory=list, description="Supported output formats"
    )


def create_analyzer_plugin_class(template: PluginTemplate) -> type[AnalyzerPlugin]:
    """Create an analyzer plugin class from a template.

    Args:
        template: Plugin template

    Returns:
        Analyzer plugin class
    """

    class CustomAnalyzerPlugin(AnalyzerPlugin):
        """Custom analyzer plugin created from template."""

        def __init__(self, config: Config, metadata: PluginMetadata):
            super().__init__(config, metadata)
            self.template = template
            self._logger = logging.getLogger(f"drill_sergeant.analyzer.{template.name}")

        def initialize(self) -> None:
            """Initialize the custom analyzer."""
            self._logger.info("Initialized custom analyzer: %s", template.name)

        def cleanup(self) -> None:
            """Clean up the custom analyzer."""
            self._logger.info("Cleaned up custom analyzer: %s", template.name)

        def analyze_file(self, _file_path: Path) -> list[Finding]:
            """Analyze a file and return findings.

            This is a template method that should be overridden
            with actual analysis logic.
            """
            # Template implementation - should be overridden
            return []

        def get_supported_extensions(self) -> set[str]:
            """Get supported file extensions."""
            return set(template.supported_extensions)

        def get_rule_ids(self) -> set[str]:
            """Get rule IDs this analyzer can generate."""
            return set(template.rule_ids)

    return CustomAnalyzerPlugin


def create_persona_plugin_class(template: PluginTemplate) -> type[PersonaPlugin]:
    """Create a persona plugin class from a template.

    Args:
        template: Plugin template

    Returns:
        Persona plugin class
    """

    class CustomPersonaPlugin(PersonaPlugin):
        """Custom persona plugin created from template."""

        def __init__(self, config: Config, metadata: PluginMetadata):
            super().__init__(config, metadata)
            self.template = template
            self._logger = logging.getLogger(f"drill_sergeant.persona.{template.name}")

        def initialize(self) -> None:
            """Initialize the custom persona."""
            self._logger.info("Initialized custom persona: %s", template.name)

        def cleanup(self) -> None:
            """Clean up the custom persona."""
            self._logger.info("Cleaned up custom persona: %s", template.name)

        def generate_message(self, context: str, **kwargs: str) -> str:
            """Generate a message for the given context.

            This is a template method that should be overridden
            with actual message generation logic.
            """
            # Template implementation - should be overridden
            return f"[{template.name}] {context}: {kwargs}"

        def get_supported_contexts(self) -> set[str]:
            """Get supported message contexts."""
            return set(template.supported_contexts)

    return CustomPersonaPlugin


def create_reporter_plugin_class(template: PluginTemplate) -> type[ReporterPlugin]:
    """Create a reporter plugin class from a template.

    Args:
        template: Plugin template

    Returns:
        Reporter plugin class
    """

    class CustomReporterPlugin(ReporterPlugin):
        """Custom reporter plugin created from template."""

        def __init__(self, config: Config, metadata: PluginMetadata):
            super().__init__(config, metadata)
            self.template = template
            self._logger = logging.getLogger(f"drill_sergeant.reporter.{template.name}")

        def initialize(self) -> None:
            """Initialize the custom reporter."""
            self._logger.info("Initialized custom reporter: %s", template.name)

        def cleanup(self) -> None:
            """Clean up the custom reporter."""
            self._logger.info("Cleaned up custom reporter: %s", template.name)

        def generate_report(
            self, findings: list[Finding], _output_path: Path | None = None
        ) -> str:
            """Generate a report from findings.

            This is a template method that should be overridden
            with actual report generation logic.
            """
            # Template implementation - should be overridden
            return f"[{template.name}] Report with {len(findings)} findings"

        def get_supported_formats(self) -> set[str]:
            """Get supported output formats."""
            return set(template.supported_formats)

    return CustomReporterPlugin


class PluginBuilder:
    """Builder for creating custom plugins."""

    def __init__(self, config: Config):
        """Initialize the plugin builder.

        Args:
            config: Global configuration
        """
        self.config = config
        self._logger = logging.getLogger("drill_sergeant.builder")

    def build_analyzer_plugin(
        self,
        template: PluginTemplate,
        analyze_func: Callable[[Path, Config], list[Finding]],
        rule_ids: list[str] | None = None,
    ) -> AnalyzerPlugin:
        """Build a custom analyzer plugin.

        Args:
            template: Plugin template
            analyze_func: Function to analyze files
            rule_ids: Optional list of rule IDs

        Returns:
            Built analyzer plugin
        """
        if rule_ids:
            template.rule_ids = rule_ids

        base_plugin_class = create_analyzer_plugin_class(template)

        # Create a custom class that overrides the analyze_file method
        attrs = {
            "analyze_file": lambda self, file_path: analyze_func(file_path, self.config)
        }
        plugin_class = create_plugin_class(
            "CustomAnalyzerPlugin", base_plugin_class, attrs
        )

        # Create metadata
        metadata = PluginMetadata(
            plugin_id=template.name.lower().replace(" ", "_"),
            name=template.name,
            version=template.version,
            description=template.description,
            author=template.author,
            category=template.category,
            enabled=True,
            priority=0,
        )

        plugin = plugin_class(self.config, metadata)
        self._logger.info("Built analyzer plugin: %s", template.name)
        return plugin

    def build_persona_plugin(
        self,
        template: PluginTemplate,
        message_func: Callable[..., str],
        contexts: list[str] | None = None,
    ) -> PersonaPlugin:
        """Build a custom persona plugin.

        Args:
            template: Plugin template
            message_func: Function to generate messages
            contexts: Optional list of supported contexts

        Returns:
            Built persona plugin
        """
        if contexts:
            template.supported_contexts = contexts

        base_plugin_class = create_persona_plugin_class(template)

        attrs = {
            "generate_message": lambda self, context, **kwargs: message_func(  # noqa: ARG005
                context, **kwargs
            )
        }
        plugin_class = create_plugin_class(
            "CustomPersonaPlugin", base_plugin_class, attrs
        )

        # Create metadata
        metadata = PluginMetadata(
            plugin_id=template.name.lower().replace(" ", "_"),
            name=template.name,
            version=template.version,
            description=template.description,
            author=template.author,
            category=template.category,
            enabled=True,
            priority=0,
        )

        plugin = plugin_class(self.config, metadata)
        self._logger.info("Built persona plugin: %s", template.name)
        return plugin

    def build_reporter_plugin(
        self,
        template: PluginTemplate,
        report_func: Callable[[list[Finding], Path | None, Config], str],
        formats: list[str] | None = None,
    ) -> ReporterPlugin:
        """Build a custom reporter plugin.

        Args:
            template: Plugin template
            report_func: Function to generate reports
            formats: Optional list of supported formats

        Returns:
            Built reporter plugin
        """
        if formats:
            template.supported_formats = formats

        base_plugin_class = create_reporter_plugin_class(template)

        attrs = {
            "generate_report": lambda self, findings, output_path=None: report_func(
                findings, output_path, self.config
            )
        }
        plugin_class = create_plugin_class(
            "CustomReporterPlugin", base_plugin_class, attrs
        )

        # Create metadata
        metadata = PluginMetadata(
            plugin_id=template.name.lower().replace(" ", "_"),
            name=template.name,
            version=template.version,
            description=template.description,
            author=template.author,
            category=template.category,
            enabled=True,
            priority=0,
        )

        plugin = plugin_class(self.config, metadata)
        self._logger.info("Built reporter plugin: %s", template.name)
        return plugin


def create_plugin_from_config(config_dict: dict[str, object]) -> PluginTemplate:
    """Create a plugin template from configuration.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Plugin template

    Raises:
        TemplateError: If configuration is invalid
    """
    # Safe config parsing with proper type checking
    raw_config = cast("Mapping[str, object]", config_dict)

    # Convert dict[str, object] to the expected types for PluginTemplate
    def safe_list(value: object, default: list[str]) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return default

    # Extract config with safe coercion
    config_raw = raw_config.get("config")
    if isinstance(config_raw, dict):
        config = cast("dict[str, object]", config_raw)
    else:
        config = {}

    return PluginTemplate(
        plugin_type=str(raw_config.get("plugin_type", "")),
        name=str(raw_config.get("name", "")),
        description=str(raw_config.get("description", "")),
        author=str(raw_config.get("author", "")),
        version=str(raw_config.get("version", "1.0.0")),
        category=str(raw_config.get("category", "custom")),
        config=config,
        supported_extensions=safe_list(raw_config.get("supported_extensions"), [".py"]),
        rule_ids=safe_list(raw_config.get("rule_ids"), []),
        supported_contexts=safe_list(raw_config.get("supported_contexts"), []),
        personality_traits=safe_list(raw_config.get("personality_traits"), []),
        supported_formats=safe_list(raw_config.get("supported_formats"), []),
    )
