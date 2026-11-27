"""Near-misses: the same call on both sides where the call is a constructor, by
its definition or as a builtin type, or is code the check can't see, so nothing
says it is the code under test. Analysed, never run."""

import pytest
from shop import Money
from stocklib import fetch_price

pytestmark = pytest.mark.unit


def test_project_class_constructed_on_both_sides():
    assert Money(100) == Money(100)


def test_builtin_type_on_both_sides(order_id):
    assert str(order_id) == str(order_id)


def test_third_party_call_on_both_sides():
    assert fetch_price("sku-1") == fetch_price("sku-1")


def test_method_of_a_fixture_on_both_sides(client):
    assert client.get("/") == client.get("/")


def test_lowercase_class_defined_beside_the_test():
    class point:
        def __init__(self, x):
            self.x = x

        def __eq__(self, other):
            return self.x == other.x

    assert point(1) == point(1)
