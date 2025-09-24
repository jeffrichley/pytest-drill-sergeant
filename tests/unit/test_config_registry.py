"""Comprehensive tests for the configuration registry system.

This module provides Google-quality tests for the ConfigRegistry class and
all associated global functions, ensuring complete coverage of the critical
configuration management system.

Test Categories:
1. Singleton Pattern Tests
2. Configuration Loading Tests
3. Error Handling Tests
4. Global Registry Functions Tests
5. Convenience Functions Tests
6. Edge Cases and Integration Tests
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from pytest_drill_sergeant.core.config_registry import (
    ConfigRegistry,
    get_active_profile,
    get_config,
    get_config_registry,
    get_fail_on_level,
    get_output_formats,
    get_project_root,
    get_rule_config,
    get_rule_severity,
    initialize_config,
    is_quiet,
    is_rule_enabled,
    is_verbose,
    reload_config,
    reset_config,
    should_fail_on_severity,
)
from pytest_drill_sergeant.core.config_schema import (
    DSConfig,
    OutputFormat,
    Profile,
    RuleConfig,
    SeverityLevel,
    create_default_config,
)


class TestConfigRegistrySingleton:
    """Test the singleton pattern implementation."""

    def test_singleton_returns_same_instance(self):
        """Test that ConfigRegistry always returns the same instance."""
        # Reset singleton state
        ConfigRegistry().reset()

        instance1 = ConfigRegistry()
        instance2 = ConfigRegistry()

        assert instance1 is instance2
        assert id(instance1) == id(instance2)

    def test_singleton_persistence_across_calls(self):
        """Test that singleton persists across multiple calls."""
        # Reset singleton state
        ConfigRegistry().reset()

        registry1 = ConfigRegistry()
        registry1._config = "test_config"

        registry2 = ConfigRegistry()
        assert registry2._config == "test_config"

    def test_reset_clears_singleton(self):
        """Test that reset() properly clears the singleton instance."""
        # Reset singleton state
        ConfigRegistry().reset()

        registry1 = ConfigRegistry()
        registry1._config = "test_config"

        ConfigRegistry().reset()

        registry2 = ConfigRegistry()
        assert registry2._config is None
        # Note: Due to singleton pattern, registry1 and registry2 are the same instance
        # but the internal state has been cleared
        assert registry1 is registry2

    def test_reset_clears_all_state(self):
        """Test that reset() clears all instance state."""
        # Reset singleton state
        ConfigRegistry().reset()

        registry = ConfigRegistry()
        registry._config = "test_config"
        registry._project_root = Path("/test")

        ConfigRegistry().reset()

        new_registry = ConfigRegistry()
        assert new_registry._config is None
        assert new_registry._project_root is None


class TestConfigRegistryInitialization:
    """Test configuration initialization functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_initialize_with_defaults(self):
        """Test initialization with default parameters."""
        registry = ConfigRegistry()

        registry.initialize()

        assert registry.is_initialized()
        assert registry._config is not None
        assert isinstance(registry._config, DSConfig)
        assert registry._project_root == Path.cwd()

    def test_initialize_with_custom_project_root(self):
        """Test initialization with custom project root."""
        registry = ConfigRegistry()
        custom_root = Path("/custom/project")

        registry.initialize(project_root=custom_root)

        assert registry._project_root == custom_root
        assert registry.is_initialized()

    def test_initialize_with_cli_args(self):
        """Test initialization with CLI arguments."""
        registry = ConfigRegistry()
        cli_args = {"profile": "strict", "verbose": True}

        registry.initialize(cli_args=cli_args)

        assert registry.is_initialized()
        # Configuration should be loaded with CLI args
        assert registry._config is not None

    def test_initialize_with_pytest_config(self):
        """Test initialization with pytest configuration."""
        registry = ConfigRegistry()
        pytest_config = Mock()
        pytest_config.getoption.return_value = "strict"

        registry.initialize(pytest_config=pytest_config)

        assert registry.is_initialized()
        assert registry._config is not None

    def test_initialize_idempotent(self):
        """Test that initialization is idempotent."""
        registry = ConfigRegistry()

        # First initialization
        registry.initialize()
        first_config = registry._config

        # Second initialization should not change anything
        registry.initialize()
        second_config = registry._config

        assert first_config is second_config

    def test_initialize_with_profile_loader_success(self):
        """Test successful initialization with ProfileConfigLoader."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_config = create_default_config()
            mock_loader.load_config.return_value = mock_config
            mock_loader_class.return_value = mock_loader

            registry.initialize()

            assert registry._config is mock_config
            mock_loader.load_config.assert_called_once_with(None, None)

    def test_initialize_with_profile_loader_failure(self):
        """Test initialization fallback when ProfileConfigLoader fails."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_config.side_effect = Exception("Loader failed")
            mock_loader_class.return_value = mock_loader

            with patch(
                "pytest_drill_sergeant.core.config_registry.create_default_config"
            ) as mock_default:
                mock_default_config = create_default_config()
                mock_default.return_value = mock_default_config

                registry.initialize()

                assert registry._config is mock_default_config
                mock_default.assert_called_once()

    def test_initialize_logs_warning_on_failure(self):
        """Test that initialization logs warning when ProfileConfigLoader fails."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_config.side_effect = Exception("Loader failed")
            mock_loader_class.return_value = mock_loader

            with patch(
                "pytest_drill_sergeant.core.config_registry.create_default_config"
            ):
                with patch("logging.getLogger") as mock_logger:
                    mock_log = Mock()
                    mock_logger.return_value = mock_log

                    registry.initialize()

                    mock_log.warning.assert_called_once()
                    assert (
                        "Failed to load configuration, using defaults"
                        in mock_log.warning.call_args[0][0]
                    )

    def test_initialize_handles_import_error(self):
        """Test that initialization handles ImportError gracefully."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_config.side_effect = Exception("Loader failed")
            mock_loader_class.return_value = mock_loader

            with patch(
                "pytest_drill_sergeant.core.config_registry.create_default_config"
            ):
                with patch(
                    "builtins.__import__", side_effect=ImportError("No logging")
                ):
                    # Should not raise an exception
                    registry.initialize()
                    assert registry._config is not None


