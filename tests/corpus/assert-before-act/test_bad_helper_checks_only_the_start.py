"""The only assertions are in helpers that check the starting state, called before
the act: a helper that asserts is an assertion, so no act comes before the last one.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def _check_empty(cart):
    assert cart.items == []


def test_add_after_a_helper_checks_the_start(cart):
    _check_empty(cart)
    cart.add("apple")  # expect: DS103


def test_add_after_a_nested_helper_checks_the_start(cart):
    def check_empty():
        assert cart.items == []

    check_empty()
    cart.add("apple")  # expect: DS103
