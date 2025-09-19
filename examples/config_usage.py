#!/usr/bin/env python3
"""Example showing how to use the context-based configuration system."""


# Example 1: Basic usage in a detector
def example_detector_usage():
    """Example of how a detector would use the context-based config."""
    from pytest_drill_sergeant.core.config_context import (
        get_rule_severity,
        is_rule_enabled,
        should_fail_on_severity,
    )

    # Check if a rule is enabled
    if is_rule_enabled("private_access"):
        # Get the severity level for the rule
        severity = get_rule_severity("private_access")
        print(f"Private access rule is enabled with severity: {severity.value}")

    # Check if a severity should cause a failure
    from pytest_drill_sergeant.core.models import Severity

    if should_fail_on_severity(Severity.WARNING):
        print("Warnings will cause failures")
    else:
        print("Warnings will not cause failures")


# Example 2: CLI initialization
def example_cli_initialization():
    """Example of how CLI would initialize the config."""
    from pytest_drill_sergeant.core.config_context import initialize_config, get_config

    # Initialize with CLI arguments
    cli_args = {"profile": "strict", "fail_on": "warning", "verbose": True}

    initialize_config(cli_args=cli_args)

    # Now any part of the system can access the config
    config = get_config()
    print(f"Active profile: {config.get_active_profile().value}")
    print(f"Fail on: {config.fail_on.value}")


# Example 3: Plugin initialization
def example_plugin_initialization():
    """Example of how pytest plugin would initialize the config."""
    from pytest_drill_sergeant.core.config_context import initialize_config

    # Initialize with defaults (no CLI args in plugin mode)
    initialize_config()

    # Now all detectors and components can access the same config
    from pytest_drill_sergeant.core.config_context import get_rule_severity

    severity = get_rule_severity("private_access")
    print(f"Plugin mode - private access severity: {severity.value}")


# Example 4: Testing with config reset
def example_testing():
    """Example of how to test with different configurations."""
    from pytest_drill_sergeant.core.config_context import (
        initialize_config,
        reset_config,
        get_config,
    )

    # Test with strict profile
    reset_config()  # Clear any existing config
    initialize_config(cli_args={"profile": "strict"})
    strict_config = get_config()
    print(f"Test 1 - Profile: {strict_config.get_active_profile().value}")

    # Test with chill profile
    reset_config()  # Clear any existing config
    initialize_config(cli_args={"profile": "chill"})
    chill_config = get_config()
    print(f"Test 2 - Profile: {chill_config.get_active_profile().value}")


if __name__ == "__main__":
    print("🎯 Centralized Configuration Registry Examples")
    print("=" * 50)

    print("\n1. Detector Usage:")
    example_detector_usage()

    print("\n2. CLI Initialization:")
    example_cli_initialization()

    print("\n3. Plugin Initialization:")
    example_plugin_initialization()

    print("\n4. Testing:")
    example_testing()

    print("\n" + "=" * 50)
    print("✅ All examples completed!")
    print("\n💡 Key Benefits:")
    print("  • Single source of truth for all configuration")
    print("  • No need to pass configs around")
    print("  • Easy to access from anywhere in the codebase")
    print("  • Simple testing with reset functionality")
    print("  • Automatic fallback to defaults")
