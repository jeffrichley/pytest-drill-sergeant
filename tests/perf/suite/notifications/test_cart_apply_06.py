"""Tests for notifications cart handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_cart, apply

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_apply_cart_many_0():
    cart = make_cart(amount=36, count=43)

    result = apply(cart)

    assert result.total == 1548


def test_apply_cart_empty_1_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        apply(None)


def test_apply_cart_edge_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    apply(repo, 135)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_apply_cart_basic_3_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        apply(None)


def test_apply_cart_large_4():
    cart = make_cart(amount=12, count=67)

    result = apply(cart)

    assert result.total == 804


def test_apply_cart_empty_5_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        apply(None)


@pytest.mark.parametrize(("value", "expected"), [(19, 38), (11, 22), (17, 34)])
def test_apply_cart_single_6(value, expected):
    assert apply(value) == expected
