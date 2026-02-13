"""Configuration management for pytest-drill-sergeant."""

from dataclasses import dataclass, field

import pytest

from pytest_drill_sergeant.config_schema import (
    normalize_aaa_mode,
    normalize_non_negative_int,
    normalize_positive_int,
    normalize_rule_severity,
)
from pytest_drill_sergeant.utils import (
    get_bool_option,
    get_int_option,
    get_marker_mappings,
    get_string_option,
    get_synonym_list,
)


@dataclass
class DrillSergeantConfig:
    """Configuration for pytest-drill-sergeant plugin."""

    enabled: bool = True
    enforce_markers: bool = True
    enforce_aaa: bool = True
    enforce_file_length: bool = True
    marker_severity: str = "error"  # "error", "warn", or "off"
    aaa_severity: str = "error"  # "error", "warn", or "off"
    auto_detect_markers: bool = True
    min_description_length: int = 3
    max_file_length: int = 350
    file_length_mode: str = "error"  # "error", "warn", or "off"
    file_length_exclude: list[str] = field(default_factory=list)
    file_length_inline_ignore: bool = True
    file_length_inline_ignore_token: str = "drill-sergeant: file-length ignore"
    marker_mappings: dict[str, str] = field(default_factory=dict)

    # AAA Synonym Recognition
    aaa_mode: str = "basic"  # "basic" or "strict"
    aaa_synonyms_enabled: bool = False
    aaa_builtin_synonyms: bool = True
    aaa_arrange_synonyms: list[str] = field(default_factory=list)
    aaa_act_synonyms: list[str] = field(default_factory=list)
    aaa_assert_synonyms: list[str] = field(default_factory=list)

    @classmethod
    def from_pytest_config(cls, config: pytest.Config) -> "DrillSergeantConfig":
        """Create config from pytest configuration and environment variables."""
        # Environment variables take precedence
        enabled = get_bool_option(
            config,
            "drill_sergeant_enabled",
            env_var="DRILL_SERGEANT_ENABLED",
            default=True,
        )

        # If disabled globally, return early
        if not enabled:
            return cls(enabled=False)

        enforce_markers = get_bool_option(
            config,
            "drill_sergeant_enforce_markers",
            env_var="DRILL_SERGEANT_ENFORCE_MARKERS",
            default=True,
        )

        enforce_aaa = get_bool_option(
            config,
            "drill_sergeant_enforce_aaa",
            env_var="DRILL_SERGEANT_ENFORCE_AAA",
            default=True,
        )

        enforce_file_length = get_bool_option(
            config,
            "drill_sergeant_enforce_file_length",
            env_var="DRILL_SERGEANT_ENFORCE_FILE_LENGTH",
            default=True,
        )
        marker_severity = get_string_option(
            config,
            "drill_sergeant_marker_severity",
            "DRILL_SERGEANT_MARKER_SEVERITY",
            "error",
        )
        aaa_severity = get_string_option(
            config,
            "drill_sergeant_aaa_severity",
            "DRILL_SERGEANT_AAA_SEVERITY",
            "error",
        )

        auto_detect_markers = get_bool_option(
            config,
            "drill_sergeant_auto_detect_markers",
            env_var="DRILL_SERGEANT_AUTO_DETECT_MARKERS",
            default=True,
        )

        min_description_length = get_int_option(
            config,
            "drill_sergeant_min_description_length",
            env_var="DRILL_SERGEANT_MIN_DESCRIPTION_LENGTH",
            default=3,
        )

        max_file_length = get_int_option(
            config,
            "drill_sergeant_max_file_length",
            env_var="DRILL_SERGEANT_MAX_FILE_LENGTH",
            default=350,
        )

        file_length_mode = get_string_option(
            config,
            "drill_sergeant_file_length_mode",
            "DRILL_SERGEANT_FILE_LENGTH_MODE",
            "error",
        )
        file_length_exclude = get_synonym_list(
            config,
            "drill_sergeant_file_length_exclude",
            "DRILL_SERGEANT_FILE_LENGTH_EXCLUDE",
        )
        file_length_inline_ignore = get_bool_option(
            config,
            "drill_sergeant_file_length_inline_ignore",
            env_var="DRILL_SERGEANT_FILE_LENGTH_INLINE_IGNORE",
            default=True,
        )
        file_length_inline_ignore_token = get_string_option(
            config,
            "drill_sergeant_file_length_inline_ignore_token",
            "DRILL_SERGEANT_FILE_LENGTH_INLINE_IGNORE_TOKEN",
            "drill-sergeant: file-length ignore",
        )

        # Get custom marker mappings from TOML configuration
        marker_mappings = get_marker_mappings(config)

        # AAA Synonym Recognition settings
        aaa_mode = get_string_option(
            config,
            "drill_sergeant_aaa_mode",
            "DRILL_SERGEANT_AAA_MODE",
            "basic",
        )

        aaa_synonyms_enabled = get_bool_option(
            config,
            "drill_sergeant_aaa_synonyms_enabled",
            env_var="DRILL_SERGEANT_AAA_SYNONYMS_ENABLED",
            default=False,
        )

        aaa_builtin_synonyms = get_bool_option(
            config,
            "drill_sergeant_aaa_builtin_synonyms",
            env_var="DRILL_SERGEANT_AAA_BUILTIN_SYNONYMS",
            default=True,
        )

        aaa_arrange_synonyms = get_synonym_list(
            config,
            "drill_sergeant_aaa_arrange_synonyms",
            "DRILL_SERGEANT_AAA_ARRANGE_SYNONYMS",
        )

        aaa_act_synonyms = get_synonym_list(
            config,
            "drill_sergeant_aaa_act_synonyms",
            "DRILL_SERGEANT_AAA_ACT_SYNONYMS",
        )

        aaa_assert_synonyms = get_synonym_list(
            config,
            "drill_sergeant_aaa_assert_synonyms",
            "DRILL_SERGEANT_AAA_ASSERT_SYNONYMS",
        )

        marker_severity = normalize_rule_severity(
            marker_severity, "drill_sergeant_marker_severity"
        )
        aaa_severity = normalize_rule_severity(
            aaa_severity, "drill_sergeant_aaa_severity"
        )
        file_length_mode = normalize_rule_severity(
            file_length_mode, "drill_sergeant_file_length_mode"
        )
        aaa_mode = normalize_aaa_mode(aaa_mode)
        min_description_length = normalize_non_negative_int(
            min_description_length, "drill_sergeant_min_description_length"
        )
        max_file_length = normalize_positive_int(
            max_file_length, "drill_sergeant_max_file_length"
        )

        return cls(
            enabled=enabled,
            enforce_markers=enforce_markers,
            enforce_aaa=enforce_aaa,
            enforce_file_length=enforce_file_length,
            marker_severity=marker_severity,
            aaa_severity=aaa_severity,
            auto_detect_markers=auto_detect_markers,
            min_description_length=min_description_length,
            max_file_length=max_file_length,
            file_length_mode=file_length_mode,
            file_length_exclude=file_length_exclude,
            file_length_inline_ignore=file_length_inline_ignore,
            file_length_inline_ignore_token=file_length_inline_ignore_token,
            marker_mappings=marker_mappings,
            aaa_mode=aaa_mode,
            aaa_synonyms_enabled=aaa_synonyms_enabled,
            aaa_builtin_synonyms=aaa_builtin_synonyms,
            aaa_arrange_synonyms=aaa_arrange_synonyms,
            aaa_act_synonyms=aaa_act_synonyms,
            aaa_assert_synonyms=aaa_assert_synonyms,
        )
