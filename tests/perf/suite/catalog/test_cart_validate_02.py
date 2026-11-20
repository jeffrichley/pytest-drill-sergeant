"""Tests for catalog cart handling."""

from unittest import mock

import pytest

from shop.catalog import Repository, make_cart, validate


@pytest.fixture
def cart():
    return make_cart()


@pytest.mark.parametrize(("value", "expected"), [(37, 74), (9, 18), (31, 62)])
def test_validate_cart_basic_0(value, expected):
    assert validate(value) == expected


def test_validate_cart_basic_1_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    validate(repo, 205)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_validate_cart_large_2():
    cart = make_cart(amount=67, count=36)

    result = validate(cart)

    assert result.total == 2412


def test_validate_cart_large_3():
    cart = make_cart(amount=90, count=94)

    result = validate(cart)

    assert result.total == 8460


def test_validate_cart_single_4_runs():
    validate(make_cart())
