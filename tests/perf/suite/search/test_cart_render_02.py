"""Tests for search cart handling."""

from unittest import mock

import pytest

from shop.search import Repository, make_cart, render


@pytest.fixture
def cart():
    return make_cart()


def test_render_cart_large_0_saves():
    repo = mock.create_autospec(Repository, instance=True)
    repo.get.return_value = make_cart()

    render(repo, 214)

    repo.save.assert_called_once()
    assert repo.get.call_count == 1


def test_render_cart_large_1():
    cart = make_cart(amount=91, count=12)

    result = render(cart)

    assert result.total == 1092


def test_render_cart_many_2():
    cart = make_cart(amount=31, count=44)

    result = render(cart)

    assert result.total == 1364


def test_render_cart_single_3():
    cart = make_cart(amount=57, count=75)

    result = render(cart)

    assert result.total == 4275