class TestConfigRegistryAccess:
    """Test configuration access methods."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_get_config_returns_config(self):
        """Test that get_config returns the loaded configuration."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        registry._config = test_config

        result = registry.get_config()

        assert result is test_config

    def test_get_config_auto_initializes(self):
        """Test that get_config auto-initializes if not initialized."""
        registry = ConfigRegistry()

        # Should not be initialized yet
        assert not registry.is_initialized()

        # get_config should auto-initialize
        config = registry.get_config()

        assert registry.is_initialized()
        assert config is not None
        assert isinstance(config, DSConfig)

    def test_get_project_root_returns_set_root(self):
        """Test that get_project_root returns the set project root."""
        registry = ConfigRegistry()
        test_root = Path("/test/project")
        registry._project_root = test_root

        result = registry.get_project_root()

        assert result == test_root

    def test_get_project_root_defaults_to_cwd(self):
        """Test that get_project_root defaults to current working directory."""
        registry = ConfigRegistry()

        result = registry.get_project_root()

        assert result == Path.cwd()

    def test_is_initialized_returns_correct_state(self):
        """Test that is_initialized returns the correct state."""
        registry = ConfigRegistry()

        # Initially not initialized
        assert not registry.is_initialized()

        # After setting config
        registry._config = create_default_config()
        assert registry.is_initialized()

        # After clearing config
        registry._config = None
        assert not registry.is_initialized()


