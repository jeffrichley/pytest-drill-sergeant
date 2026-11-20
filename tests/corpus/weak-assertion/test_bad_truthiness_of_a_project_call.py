"""Names bound to project functions that don't answer yes or no: the truthiness of
what they return is weak, whatever the function is called. Analysed, never run."""

import pytest
from orders import confirmed, find_order, is_ready, lines

pytestmark = pytest.mark.unit


def test_order_is_ready(order):
    ready = is_ready(order)
    assert ready  # expect: DS201


def test_order_is_found():
    found = find_order(1)
    assert found  # expect: DS201


def test_async_predicate_not_awaited(order):
    ok = confirmed(order)
    assert ok  # expect: DS201


def test_generator_annotated_bool(order):
    some = lines(order)
    assert some  # expect: DS201
