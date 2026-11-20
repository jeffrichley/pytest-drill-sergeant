"""Near-misses: the assertion is in a helper the file defines, at any depth. Modelled
on networkx's `_augment_and_check` and bookwright's `_assert_contrast`, whose leading
`_` the `assert*` name rule doesn't see. Analysed, never run."""

from functools import partial

import pytest
from shop import countdown

pytestmark = pytest.mark.unit


def _check_total(cart, expected):
    assert cart.total() == expected


def _checked_twice(cart):
    _check_total_again(cart)


def _check_total_again(cart):
    _check_total(cart, 3)


def _count_down(n):
    if n:
        _count_up(n - 1)


def _count_up(n):
    _count_down(n)
    assert countdown(n) == []


_check_three = partial(_check_total, expected=3)


def test_a_helper_that_asserts_is_an_assertion(cart):
    _check_total(cart, 3)


def test_a_helper_two_calls_down_is_an_assertion(cart):
    _checked_twice(cart)


def test_helpers_calling_each_other_reach_their_assertion():
    _count_down(3)


def test_the_other_end_of_the_cycle_reaches_it_too():
    _count_up(3)


def test_a_module_level_partial_of_a_helper_is_an_assertion(cart):
    _check_three(cart)


def test_a_local_partial_of_a_helper_is_an_assertion(cart):
    check = partial(_check_total, expected=3)
    check(cart)
