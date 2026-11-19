"""Near-misses: shapes DS201 leaves alone. Analysed, never run."""

from shop import make_order, render


def test_membership_is_not_weak():
    assert "Total: 10.00" in render(make_order(lines=[1000]))


def test_assertion_in_a_helper():
    def check(order):
        assert order.total == 1000

    check(make_order(lines=[1000]))


def test_strong_assertion_inside_a_branch_still_counts():
    order = make_order(lines=[1000])
    if order.total:
        assert order.total == 1000
    assert order is not None