class TestConfigRegistryReload:
    """Test configuration reloading functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_reload_config_clears_and_reinitializes(self):
        """Test that reload_config clears and reinitializes configuration."""
        registry = ConfigRegistry()

        # Initial configuration
        registry.initialize()
        original_config = registry._config
        original_root = registry._project_root

        # Reload with new parameters
        new_cli_args = {"profile": "strict"}
        new_pytest_config = Mock()

        registry.reload_config(new_cli_args, new_pytest_config)

        # Should have new configuration
        assert registry._config is not original_config
        assert registry._project_root is original_root  # Should preserve project root

    def test_reload_config_with_none_parameters(self):
        """Test reload_config with None parameters."""
        registry = ConfigRegistry()

        registry.initialize()
        registry.reload_config()

        assert registry.is_initialized()
        assert registry._config is not None

    def test_reload_config_preserves_project_root(self):
        """Test that reload_config preserves the project root."""
        registry = ConfigRegistry()
        test_root = Path("/test/project")

        registry.initialize(project_root=test_root)
        registry.reload_config()

        assert registry._project_root == test_root


class TestGlobalRegistryFunctions:
    """Test global registry functions."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_get_config_registry_returns_singleton(self):
        """Test that get_config_registry returns the singleton instance."""
        registry1 = get_config_registry()
        registry2 = get_config_registry()

        assert registry1 is registry2
        assert isinstance(registry1, ConfigRegistry)

    def test_initialize_config_delegates_to_registry(self):
        """Test that initialize_config delegates to registry."""
        with patch(
            "pytest_drill_sergeant.core.config_registry._registry"
        ) as mock_registry:
            cli_args = {"profile": "strict"}
            pytest_config = Mock()
            project_root = Path("/test")

            initialize_config(cli_args, pytest_config, project_root)

            mock_registry.initialize.assert_called_once_with(
                cli_args, pytest_config, project_root
            )

    def test_get_config_delegates_to_registry(self):
        """Test that get_config delegates to registry."""
        with patch(
            "pytest_drill_sergeant.core.config_registry._registry"
        ) as mock_registry:
            test_config = create_default_config()
            mock_registry.get_config.return_value = test_config

            result = get_config()

            assert result is test_config
            mock_registry.get_config.assert_called_once()

    def test_reload_config_delegates_to_registry(self):
        """Test that reload_config delegates to registry."""
        with patch(
            "pytest_drill_sergeant.core.config_registry._registry"
        ) as mock_registry:
            cli_args = {"profile": "strict"}
            pytest_config = Mock()

            reload_config(cli_args, pytest_config)

            mock_registry.reload_config.assert_called_once_with(cli_args, pytest_config)

    def test_get_project_root_delegates_to_registry(self):
        """Test that get_project_root delegates to registry."""
        with patch(
            "pytest_drill_sergeant.core.config_registry._registry"
        ) as mock_registry:
            test_root = Path("/test/project")
            mock_registry.get_project_root.return_value = test_root

            result = get_project_root()

            assert result == test_root
            mock_registry.get_project_root.assert_called_once()

    def test_reset_config_delegates_to_registry(self):
        """Test that reset_config delegates to registry."""
        with patch(
            "pytest_drill_sergeant.core.config_registry._registry"
        ) as mock_registry:
            reset_config()

            mock_registry.reset.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions for configuration access."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_get_active_profile(self):
        """Test get_active_profile function."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.profile = Profile.STRICT
        registry._config = test_config

        result = get_active_profile()

        assert result == Profile.STRICT

    def test_get_rule_config_existing_rule(self):
        """Test get_rule_config with existing rule."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_rule_config = RuleConfig(enabled=True, severity=SeverityLevel.WARNING)
        test_config.rules = {"DS201": test_rule_config}
        registry._config = test_config

        result = get_rule_config("DS201")

        assert result is test_rule_config

    def test_get_rule_config_nonexistent_rule(self):
        """Test get_rule_config with nonexistent rule."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.rules = {}
        registry._config = test_config

        result = get_rule_config("nonexistent_rule")

        assert result is None

    def test_is_rule_enabled_existing_enabled_rule(self):
        """Test is_rule_enabled with existing enabled rule."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_rule_config = RuleConfig(enabled=True)
        test_config.rules = {"DS201": test_rule_config}
        registry._config = test_config

        result = is_rule_enabled("DS201")

        assert result is True

    def test_is_rule_enabled_existing_disabled_rule(self):
        """Test is_rule_enabled with existing disabled rule."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_rule_config = RuleConfig(enabled=False)
        test_config.rules = {"DS201": test_rule_config}
        registry._config = test_config

        result = is_rule_enabled("DS201")

        assert result is False

    def test_is_rule_enabled_nonexistent_rule(self):
        """Test is_rule_enabled with nonexistent rule (defaults to True)."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.rules = {}
        registry._config = test_config

        result = is_rule_enabled("nonexistent_rule")

        assert result is True

    def test_get_rule_severity_existing_rule_with_severity(self):
        """Test get_rule_severity with existing rule that has severity."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_rule_config = RuleConfig(severity=SeverityLevel.WARNING)
        test_config.rules = {"DS201": test_rule_config}
        registry._config = test_config

        result = get_rule_severity("DS201")

        assert result == SeverityLevel.WARNING

    def test_get_rule_severity_existing_rule_without_severity(self):
        """Test get_rule_severity with existing rule without severity."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_rule_config = RuleConfig(severity=None)
        test_config.rules = {"DS201": test_rule_config}
        registry._config = test_config

        result = get_rule_severity("DS201")

        assert result is None

    def test_get_rule_severity_nonexistent_rule(self):
        """Test get_rule_severity with nonexistent rule."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.rules = {}
        registry._config = test_config

        result = get_rule_severity("nonexistent_rule")

        assert result is None

    def test_should_fail_on_severity_with_enum(self):
        """Test should_fail_on_severity with SeverityLevel enum."""
        result = should_fail_on_severity(SeverityLevel.ERROR)
        assert result is True

        result = should_fail_on_severity(SeverityLevel.WARNING)
        assert result is False

    def test_should_fail_on_severity_with_string(self):
        """Test should_fail_on_severity with string severity."""
        result = should_fail_on_severity("error")
        assert result is True

        result = should_fail_on_severity("warning")
        assert result is False

    def test_get_fail_on_level(self):
        """Test get_fail_on_level function."""
        result = get_fail_on_level()
        assert result == SeverityLevel.ERROR

    def test_get_output_formats(self):
        """Test get_output_formats function."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.output.format = OutputFormat.JSON
        registry._config = test_config

        result = get_output_formats()

        assert result == ["json"]

    def test_is_verbose(self):
        """Test is_verbose function."""
        registry = ConfigRegistry()
        test_config = create_default_config()
        test_config.output.verbose = True
        registry._config = test_config

        result = is_verbose()

        assert result is True

    def test_is_quiet(self):
        """Test is_quiet function (always returns False)."""
        result = is_quiet()
        assert result is False


class TestConfigRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_initialize_with_none_values(self):
        """Test initialization with None values."""
        registry = ConfigRegistry()

        registry.initialize(None, None, None)

        assert registry.is_initialized()
        assert registry._project_root == Path.cwd()

    def test_initialize_with_empty_cli_args(self):
        """Test initialization with empty CLI args."""
        registry = ConfigRegistry()

        registry.initialize(cli_args={})

        assert registry.is_initialized()

    def test_get_config_multiple_calls(self):
        """Test multiple calls to get_config."""
        registry = ConfigRegistry()

        config1 = registry.get_config()
        config2 = registry.get_config()

        assert config1 is config2

    def test_reload_config_when_not_initialized(self):
        """Test reload_config when not initialized."""
        registry = ConfigRegistry()

        # Should not raise an exception
        registry.reload_config()

        assert registry.is_initialized()

    def test_get_project_root_multiple_calls(self):
        """Test multiple calls to get_project_root."""
        registry = ConfigRegistry()

        root1 = registry.get_project_root()
        root2 = registry.get_project_root()

        assert root1 == root2

    def test_reset_clears_all_instances(self):
        """Test that reset clears all instance variables."""
        registry = ConfigRegistry()
        registry._config = "test"
        registry._project_root = Path("/test")

        ConfigRegistry().reset()

        new_registry = ConfigRegistry()
        assert new_registry._config is None
        assert new_registry._project_root is None


class TestConfigRegistryIntegration:
    """Test integration scenarios and real-world usage patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_full_initialization_workflow(self):
        """Test complete initialization workflow."""
        registry = ConfigRegistry()

        # Test initial state
        assert not registry.is_initialized()
        assert registry._config is None
        assert registry._project_root is None

        # Initialize
        cli_args = {"profile": "strict", "verbose": True}
        project_root = Path("/test/project")
        registry.initialize(cli_args=cli_args, project_root=project_root)

        # Test post-initialization state
        assert registry.is_initialized()
        assert registry._config is not None
        assert registry._project_root == project_root

        # Test configuration access
        config = registry.get_config()
        assert isinstance(config, DSConfig)

        # Test project root access
        root = registry.get_project_root()
        assert root == project_root

    def test_configuration_reload_workflow(self):
        """Test configuration reload workflow."""
        registry = ConfigRegistry()

        # Initial configuration
        registry.initialize()
        original_config = registry._config

        # Reload configuration
        new_cli_args = {"profile": "relaxed"}
        registry.reload_config(cli_args=new_cli_args)

        # Verify reload
        assert registry._config is not original_config
        assert registry.is_initialized()

    def test_global_functions_workflow(self):
        """Test workflow using global functions."""
        # Reset global state
        reset_config()

        # Initialize using global function
        cli_args = {"profile": "strict"}
        initialize_config(cli_args=cli_args)

        # Access configuration using global functions
        config = get_config()
        assert isinstance(config, DSConfig)

        # Access project root
        root = get_project_root()
        assert isinstance(root, Path)

        # Test convenience functions
        profile = get_active_profile()
        assert profile is not None

        formats = get_output_formats()
        assert isinstance(formats, list)

    def test_error_recovery_workflow(self):
        """Test error recovery workflow."""
        registry = ConfigRegistry()

        # Simulate configuration loading failure
        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_config.side_effect = Exception("Configuration error")
            mock_loader_class.return_value = mock_loader

            # Should fall back to default configuration
            registry.initialize()

            assert registry.is_initialized()
            assert registry._config is not None

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access patterns."""
        registry = ConfigRegistry()

        # Simulate multiple threads accessing the same registry
        configs = []
        for _ in range(10):
            config = registry.get_config()
            configs.append(config)

        # All should be the same instance
        assert all(config is configs[0] for config in configs)

    def test_memory_cleanup_workflow(self):
        """Test memory cleanup workflow."""
        registry = ConfigRegistry()

        # Initialize and use
        registry.initialize()
        config = registry.get_config()

        # Reset and verify cleanup
        ConfigRegistry().reset()
        new_registry = ConfigRegistry()

        assert new_registry._config is None
        # Note: Due to singleton pattern, new_registry and registry are the same instance
        # but the internal state has been cleared
        assert new_registry is registry


