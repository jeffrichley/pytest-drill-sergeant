"""Tests for inventory cart handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_cart, build


@pytest.fixture
def cart():
    return make_cart()


def test_build_cart_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    build(repo, 238)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_cart_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    build(repo, 130)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_build_cart_many_2(cart):
    cart.label = "price-982"

    build(cart)

    assert cart.state == "done"


@pytest.mark.parametrize(("value", "expected"), [(33, 66), (28, 56), (37, 74)])
def test_build_cart_edge_3(value, expected):
    assert build(value) == expected


def test_build_cart_single_4():
    cart = make_cart(amount=59, count=5)

    result = build(cart)

    assert result.total == 295
