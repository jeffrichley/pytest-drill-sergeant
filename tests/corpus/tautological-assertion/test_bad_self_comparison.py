"""Assertions that ask whether a bare name is itself, as pandas
`tests/series/methods/test_copy.py:71` does (`assert datetime_series is
datetime_series`): identity can't be overridden, so `x is x` holds whatever the
code did. Analysed, never run."""

import pytest
from shop import make_order

pytestmark = pytest.mark.unit


def test_order_is_itself():
    order = make_order(lines=[1000])
    assert order is order  # expect: DS202


def test_fixture_is_itself(order):
    order.lines.clear()
    assert order is order  # expect: DS202


def test_alias_is_its_source():
    order = make_order(lines=[1000])
    same = order
    assert same is order  # expect: DS202


def test_alias_of_a_result_is_the_result(render):
    # The pandas `test_info.py:237` shape with no rebinding between: `expected`
    # still names what `result` names.
    result = render(columns=101)
    expected = result
    assert result is expected  # expect: DS202


class TestOrder:
    def test_lines_are_themselves(self, order):
        lines = order.lines
        assert lines is lines, "lines drifted"  # expect: DS202