class TestConfigRegistryLogging:
    """Test logging functionality in configuration registry."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_logging_warning_on_config_failure(self):
        """Test that warning is logged when configuration loading fails."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            mock_loader.load_config.side_effect = Exception("Config failed")
            mock_loader_class.return_value = mock_loader

            with patch(
                "pytest_drill_sergeant.core.config_registry.create_default_config"
            ):
                with patch("logging.getLogger") as mock_logger:
                    mock_log = Mock()
                    mock_logger.return_value = mock_log

                    registry.initialize()

                    # Verify warning was logged
                    mock_log.warning.assert_called_once()
                    call_args = mock_log.warning.call_args[0]
                    assert (
                        "Failed to load configuration, using defaults" in call_args[0]
                    )
                    assert "Config failed" in str(call_args[1])

    def test_logging_with_caught_exception(self):
        """Test logging with specific exception details."""
        registry = ConfigRegistry()

        with patch(
            "pytest_drill_sergeant.core.config_registry.ProfileConfigLoader"
        ) as mock_loader_class:
            mock_loader = Mock()
            test_exception = ValueError("Invalid configuration format")
            mock_loader.load_config.side_effect = test_exception
            mock_loader_class.return_value = mock_loader

            with patch(
                "pytest_drill_sergeant.core.config_registry.create_default_config"
            ):
                with patch("logging.getLogger") as mock_logger:
                    mock_log = Mock()
                    mock_logger.return_value = mock_log

                    registry.initialize()

                    # Verify exception details in log
                    mock_log.warning.assert_called_once()
                    call_args = mock_log.warning.call_args[0]
                    assert "Invalid configuration format" in str(call_args[1])


class TestConfigRegistryTypeSafety:
    """Test type safety and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        ConfigRegistry().reset()

    def teardown_method(self):
        """Clean up after tests."""
        ConfigRegistry().reset()

    def test_initialize_with_correct_types(self):
        """Test initialization with correct parameter types."""
        registry = ConfigRegistry()

        cli_args: dict[str, Any] = {"profile": "strict"}
        pytest_config = Mock()
        project_root = Path("/test")

        # Should not raise type errors
        registry.initialize(cli_args, pytest_config, project_root)

        assert registry.is_initialized()

    def test_get_config_return_type(self):
        """Test that get_config returns correct type."""
        registry = ConfigRegistry()
        registry.initialize()

        config = registry.get_config()

        assert isinstance(config, DSConfig)

    def test_get_project_root_return_type(self):
        """Test that get_project_root returns correct type."""
        registry = ConfigRegistry()

        root = registry.get_project_root()

        assert isinstance(root, Path)

    def test_is_initialized_return_type(self):
        """Test that is_initialized returns correct type."""
        registry = ConfigRegistry()

        # Initially False
        assert isinstance(registry.is_initialized(), bool)
        assert registry.is_initialized() is False

        # After initialization True
        registry.initialize()
        assert isinstance(registry.is_initialized(), bool)
        assert registry.is_initialized() is True
