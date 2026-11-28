"""Near-misses: comparisons of an expression with itself that test the code. `==`
and `!=` call `__eq__`, which may be what is under test (networkx
`utils/tests/test_config.py:85`, `cfg == cfg`; pandas `tests/test_flags.py:11`,
`a == a`), and an attribute or call on both sides reads a property or calls code
twice (pandas `tests/generic/test_generic.py:487`, `obj.flags is obj.flags`).
`x == x` on a bare name has its own check, not this one. Analysed, never run."""

import pytest
from shop import Config, make_order

pytestmark = pytest.mark.unit


def test_config_equals_itself():
    cfg = Config(x=2, y="bar")
    assert cfg == cfg
    assert cfg != Config(x=3, y="baz")


def test_flags_equal_themselves():
    a = make_order(lines=[1000]).flags
    b = make_order(lines=[2000]).flags
    assert a == a
    assert not a != a
    assert a != b


def test_flags_are_cached(frame):
    obj = frame.copy()
    assert obj.flags is obj.flags
    other = obj.copy()
    assert other.flags is not obj.flags


def test_total_compared_with_itself(order):
    assert order.total == order.total
    assert order.lines[0] >= order.lines[0]


def test_same_call_twice(order):
    assert order.snapshot() is order.snapshot()
