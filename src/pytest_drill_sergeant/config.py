"""Configuration management for pytest-drill-sergeant."""

from dataclasses import dataclass, field

import pytest

from pytest_drill_sergeant.utils import (
    get_bool_option,
    get_int_option,
    get_marker_mappings,
    get_synonym_list,
)


@dataclass
class DrillSergeantConfig:
    """Configuration for pytest-drill-sergeant plugin."""

    enabled: bool = True
    enforce_markers: bool = True
    enforce_aaa: bool = True
    enforce_file_length: bool = True
    auto_detect_markers: bool = True
    min_description_length: int = 3
    max_file_length: int = 350
    marker_mappings: dict[str, str] = field(default_factory=dict)

    # AAA Synonym Recognition
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

        # Get custom marker mappings from TOML configuration
        marker_mappings = get_marker_mappings(config)

        # AAA Synonym Recognition settings
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

        return cls(
            enabled=enabled,
            enforce_markers=enforce_markers,
            enforce_aaa=enforce_aaa,
            enforce_file_length=enforce_file_length,
            auto_detect_markers=auto_detect_markers,
            min_description_length=min_description_length,
            max_file_length=max_file_length,
            marker_mappings=marker_mappings,
            aaa_synonyms_enabled=aaa_synonyms_enabled,
            aaa_builtin_synonyms=aaa_builtin_synonyms,
            aaa_arrange_synonyms=aaa_arrange_synonyms,
            aaa_act_synonyms=aaa_act_synonyms,
            aaa_assert_synonyms=aaa_assert_synonyms,
        )
