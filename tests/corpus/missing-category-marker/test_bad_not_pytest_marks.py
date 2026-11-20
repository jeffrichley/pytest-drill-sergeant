"""Marks named like category markers that are not pytest's, or not a configured
name, and a `pytestmark` that applies to nothing. Analysed, never run.
"""

import pytest
from gauges import Gauge, mark

unit = pytest.mark.slow


@mark.unit
def test_gauge_reads_zero_at_rest():  # expect: DS901
    assert Gauge().read() == 0


@unit
def test_gauge_reads_the_pressure():  # expect: DS901
    gauge = Gauge()
    gauge.apply(3)
    assert gauge.read() == 3


@pytest.mark.unit_tests
@pytest.mark.Integration
def test_gauge_clamps_at_its_limit():  # expect: DS901
    gauge = Gauge(limit=10)
    gauge.apply(99)
    assert gauge.read() == 10


def test_gauge_resets():  # expect: DS901
    """Marked `pytest.mark.unit` in this docstring only."""
    pytestmark = pytest.mark.unit
    gauge = Gauge(mark=pytestmark)
    gauge.reset()
    assert gauge.read() == 0
