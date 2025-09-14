"""Shared type definitions for reporting modules.

This module contains all shared type definitions used across the reporting
modules to avoid circular imports and provide a single source of truth for
type definitions.
"""

from __future__ import annotations

# Recursive JSON types
from typing import TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
JSONDict: TypeAlias = dict[str, JSONValue]
