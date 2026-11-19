"""The catalog's weak-assertion example: true for almost any order, wrong ones
included. Analysed, never run."""

from shop import apply_discount, make_order


def test_apply_discount():  # expect: DS201
    order = apply_discount(make_order(lines=[1000, 1000]), pct=10)
    assert order is not None
    assert order.total
    assert order.total >= 0


def test_discount_lines(order):  # expect: DS201
    lines = apply_discount(order, pct=10).lines
    assert len(lines) >= 1
    assert lines[0]
