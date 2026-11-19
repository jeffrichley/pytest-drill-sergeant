"""The check registry: every check, with what it needs to report and teach."""

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.structure import (
    NO_ACTION_UNDER_TEST,
    NO_REAL_ASSERTION,
)

CHECKS: tuple[Check, ...] = (NO_REAL_ASSERTION, NO_ACTION_UNDER_TEST)

__all__ = ["CHECKS", "Check", "Hit", "TestFile", "TestFunction"]
