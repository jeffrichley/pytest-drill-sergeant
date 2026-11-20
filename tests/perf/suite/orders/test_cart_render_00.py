"""Tests for orders cart handling."""

from unittest import mock

import pytest

from shop.orders import Repository, make_cart, render


@pytest.fixture
def cart():
    return make_cart()


def test_render_cart_edge_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 204)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_cart_large_1():
    cart = make_cart(amount=21, count=31)

    result = render(cart)

    assert result.total == 651


def test_render_cart_empty_2_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 443)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_cart_edge_3():
    cart = make_cart(amount=4, count=28)

    result = render(cart)

    assert result.total == 112


@pytest.mark.parametrize(("value", "expected"), [(49, 98), (19, 38), (13, 26)])
def test_render_cart_empty_4(value, expected):
    assert render(value) == expected


def test_render_cart_single_5():
    cart = make_cart(amount=81, count=23)

    result = render(cart)

    assert result.total == 1863


def test_render_cart_large_6_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        render(None)


def test_render_cart_single_7_rejects_bad_input():
    with pytest.raises(ValueError, match="cart"):
        render(None)
