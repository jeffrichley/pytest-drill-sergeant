"""Type stubs for sarif_om library.

These stubs define the minimal interface needed by pytest-drill-sergeant
for SARIF 2.1.0 compliant output generation.

The stubs use precise types for core SARIF fields to maintain type safety,
with properties fields using a union type that covers both metrics and config data.
"""

from typing import Sequence, Union

# Import the JSON types used in the codebase
from pytest_drill_sergeant.core.reporting.types import JSONValue

# SARIF properties can contain metrics data and configuration data
SarifPropertyValue = Union[
    str,
    int,
    float,
    bool,
    list[str],
    dict[str, Union[str, int, float, bool]],  # metrics format
    JSONValue,  # config format (includes None and nested structures)
]

class Message:
    def __init__(self, text: str = ...) -> None: ...
    text: str

class Region:
    def __init__(self) -> None: ...
    start_line: int
    start_column: int
    snippet: Message

class ArtifactLocation:
    def __init__(self, uri: str = ...) -> None: ...
    uri: str

class PhysicalLocation:
    def __init__(
        self, artifact_location: ArtifactLocation = ..., region: Region = ...
    ) -> None: ...
    artifact_location: ArtifactLocation
    region: Region

class Result:
    def __init__(
        self,
        message: Message = ...,
        rule_id: str = ...,
        level: str = ...,
        locations: Sequence[PhysicalLocation] = ...,
    ) -> None: ...
    message: Message
    rule_id: str
    level: str
    locations: Sequence[PhysicalLocation]
    # Properties can contain arbitrary values per SARIF spec
    properties: dict[str, SarifPropertyValue]

class ReportingDescriptor:
    def __init__(self) -> None: ...
    id: str
    name: str
    short_description: Message
    help_uri: str
    # Properties can contain arbitrary values per SARIF spec
    properties: dict[str, SarifPropertyValue]

class ToolComponent:
    def __init__(self) -> None: ...
    name: str
    version: str
    information_uri: str
    rules: Sequence[ReportingDescriptor]

class Tool:
    def __init__(self, driver: ToolComponent = ...) -> None: ...
    driver: ToolComponent

class Run:
    def __init__(self) -> None: ...
    tool: Tool
    results: Sequence[Result]
    # Properties can contain arbitrary values per SARIF spec
    properties: dict[str, SarifPropertyValue]

class SarifLog:
    def __init__(self) -> None: ...
    version: str
    schema: str
    runs: Sequence[Run]

__all__ = [
    "ArtifactLocation",
    "Message",
    "PhysicalLocation",
    "Region",
    "ReportingDescriptor",
    "Result",
    "Run",
    "SarifLog",
    "Tool",
    "ToolComponent",
]
