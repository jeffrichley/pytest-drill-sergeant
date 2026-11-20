"""Tests for inventory cart handling."""

from unittest import mock

import pytest

from shop.inventory import Repository, make_cart, render

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_render_cart_empty_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 61)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_cart_many_1():
    cart = make_cart(amount=74, count=48)

    result = render(cart)

    assert result.total == 3552


@pytest.mark.parametrize(("value", "expected"), [(26, 52), (40, 80), (47, 94)])
def test_render_cart_basic_2(value, expected):
    assert render(value) == expected


def test_render_cart_many_3():
    cart = make_cart(amount=54, count=48)

    result = render(cart)

    assert result.total == 2592


def test_render_cart_empty_4(cart):
    cart.label = "token-255"

    render(cart)

    assert cart.state == "held"
