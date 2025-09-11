"""Data models for pytest-drill-sergeant."""

from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    """Represents a single test validation issue."""

    issue_type: str  # "marker" or "aaa"
    message: str
    suggestion: str


@dataclass
class AAAStatus:
    """Track AAA section status and validation issues."""

    arrange_found: bool = False
    act_found: bool = False
    assert_found: bool = False
    issues: list[ValidationIssue] = field(default_factory=list)
