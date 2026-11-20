"""Near-misses: unmarked code pytest never collects as a test, a fixture, a helper
and classes it skips, needs no category marker. Analysed, never run.
"""

import pytest
from clock import Clock


@pytest.fixture
def test_clock():
    return Clock(now=0)


def build_clock():
    return Clock(now=5)


class TestClockFactory:
    def __init__(self):
        self.clock = build_clock()

    def test_like_name(self):
        return self.clock


class ClockSuite:
    def test_not_collected(self):
        return Clock(now=9)
