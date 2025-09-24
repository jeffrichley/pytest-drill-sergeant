"""Enhanced configuration validation with detailed error reporting.

This module provides comprehensive configuration validation with detailed
error messages and suggestions for fixing common configuration issues.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pytest_drill_sergeant.core.error_handler import (
    AnalysisError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    create_error_context,
)
from pytest_drill_sergeant.core.models import Severity


class ConfigurationValidationError(Exception):
    """Exception raised for configuration validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        """Initialize configuration validation error.

        Args:
            message: Error message
            field: Field that caused the error
            suggestion: Suggestion for fixing the error
        """
        super().__init__(message)
        self.field = field
        self.suggestion = suggestion


class EnhancedConfigValidator:
    """Enhanced configuration validator with detailed error reporting."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the enhanced configuration validator.

        Args:
            logger: Logger instance for validation messages
        """
        self.logger = logger or logging.getLogger("drill_sergeant.config_validator")
        self.validation_errors: List[AnalysisError] = []

    def validate_config(self, config: Dict[str, Any]) -> List[AnalysisError]:
        """Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            List of validation errors
        """
        self.validation_errors.clear()
        
        # Validate basic structure
        self._validate_basic_structure(config)
        
        # Validate profiles
        if "profiles" in config:
            self._validate_profiles(config["profiles"])
        
        # Validate rules
        if "rules" in config:
            self._validate_rules(config["rules"])
        
        # Validate paths
        if "paths" in config:
            self._validate_paths(config["paths"])
        
        # Validate output settings
        if "output" in config:
            self._validate_output_settings(config["output"])
        
        # Validate persona settings
        if "persona" in config:
            self._validate_persona_settings(config["persona"])
        
        return self.validation_errors.copy()

    def _validate_basic_structure(self, config: Dict[str, Any]) -> None:
        """Validate basic configuration structure.

        Args:
            config: Configuration dictionary
        """
        required_fields = ["version"]
        for field in required_fields:
            if field not in config:
                self._add_validation_error(
                    f"Missing required field: {field}",
                    field=field,
                    suggestion=f"Add '{field}' field to your configuration"
                )

    def _validate_profiles(self, profiles: Dict[str, Any]) -> None:
        """Validate profile configurations.

        Args:
            profiles: Profiles configuration
        """
        if not isinstance(profiles, dict):
            self._add_validation_error(
                "Profiles must be a dictionary",
                field="profiles",
                suggestion="Ensure profiles is a dictionary with profile names as keys"
            )
            return

        for profile_name, profile_config in profiles.items():
            if not isinstance(profile_config, dict):
                self._add_validation_error(
                    f"Profile '{profile_name}' must be a dictionary",
                    field=f"profiles.{profile_name}",
                    suggestion="Ensure each profile is a dictionary with configuration options"
                )
                continue

            # Validate profile structure
            self._validate_profile_structure(profile_name, profile_config)

    def _validate_profile_structure(self, profile_name: str, profile_config: Dict[str, Any]) -> None:
        """Validate individual profile structure.

        Args:
            profile_name: Name of the profile
            profile_config: Profile configuration
        """
        # Validate fail_on setting
        if "fail_on" in profile_config:
            fail_on = profile_config["fail_on"]
            valid_fail_on = ["error", "warning", "info", "hint"]
            if fail_on not in valid_fail_on:
                self._add_validation_error(
                    f"Invalid fail_on value '{fail_on}' in profile '{profile_name}'",
                    field=f"profiles.{profile_name}.fail_on",
                    suggestion=f"Use one of: {', '.join(valid_fail_on)}"
                )

        # Validate enable/disable rules
        for rule_setting in ["enable", "disable", "only"]:
            if rule_setting in profile_config:
                rules = profile_config[rule_setting]
                if isinstance(rules, str):
                    rules = [rules]
                elif not isinstance(rules, list):
                    self._add_validation_error(
                        f"Invalid {rule_setting} value in profile '{profile_name}'",
                        field=f"profiles.{profile_name}.{rule_setting}",
                        suggestion=f"Use a string or list of rule names for {rule_setting}"
                    )
                    continue

                # Validate rule names
                for rule in rules:
                    if not isinstance(rule, str) or not rule.strip():
                        self._add_validation_error(
                            f"Invalid rule name '{rule}' in profile '{profile_name}'",
                            field=f"profiles.{profile_name}.{rule_setting}",
                            suggestion="Use valid rule names (e.g., 'DS201', 'DS202')"
                        )

    def _validate_rules(self, rules: Dict[str, Any]) -> None:
        """Validate rule configurations.

        Args:
            rules: Rules configuration
        """
        if not isinstance(rules, dict):
            self._add_validation_error(
                "Rules must be a dictionary",
                field="rules",
                suggestion="Ensure rules is a dictionary with rule configurations"
            )
            return

        for rule_name, rule_config in rules.items():
            if not isinstance(rule_config, dict):
                self._add_validation_error(
                    f"Rule '{rule_name}' must be a dictionary",
                    field=f"rules.{rule_name}",
                    suggestion="Ensure each rule is a dictionary with configuration options"
                )
                continue

            # Validate rule structure
            self._validate_rule_structure(rule_name, rule_config)

    def _validate_rule_structure(self, rule_name: str, rule_config: Dict[str, Any]) -> None:
        """Validate individual rule structure.

        Args:
            rule_name: Name of the rule
            rule_config: Rule configuration
        """
        # Validate severity
        if "severity" in rule_config:
            severity = rule_config["severity"]
            valid_severities = [s.value for s in Severity]
            if severity not in valid_severities:
                self._add_validation_error(
                    f"Invalid severity '{severity}' for rule '{rule_name}'",
                    field=f"rules.{rule_name}.severity",
                    suggestion=f"Use one of: {', '.join(valid_severities)}"
                )

        # Validate enabled flag
        if "enabled" in rule_config:
            enabled = rule_config["enabled"]
            if not isinstance(enabled, bool):
                self._add_validation_error(
                    f"Invalid enabled value for rule '{rule_name}'",
                    field=f"rules.{rule_name}.enabled",
                    suggestion="Use true or false for the enabled field"
                )

        # Validate threshold
        if "threshold" in rule_config:
            threshold = rule_config["threshold"]
            if not isinstance(threshold, (int, float)) or threshold < 0:
                self._add_validation_error(
                    f"Invalid threshold '{threshold}' for rule '{rule_name}'",
                    field=f"rules.{rule_name}.threshold",
                    suggestion="Use a non-negative number for threshold"
                )

    def _validate_paths(self, paths: Union[str, List[str]]) -> None:
        """Validate path configurations.

        Args:
            paths: Path configuration
        """
        if isinstance(paths, str):
            paths = [paths]
        elif not isinstance(paths, list):
            self._add_validation_error(
                "Paths must be a string or list of strings",
                field="paths",
                suggestion="Use a string or list of strings for paths"
            )
            return

        for i, path_str in enumerate(paths):
            if not isinstance(path_str, str):
                self._add_validation_error(
                    f"Path at index {i} must be a string",
                    field=f"paths[{i}]",
                    suggestion="Use string paths only"
                )
                continue

            # Check if path exists
            path = Path(path_str)
            if not path.exists():
                self._add_validation_error(
                    f"Path does not exist: {path_str}",
                    field=f"paths[{i}]",
                    suggestion=f"Check if the path exists: {path.absolute()}"
                )

    def _validate_output_settings(self, output: Dict[str, Any]) -> None:
        """Validate output configuration.

        Args:
            output: Output configuration
        """
        if not isinstance(output, dict):
            self._add_validation_error(
                "Output must be a dictionary",
                field="output",
                suggestion="Ensure output is a dictionary with output settings"
            )
            return

        # Validate format
        if "format" in output:
            format_value = output["format"]
            valid_formats = ["terminal", "json", "sarif"]
            if format_value not in valid_formats:
                self._add_validation_error(
                    f"Invalid output format '{format_value}'",
                    field="output.format",
                    suggestion=f"Use one of: {', '.join(valid_formats)}"
                )

        # Validate output file
        if "file" in output:
            output_file = output["file"]
            if not isinstance(output_file, str):
                self._add_validation_error(
                    "Output file must be a string",
                    field="output.file",
                    suggestion="Use a string path for the output file"
                )
            else:
                # Check if output directory exists
                output_path = Path(output_file)
                if not output_path.parent.exists():
                    self._add_validation_error(
                        f"Output directory does not exist: {output_path.parent}",
                        field="output.file",
                        suggestion=f"Create the directory: {output_path.parent.absolute()}"
                    )

    def _validate_persona_settings(self, persona: Union[str, Dict[str, Any]]) -> None:
        """Validate persona configuration.

        Args:
            persona: Persona configuration
        """
        if isinstance(persona, str):
            # Validate persona name
            valid_personas = ["drill_sergeant", "snoop_dogg", "manager"]
            if persona not in valid_personas:
                self._add_validation_error(
                    f"Invalid persona '{persona}'",
                    field="persona",
                    suggestion=f"Use one of: {', '.join(valid_personas)}"
                )
        elif isinstance(persona, dict):
            # Validate persona configuration
            if "name" not in persona:
                self._add_validation_error(
                    "Persona configuration must have a 'name' field",
                    field="persona.name",
                    suggestion="Add a 'name' field to persona configuration"
                )
            else:
                self._validate_persona_settings(persona["name"])
        else:
            self._add_validation_error(
                "Persona must be a string or dictionary",
                field="persona",
                suggestion="Use a string persona name or dictionary with persona configuration"
            )

    def _add_validation_error(
        self,
        message: str,
        field: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a validation error to the list.

        Args:
            message: Error message
            field: Field that caused the error
            suggestion: Suggestion for fixing the error
        """
        context = create_error_context(
            analyzer_name="config_validator",
            function_name="_add_validation_error",
            field=field,
            suggestion=suggestion,
        )

        error = AnalysisError(
            error_id="",
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            message=message,
            context=context,
            suggestion=suggestion,
            recoverable=True,
        )

        self.validation_errors.append(error)
        self.logger.warning(f"Configuration validation error: {message}")

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation errors.

        Returns:
            Dictionary with validation error summary
        """
        if not self.validation_errors:
            return {"total_errors": 0, "by_field": {}, "by_severity": {}}

        by_field = {}
        by_severity = {}

        for error in self.validation_errors:
            # Count by field
            field = error.context.user_data.get("field", "unknown") if error.context else "unknown"
            by_field[field] = by_field.get(field, 0) + 1

            # Count by severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_errors": len(self.validation_errors),
            "by_field": by_field,
            "by_severity": by_severity,
            "critical_errors": sum(1 for e in self.validation_errors if e.severity == ErrorSeverity.CRITICAL),
        }

    def clear_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()


def validate_config_file(config_path: Path) -> List[AnalysisError]:
    """Validate a configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        List of validation errors
    """
    validator = EnhancedConfigValidator()
    
    try:
        # Try to load the configuration file
        if config_path.suffix == ".json":
            import json
            with config_path.open("r") as f:
                config = json.load(f)
        elif config_path.suffix in [".yaml", ".yml"]:
            import yaml
            with config_path.open("r") as f:
                config = yaml.safe_load(f)
        else:
            # Try to load as Python module
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                config = getattr(module, "config", {})
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        return validator.validate_config(config)
        
    except Exception as e:
        # Create error for file loading failure
        context = create_error_context(
            file_path=config_path,
            analyzer_name="config_validator",
            function_name="validate_config_file",
        )
        
        error = AnalysisError(
            error_id="",
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message=f"Failed to load configuration file: {e}",
            context=context,
            suggestion="Check if the file exists and has valid syntax",
            recoverable=False,
        )
        
        return [error]
