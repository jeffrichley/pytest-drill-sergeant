"""Tests for notifications cart handling."""

from unittest import mock

import pytest

from shop.notifications import Repository, make_cart, render

pytestmark = pytest.mark.unit


@pytest.fixture
def cart():
    return make_cart()


def test_render_cart_basic_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 73)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


@pytest.mark.parametrize(("value", "expected"), [(2, 4), (7, 14), (1, 2)])
def test_render_cart_single_1(value, expected):
    assert render(value) == expected


def test_render_cart_edge_2():
    cart = make_cart(amount=19, count=46)

    result = render(cart)

    assert result.total == 874


def test_render_cart_basic_3():
    cart = make_cart(amount=55, count=43)

    result = render(cart)

    assert result.total == 2365
