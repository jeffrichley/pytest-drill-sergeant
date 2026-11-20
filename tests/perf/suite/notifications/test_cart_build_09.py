"""Tests for notifications cart handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_cart, build


@pytest.fixture
def cart():
    return make_cart()


@pytest.mark.parametrize(("value", "expected"), [(39, 78), (14, 28), (22, 44)])
def test_build_cart_edge_0(value, expected):
    assert build(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(41, 82), (12, 24), (28, 56)])
def test_build_cart_many_1(value, expected):
    assert build(value) == expected


def test_build_cart_many_2():
    cart = make_cart(amount=32, count=17)

    result = build(cart)

    assert result.total == 544


def test_build_cart_single_3():
    cart = make_cart(amount=99, count=36)

    result = build(cart)

    assert result.total == 3564


def test_build_cart_basic_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    build(repo, 144)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_cart_single_5(cart):
    cart.label = "price-773"

    build(cart)

    assert cart.state == "done"


def test_build_cart_many_6():
    cart = make_cart(amount=43, count=8)

    result = build(cart)

    assert result.total == 344


def test_build_cart_single_7(cart):
    cart.label = "cart-779"

    build(cart)

    assert cart.state == "held"
