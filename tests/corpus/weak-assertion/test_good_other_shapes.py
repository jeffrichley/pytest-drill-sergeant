"""Near-misses: shapes DS201 leaves alone. Analysed, never run."""

import pytest
from shop import make_order, render

pytestmark = pytest.mark.unit


def test_membership_is_not_weak():
    assert "Total: 10.00" in render(make_order(lines=[1000]))


def test_assertion_in_a_helper():
    def check(order):
        assert order.total == 1000

    check(make_order(lines=[1000]))


def test_assert_false_is_a_deliberate_failure():
    order = make_order(lines=[1000])
    assert order is not None
    if order.total != 1000:
        assert False, "wrong total"
