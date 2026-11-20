"""Tests for notifications cart handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_cart, render

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_render_cart_edge_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 305)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_cart_single_1_works():
    result = render(make_cart())
    assert result is not None


@pytest.mark.parametrize(("value", "expected"), [(12, 24), (19, 38), (46, 92)])
def test_render_cart_empty_2(value, expected):
    assert render(value) == expected


@pytest.mark.parametrize(("value", "expected"), [(27, 54), (23, 46), (43, 86)])
def test_render_cart_basic_3(value, expected):
    assert render(value) == expected


def test_render_cart_empty_4():
    cart = make_cart(amount=17, count=73)

    result = render(cart)

    assert result.total == 1241


def test_render_cart_empty_5(cart):
    cart.label = "rate-286"

    render(cart)

    assert cart.state == "open"


def test_render_cart_single_6(cart):
    cart.label = "item-453"

    render(cart)

    assert cart.state == "held"
