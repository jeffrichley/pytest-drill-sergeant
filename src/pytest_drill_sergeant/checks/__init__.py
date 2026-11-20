"""The check registry: every check, with what it needs to report and teach."""

from pytest_drill_sergeant.checks.assertions import (
    MIRROR_ASSERTION,
    TAUTOLOGICAL_ASSERTION,
    WEAK_ASSERTION,
)
from pytest_drill_sergeant.checks.base import (
    Check,
    Hit,
    SourceFile,
    TestFile,
    TestFunction,
)
from pytest_drill_sergeant.checks.brittleness import (
    BRITTLE_STRING_MATCH,
    PRIVATE_STATE_ASSERTION,
    SOURCE_TEXT_GREP,
)
from pytest_drill_sergeant.checks.cheating import (
    SKIP_WITHOUT_REASON,
    TEST_SPECIAL_CASING,
    UNCONDITIONAL_SKIP,
)
from pytest_drill_sergeant.checks.duplication import (
    COPY_PASTE_SETUP,
    NEAR_DUPLICATE_TESTS,
)
from pytest_drill_sergeant.checks.exceptions import BROAD_RAISES, SWALLOWED_EXCEPTION
from pytest_drill_sergeant.checks.flakiness import (
    SLEEP_IN_TEST,
    UNSEEDED_RANDOM,
    WALL_CLOCK_READ,
)
from pytest_drill_sergeant.checks.mocking import (
    MOCK_ONLY_ASSERTION,
    MOCK_WITHOUT_SPEC,
    OVERGROWN_MOCK_SETUP,
)
from pytest_drill_sergeant.checks.structure import (
    ASSERT_BEFORE_ACT,
    CONDITIONAL_LOGIC,
    INTERLEAVED_ACT_ASSERT,
    LONG_FILE,
    LONG_TEST,
    NO_ACTION_UNDER_TEST,
    NO_REAL_ASSERTION,
)
from pytest_drill_sergeant.checks.waivers import MALFORMED_WAIVER

CHECKS: tuple[Check, ...] = (
    MALFORMED_WAIVER,
    NO_REAL_ASSERTION,
    NO_ACTION_UNDER_TEST,
    ASSERT_BEFORE_ACT,
    INTERLEAVED_ACT_ASSERT,
    LONG_TEST,
    LONG_FILE,
    CONDITIONAL_LOGIC,
    WEAK_ASSERTION,
    TAUTOLOGICAL_ASSERTION,
    MIRROR_ASSERTION,
    MOCK_ONLY_ASSERTION,
    MOCK_WITHOUT_SPEC,
    OVERGROWN_MOCK_SETUP,
    SKIP_WITHOUT_REASON,
    UNCONDITIONAL_SKIP,
    TEST_SPECIAL_CASING,
    COPY_PASTE_SETUP,
    NEAR_DUPLICATE_TESTS,
    BRITTLE_STRING_MATCH,
    PRIVATE_STATE_ASSERTION,
    SOURCE_TEXT_GREP,
    BROAD_RAISES,
    SWALLOWED_EXCEPTION,
    SLEEP_IN_TEST,
    WALL_CLOCK_READ,
    UNSEEDED_RANDOM,
)


__all__ = ["CHECKS", "Check", "Hit", "SourceFile", "TestFile", "TestFunction"]
