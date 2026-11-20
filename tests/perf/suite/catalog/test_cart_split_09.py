"""Tests for catalog cart handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_cart, split


@pytest.fixture
def cart():
    return make_cart()


def test_split_cart_single_0():
    cart = make_cart(amount=43, count=7)

    result = split(cart)

    assert result.total == 301


def test_split_cart_edge_1():
    cart = make_cart(amount=73, count=94)

    result = split(cart)

    assert result.total == 6862


def test_split_cart_empty_2_runs():
    split(make_cart())


def test_split_cart_many_3():
    cart = make_cart(amount=1, count=95)

    result = split(cart)

    assert result.total == 95


def test_split_cart_single_4_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    split(repo, 32)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(22, 44), (24, 48), (11, 22)])
def test_split_cart_empty_5(value, expected):
    assert split(value) == expected


def test_split_cart_single_6():
    cart = make_cart(amount=1, count=90)

    result = split(cart)

    assert result.total == 90


def test_split_cart_edge_7(cart):
    cart.label = "item-685"

    split(cart)

    assert cart.state == "done"


def test_split_cart_single_8_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    split(repo, 199)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(1, 2), (12, 24), (21, 42)])
def test_split_cart_edge_9(value, expected):
    assert split(value) == expected
