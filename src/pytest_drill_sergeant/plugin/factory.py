"""Plugin factory for creating and managing plugins."""

from __future__ import annotations

import importlib
import inspect
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    NotRequired,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeGuard,
    cast,
)

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.config import DrillSergeantConfig as Config
    from pytest_drill_sergeant.plugin.base import (
        AnalyzerPlugin,
        DrillSergeantPlugin,
        PersonaPlugin,
        PluginManager,
        PluginMetadata,
        ReporterPlugin,
    )
else:
    from pytest_drill_sergeant.plugin.base import PluginManager, PluginMetadata

# JSON types for plugin configuration
JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


class PluginConfigRaw(TypedDict, total=False):
    """Raw plugin configuration from config files."""

    metadata: dict[str, JSONValue]
    module_path: NotRequired[str]
    plugin_class_name: NotRequired[str]
    plugin_class: NotRequired[type[DrillSergeantPlugin]]


class DrillSergeantPluginProtocol(Protocol):
    """Minimal interface that all plugins must implement."""

    def __init__(self, config: Config, metadata: PluginMetadata) -> None:
        """Initialize the plugin with config and metadata."""
        ...

    name: str  # class or instance attr


class PluginConfigError(ValueError):
    """Raised when plugin configuration is invalid."""


# Safe coercion helpers
def _to_bool(v: bool | str | None, field: str, default: bool = True) -> bool:
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
    raise PluginConfigError(msg)


def _to_mapping(
    v: Mapping[str, JSONValue] | dict[str, JSONValue] | None, field: str
) -> Mapping[str, JSONValue]:
    """Coerce a value to mapping with proper error handling."""
    if v is None:
        return {}
    if isinstance(v, Mapping):
        return v
    msg = f"`{field}` must be a mapping of JSON-like values"
    raise PluginConfigError(msg)


def _create_plugin_config_error(
    plugin_index: int, field: str, expected_type: str
) -> PluginConfigError:
    """Create a standardized plugin configuration error."""
    msg = f"Plugin #{plugin_index}: `{field}` is required and must be {expected_type}"
    return PluginConfigError(msg)


def _create_import_error(module_path: str) -> PluginConfigError:
    """Create an import error for a module."""
    msg = f"Cannot import module {module_path!r}"
    return PluginConfigError(msg)


def _create_attribute_error(module_path: str, class_name: str) -> PluginConfigError:
    """Create an attribute error for a missing class."""
    msg = f"Module {module_path!r} has no class {class_name!r}"
    return PluginConfigError(msg)


def _create_invalid_class_error(module_path: str, class_name: str) -> PluginConfigError:
    """Create an error for an invalid plugin class."""
    msg = f"{module_path}.{class_name} is not a valid plugin class"
    return PluginConfigError(msg)


def _extract_string_field(
    metadata_dict: Mapping[str, JSONValue],
    plugin_index: int,
    field_name: str,
    default: str = "",
) -> str:
    """Extract and validate a string field from metadata."""
    value = metadata_dict.get(field_name, default)
    if not isinstance(value, str):
        raise _create_plugin_config_error(
            plugin_index, f"metadata.{field_name}", "a string"
        )
    return value


def _extract_dependencies_field(metadata_dict: Mapping[str, JSONValue]) -> list[str]:
    """Extract and validate dependencies field from metadata."""
    dependencies_raw = metadata_dict.get("dependencies", [])
    if isinstance(dependencies_raw, list) and all(
        isinstance(x, str) for x in dependencies_raw
    ):
        return cast("list[str]", dependencies_raw)
    return []


def _extract_bool_field(
    metadata_dict: Mapping[str, JSONValue], field_name: str, default: bool = True
) -> bool:
    """Extract and validate a boolean field from metadata."""
    value = metadata_dict.get(field_name, default)
    if not isinstance(value, bool):
        return default
    return value


def _extract_int_field(
    metadata_dict: Mapping[str, JSONValue], field_name: str, default: int = 0
) -> int:
    """Extract and validate an integer field from metadata."""
    value = metadata_dict.get(field_name, default)
    if not isinstance(value, int):
        return default
    return value


def _parse_plugin_metadata(
    plugin_index: int, metadata_dict: Mapping[str, JSONValue]
) -> PluginMetadata:
    """Parse plugin metadata from raw configuration data."""
    plugin_id = _extract_string_field(metadata_dict, plugin_index, "plugin_id")
    name = _extract_string_field(metadata_dict, plugin_index, "name")
    version = _extract_string_field(metadata_dict, plugin_index, "version")
    description = _extract_string_field(metadata_dict, plugin_index, "description")
    author = _extract_string_field(metadata_dict, plugin_index, "author")
    category = _extract_string_field(metadata_dict, plugin_index, "category")

    dependencies = _extract_dependencies_field(metadata_dict)
    enabled = _extract_bool_field(metadata_dict, "enabled", True)
    priority = _extract_int_field(metadata_dict, "priority", 0)

    return PluginMetadata(
        plugin_id=plugin_id,
        name=name,
        version=version,
        description=description,
        author=author,
        category=category,
        dependencies=dependencies,
        enabled=enabled,
        priority=priority,
    )


