"""Tests for orders cart handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_cart, load

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_load_cart_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    load(repo, 130)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_cart_single_1():
    cart = make_cart(amount=45, count=80)

    result = load(cart)

    assert result.total == 3600


def test_load_cart_single_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    load(repo, 304)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_load_cart_large_3(cart):
    cart.label = "price-622"

    load(cart)

    assert cart.state == "open"


def test_load_cart_single_4(cart):
    cart.label = "address-347"

    load(cart)

    assert cart.state == "held"


def test_load_cart_edge_5(cart):
    cart.label = "user-994"

    load(cart)

    assert cart.state == "open"


def test_load_cart_basic_6():
    cart = make_cart(amount=75, count=59)

    result = load(cart)

    assert result.total == 4425


def test_load_cart_basic_7(cart):
    cart.label = "price-440"

    load(cart)

    assert cart.state == "open"


def test_load_cart_single_8():
    cart = make_cart(amount=22, count=25)

    result = load(cart)

    assert result.total == 550
