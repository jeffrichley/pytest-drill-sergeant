"""The check registry: every check, with what it needs to report and teach."""

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.flakiness import (
    SLEEP_IN_TEST,
    UNSEEDED_RANDOM,
    WALL_CLOCK_READ,
)
from pytest_drill_sergeant.checks.structure import NO_REAL_ASSERTION

CHECKS: tuple[Check, ...] = (
    NO_REAL_ASSERTION,
    SLEEP_IN_TEST,
    WALL_CLOCK_READ,
    UNSEEDED_RANDOM,
)

__all__ = ["CHECKS", "Check", "Hit", "TestFile", "TestFunction"]
