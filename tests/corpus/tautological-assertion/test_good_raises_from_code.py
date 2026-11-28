"""Near-misses: `pytest.raises` blocks where something other than the test's own
`raise` of the expected exception decides the outcome. Analysed, never run."""

import pytest
from shop import OutOfStock, SoldOut, reserve

pytestmark = pytest.mark.unit


def test_raises_a_different_exception():
    # Passes only if `SoldOut` is a subclass of `OutOfStock`: a fact about the code.
    with pytest.raises(OutOfStock):
        raise SoldOut


def test_block_also_calls_code():
    with pytest.raises(OutOfStock):
        reserve("apple", 3)
        raise OutOfStock


def test_raise_under_a_branch(stock):
    with pytest.raises(OutOfStock):
        if reserve("apple", stock) is None:
            raise OutOfStock


def test_raise_checked_against_its_message():
    # pandas `tests/test_errors.py:80`: `match=` checks the message the
    # exception's class builds from its arguments.
    with pytest.raises(OutOfStock, match="apple is sold out"):
        raise OutOfStock("apple", 0)


def test_raise_checked_through_what_it_caught():
    with pytest.raises(OutOfStock) as caught:
        raise OutOfStock("apple", 0)
    assert caught.value.item == "apple"
