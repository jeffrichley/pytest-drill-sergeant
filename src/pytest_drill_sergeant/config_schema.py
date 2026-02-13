"""Configuration schema validation and normalization for drill-sergeant."""

from __future__ import annotations

from typing import Literal

RuleSeverity = Literal["error", "warn", "off"]
AAAMode = Literal["basic", "strict"]

_VALID_RULE_SEVERITIES = {"error", "warn", "off"}
_VALID_AAA_MODES = {"basic", "strict"}


def _normalize_string(value: object, default: str) -> str:
    """Normalize arbitrary config value to lowercase string."""
    if value is None:
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    return text


def normalize_rule_severity(value: object, setting_name: str) -> RuleSeverity:
    """Normalize and validate a rule severity setting."""
    normalized = _normalize_string(value, "error")
    if normalized not in _VALID_RULE_SEVERITIES:
        allowed = ", ".join(sorted(_VALID_RULE_SEVERITIES))
        message = (
            f"Invalid value for {setting_name}: {value!r}. "
            f"Expected one of: {allowed}."
        )
        raise ValueError(message)
    return normalized  # type: ignore[return-value]


def normalize_aaa_mode(value: object) -> AAAMode:
    """Normalize and validate AAA mode."""
    normalized = _normalize_string(value, "basic")
    if normalized not in _VALID_AAA_MODES:
        allowed = ", ".join(sorted(_VALID_AAA_MODES))
        message = (
            f"Invalid value for drill_sergeant_aaa_mode: {value!r}. "
            f"Expected one of: {allowed}."
        )
        raise ValueError(message)
    return normalized  # type: ignore[return-value]


def normalize_non_negative_int(value: int, setting_name: str) -> int:
    """Validate non-negative integer settings."""
    if value < 0:
        message = (
            f"Invalid value for {setting_name}: {value}. "
            "Expected a non-negative integer."
        )
        raise ValueError(message)
    return value


def normalize_positive_int(value: int, setting_name: str) -> int:
    """Validate positive integer settings."""
    if value <= 0:
        message = f"Invalid value for {setting_name}: {value}. Expected an integer > 0."
        raise ValueError(message)
    return value
