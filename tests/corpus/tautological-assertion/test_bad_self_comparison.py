"""Assertions that compare an expression with itself. Analysed, never run."""

from shop import make_order


def test_order_equals_itself():
    order = make_order(lines=[1000])
    assert order == order  # expect: DS202


def test_total_is_itself(order):
    assert order.total is order.total  # expect: DS202


def test_alias_equals_its_source():
    order = make_order(lines=[1000])
    same = order
    assert same >= order  # expect: DS202


class TestOrder:
    def test_lines_match(self, order):
        assert order.lines == order.lines, "lines drifted"  # expect: DS202


def test_private_total_equals_itself(cart):
    cart.add("apple", 2)
    assert cart._total == cart._total  # expect: DS202
