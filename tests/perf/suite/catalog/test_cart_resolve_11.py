"""Tests for catalog cart handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_cart, resolve

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_resolve_cart_large_0(cart):
    cart.label = "order-809"

    resolve(cart)

    assert cart.state == "done"


def test_resolve_cart_empty_1():
    cart = make_cart(amount=56, count=91)

    result = resolve(cart)

    assert result.total == 5096


def test_resolve_cart_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    resolve(repo, 228)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_resolve_cart_empty_3(cart):
    cart.label = "event-817"

    resolve(cart)

    assert cart.state == "held"


def test_resolve_cart_empty_4_works():
    result = resolve(make_cart())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(42, 84), (45, 90), (28, 56)])
def test_resolve_cart_empty_5(value, expected):
    assert resolve(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(11, 22), (2, 4), (25, 50)])
def test_resolve_cart_edge_6(value, expected):
    assert resolve(value) == expected


def test_resolve_cart_single_7_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        resolve(None)


def test_resolve_cart_single_8():
    cart = make_cart(amount=54, count=17)

    result = resolve(cart)

    assert result.total == 918
