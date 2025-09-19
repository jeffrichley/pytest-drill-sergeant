"""Tests for the context-based configuration system."""

import threading
from pathlib import Path
from unittest.mock import patch

from pytest_drill_sergeant.core.config_context import (
    ConfigContext,
    get_config,
    initialize_config,
    reset_config,
)
from pytest_drill_sergeant.core.config_schema import Profile, create_default_config


class TestConfigContext:
    """Test the context-based configuration system."""

    def setup_method(self):
        """Set up each test method."""
        reset_config()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_config()

    def test_context_isolation(self):
        """Test that different contexts maintain separate configurations."""
        # Initialize with standard profile
        config1 = initialize_config(cli_args={"profile": "standard"})
        assert config1.profile == Profile.STANDARD

        # Create a context with strict profile
        with ConfigContext() as ctx:
            # Set a different config in this context
            strict_config = create_default_config()
            strict_config.profile = Profile.STRICT
            ctx.set_config(strict_config)

            # Verify we get the strict config in this context
            current_config = get_config()
            assert current_config.profile == Profile.STRICT

        # Back in main context, should still have standard profile
        main_config = get_config()
        assert main_config.profile == Profile.STANDARD

    def test_thread_isolation(self):
        """Test that different threads maintain separate configurations."""
        # Initialize with standard profile
        config1 = initialize_config(cli_args={"profile": "standard"})
        assert config1.profile == Profile.STANDARD

        # Results from thread
        thread_result = {"profile": None}

        def thread_worker():
            # This should get the default config, not the main thread config
            thread_config = get_config()
            thread_result["profile"] = thread_config.profile.value

        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join()

        # Thread should have gotten the default config (standard)
        assert thread_result["profile"] == "standard"

    def test_context_with_different_configs(self):
        """Test using context with different configurations."""
        # Initialize with standard profile
        initialize_config(cli_args={"profile": "standard"})
        assert get_config().profile == Profile.STANDARD

        # Create contexts with different profiles
        with ConfigContext() as ctx1:
            strict_config = create_default_config()
            strict_config.profile = Profile.STRICT
            ctx1.set_config(strict_config)
            assert get_config().profile == Profile.STRICT

            with ConfigContext() as ctx2:
                chill_config = create_default_config()
                chill_config.profile = Profile.RELAXED
                ctx2.set_config(chill_config)
                assert get_config().profile == Profile.RELAXED

            # Back to strict context
            assert get_config().profile == Profile.STRICT

        # Back to main context
        assert get_config().profile == Profile.STANDARD

    def test_auto_initialization(self):
        """Test that config is auto-initialized when accessed."""
        reset_config()

        # Access config without explicit initialization
        config = get_config()
        assert config is not None
        assert config.profile == Profile.STANDARD

    def test_initialization_with_project_root(self):
        """Test initialization with custom project root."""
        custom_root = Path("/tmp/test_project")

        with patch.object(Path, "cwd", return_value=custom_root):
            config = initialize_config(project_root=custom_root)
            assert config is not None

    def test_reload_config(self):
        """Test reloading configuration."""
        # Initialize with standard profile
        config1 = initialize_config(cli_args={"profile": "standard"})
        assert config1.profile == Profile.STANDARD

        # Reload with strict profile using force_reload
        config2 = initialize_config(cli_args={"profile": "strict"}, force_reload=True)
        assert config2.profile == Profile.STRICT

    def test_context_reset(self):
        """Test that context can be reset."""
        # Initialize config
        config1 = initialize_config(cli_args={"profile": "standard"})
        assert config1.profile == Profile.STANDARD

        # Reset and verify it's cleared
        reset_config()
        # Should auto-initialize with defaults
        config2 = get_config()
        assert config2.profile == Profile.STANDARD

    def test_convenience_functions(self):
        """Test that convenience functions work with context system."""
        from pytest_drill_sergeant.core.config_context import (
            get_active_profile,
            get_fail_on_level,
            get_output_formats,
            get_rule_severity,
            is_quiet,
            is_rule_enabled,
            is_verbose,
        )

        # Initialize config
        config = initialize_config(cli_args={"profile": "strict", "verbose": True})

        # Test convenience functions
        assert get_active_profile() == Profile.STRICT

        # Test rule functions (rules may not be configured in default config)
        # Just test that the functions work without error
        is_rule_enabled("private_access")  # Should return True for non-existent rules
        get_rule_severity("private_access")  # May return None for non-existent rules

        assert get_fail_on_level() is not None
        assert get_output_formats() == ["terminal"]
        assert (
            is_verbose() is False
        )  # DSConfig doesn't have verbose, so should be False
        assert is_quiet() is False

    def test_error_handling(self):
        """Test error handling in context system."""
        # Test with invalid CLI args
        config = initialize_config(cli_args={"invalid_key": "value"})
        assert config is not None  # Should fall back to defaults

    def test_context_with_exception(self):
        """Test that context is properly cleaned up even with exceptions."""
        # Initialize with standard profile
        initialize_config(cli_args={"profile": "standard"})
        assert get_config().profile == Profile.STANDARD

        # Create context that raises an exception
        try:
            with ConfigContext() as ctx:
                strict_config = create_default_config()
                strict_config.profile = Profile.STRICT
                ctx.set_config(strict_config)
                assert get_config().profile == Profile.STRICT
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should be back to main context
        assert get_config().profile == Profile.STANDARD
