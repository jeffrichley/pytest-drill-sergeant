"""The check registry: every check, with what it needs to report and teach."""

from pytest_drill_sergeant.checks.assertions import (
    TAUTOLOGICAL_ASSERTION,
    WEAK_ASSERTION,
)
from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.structure import NO_REAL_ASSERTION

CHECKS: tuple[Check, ...] = (NO_REAL_ASSERTION, WEAK_ASSERTION, TAUTOLOGICAL_ASSERTION)

__all__ = ["CHECKS", "Check", "Hit", "TestFile", "TestFunction"]
