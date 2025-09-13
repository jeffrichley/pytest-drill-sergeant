"""Configuration validation utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_drill_sergeant.core.config import DrillSergeantConfig

# Threshold constants
MAX_THRESHOLD_VALUE = 100
MIN_THRESHOLD_VALUE = 0
MAX_HAMMING_VALUE = 64


class ConfigValidator:
    """Validates configuration values and provides helpful error messages."""

    def __init__(self) -> None:
        """Initialize the configuration validator."""
        self._logger = logging.getLogger("drill_sergeant.validator")

    def validate_config(self, config: DrillSergeantConfig) -> list[str]:
        """Validate a configuration object.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate mode
        errors.extend(self._validate_mode(config.mode))

        # Validate persona
        errors.extend(self._validate_persona(config.persona))

        # Validate budgets
        errors.extend(self._validate_budgets(config.budgets))

        # Validate thresholds
        errors.extend(self._validate_thresholds(config.thresholds))

        # Validate rules
        errors.extend(
            self._validate_rules(config.enabled_rules, config.suppressed_rules)
        )

        # Validate output paths
        errors.extend(self._validate_output_paths(config))

        # Validate consistency
        errors.extend(self._validate_consistency(config))

        return errors

    def _validate_mode(self, mode: str) -> list[str]:
        """Validate mode setting."""
        errors = []
        allowed_modes = {"advisory", "quality-gate", "strict"}

        if mode not in allowed_modes:
            errors.append(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(allowed_modes)}"
            )

        return errors

    def _validate_persona(self, persona: str) -> list[str]:
        """Validate persona setting."""
        errors = []
        allowed_personas = {
            "drill_sergeant",
            "snoop_dogg",
            "motivational_coach",
            "sarcastic_butler",
            "pirate",
        }

        if persona not in allowed_personas:
            errors.append(
                f"Invalid persona '{persona}'. Must be one of: {', '.join(allowed_personas)}"
            )

        return errors

    def _validate_budgets(self, budgets: dict[str, int]) -> list[str]:
        """Validate budget settings."""
        errors = []

        for budget_type, value in budgets.items():
            if not isinstance(value, int):
                errors.append(
                    f"Budget {budget_type} must be an integer, got {type(value).__name__}"
                )
            elif value < 0:
                errors.append(f"Budget {budget_type} must be non-negative, got {value}")

        return errors

    def _validate_thresholds(self, thresholds: dict[str, float]) -> list[str]:
        """Validate threshold settings."""
        errors = []

        for threshold_name, value in thresholds.items():
            if not isinstance(value, int | float):
                errors.append(
                    f"Threshold {threshold_name} must be a number, got {type(value).__name__}"
                )
                continue

            if threshold_name.endswith("_threshold") and not (
                MIN_THRESHOLD_VALUE <= value <= MAX_THRESHOLD_VALUE
            ):
                errors.append(
                    f"Threshold {threshold_name} must be between 0 and 100, got {value}"
                )
            elif threshold_name.endswith("_jaccard") and not (0 <= value <= 1):
                errors.append(
                    f"Jaccard threshold {threshold_name} must be between 0 and 1, got {value}"
                )
            elif threshold_name.endswith("_hamming") and not (
                MIN_THRESHOLD_VALUE <= value <= MAX_HAMMING_VALUE
            ):
                errors.append(
                    f"Hamming threshold {threshold_name} must be between 0 and 64, got {value}"
                )

        return errors

    def _validate_rules(
        self, enabled_rules: set[str], suppressed_rules: set[str]
    ) -> list[str]:
        """Validate rule settings."""
        errors = []

        # Check for unknown rules
        known_rules = {
            "aaa_comments",
            "static_clones",
            "fixture_extract",
            "private_access",
            "mock_overspecification",
            "structural_equality",
        }

        unknown_enabled = enabled_rules - known_rules
        if unknown_enabled:
            errors.append(f"Unknown enabled rules: {', '.join(unknown_enabled)}")

        unknown_suppressed = suppressed_rules - known_rules
        if unknown_suppressed:
            errors.append(f"Unknown suppressed rules: {', '.join(unknown_suppressed)}")

        # Check for suppressed rules that aren't enabled
        invalid_suppressed = suppressed_rules - enabled_rules
        if invalid_suppressed:
            errors.append(
                f"Cannot suppress rules that are not enabled: {', '.join(invalid_suppressed)}"
            )

        return errors

    def _validate_output_paths(self, config: DrillSergeantConfig) -> list[str]:
        """Validate output path settings."""
        errors = []

        # Validate JSON report path
        if config.json_report_path:
            json_path = Path(config.json_report_path)
            if not json_path.parent.exists():
                errors.append(
                    f"JSON report directory does not exist: {json_path.parent}"
                )
            elif not json_path.parent.is_dir():
                errors.append(
                    f"JSON report path is not a directory: {json_path.parent}"
                )

        # Validate SARIF report path
        if config.sarif_report_path:
            sarif_path = Path(config.sarif_report_path)
            if not sarif_path.parent.exists():
                errors.append(
                    f"SARIF report directory does not exist: {sarif_path.parent}"
                )
            elif not sarif_path.parent.is_dir():
                errors.append(
                    f"SARIF report path is not a directory: {sarif_path.parent}"
                )

        return errors

    def _validate_consistency(self, config: DrillSergeantConfig) -> list[str]:
        """Validate configuration consistency."""
        errors = []

        # Can't be both verbose and quiet
        if config.verbose and config.quiet:
            errors.append("Cannot specify both verbose and quiet modes")

        # Check threshold consistency
        if (
            "bis_threshold_warn" in config.thresholds
            and "bis_threshold_fail" in config.thresholds
        ):
            warn_threshold = config.thresholds["bis_threshold_warn"]
            fail_threshold = config.thresholds["bis_threshold_fail"]

            if warn_threshold <= fail_threshold:
                errors.append(
                    f"BIS warning threshold ({warn_threshold}) must be greater than failure threshold ({fail_threshold})"
                )

        # Check budget consistency
        if "warn" in config.budgets and "error" in config.budgets:
            warn_budget = config.budgets["warn"]
            error_budget = config.budgets["error"]

            if warn_budget < error_budget:
                errors.append(
                    f"Warning budget ({warn_budget}) should be greater than or equal to error budget ({error_budget})"
                )

        return errors

    def validate_file_paths(self, config: DrillSergeantConfig) -> list[str]:
        """Validate that referenced files exist and are accessible.

        Args:
            config: Configuration to validate

        Returns:
            List of file-related validation errors
        """
        errors = []

        # Check if SUT package exists (if specified)
        if config.sut_package:
            try:
                __import__(config.sut_package)
            except ImportError:
                errors.append(
                    f"SUT package '{config.sut_package}' could not be imported"
                )

        return errors

    def suggest_fixes(self, errors: list[str]) -> dict[str, str]:
        """Suggest fixes for common configuration errors.

        Args:
            errors: List of validation errors

        Returns:
            Dictionary mapping error messages to suggested fixes
        """
        suggestions = {}

        for error in errors:
            if "Invalid mode" in error:
                suggestions[error] = "Use one of: advisory, quality-gate, strict"
            elif "Invalid persona" in error:
                suggestions[error] = (
                    "Use one of: drill_sergeant, snoop_dogg, motivational_coach, sarcastic_butler, pirate"
                )
            elif "must be between 0 and 100" in error:
                suggestions[error] = "Use a value between 0 and 100"
            elif "must be between 0 and 1" in error:
                suggestions[error] = "Use a value between 0 and 1"
            elif "Cannot specify both verbose and quiet" in error:
                suggestions[error] = "Remove either --ds-verbose or --ds-quiet"
            elif "directory does not exist" in error:
                suggestions[error] = "Create the directory or use a different path"
            elif "could not be imported" in error:
                suggestions[error] = "Install the package or check the package name"

        return suggestions


def validate_configuration(
    config: DrillSergeantConfig,
) -> tuple[bool, list[str], dict[str, str]]:
    """Validate a configuration and return results.

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, errors, suggestions)
    """
    validator = ConfigValidator()
    errors = validator.validate_config(config)
    file_errors = validator.validate_file_paths(config)
    all_errors = errors + file_errors

    suggestions = validator.suggest_fixes(all_errors)
    is_valid = len(all_errors) == 0

    return is_valid, all_errors, suggestions