def _is_plugin_class(obj: object) -> TypeGuard[type[DrillSergeantPluginProtocol]]:
    """Check if an object is a valid plugin class."""
    if not inspect.isclass(obj):
        return False
    try:
        # Check if it has the required __init__ signature
        sig = inspect.signature(obj)
        params = list(sig.parameters.values())
        min_plugin_params = 2  # self + config + metadata
        if len(params) >= min_plugin_params:
            return True
    except (TypeError, ValueError, AttributeError):
        pass
    return False


def load_plugin_from_module(
    module_path: str, plugin_class_name: str, config: Config, metadata: PluginMetadata
) -> DrillSergeantPluginProtocol:
    """Load a plugin from a module with proper type checking.

    Args:
        module_path: Path to the module (e.g., 'my_package.plugins')
        plugin_class_name: Name of the plugin class
        config: Global configuration
        metadata: Plugin metadata

    Returns:
        Loaded plugin instance

    Raises:
        PluginConfigError: If module or class cannot be loaded or is invalid
    """
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        raise _create_import_error(module_path) from e

    try:
        plugin_class = getattr(module, plugin_class_name)
    except AttributeError as e:
        raise _create_attribute_error(module_path, plugin_class_name) from e

    if not _is_plugin_class(plugin_class):
        raise _create_invalid_class_error(module_path, plugin_class_name)

    # Safe instantiation with verified class
    return plugin_class(config, metadata)


@dataclass
class PluginSpec:
    """Specification for creating a plugin."""

    plugin_id: str
    name: str
    version: str
    description: str
    author: str
    category: str


logger = logging.getLogger(__name__)


