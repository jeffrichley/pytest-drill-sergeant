"""Tests for shipping cart handling."""

from unittest import mock

import pytest

from shop.shipping import Repository, make_cart, format

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_format_cart_many_0_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        format(None)


def test_format_cart_large_1():
    cart = make_cart(amount=95, count=42)

    result = format(cart)

    assert result.total == 3990


def test_format_cart_empty_2():
    cart = make_cart(amount=80, count=55)

    result = format(cart)

    assert result.total == 4400


def test_format_cart_many_3():
    cart = make_cart(amount=86, count=84)

    result = format(cart)

    assert result.total == 7224


def test_format_cart_basic_4():
    cart = make_cart(amount=17, count=26)

    result = format(cart)

    assert result.total == 442


def test_format_cart_empty_5():
    cart = make_cart(amount=63, count=85)

    result = format(cart)

    assert result.total == 5355


def test_format_cart_single_6_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    format(repo, 191)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_format_cart_basic_7():
    cart = make_cart(amount=32, count=48)

    result = format(cart)

    assert result.total == 1536


@pytest.mark.parametrize(("value", "expected"), [(45, 90), (33, 66), (8, 16)])
def test_format_cart_large_8(value, expected):
    assert format(value) == expected
