"""Near-misses: one act, then several assertions, reading results in between.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_get_user(client):
    response = client.get("/users/1")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ada"


def test_setup_calls_before_the_act(cart):
    cart.add("apple")
    cart.add("pear")
    cart.checkout()
    assert cart.items == []
    assert cart.orders == 1


def test_acts_inside_the_asserts(parser):
    assert parser.parse("1") == 1
    assert parser.parse("2") == 2