class PluginFactory:
    """Factory for creating and managing plugins."""

    def __init__(self, config: Config):
        """Initialize the plugin factory.

        Args:
            config: Global configuration
        """
        self.config = config
        self.manager = PluginManager(config)
        self._logger = logging.getLogger("drill_sergeant.factory")

    def create_analyzer_plugin(
        self,
        spec: PluginSpec,
        plugin_class: type[AnalyzerPlugin],
        **kwargs: str | int | bool | list[str],
    ) -> AnalyzerPlugin:
        """Create an analyzer plugin.

        Args:
            spec: Plugin specification
            plugin_class: Analyzer plugin class
            **kwargs: Additional arguments for the plugin

        Returns:
            Created analyzer plugin
        """
        # Extract valid kwargs for PluginMetadata with safe coercion
        dependencies = kwargs.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []

        enabled_val = kwargs.get("enabled", True)
        enabled = _to_bool(
            enabled_val if isinstance(enabled_val, bool | str) else True,
            "enabled",
            default=True,
        )
        priority = kwargs.get("priority", 0)
        if not isinstance(priority, int):
            priority = 0

        metadata = PluginMetadata(
            plugin_id=spec.plugin_id,
            name=spec.name,
            version=spec.version,
            description=spec.description,
            author=spec.author,
            category="analyzer",
            dependencies=dependencies,
            enabled=enabled,
            priority=priority,
        )

        plugin = plugin_class(self.config, metadata)
        self.manager.registry.register_plugin(plugin)

        self._logger.info("Created analyzer plugin: %s", spec.plugin_id)
        return plugin

    def create_persona_plugin(
        self,
        spec: PluginSpec,
        plugin_class: type[PersonaPlugin],
        **kwargs: str | int | bool | list[str],
    ) -> PersonaPlugin:
        """Create a persona plugin.

        Args:
            spec: Plugin specification
            plugin_class: Persona plugin class
            **kwargs: Additional arguments for the plugin

        Returns:
            Created persona plugin
        """
        # Extract valid kwargs for PluginMetadata with safe coercion
        dependencies = kwargs.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []

        enabled_val = kwargs.get("enabled", True)
        enabled = _to_bool(
            enabled_val if isinstance(enabled_val, bool | str) else True,
            "enabled",
            default=True,
        )
        priority = kwargs.get("priority", 0)
        if not isinstance(priority, int):
            priority = 0

        metadata = PluginMetadata(
            plugin_id=spec.plugin_id,
            name=spec.name,
            version=spec.version,
            description=spec.description,
            author=spec.author,
            category="persona",
            dependencies=dependencies,
            enabled=enabled,
            priority=priority,
        )

        plugin = plugin_class(self.config, metadata)
        self.manager.registry.register_plugin(plugin)

        self._logger.info("Created persona plugin: %s", spec.plugin_id)
        return plugin

    def create_reporter_plugin(
        self,
        spec: PluginSpec,
        plugin_class: type[ReporterPlugin],
        **kwargs: str | int | bool | list[str],
    ) -> ReporterPlugin:
        """Create a reporter plugin.

        Args:
            spec: Plugin specification
            plugin_class: Reporter plugin class
            **kwargs: Additional arguments for the plugin

        Returns:
            Created reporter plugin
        """
        # Extract valid kwargs for PluginMetadata with safe coercion
        dependencies = kwargs.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []

        enabled_val = kwargs.get("enabled", True)
        enabled = _to_bool(
            enabled_val if isinstance(enabled_val, bool | str) else True,
            "enabled",
            default=True,
        )
        priority = kwargs.get("priority", 0)
        if not isinstance(priority, int):
            priority = 0

        metadata = PluginMetadata(
            plugin_id=spec.plugin_id,
            name=spec.name,
            version=spec.version,
            description=spec.description,
            author=spec.author,
            category="reporter",
            dependencies=dependencies,
            enabled=enabled,
            priority=priority,
        )

        plugin = plugin_class(self.config, metadata)
        self.manager.registry.register_plugin(plugin)

        self._logger.info("Created reporter plugin: %s", spec.plugin_id)
        return plugin

    def load_plugin_from_module(
        self, module_path: str, plugin_class_name: str, metadata: PluginMetadata
    ) -> DrillSergeantPlugin:
        """Load a plugin from a module.

        Args:
            module_path: Path to the module (e.g., 'my_package.plugins')
            plugin_class_name: Name of the plugin class
            metadata: Plugin metadata

        Returns:
            Loaded plugin instance
        """
        try:
            plugin = load_plugin_from_module(
                module_path, plugin_class_name, self.config, metadata
            )
            # Cast to the expected type for registration
            drill_plugin = cast("DrillSergeantPlugin", plugin)
            self.manager.registry.register_plugin(drill_plugin)

            self._logger.info(
                "Loaded plugin from module: %s.%s", module_path, plugin_class_name
            )
            return cast("DrillSergeantPlugin", plugin)

        except Exception:
            self._logger.exception(
                "Failed to load plugin from %s.%s", module_path, plugin_class_name
            )
            raise

    def load_plugins_from_config(self, plugin_configs: list[dict[str, object]]) -> None:
        """Load plugins from configuration.

        Args:
            plugin_configs: List of plugin configurations
        """
        for i, plugin_config in enumerate(plugin_configs):
            try:
                self._load_single_plugin_config(i, plugin_config)
            except PluginConfigError:
                self._logger.exception("Plugin configuration error")
                continue
            except Exception:
                self._logger.exception("Failed to load plugin from config")
                continue

    def _load_single_plugin_config(
        self, plugin_index: int, plugin_config: dict[str, object]
    ) -> None:
        """Load a single plugin from configuration."""
        # Safe config parsing with proper type checking
        raw_config = cast("Mapping[str, object]", plugin_config)

        # Extract metadata with safe coercion
        metadata_raw = raw_config.get("metadata")
        if not isinstance(metadata_raw, dict):
            raise _create_plugin_config_error(plugin_index, "metadata", "a dict")

        # Parse metadata using helper function
        metadata_dict = cast("Mapping[str, JSONValue]", metadata_raw)
        metadata = _parse_plugin_metadata(plugin_index, metadata_dict)

        # Check if loading from module or class
        module_path = raw_config.get("module_path")
        if isinstance(module_path, str):
            # Load from module
            plugin_class_name = raw_config.get("plugin_class_name")
            if not isinstance(plugin_class_name, str):
                raise _create_plugin_config_error(
                    plugin_index, "plugin_class_name", "a string when using module_path"
                )

            self.load_plugin_from_module(module_path, plugin_class_name, metadata)
        else:
            # Load from class
            plugin_class = raw_config.get("plugin_class")
            if not _is_plugin_class(plugin_class):
                raise _create_plugin_config_error(
                    plugin_index, "plugin_class", "a valid plugin class"
                )

            plugin = plugin_class(self.config, metadata)
            # Cast to the expected type for registration
            drill_plugin = cast("DrillSergeantPlugin", plugin)
            self.manager.registry.register_plugin(drill_plugin)

        self._logger.info("Loaded plugin from config: %s", metadata.plugin_id)

    def get_manager(self) -> PluginManager:
        """Get the plugin manager.

        Returns:
            Plugin manager instance
        """
        return self.manager
