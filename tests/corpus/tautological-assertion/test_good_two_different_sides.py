"""Near-misses: comparisons whose two sides look alike but differ, or can fail.
Analysed, never run."""

import pytest
from shop import make_order, parse_price

pytestmark = pytest.mark.unit


def test_two_orders_differ():
    first = make_order(lines=[1000])
    second = make_order(lines=[2000])
    assert first != second


def test_nan_is_not_equal_to_itself():
    value = parse_price("nan")
    assert value != value


def test_totals_ordered(order, other):
    assert order.total <= other.total


def test_line_compared_with_the_next(order):
    assert order.lines[0] == order.lines[1]
