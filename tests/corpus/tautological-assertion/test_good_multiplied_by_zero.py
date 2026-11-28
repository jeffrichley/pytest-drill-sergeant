"""Near-misses: multiplying by zero. It isn't an agent idiom, and where real suites
do it the other side is the code's result or `0 * x` is the act: pandas
`tests/tseries/offsets/test_business_hour.py:246` (`dt + 0 * offset2` rolls
forward) and `tests/tseries/holiday/test_calendar.py:103`. Analysed, never run."""

import pytest
from shop import price

pytestmark = pytest.mark.unit


def test_price_of_846():
    assert 5 + (price(846) * 0) == 5


def test_price_through_a_name():
    result = price(846)
    assert 0 * result == 0


def test_zero_offset_rolls_forward(dt, offset):
    assert dt + 0 * offset == offset.rollforward(dt)
