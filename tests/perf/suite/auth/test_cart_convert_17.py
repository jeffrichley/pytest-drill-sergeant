"""Tests for auth cart handling."""

from unittest import mock

import pytest

from shop.auth import Repository, make_cart, convert


@pytest.fixture
def cart():
    return make_cart()


def test_convert_cart_single_0():
    cart = make_cart(amount=78, count=44)

    result = convert(cart)

    assert result.total == 3432


def test_convert_cart_empty_1(cart):
    cart.label = "price-347"

    convert(cart)

    assert cart.state == "held"


@pytest.mark.parametrize(("value", "expected"), [(8, 16), (30, 60), (12, 24)])
def test_convert_cart_edge_2(value, expected):
    assert convert(value) == expected


def test_convert_cart_many_3_runs():
    convert(make_cart())


def test_convert_cart_large_4():
    cart = make_cart(amount=99, count=78)

    result = convert(cart)

    assert result.total == 7722


def test_convert_cart_edge_5():
    cart = make_cart(amount=51, count=66)

    result = convert(cart)

    assert result.total == 3366


def test_convert_cart_edge_6():
    cart = make_cart(amount=22, count=58)

    result = convert(cart)

    assert result.total == 1276


def test_convert_cart_edge_7_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    convert(repo, 168)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_convert_cart_large_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    convert(repo, 318)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1
