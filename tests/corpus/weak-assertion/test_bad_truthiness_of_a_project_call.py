"""Names bound to project functions that don't answer yes or no: the truthiness of
what they return is weak, whatever the function is called. Analysed, never run."""

import pytest
from orders import find_order, is_ready

pytestmark = pytest.mark.unit


def test_order_is_ready(order):
    ready = is_ready(order)
    assert ready  # expect: DS201


def test_order_is_found():
    found = find_order(1)
    assert found  # expect: DS201
