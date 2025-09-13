"""Shared type definitions for reporting modules.

This module contains all shared type definitions used across the reporting
modules to avoid circular imports and provide a single source of truth for
type definitions.
"""

from __future__ import annotations

# Recursive JSON types
type JSONScalar = str | int | float | bool | None
type JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
type JSONDict = dict[str, JSONValue]
