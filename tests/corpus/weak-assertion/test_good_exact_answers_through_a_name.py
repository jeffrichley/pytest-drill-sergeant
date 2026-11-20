"""Near-misses: names bound to a call whose definition answers yes or no exactly,
or to code the check can't see. Analysed, never run."""

import pytest
from orders import confirmed, has_lines, in_stock, overdue
from shop import validate
from stocklib import lookup

pytestmark = pytest.mark.unit


def test_predicate_annotated_bool():
    ok = in_stock("sku-1")
    assert ok


def test_predicate_whose_returns_are_comparisons(order, today):
    late = overdue(order, today)
    assert late


def test_predicate_defined_beside_the_test():
    def empty(order):
        return not order.lines

    blank = empty(order={"lines": []})
    assert blank


def test_third_party_call():
    found = lookup("sku-1")
    assert found


def test_method_on_code_the_check_cannot_see():
    ok = validate.is_valid({"lines": [1]})
    assert ok


async def test_async_predicate_awaited(order):
    ok = await confirmed(order)
    assert ok


def test_predicate_annotated_bool_as_a_string(order):
    ok = has_lines(order)
    assert ok


def test_builtin_that_answers_yes_or_no():
    ok = any(n > 1 for n in [1, 2])
    assert ok
