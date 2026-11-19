"""The check registry: every check, with what it needs to report and teach."""

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.brittleness import (
    BRITTLE_STRING_MATCH,
    PRIVATE_STATE_ASSERTION,
    SOURCE_TEXT_GREP,
)
from pytest_drill_sergeant.checks.structure import NO_REAL_ASSERTION

CHECKS: tuple[Check, ...] = (
    NO_REAL_ASSERTION,
    BRITTLE_STRING_MATCH,
    PRIVATE_STATE_ASSERTION,
    SOURCE_TEXT_GREP,
)

__all__ = ["CHECKS", "Check", "Hit", "TestFile", "TestFunction"]
